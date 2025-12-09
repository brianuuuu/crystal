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

    async def fetch_following_feed(
        self,
        from_date: datetime,
        to_date: datetime,
        max_pages: int = 5
    ) -> List[Dict]:
        """
        Fetch posts from all users the logged-in account is following.
        Uses Playwright (sync API via executor) to render the page.
        """
        if not self.cookies:
            logger.warning("No cookies for fetching Weibo following feed")
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
                logger.info(f"Adding {len(self.cookies)} cookies for Weibo")
                cookie_list = []
                for name, value in self.cookies.items():
                    cookie_list.append({
                        "name": name,
                        "value": str(value),
                        "domain": ".weibo.com",
                        "path": "/",
                    })
                context.add_cookies(cookie_list)
                
                page = context.new_page()
                
                # Navigate to Weibo main site homepage
                page.goto("https://weibo.com/", timeout=60000)
                page.wait_for_load_state("domcontentloaded", timeout=30000)
                page.wait_for_timeout(8000)  # Extra wait for dynamic content
                
                # Save debug screenshot
                import os
                debug_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "weibo_debug.png")
                page.screenshot(path=debug_path)
                logger.info(f"Saved Weibo debug screenshot to {debug_path}")
                logger.info(f"Page title: {page.title()}")
                logger.info(f"Page URL: {page.url}")
                
                # Scroll to load more content
                for i in range(max_pages):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                
                # Log page HTML structure for debugging
                all_divs = page.query_selector_all("div")
                logger.info(f"Found {len(all_divs)} divs on page")
                
                # Try multiple selectors to find feed content
                selectors_to_try = [
                    "div[class*='detail']",
                    "div[class*='content']",
                    "div[class*='text']",
                    "div[class*='weibo']",
                    "div[class*='card']",
                    "article",
                    "main div > div > div"
                ]
                
                for selector in selectors_to_try:
                    elements = page.query_selector_all(selector)
                    logger.info(f"Selector '{selector}': found {len(elements)} elements")
                
                # First try to get content from article elements (most reliable)
                seen_ids = set()
                articles = page.query_selector_all("article")
                logger.info(f"Found {len(articles)} article elements, extracting content...")
                
                for article in articles:
                    try:
                        # Get full article text
                        full_text = article.inner_text() or ""
                        full_text = full_text.strip()
                        
                        if len(full_text) < 50:
                            continue
                        
                        # Parse the article structure:
                        # Line 1: Author name
                        # Line 2: Time
                        # Line 3: Source (来自 xxx)
                        # Line 4+: Actual content
                        lines = full_text.split('\n')
                        
                        author_name = lines[0].strip() if len(lines) > 0 else ""
                        
                        # Parse the date from line 2 (e.g. "12-6 15:10" or "昨天 18:19" or "13小时前")
                        posted_at = datetime.now()  # Default to now
                        if len(lines) > 1:
                            time_str = lines[1].strip()
                            try:
                                import re
                                from datetime import timedelta
                                
                                # Match "X小时前" format
                                hours_match = re.match(r'(\d+)小时前', time_str)
                                if hours_match:
                                    hours = int(hours_match.group(1))
                                    posted_at = datetime.now() - timedelta(hours=hours)
                                # Match "X分钟前" format
                                elif '分钟前' in time_str:
                                    mins_match = re.match(r'(\d+)分钟前', time_str)
                                    if mins_match:
                                        mins = int(mins_match.group(1))
                                        posted_at = datetime.now() - timedelta(minutes=mins)
                                # Match "昨天 HH:MM" format
                                elif '昨天' in time_str:
                                    time_match = re.search(r'(\d{1,2}):(\d{2})', time_str)
                                    if time_match:
                                        hour, minute = int(time_match.group(1)), int(time_match.group(2))
                                        yesterday = datetime.now() - timedelta(days=1)
                                        posted_at = yesterday.replace(hour=hour, minute=minute, second=0, microsecond=0)
                                    else:
                                        posted_at = datetime.now() - timedelta(days=1)
                                # Match "今天" or "刚刚"
                                elif '今天' in time_str or '刚刚' in time_str:
                                    posted_at = datetime.now()
                                # Match "M-D HH:MM" format (e.g. "12-7 13:20")
                                else:
                                    date_match = re.match(r'(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})', time_str)
                                    if date_match:
                                        month, day, hour, minute = map(int, date_match.groups())
                                        year = datetime.now().year
                                        posted_at = datetime(year, month, day, hour, minute)
                            except Exception as e:
                                logger.debug(f"Failed to parse time: {time_str}, error: {e}")
                                pass
                        
                        # Find the content start (skip author, time, source lines)
                        content_start = 0
                        for i, line in enumerate(lines):
                            if '来自' in line or '微博发布' in line:
                                content_start = i + 1
                                break
                        
                        # Get content (skip trailing UI elements like 转发/评论/赞)
                        content_lines = []
                        for line in lines[content_start:]:
                            line = line.strip()
                            # Stop at UI elements
                            if line in ['转发', '评论', '赞', '收藏', '展开', '...展开'] or line.isdigit():
                                continue
                            if len(line) > 5:
                                content_lines.append(line)
                        
                        content = ' '.join(content_lines)
                        
                        # Skip if no real content
                        if len(content) < 30:
                            continue
                        
                        # Skip UI-only content
                        if '关注已刷完' in content or '为你推荐更多微博' in content:
                            continue
                        
                        # Generate unique ID based on content
                        content_hash = hashlib.md5(content[:100].encode()).hexdigest()[:16]
                        
                        if content_hash in seen_ids:
                            continue
                        seen_ids.add(content_hash)
                        
                        # Try to find a link
                        link_el = article.query_selector("a[href*='/detail/'], a[href*='/status/']")
                        href = link_el.get_attribute("href") if link_el else ""
                        
                        item = self._build_item(
                            comment_id=content_hash,
                            content=content[:500],
                            author_name=author_name,
                            url=href if href and href.startswith("http") else (f"https://weibo.com{href}" if href else ""),
                            posted_at=posted_at,
                            topic="关注动态",
                        )
                        items.append(item)
                        logger.info(f"Extracted from {author_name}: {content[:50]}...")
                        
                        # Limit to 30 items
                        if len(items) >= 30:
                            break
                            
                    except Exception as e:
                        logger.debug(f"Error extracting from article: {e}")
                        continue
                
                browser.close()
                
        except Exception as e:
            import traceback
            logger.error(f"Error fetching Weibo following feed: {e}\n{traceback.format_exc()}")
        
        logger.info(f"Weibo: fetched {len(items)} items from following feed")
        return items
