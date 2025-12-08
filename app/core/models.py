"""
SQLAlchemy ORM Models for Crystal System
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float, JSON,
    UniqueConstraint, Index, Enum as SQLEnum
)
from sqlalchemy.orm import DeclarativeBase
import enum


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Platform(str, enum.Enum):
    """Supported platforms."""
    WEIBO = "weibo"
    ZHIHU = "zhihu"
    XUEQIU = "xueqiu"


class LoginType(str, enum.Enum):
    """Login methods."""
    PASSWORD = "password"
    QRCODE = "qrcode"
    COOKIE = "cookie"


class LoginStatus(str, enum.Enum):
    """Account login status."""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


class TargetType(str, enum.Enum):
    """Watch target types."""
    ACCOUNT = "account"
    SYMBOL = "symbol"
    KEYWORD = "keyword"


class JobStatus(str, enum.Enum):
    """Daily job status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class PlatformAccount(Base):
    """Platform account management table."""
    __tablename__ = "platform_account"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(20), nullable=False, index=True)
    username = Column(String(100), nullable=False)
    login_type = Column(String(20), default=LoginType.COOKIE.value)
    login_status = Column(String(20), default=LoginStatus.OFFLINE.value)
    last_login_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    cookies = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('platform', 'username', name='uq_platform_username'),
    )


class WatchTarget(Base):
    """Watch target table for monitored accounts/symbols/keywords."""
    __tablename__ = "watch_target"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(20), nullable=False, index=True)
    target_type = Column(String(20), nullable=False)
    external_id = Column(String(100), nullable=True)  # uid / user id
    symbol = Column(String(20), nullable=True, index=True)  # Stock code
    keyword = Column(String(100), nullable=True)  # Keyword monitoring
    display_name = Column(String(100), nullable=False)  # UI display name
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_watch_target_platform_type', 'platform', 'target_type'),
    )


class SentimentItem(Base):
    """Sentiment record table for captured posts/comments."""
    __tablename__ = "sentiment_item"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(20), nullable=False, index=True)
    target_id = Column(Integer, nullable=True)  # Reference to watch_target
    symbol = Column(String(20), nullable=True, index=True)
    root_post_id = Column(String(100), nullable=True)  # Main post ID
    comment_id = Column(String(100), nullable=False)  # Comment ID (unique)
    author_id = Column(String(100), nullable=True)
    author_name = Column(String(100), nullable=True)
    content = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    posted_at = Column(DateTime, nullable=True, index=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    sentiment_score = Column(Float, nullable=True)  # Sentiment score
    heat_score = Column(Float, nullable=True)  # Heat/popularity score
    topic = Column(String(200), nullable=True)
    extra = Column(JSON, nullable=True)  # Extended JSON field
    
    __table_args__ = (
        UniqueConstraint('platform', 'comment_id', name='uq_platform_comment'),
        Index('ix_sentiment_platform_posted', 'platform', 'posted_at'),
        Index('ix_sentiment_symbol_posted', 'symbol', 'posted_at'),
    )


class DailyJobRun(Base):
    """Daily job execution log table."""
    __tablename__ = "daily_job_run"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD format
    platform = Column(String(20), nullable=False)  # all / weibo / zhihu / xueqiu
    status = Column(String(20), default=JobStatus.PENDING.value)
    total_targets = Column(Integer, default=0)
    total_items = Column(Integer, default=0)
    error_detail = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('date', 'platform', name='uq_date_platform'),
    )
