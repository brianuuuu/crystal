"""
Public API Router - Health Check and Snapshot Endpoints
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.core.schemas import HealthResponse, SnapshotResponse, SentimentItemResponse
from app.core.utils import get_date_range
from app.storage.database import get_db
from app.storage.repositories import SentimentRepository


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow()
    )


@router.get("/snapshot", response_model=SnapshotResponse)
async def get_snapshot(
    symbol: Optional[str] = Query(None, description="Stock symbol filter"),
    platform: Optional[str] = Query(None, description="Platform filter: weibo/zhihu/xueqiu"),
    from_date: Optional[str] = Query(None, alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, alias="to", description="End date (YYYY-MM-DD)"),
    keyword: Optional[str] = Query(None, description="Keyword search in content/author/topic"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get sentiment snapshot with filters.
    
    This is the main API for external services to query sentiment data.
    """
    # Parse date range
    start_date, end_date = get_date_range(from_date, to_date)
    
    # Query repository
    repo = SentimentRepository(db)
    items, total = repo.get_by_filters(
        platform=platform,
        symbol=symbol,
        from_date=start_date,
        to_date=end_date,
        keyword=keyword,
        page=page,
        page_size=page_size
    )
    
    # Convert to response model
    response_items = [
        SentimentItemResponse.model_validate(item)
        for item in items
    ]
    
    return SnapshotResponse(
        items=response_items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/crawl")
async def trigger_crawl(
    platform: str = Query(..., description="Platform to crawl: weibo/zhihu/xueqiu/all"),
    db: Session = Depends(get_db)
):
    """
    Manually trigger crawling for a platform.
    Crawls data from today 00:00 to current time.
    """
    from datetime import timedelta
    from app.config.settings import beijing_now, BEIJING_TZ
    from app.crawler import WeiboCrawler, ZhihuCrawler, XueqiuCrawler
    from app.storage.repositories import WatchTargetRepository, SentimentRepository, AccountRepository
    from app.core.models import LoginStatus
    from loguru import logger
    
    # Get today's date range (Beijing time)
    now = beijing_now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Validate platform
    valid_platforms = ["weibo", "zhihu", "xueqiu", "all"]
    if platform not in valid_platforms:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid platform. Must be one of: {valid_platforms}")
    
    # Get platforms to crawl
    platforms_to_crawl = [platform] if platform != "all" else ["weibo", "zhihu", "xueqiu"]
    
    # Crawler mapping
    crawler_classes = {
        "weibo": WeiboCrawler,
        "zhihu": ZhihuCrawler,
        "xueqiu": XueqiuCrawler,
    }
    
    account_repo = AccountRepository(db)
    target_repo = WatchTargetRepository(db)
    sentiment_repo = SentimentRepository(db)
    
    results = {}
    total_items = 0
    
    for plat in platforms_to_crawl:
        logger.info(f"Starting crawl for {plat}")
        
        # Get active account with cookies
        account = account_repo.get_active_by_platform(plat)
        if not account or not account.cookies:
            results[plat] = {"success": False, "error": "No active account with cookies"}
            continue
        
        # Get watch targets for this platform
        targets = target_repo.get_by_platform(plat)
        
        # Initialize crawler
        crawler_class = crawler_classes.get(plat)
        if not crawler_class:
            results[plat] = {"success": False, "error": "Crawler not found"}
            continue
        
        crawler = crawler_class(cookies=account.cookies)
        
        # Fetch data
        platform_items = []
        try:
            # For Xueqiu/Zhihu/Weibo: if no watch targets, use following feed
            if plat == "xueqiu" and not targets:
                logger.info("Xueqiu: using following feed (no watch targets)")
                items = await crawler.fetch_following_feed(today_start, now)
                platform_items.extend(items)
            elif plat == "zhihu" and not targets:
                logger.info("Zhihu: using following feed (no watch targets)")
                items = await crawler.fetch_following_feed(today_start, now)
                platform_items.extend(items)
            elif plat == "weibo" and not targets:
                logger.info("Weibo: using following feed (no watch targets)")
                items = await crawler.fetch_following_feed(today_start, now)
                platform_items.extend(items)
            elif not targets:
                results[plat] = {"success": False, "error": "No watch targets configured"}
                continue
            else:
                # Fetch from configured targets
                for target in targets:
                    items = await crawler.fetch(target, today_start, now)
                    platform_items.extend(items)
            
            # Save to database (with deduplication)
            created_count = sentiment_repo.bulk_create(platform_items)
            total_items += created_count
            
            results[plat] = {
                "success": True,
                "targets": len(targets),
                "fetched": len(platform_items),
                "saved": created_count
            }
            logger.info(f"Crawl complete for {plat}: fetched {len(platform_items)}, saved {created_count}")
            
        except Exception as e:
            logger.error(f"Crawl error for {plat}: {e}")
            results[plat] = {"success": False, "error": str(e)}
    
    return {
        "message": "Crawl completed",
        "date_range": {
            "from": today_start.isoformat(),
            "to": now.isoformat()
        },
        "results": results,
        "total_saved": total_items
    }
