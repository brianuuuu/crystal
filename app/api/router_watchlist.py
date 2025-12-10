"""
Watchlist API Router - CRUD endpoints for watch targets.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.storage.database import get_db
from app.storage.repositories import WatchTargetRepository
from app.core.schemas import WatchTargetCreate, WatchTargetResponse

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchTargetUpdate(BaseModel):
    """Update watch target request."""
    display_name: Optional[str] = None
    external_id: Optional[str] = None
    symbol: Optional[str] = None
    keyword: Optional[str] = None
    enabled: Optional[bool] = None


@router.get("", response_model=List[WatchTargetResponse])
async def list_watch_targets(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    db: Session = Depends(get_db)
):
    """
    List all watch targets, optionally filtered by platform.
    """
    repo = WatchTargetRepository(db)
    
    if platform:
        targets = repo.get_by_platform(platform)
    else:
        targets = repo.get_all_enabled()
    
    return targets


@router.get("/all")
async def list_all_watch_targets(db: Session = Depends(get_db)):
    """
    List all watch targets grouped by platform.
    """
    from app.core.models import WatchTarget
    
    targets = db.query(WatchTarget).all()
    
    # Group by platform
    grouped = {}
    for t in targets:
        if t.platform not in grouped:
            grouped[t.platform] = []
        grouped[t.platform].append({
            "id": t.id,
            "platform": t.platform,
            "target_type": t.target_type,
            "external_id": t.external_id,
            "symbol": t.symbol,
            "keyword": t.keyword,
            "display_name": t.display_name,
            "enabled": t.enabled,
        })
    
    return grouped


@router.get("/{target_id}", response_model=WatchTargetResponse)
async def get_watch_target(
    target_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific watch target by ID.
    """
    repo = WatchTargetRepository(db)
    target = repo.get_by_id(target_id)
    
    if not target:
        raise HTTPException(status_code=404, detail="Watch target not found")
    
    return target


@router.post("", response_model=WatchTargetResponse)
async def create_watch_target(
    request: WatchTargetCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new watch target.
    """
    repo = WatchTargetRepository(db)
    
    target = repo.create(
        platform=request.platform,
        target_type=request.target_type,
        external_id=request.external_id,
        symbol=request.symbol,
        keyword=request.keyword,
        display_name=request.display_name,
    )
    
    return target


@router.put("/{target_id}", response_model=WatchTargetResponse)
async def update_watch_target(
    target_id: int,
    request: WatchTargetUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a watch target.
    """
    repo = WatchTargetRepository(db)
    
    target = repo.get_by_id(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Watch target not found")
    
    # Only update provided fields
    update_data = request.model_dump(exclude_unset=True)
    target = repo.update(target_id, **update_data)
    
    return target


@router.delete("/{target_id}")
async def delete_watch_target(
    target_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a watch target.
    """
    repo = WatchTargetRepository(db)
    
    target = repo.get_by_id(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Watch target not found")
    
    success = repo.delete(target_id)
    
    return {"success": success, "message": "Watch target deleted"}
