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
