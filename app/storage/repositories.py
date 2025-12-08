"""
Data Repositories for CRUD Operations
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.models import (
    PlatformAccount, WatchTarget, SentimentItem, DailyJobRun,
    LoginStatus, JobStatus
)
from app.config.settings import beijing_now


class AccountRepository:
    """Repository for platform account operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[PlatformAccount]:
        """Get all accounts."""
        return self.db.query(PlatformAccount).all()
    
    def get_by_platform(self, platform: str) -> List[PlatformAccount]:
        """Get accounts by platform."""
        return self.db.query(PlatformAccount).filter(
            PlatformAccount.platform == platform
        ).all()
    
    def get_active_by_platform(self, platform: str) -> Optional[PlatformAccount]:
        """Get active online account for a platform."""
        return self.db.query(PlatformAccount).filter(
            and_(
                PlatformAccount.platform == platform,
                PlatformAccount.is_active == True,
                PlatformAccount.login_status == LoginStatus.ONLINE.value
            )
        ).first()
    
    def get_by_id(self, account_id: int) -> Optional[PlatformAccount]:
        """Get account by ID."""
        return self.db.query(PlatformAccount).filter(
            PlatformAccount.id == account_id
        ).first()
    
    def get_by_platform_username(self, platform: str, username: str) -> Optional[PlatformAccount]:
        """Get account by platform and username."""
        return self.db.query(PlatformAccount).filter(
            and_(
                PlatformAccount.platform == platform,
                PlatformAccount.username == username
            )
        ).first()
    
    def create(self, **kwargs) -> PlatformAccount:
        """Create new account."""
        account = PlatformAccount(**kwargs)
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account
    
    def update(self, account_id: int, **kwargs) -> Optional[PlatformAccount]:
        """Update account."""
        account = self.get_by_id(account_id)
        if account:
            for key, value in kwargs.items():
                setattr(account, key, value)
            account.updated_at = beijing_now()
            self.db.commit()
            self.db.refresh(account)
        return account
    
    def update_login_status(
        self, 
        account_id: int, 
        status: str, 
        cookies: dict = None,
        error: str = None
    ) -> Optional[PlatformAccount]:
        """Update login status and cookies."""
        update_data = {
            "login_status": status,
            "last_error": error,
        }
        if status == LoginStatus.ONLINE.value:
            update_data["last_login_at"] = beijing_now()
        if cookies is not None:
            update_data["cookies"] = cookies
        return self.update(account_id, **update_data)


class WatchTargetRepository:
    """Repository for watch target operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_enabled(self) -> List[WatchTarget]:
        """Get all enabled watch targets."""
        return self.db.query(WatchTarget).filter(
            WatchTarget.enabled == True
        ).all()
    
    def get_by_platform(self, platform: str) -> List[WatchTarget]:
        """Get enabled targets by platform."""
        return self.db.query(WatchTarget).filter(
            and_(
                WatchTarget.platform == platform,
                WatchTarget.enabled == True
            )
        ).all()
    
    def get_by_id(self, target_id: int) -> Optional[WatchTarget]:
        """Get target by ID."""
        return self.db.query(WatchTarget).filter(
            WatchTarget.id == target_id
        ).first()
    
    def create(self, **kwargs) -> WatchTarget:
        """Create new watch target."""
        target = WatchTarget(**kwargs)
        self.db.add(target)
        self.db.commit()
        self.db.refresh(target)
        return target
    
    def update(self, target_id: int, **kwargs) -> Optional[WatchTarget]:
        """Update watch target."""
        target = self.get_by_id(target_id)
        if target:
            for key, value in kwargs.items():
                setattr(target, key, value)
            target.updated_at = beijing_now()
            self.db.commit()
            self.db.refresh(target)
        return target
    
    def delete(self, target_id: int) -> bool:
        """Delete watch target."""
        target = self.get_by_id(target_id)
        if target:
            self.db.delete(target)
            self.db.commit()
            return True
        return False


class SentimentRepository:
    """Repository for sentiment item operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_filters(
        self,
        platform: Optional[str] = None,
        symbol: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[SentimentItem], int]:
        """Get sentiment items with filters and pagination."""
        query = self.db.query(SentimentItem)
        
        # Apply filters
        if platform:
            query = query.filter(SentimentItem.platform == platform)
        if symbol:
            query = query.filter(SentimentItem.symbol == symbol)
        if from_date:
            query = query.filter(SentimentItem.posted_at >= from_date)
        if to_date:
            query = query.filter(SentimentItem.posted_at <= to_date)
        if keyword:
            keyword_pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    SentimentItem.content.ilike(keyword_pattern),
                    SentimentItem.author_name.ilike(keyword_pattern),
                    SentimentItem.topic.ilike(keyword_pattern)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        items = query.order_by(SentimentItem.posted_at.desc())\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()
        
        return items, total
    
    def exists(self, platform: str, comment_id: str) -> bool:
        """Check if sentiment item already exists (for deduplication)."""
        return self.db.query(SentimentItem).filter(
            and_(
                SentimentItem.platform == platform,
                SentimentItem.comment_id == comment_id
            )
        ).first() is not None
    
    def create(self, **kwargs) -> SentimentItem:
        """Create new sentiment item."""
        item = SentimentItem(**kwargs)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
    
    def bulk_create(self, items: List[dict]) -> int:
        """Bulk create sentiment items with deduplication."""
        created_count = 0
        for item_data in items:
            if not self.exists(item_data.get("platform"), item_data.get("comment_id")):
                self.db.add(SentimentItem(**item_data))
                created_count += 1
        self.db.commit()
        return created_count


class JobRepository:
    """Repository for daily job run operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_date(self, date: str) -> List[DailyJobRun]:
        """Get all job runs for a date."""
        return self.db.query(DailyJobRun).filter(
            DailyJobRun.date == date
        ).all()
    
    def get_by_date_platform(self, date: str, platform: str) -> Optional[DailyJobRun]:
        """Get specific job run by date and platform."""
        return self.db.query(DailyJobRun).filter(
            and_(
                DailyJobRun.date == date,
                DailyJobRun.platform == platform
            )
        ).first()
    
    def create(self, date: str, platform: str) -> DailyJobRun:
        """Create new job run record."""
        job = DailyJobRun(
            date=date,
            platform=platform,
            status=JobStatus.PENDING.value,
            started_at=beijing_now()
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
    
    def update_status(
        self,
        job_id: int,
        status: str,
        total_targets: int = None,
        total_items: int = None,
        error_detail: str = None
    ) -> Optional[DailyJobRun]:
        """Update job status."""
        job = self.db.query(DailyJobRun).filter(DailyJobRun.id == job_id).first()
        if job:
            job.status = status
            if total_targets is not None:
                job.total_targets = total_targets
            if total_items is not None:
                job.total_items = total_items
            if error_detail is not None:
                job.error_detail = error_detail
            if status in [JobStatus.SUCCESS.value, JobStatus.FAILED.value, JobStatus.PARTIAL.value]:
                job.finished_at = beijing_now()
            self.db.commit()
            self.db.refresh(job)
        return job
    
    def get_recent(self, limit: int = 10) -> List[DailyJobRun]:
        """Get recent job runs."""
        return self.db.query(DailyJobRun)\
            .order_by(DailyJobRun.created_at.desc())\
            .limit(limit)\
            .all()
