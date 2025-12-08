"""
Xueqiu Crawler - Fetch Stock-Related Posts from Xueqiu
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger
import httpx

from .base import BaseCrawler
from app.config import settings


class XueqiuCrawler(BaseCrawler):
    """Crawler for Xueqiu (雪球) platform."""
    
    def __init__(self, cookies: Optional[Dict] = None):
        super().__init__(cookies)
        self.platform = "xueqiu"
        self.base_url = settings.XUEQIU_BASE_URL
        self.api_base = "https://xueqiu.com"
    
    async def fetch(
        self,
        target: Any,
        from_date: datetime,
        to_date: datetime
    ) -> List[Dict]:
        """
        Fetch posts based on target type.
        
        Args:
            target: WatchTarget (can be user, symbol, or keyword)
            from_date: Start of date range
            to_date: End of date range
        """
        if target.target_type == "account":
            return await self._fetch_user_posts(target, from_date, to_date)
        elif target.target_type == "symbol":
            return await self._fetch_symbol_posts(target, from_date, to_date)
        elif target.target_type == "keyword":
            return await self.fetch_by_keyword(target.keyword, from_date, to_date)
        
        return []
    
    async def _fetch_user_posts(
        self,
        target: Any,
        from_date: datetime,
        to_date: datetime
    ) -> List[Dict]:
        """Fetch posts from a specific user."""
        items = []
        user_id = target.external_id
        
        if not user_id:
            logger.warning(f"No external_id for target: {target.display_name}")
            return items
        
        try:
            url = f"{self.api_base}/v4/statuses/user_timeline.json"
            headers = self._get_headers()
            params = {
                "user_id": user_id,
                "page": 1,
                "count": 20,
            }
            
            async with httpx.AsyncClient() as client:
                if self.cookies:
                    client.cookies = httpx.Cookies(self.cookies)
                
                page = 1
                max_pages = 10
                
                while page <= max_pages:
                    params["page"] = page
                    response = await client.get(url, params=params, headers=headers, timeout=30)
                    
                    if response.status_code != 200:
                        logger.warning(f"Xueqiu API error: {response.status_code}")
                        break
                    
                    data = response.json()
                    statuses = data.get("statuses", [])
                    
                    if not statuses:
                        break
                    
                    for status in statuses:
                        created_at = status.get("created_at", 0)
                        posted_at = datetime.fromtimestamp(created_at / 1000) if created_at else None
                        
                        if posted_at and posted_at < from_date:
                            return items
                        
                        if not self._is_in_date_range(posted_at, from_date, to_date):
                            continue
                        
                        user = status.get("user", {})
                        
                        item = self._build_item(
                            comment_id=str(status.get("id", "")),
                            content=status.get("text", "") or status.get("description", ""),
                            author_id=str(user.get("id", "")),
                            author_name=user.get("screen_name", ""),
                            url=f"https://xueqiu.com{status.get('target', '')}",
                            posted_at=posted_at,
                            symbol=target.symbol,
                            target_id=target.id,
                            heat_score=self._calculate_heat_score(
                                likes=status.get("like_count", 0),
                                comments=status.get("reply_count", 0),
                                reposts=status.get("retweet_count", 0)
                            ),
                            extra={
                                "symbols": [s.get("symbol") for s in status.get("symbols", [])],
                            }
                        )
                        items.append(item)
                    
                    page += 1
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Error fetching Xueqiu user posts for {target.display_name}: {e}")
        
        logger.info(f"Xueqiu: fetched {len(items)} items for user {target.display_name}")
        return items
    
    async def _fetch_symbol_posts(
        self,
        target: Any,
        from_date: datetime,
        to_date: datetime
    ) -> List[Dict]:
        """Fetch posts related to a stock symbol."""
        items = []
        symbol = target.symbol
        
        if not symbol:
            logger.warning(f"No symbol for target: {target.display_name}")
            return items
        
        try:
            url = f"{self.api_base}/v4/statuses/stock_timeline.json"
            headers = self._get_headers()
            params = {
                "symbol": symbol,
                "count": 20,
                "source": "all",
            }
            
            async with httpx.AsyncClient() as client:
                if self.cookies:
                    client.cookies = httpx.Cookies(self.cookies)
                
                # First get xq_a_token cookie if not present
                if "xq_a_token" not in self.cookies:
                    await client.get(self.base_url, headers=headers)
                
                max_id = None
                max_pages = 10
                
                for _ in range(max_pages):
                    if max_id:
                        params["max_id"] = max_id
                    
                    response = await client.get(url, params=params, headers=headers, timeout=30)
                    
                    if response.status_code != 200:
                        logger.warning(f"Xueqiu API error: {response.status_code}")
                        break
                    
                    data = response.json()
                    statuses = data.get("list", [])
                    
                    if not statuses:
                        break
                    
                    for status in statuses:
                        created_at = status.get("created_at", 0)
                        posted_at = datetime.fromtimestamp(created_at / 1000) if created_at else None
                        
                        if posted_at and posted_at < from_date:
                            return items
                        
                        if not self._is_in_date_range(posted_at, from_date, to_date):
                            continue
                        
                        user = status.get("user", {})
                        
                        item = self._build_item(
                            comment_id=str(status.get("id", "")),
                            content=status.get("text", "") or status.get("description", ""),
                            author_id=str(user.get("id", "")),
                            author_name=user.get("screen_name", ""),
                            url=f"https://xueqiu.com{status.get('target', '')}",
                            posted_at=posted_at,
                            symbol=symbol,
                            target_id=target.id,
                            heat_score=self._calculate_heat_score(
                                likes=status.get("like_count", 0),
                                comments=status.get("reply_count", 0),
                                reposts=status.get("retweet_count", 0)
                            ),
                        )
                        items.append(item)
                        max_id = status.get("id")
                    
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Error fetching Xueqiu symbol posts for {symbol}: {e}")
        
        logger.info(f"Xueqiu: fetched {len(items)} items for symbol {symbol}")
        return items
    
    async def fetch_by_keyword(
        self,
        keyword: str,
        from_date: datetime,
        to_date: datetime
    ) -> List[Dict]:
        """Search Xueqiu by keyword."""
        items = []
        
        try:
            url = f"{self.api_base}/query/v1/search/status.json"
            headers = self._get_headers()
            params = {
                "q": keyword,
                "count": 20,
                "page": 1,
            }
            
            async with httpx.AsyncClient() as client:
                if self.cookies:
                    client.cookies = httpx.Cookies(self.cookies)
                
                # Get initial cookie
                await client.get(self.base_url, headers=headers)
                
                page = 1
                max_pages = 5
                
                while page <= max_pages:
                    params["page"] = page
                    response = await client.get(url, params=params, headers=headers, timeout=30)
                    
                    if response.status_code != 200:
                        break
                    
                    data = response.json()
                    statuses = data.get("list", [])
                    
                    if not statuses:
                        break
                    
                    for status in statuses:
                        created_at = status.get("created_at", 0)
                        posted_at = datetime.fromtimestamp(created_at / 1000) if created_at else None
                        
                        if not self._is_in_date_range(posted_at, from_date, to_date):
                            continue
                        
                        user = status.get("user", {})
                        
                        item = self._build_item(
                            comment_id=str(status.get("id", "")),
                            content=status.get("text", "") or status.get("description", ""),
                            author_id=str(user.get("id", "")),
                            author_name=user.get("screen_name", ""),
                            url=f"https://xueqiu.com{status.get('target', '')}",
                            posted_at=posted_at,
                            topic=keyword,
                            heat_score=self._calculate_heat_score(
                                likes=status.get("like_count", 0),
                                comments=status.get("reply_count", 0),
                                reposts=status.get("retweet_count", 0)
                            ),
                        )
                        items.append(item)
                    
                    page += 1
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Error searching Xueqiu for '{keyword}': {e}")
        
        return items
    
    def _get_headers(self) -> Dict:
        """Get common headers for Xueqiu requests."""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Origin": "https://xueqiu.com",
            "Referer": "https://xueqiu.com/",
        }
