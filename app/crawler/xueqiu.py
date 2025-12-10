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
    
    async def fetch_following_feed(
        self,
        from_date: datetime,
        to_date: datetime,
        max_pages: int = 5
    ) -> List[Dict]:
        """
        Fetch posts from all users the logged-in account is following.
        Uses Playwright (sync API via executor) to render the page and bypass WAF protection.
        
        Args:
            from_date: Start of date range
            to_date: End of date range  
            max_pages: Maximum scrolls to perform
        
        Returns:
            List of sentiment item dictionaries
        """
        if not self.cookies:
            logger.warning("No cookies for fetching following feed")
            return []
        
        # Run sync playwright in thread pool to avoid Windows asyncio issue
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            items = await loop.run_in_executor(
                executor,
                self._sync_fetch_following_feed,
                from_date,
                to_date,
                max_pages
            )
        
        return items
    
    def _sync_fetch_following_feed(
        self,
        from_date: datetime,
        to_date: datetime,
        max_pages: int
    ) -> List[Dict]:
        """Sync implementation of fetch_following_feed using Playwright sync API."""
        items = []
        
        try:
            from playwright.sync_api import sync_playwright
            import re
            import hashlib
            
            with sync_playwright() as p:
                # Use visible browser so user can complete verification if needed
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                
                # Add cookies BEFORE creating page - use domain format
                logger.info(f"Adding {len(self.cookies)} cookies for Xueqiu")
                cookie_list = []
                for name, value in self.cookies.items():
                    cookie_list.append({
                        "name": name,
                        "value": str(value),
                        "domain": ".xueqiu.com",
                        "path": "/",
                    })
                context.add_cookies(cookie_list)
                
                page = context.new_page()
                
                # Navigate to homepage (cookies should already be set)
                page.goto("https://xueqiu.com/", timeout=60000)
                # Use domcontentloaded - Xueqiu may have long-running requests
                page.wait_for_load_state("domcontentloaded", timeout=30000)
                page.wait_for_timeout(8000)  # Extra wait for dynamic content
                
                # Save screenshot for debugging
                import os
                debug_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "xueqiu_debug.png")
                page.screenshot(path=debug_path)
                logger.info(f"Saved debug screenshot to {debug_path}")
                
                # Log page title and URL to check if we're on the right page
                logger.info(f"Page title: {page.title()}")
                logger.info(f"Page URL: {page.url}")
                
                # Scroll to load more content
                for i in range(max_pages):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                
                import re
                import hashlib
                
                # Log element counts for debugging
                logger.info(f"Looking for feed content...")
                all_divs = page.query_selector_all("div")
                logger.info(f"Found {len(all_divs)} divs on page")
                
                # Find content blocks
                seen_ids = set()
                all_elements = page.query_selector_all("article, div[class*='timeline'], div[class*='status'], div[class*='card']")
                
                if not all_elements or len(all_elements) < 5:
                    all_elements = page.query_selector_all("div")
                    logger.info(f"Using fallback div selector")
                
                logger.info(f"Processing {len(all_elements)} elements")
                
                for el in all_elements:
                    try:
                        full_text = el.inner_text() or ""
                        full_text = full_text.strip()
                        
                        # Skip short or too long content
                        if len(full_text) < 50 or len(full_text) > 2000:
                            continue
                        
                        # Skip UI elements
                        if any(x in full_text for x in ['登录', '注册', '全部关注', '自选股', '条新帖', '搜索']):
                            continue
                        
                        # Generate unique ID
                        content_hash = hashlib.md5(full_text[:100].encode()).hexdigest()[:16]
                        
                        if content_hash in seen_ids:
                            continue
                        seen_ids.add(content_hash)
                        
                        # Take content as-is, clean whitespace
                        content = ' '.join(full_text.split())
                        
                        # Try to find link
                        link_el = el.query_selector("a[href*='/status/'], a[href*='/u/']")
                        href = link_el.get_attribute("href") if link_el else ""
                        if href:
                            if href.startswith("//"):
                                href = f"https:{href}"
                            elif href.startswith("/"):
                                href = f"https://xueqiu.com{href}"
                        
                        # Get first line as author
                        lines = full_text.split('\n')
                        author_name = lines[0].strip()[:20] if lines else ""
                        
                        item = self._build_item(
                            comment_id=content_hash,
                            content=content[:500],
                            author_name=author_name,
                            url=href,
                            posted_at=datetime.now(),
                            topic="关注动态",
                        )
                        items.append(item)
                        logger.info(f"Extracted: {content[:50]}...")
                        
                        if len(items) >= 30:
                            break
                            
                    except Exception as e:
                        continue
                
                browser.close()
                
        except Exception as e:
            import traceback
            logger.error(f"Error fetching Xueqiu following feed: {e}\n{traceback.format_exc()}")
        
        logger.info(f"Xueqiu: fetched {len(items)} items from following feed")
        return items
    
    def _get_headers(self) -> Dict:
        """Get common headers for Xueqiu requests."""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Origin": "https://xueqiu.com",
            "Referer": "https://xueqiu.com/",
        }
