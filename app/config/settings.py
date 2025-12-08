"""
Crystal System Configuration
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "Crystal"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOG_DIR: Path = BASE_DIR / "logs"
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'crystal.db'}"
    
    # API
    API_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Scheduler
    SCHEDULER_TIMEZONE: str = "Asia/Shanghai"
    DAILY_JOB_HOUR: int = 6
    DAILY_JOB_MINUTE: int = 0
    
    # Playwright
    HEADLESS: bool = True
    BROWSER_TIMEOUT: int = 30000  # 30 seconds
    
    # Platform-specific settings
    WEIBO_BASE_URL: str = "https://weibo.com"
    ZHIHU_BASE_URL: str = "https://www.zhihu.com"
    XUEQIU_BASE_URL: str = "https://xueqiu.com"
    
    # Manual Login
    MANUAL_LOGIN_TIMEOUT: int = 120  # seconds
    MANUAL_LOGIN_POLL_INTERVAL: int = 2  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()


# Beijing timezone utility
from datetime import timezone, timedelta

BEIJING_TZ = timezone(timedelta(hours=8))


def beijing_now():
    """Get current time in Beijing timezone."""
    from datetime import datetime
    return datetime.now(BEIJING_TZ)
