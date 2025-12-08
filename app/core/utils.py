"""
Utility functions for Crystal System
"""
from datetime import datetime, timedelta
from typing import Optional
import pytz


SHANGHAI_TZ = pytz.timezone("Asia/Shanghai")


def get_shanghai_now() -> datetime:
    """Get current time in Shanghai timezone."""
    return datetime.now(SHANGHAI_TZ)


def get_yesterday_range() -> tuple[datetime, datetime]:
    """
    Get yesterday's date range (00:00:00 - 23:59:59) in Shanghai timezone.
    Used for daily settlement job.
    """
    now = get_shanghai_now()
    yesterday = now - timedelta(days=1)
    start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


def get_date_range(from_date: Optional[str], to_date: Optional[str]) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    Parse date range from string to datetime.
    Format: YYYY-MM-DD
    """
    start = None
    end = None
    
    if from_date:
        try:
            start = datetime.strptime(from_date, "%Y-%m-%d")
            start = SHANGHAI_TZ.localize(start)
        except ValueError:
            pass
    
    if to_date:
        try:
            end = datetime.strptime(to_date, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
            end = SHANGHAI_TZ.localize(end)
        except ValueError:
            pass
    
    return start, end


def format_date(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to YYYY-MM-DD string."""
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d")


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
