"""
Base Crawler - Abstract Base Class for All Platform Crawlers
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger


class BaseCrawler(ABC):
    """Abstract base class for platform crawlers."""
    
    def __init__(self, cookies: Optional[Dict] = None):
        """
        Initialize crawler with optional cookies.
        
        Args:
            cookies: Dictionary of cookies for authentication
        """
        self.cookies = cookies or {}
        self.platform: str = "base"
    
    @abstractmethod
    async def fetch(
        self,
        target: Any,
        from_date: datetime,
        to_date: datetime
    ) -> List[Dict]:
        """
        Fetch sentiment items for a target within date range.
        
        Args:
            target: WatchTarget object
            from_date: Start of date range
            to_date: End of date range
            
        Returns:
            List of sentiment item dictionaries
        """
        pass
    
    @abstractmethod
    async def fetch_by_keyword(
        self,
        keyword: str,
        from_date: datetime,
        to_date: datetime
    ) -> List[Dict]:
        """
        Fetch sentiment items by keyword search.
        
        Args:
            keyword: Search keyword
            from_date: Start of date range
            to_date: End of date range
            
        Returns:
            List of sentiment item dictionaries
        """
        pass
    
    def _build_item(
        self,
        comment_id: str,
        content: str,
        author_id: str = None,
        author_name: str = None,
        url: str = None,
        posted_at: datetime = None,
        symbol: str = None,
        target_id: int = None,
        root_post_id: str = None,
        sentiment_score: float = None,
        heat_score: float = None,
        topic: str = None,
        extra: Dict = None
    ) -> Dict:
        """
        Build a standardized sentiment item dictionary.
        
        Returns:
            Dict ready to be inserted into sentiment_item table
        """
        return {
            "platform": self.platform,
            "target_id": target_id,
            "symbol": symbol,
            "root_post_id": root_post_id,
            "comment_id": comment_id,
            "author_id": author_id,
            "author_name": author_name,
            "content": content,
            "url": url,
            "posted_at": posted_at,
            "fetched_at": datetime.utcnow(),
            "sentiment_score": sentiment_score,
            "heat_score": heat_score,
            "topic": topic,
            "extra": extra,
        }
    
    def _parse_datetime(self, time_str: str) -> Optional[datetime]:
        """
        Parse datetime string to datetime object.
        Handles various formats common on Chinese social platforms.
        """
        if not time_str:
            return None
        
        # Common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%m-%d %H:%M",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str.strip(), fmt)
            except ValueError:
                continue
        
        # Handle relative time (e.g., "5分钟前", "2小时前", "昨天")
        try:
            return self._parse_relative_time(time_str)
        except:
            logger.warning(f"Could not parse time string: {time_str}")
            return None
    
    def _parse_relative_time(self, time_str: str) -> Optional[datetime]:
        """Parse relative time strings like '5分钟前', '2小时前'."""
        from datetime import timedelta
        
        now = datetime.now()
        time_str = time_str.strip()
        
        if "刚刚" in time_str or "秒" in time_str:
            return now
        elif "分钟前" in time_str:
            minutes = int("".join(filter(str.isdigit, time_str)) or 1)
            return now - timedelta(minutes=minutes)
        elif "小时前" in time_str:
            hours = int("".join(filter(str.isdigit, time_str)) or 1)
            return now - timedelta(hours=hours)
        elif "昨天" in time_str:
            return now - timedelta(days=1)
        elif "天前" in time_str:
            days = int("".join(filter(str.isdigit, time_str)) or 1)
            return now - timedelta(days=days)
        
        return None
    
    def _calculate_heat_score(self, likes: int = 0, comments: int = 0, reposts: int = 0) -> float:
        """
        Calculate heat score based on engagement metrics.
        Simple formula: likes + comments*2 + reposts*3
        """
        return float(likes + comments * 2 + reposts * 3)
    
    def _is_in_date_range(self, posted_at: datetime, from_date: datetime, to_date: datetime) -> bool:
        """Check if posted_at is within date range."""
        if posted_at is None:
            return False
        # Remove timezone info for comparison if present
        if posted_at.tzinfo:
            posted_at = posted_at.replace(tzinfo=None)
        if from_date.tzinfo:
            from_date = from_date.replace(tzinfo=None)
        if to_date.tzinfo:
            to_date = to_date.replace(tzinfo=None)
        return from_date <= posted_at <= to_date
