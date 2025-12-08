"""
Pydantic Schemas for API Request/Response Validation
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ============== Platform Account ==============

class PlatformAccountResponse(BaseModel):
    """Platform account response."""
    id: int
    platform: str
    username: str
    login_type: str
    login_status: str
    last_login_at: Optional[datetime] = None
    last_error: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Login request body."""
    platform: str = Field(..., description="Platform: weibo/zhihu/xueqiu")
    username: str = Field(..., description="Account username")
    password: Optional[str] = Field(None, description="Account password")
    login_type: str = Field(default="password", description="Login type")


class AuthStatusResponse(BaseModel):
    """Auth status response."""
    accounts: List[PlatformAccountResponse]
    online_count: int
    offline_count: int


# ============== Watch Target ==============

class WatchTargetCreate(BaseModel):
    """Create watch target request."""
    platform: str
    target_type: str = Field(..., description="account/symbol/keyword")
    external_id: Optional[str] = None
    symbol: Optional[str] = None
    keyword: Optional[str] = None
    display_name: str


class WatchTargetResponse(BaseModel):
    """Watch target response."""
    id: int
    platform: str
    target_type: str
    external_id: Optional[str] = None
    symbol: Optional[str] = None
    keyword: Optional[str] = None
    display_name: str
    enabled: bool
    
    class Config:
        from_attributes = True


# ============== Sentiment Item ==============

class SentimentItemResponse(BaseModel):
    """Sentiment item response."""
    id: int
    platform: str
    symbol: Optional[str] = None
    author_name: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    posted_at: Optional[datetime] = None
    sentiment_score: Optional[float] = None
    heat_score: Optional[float] = None
    topic: Optional[str] = None
    
    class Config:
        from_attributes = True


class SnapshotRequest(BaseModel):
    """Snapshot query parameters."""
    symbol: Optional[str] = None
    platform: Optional[str] = None
    from_date: Optional[str] = Field(None, alias="from")
    to_date: Optional[str] = Field(None, alias="to")
    keyword: Optional[str] = None
    page: int = 1
    page_size: int = 50


class SnapshotResponse(BaseModel):
    """Snapshot response."""
    items: List[SentimentItemResponse]
    total: int
    page: int
    page_size: int


# ============== Daily Job ==============

class DailyJobRunResponse(BaseModel):
    """Daily job run response."""
    id: int
    date: str
    platform: str
    status: str
    total_targets: int
    total_items: int
    error_detail: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============== Health ==============

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
