"""
Scheduler Jobs - Daily Sentiment Collection Job
"""
import asyncio
from datetime import datetime
from typing import Optional
from loguru import logger

from app.config import settings
from app.core.models import Platform, JobStatus
from app.core.utils import get_yesterday_range, format_date
from app.storage.database import SessionLocal
from app.storage.repositories import (
    AccountRepository, WatchTargetRepository, SentimentRepository, JobRepository
)
from app.crawler import WeiboCrawler, ZhihuCrawler, XueqiuCrawler


async def run_daily_crystal_job(target_date: Optional[str] = None) -> dict:
    """
    Run daily sentiment collection job.
    
    Args:
        target_date: Optional date string (YYYY-MM-DD). If None, uses yesterday.
        
    Returns:
        Dict with job execution result
    """
    logger.info("=" * 50)
    logger.info("Starting daily crystal job")
    
    # Determine date range
    if target_date:
        from app.core.utils import get_date_range
        from_date, to_date = get_date_range(target_date, target_date)
        date_str = target_date
    else:
        from_date, to_date = get_yesterday_range()
        date_str = format_date(from_date)
    
    logger.info(f"Target date: {date_str}")
    logger.info(f"Date range: {from_date} to {to_date}")
    
    db = SessionLocal()
    
    try:
        job_repo = JobRepository(db)
        account_repo = AccountRepository(db)
        target_repo = WatchTargetRepository(db)
        sentiment_repo = SentimentRepository(db)
        
        # Create main job record
        main_job = job_repo.create(date_str, "all")
        job_repo.update_status(main_job.id, JobStatus.RUNNING.value)
        
        total_items = 0
        total_targets = 0
        errors = []
        
        # Process each platform
        platforms = [Platform.WEIBO, Platform.ZHIHU, Platform.XUEQIU]
        
        for platform in platforms:
            platform_name = platform.value
            logger.info(f"Processing platform: {platform_name}")
            
            # Create platform job record
            platform_job = job_repo.create(date_str, platform_name)
            job_repo.update_status(platform_job.id, JobStatus.RUNNING.value)
            
            try:
                # Get active account for platform
                account = account_repo.get_active_by_platform(platform_name)
                cookies = account.cookies if account else {}
                
                # Initialize crawler
                if platform == Platform.WEIBO:
                    crawler = WeiboCrawler(cookies)
                elif platform == Platform.ZHIHU:
                    crawler = ZhihuCrawler(cookies)
                else:
                    crawler = XueqiuCrawler(cookies)
                
                # Get targets for platform
                targets = target_repo.get_by_platform(platform_name)
                platform_items = 0
                
                for target in targets:
                    total_targets += 1
                    logger.info(f"  Fetching: {target.display_name}")
                    
                    try:
                        items = await crawler.fetch(target, from_date, to_date)
                        
                        # Bulk insert with deduplication
                        if items:
                            created = sentiment_repo.bulk_create(items)
                            platform_items += created
                            logger.info(f"    Created {created} items")
                            
                    except Exception as e:
                        logger.error(f"    Error: {e}")
                        errors.append(f"{platform_name}/{target.display_name}: {str(e)}")
                
                total_items += platform_items
                
                job_repo.update_status(
                    platform_job.id,
                    JobStatus.SUCCESS.value,
                    total_targets=len(targets),
                    total_items=platform_items
                )
                
            except Exception as e:
                logger.error(f"Platform {platform_name} error: {e}")
                errors.append(f"{platform_name}: {str(e)}")
                job_repo.update_status(
                    platform_job.id,
                    JobStatus.FAILED.value,
                    error_detail=str(e)
                )
        
        # Update main job
        final_status = JobStatus.SUCCESS.value if not errors else JobStatus.PARTIAL.value
        job_repo.update_status(
            main_job.id,
            final_status,
            total_targets=total_targets,
            total_items=total_items,
            error_detail="\n".join(errors) if errors else None
        )
        
        result = {
            "date": date_str,
            "status": final_status,
            "total_targets": total_targets,
            "total_items": total_items,
            "errors": errors,
        }
        
        logger.info(f"Daily job completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Daily job failed: {e}")
        raise
    finally:
        db.close()


def sync_run_daily_job(target_date: Optional[str] = None) -> dict:
    """Synchronous wrapper for daily job."""
    return asyncio.run(run_daily_crystal_job(target_date))
