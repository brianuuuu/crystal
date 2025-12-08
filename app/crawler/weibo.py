"""
Weibo Crawler - Fetch Posts from Weibo
"""
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger
import httpx

from .base import BaseCrawler
from app.config import settings


class WeiboCrawler(BaseCrawler):
    """Crawler for Weibo (微博) platform."""
    
    def __init__(self, cookies: Optional[Dict] = None):
        super().__init__(cookies)
        self.platform = "weibo"
        self.base_url = settings.WEIBO_BASE_URL
        self.api_base = "https://m.weibo.cn/api"
    
    async def fetch(
        self,
        target: Any,
        from_date: datetime,
        to_date: datetime
    ) -> List[Dict]:
        """
        Fetch posts from a Weibo user.
        
        Args:
            target: WatchTarget with external_id (uid)
            from_date: Start of date range
            to_date: End of date range
        """
        items = []
        uid = target.external_id
        
        if not uid:
            logger.warning(f"No external_id for target: {target.display_name}")
            return items
        
        try:
            # Use mobile API to fetch user posts
            url = f"{self.api_base}/container/getIndex"
            params = {
                "type": "uid",
                "value": uid,
                "containerid": f"107603{uid}",  # User timeline container
            }
            
            async with httpx.AsyncClient() as client:
                # Set cookies
                if self.cookies:
                    client.cookies = httpx.Cookies(self.cookies)
                
                page = 1
                max_pages = 10  # Limit pages to avoid excessive requests
                
                while page <= max_pages:
                    params["page"] = page
                    response = await client.get(url, params=params, timeout=30)
                    
                    if response.status_code != 200:
                        logger.error(f"Weibo API error: {response.status_code}")
                        break
                    
                    data = response.json()
                    cards = data.get("data", {}).get("cards", [])
                    
                    if not cards:
                        break
                    
                    for card in cards:
                        if card.get("card_type") != 9:  # Only process weibo cards
                            continue
                        
                        mblog = card.get("mblog", {})
                        if not mblog:
                            continue
                        
                        posted_at = self._parse_weibo_time(mblog.get("created_at", ""))
                        
                        # Check date range
                        if posted_at and posted_at < from_date:
                            # Reached posts older than our range, stop
                            return items
                        
                        if not self._is_in_date_range(posted_at, from_date, to_date):
                            continue
                        
                        item = self._build_item(
                            comment_id=str(mblog.get("id", "")),
                            content=mblog.get("text", ""),
                            author_id=str(mblog.get("user", {}).get("id", "")),
                            author_name=mblog.get("user", {}).get("screen_name", ""),
                            url=f"https://m.weibo.cn/status/{mblog.get('id', '')}",
                            posted_at=posted_at,
                            symbol=target.symbol,
                            target_id=target.id,
                            heat_score=self._calculate_heat_score(
                                likes=mblog.get("attitudes_count", 0),
                                comments=mblog.get("comments_count", 0),
                                reposts=mblog.get("reposts_count", 0)
                            ),
                            extra={
                                "pics": [p.get("url") for p in mblog.get("pics", [])],
                                "source": mblog.get("source", ""),
                            }
                        )
                        items.append(item)
                    
                    page += 1
                    await asyncio.sleep(1)  # Rate limiting
                    
        except Exception as e:
            logger.error(f"Error fetching Weibo posts for {target.display_name}: {e}")
        
        logger.info(f"Weibo: fetched {len(items)} items for {target.display_name}")
        return items
    
    async def fetch_by_keyword(
        self,
        keyword: str,
        from_date: datetime,
        to_date: datetime
    ) -> List[Dict]:
        """Search Weibo by keyword."""
        items = []
        
        try:
            url = f"{self.api_base}/container/getIndex"
            params = {
                "containerid": f"100103type=1&q={keyword}",
                "page_type": "searchall",
            }
            
            async with httpx.AsyncClient() as client:
                if self.cookies:
                    client.cookies = httpx.Cookies(self.cookies)
                
                page = 1
                max_pages = 5
                
                while page <= max_pages:
                    params["page"] = page
                    response = await client.get(url, params=params, timeout=30)
                    
                    if response.status_code != 200:
                        break
                    
                    data = response.json()
                    cards = data.get("data", {}).get("cards", [])
                    
                    if not cards:
                        break
                    
                    for card in cards:
                        card_group = card.get("card_group", [])
                        for sub_card in card_group:
                            if sub_card.get("card_type") != 9:
                                continue
                            
                            mblog = sub_card.get("mblog", {})
                            if not mblog:
                                continue
                            
                            posted_at = self._parse_weibo_time(mblog.get("created_at", ""))
                            
                            if not self._is_in_date_range(posted_at, from_date, to_date):
                                continue
                            
                            item = self._build_item(
                                comment_id=str(mblog.get("id", "")),
                                content=mblog.get("text", ""),
                                author_id=str(mblog.get("user", {}).get("id", "")),
                                author_name=mblog.get("user", {}).get("screen_name", ""),
                                url=f"https://m.weibo.cn/status/{mblog.get('id', '')}",
                                posted_at=posted_at,
                                topic=keyword,
                                heat_score=self._calculate_heat_score(
                                    likes=mblog.get("attitudes_count", 0),
                                    comments=mblog.get("comments_count", 0),
                                    reposts=mblog.get("reposts_count", 0)
                                ),
                            )
                            items.append(item)
                    
                    page += 1
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Error searching Weibo for '{keyword}': {e}")
        
        return items
    
    def _parse_weibo_time(self, time_str: str) -> Optional[datetime]:
        """Parse Weibo's time format."""
        if not time_str:
            return None
        
        # Weibo uses format like "Sat Dec 07 10:30:00 +0800 2024"
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(time_str.replace("+0800", "GMT+0800"))
        except:
            pass
        
        # Fallback to base class parser
        return self._parse_datetime(time_str)
