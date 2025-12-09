"""
Zhihu Crawler - Fetch Answers and Articles from Zhihu
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger
import httpx

from .base import BaseCrawler
from app.config import settings


class ZhihuCrawler(BaseCrawler):
    """Crawler for Zhihu (知乎) platform."""
    
    def __init__(self, cookies: Optional[Dict] = None):
        super().__init__(cookies)
        self.platform = "zhihu"
        self.base_url = settings.ZHIHU_BASE_URL
        self.api_base = "https://www.zhihu.com/api/v4"
    
    async def fetch(
        self,
        target: Any,
        from_date: datetime,
        to_date: datetime
    ) -> List[Dict]:
        """
        Fetch content from a Zhihu user.
        
        Args:
            target: WatchTarget with external_id (user url_token)
            from_date: Start of date range
            to_date: End of date range
        """
        items = []
        url_token = target.external_id
        
        if not url_token:
            logger.warning(f"No external_id for target: {target.display_name}")
            return items
        
        try:
            # Fetch user's activities (answers + articles)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": f"https://www.zhihu.com/people/{url_token}",
            }
            
            async with httpx.AsyncClient() as client:
                if self.cookies:
                    client.cookies = httpx.Cookies(self.cookies)
                
                # Fetch answers
                answers = await self._fetch_answers(client, headers, url_token, from_date, to_date, target)
                items.extend(answers)
                
                # Fetch articles
                articles = await self._fetch_articles(client, headers, url_token, from_date, to_date, target)
                items.extend(articles)
                
        except Exception as e:
            logger.error(f"Error fetching Zhihu content for {target.display_name}: {e}")
        
        logger.info(f"Zhihu: fetched {len(items)} items for {target.display_name}")
        return items
    
    async def _fetch_answers(
        self,
        client: httpx.AsyncClient,
        headers: Dict,
        url_token: str,
        from_date: datetime,
        to_date: datetime,
        target: Any
    ) -> List[Dict]:
        """Fetch user's answers."""
        items = []
        url = f"{self.api_base}/members/{url_token}/answers"
        params = {
            "include": "data[*].content,created_time,updated_time,voteup_count,comment_count",
            "offset": 0,
            "limit": 20,
            "sort_by": "created",
        }
        
        try:
            offset = 0
            max_offset = 100
            
            while offset < max_offset:
                params["offset"] = offset
                response = await client.get(url, params=params, headers=headers, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"Zhihu API error: {response.status_code}")
                    break
                
                data = response.json()
                answers = data.get("data", [])
                
                if not answers:
                    break
                
                for answer in answers:
                    created_time = answer.get("created_time", 0)
                    posted_at = datetime.fromtimestamp(created_time) if created_time else None
                    
                    if posted_at and posted_at < from_date:
                        return items
                    
                    if not self._is_in_date_range(posted_at, from_date, to_date):
                        continue
                    
                    question = answer.get("question", {})
                    content = answer.get("content", "")
                    # Strip HTML tags
                    import re
                    content = re.sub(r'<[^>]+>', '', content)
                    
                    item = self._build_item(
                        comment_id=str(answer.get("id", "")),
                        content=f"【{question.get('title', '')}】{content[:500]}",
                        author_id=url_token,
                        author_name=target.display_name,
                        url=f"https://www.zhihu.com/question/{question.get('id')}/answer/{answer.get('id')}",
                        posted_at=posted_at,
                        symbol=target.symbol,
                        target_id=target.id,
                        heat_score=self._calculate_heat_score(
                            likes=answer.get("voteup_count", 0),
                            comments=answer.get("comment_count", 0)
                        ),
                        topic=question.get("title", ""),
                    )
                    items.append(item)
                
                if data.get("paging", {}).get("is_end", True):
                    break
                
                offset += 20
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error fetching Zhihu answers: {e}")
        
        return items
    
    async def _fetch_articles(
        self,
        client: httpx.AsyncClient,
        headers: Dict,
        url_token: str,
        from_date: datetime,
        to_date: datetime,
        target: Any
    ) -> List[Dict]:
        """Fetch user's articles."""
        items = []
        url = f"{self.api_base}/members/{url_token}/articles"
        params = {
            "include": "data[*].content,created,voteup_count,comment_count",
            "offset": 0,
            "limit": 20,
            "sort_by": "created",
        }
        
        try:
            offset = 0
            max_offset = 100
            
            while offset < max_offset:
                params["offset"] = offset
                response = await client.get(url, params=params, headers=headers, timeout=30)
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                articles = data.get("data", [])
                
                if not articles:
                    break
                
                for article in articles:
                    created_time = article.get("created", 0)
                    posted_at = datetime.fromtimestamp(created_time) if created_time else None
                    
                    if posted_at and posted_at < from_date:
                        return items
                    
                    if not self._is_in_date_range(posted_at, from_date, to_date):
                        continue
                    
                    content = article.get("content", "")
                    import re
                    content = re.sub(r'<[^>]+>', '', content)
                    
                    item = self._build_item(
                        comment_id=f"article_{article.get('id', '')}",
                        content=f"【专栏】{article.get('title', '')}: {content[:500]}",
                        author_id=url_token,
                        author_name=target.display_name,
                        url=f"https://zhuanlan.zhihu.com/p/{article.get('id')}",
                        posted_at=posted_at,
                        symbol=target.symbol,
                        target_id=target.id,
                        heat_score=self._calculate_heat_score(
                            likes=article.get("voteup_count", 0),
                            comments=article.get("comment_count", 0)
                        ),
                        topic=article.get("title", ""),
                    )
                    items.append(item)
                
                if data.get("paging", {}).get("is_end", True):
                    break
                
                offset += 20
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error fetching Zhihu articles: {e}")
        
        return items
    
    async def fetch_by_keyword(
        self,
        keyword: str,
        from_date: datetime,
        to_date: datetime
    ) -> List[Dict]:
        """Search Zhihu by keyword."""
        items = []
        
        try:
            url = f"{self.api_base}/search_v3"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            params = {
                "t": "general",
                "q": keyword,
                "correction": 1,
                "offset": 0,
                "limit": 20,
            }
            
            async with httpx.AsyncClient() as client:
                if self.cookies:
                    client.cookies = httpx.Cookies(self.cookies)
                
                offset = 0
                max_offset = 60
                
                while offset < max_offset:
                    params["offset"] = offset
                    response = await client.get(url, params=params, headers=headers, timeout=30)
                    
                    if response.status_code != 200:
                        break
                    
                    data = response.json()
                    results = data.get("data", [])
                    
                    if not results:
                        break
                    
                    for result in results:
                        obj = result.get("object", {})
                        if not obj:
                            continue
                        
                        obj_type = obj.get("type", "")
                        created_time = obj.get("created_time", 0) or obj.get("created", 0)
                        posted_at = datetime.fromtimestamp(created_time) if created_time else None
                        
                        if not self._is_in_date_range(posted_at, from_date, to_date):
                            continue
                        
                        content = obj.get("content", "") or obj.get("excerpt", "")
                        import re
                        content = re.sub(r'<[^>]+>', '', content)
                        
                        author = obj.get("author", {})
                        
                        item = self._build_item(
                            comment_id=f"{obj_type}_{obj.get('id', '')}",
                            content=content[:500],
                            author_id=author.get("url_token", ""),
                            author_name=author.get("name", ""),
                            url=obj.get("url", ""),
                            posted_at=posted_at,
                            topic=keyword,
                            heat_score=self._calculate_heat_score(
                                likes=obj.get("voteup_count", 0),
                                comments=obj.get("comment_count", 0)
                            ),
                        )
                        items.append(item)
                    
                    if data.get("paging", {}).get("is_end", True):
                        break
                    
                    offset += 20
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Error searching Zhihu for '{keyword}': {e}")
        
        return items

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
            logger.warning("No cookies for fetching Zhihu following feed")
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
                logger.info(f"Adding {len(self.cookies)} cookies for Zhihu")
                cookie_list = []
                for name, value in self.cookies.items():
                    cookie_list.append({
                        "name": name,
                        "value": str(value),
                        "domain": ".zhihu.com",
                        "path": "/",
                    })
                context.add_cookies(cookie_list)
                
                page = context.new_page()
                
                # Navigate to Zhihu homepage (cookies should already be set)
                page.goto("https://www.zhihu.com/", timeout=30000)
                page.wait_for_load_state("networkidle", timeout=20000)
                page.wait_for_timeout(3000)
                
                # Save debug screenshot
                import os
                debug_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "zhihu_debug.png")
                page.screenshot(path=debug_path)
                logger.info(f"Saved Zhihu debug screenshot to {debug_path}")
                logger.info(f"Page title: {page.title()}")
                logger.info(f"Page URL: {page.url}")
                
                # Scroll to load more content
                for i in range(max_pages):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                
                # Find all answer/article links
                all_links = page.query_selector_all("a[href*='/answer/'], a[href*='/p/'], a[href*='/question/']")
                logger.info(f"Found {len(all_links)} content links on Zhihu page")
                
                seen_ids = set()
                
                for link in all_links:
                    try:
                        href = link.get_attribute("href") or ""
                        
                        # Extract ID from href
                        match = re.search(r'/(?:answer|p|question)/(\d+)', href)
                        if not match:
                            continue
                        
                        content_id = match.group(1)
                        if content_id in seen_ids:
                            continue
                        seen_ids.add(content_id)
                        
                        # Get text content from the link
                        content = link.inner_text() or ""
                        
                        if len(content) < 10:
                            continue
                        
                        item = self._build_item(
                            comment_id=content_id,
                            content=content[:1000],
                            url=href if href.startswith("http") else (f"https:{href}" if href.startswith("//") else f"https://www.zhihu.com{href}"),
                            posted_at=datetime.now(),  # Use current time as posted time
                            topic="关注动态",
                        )
                        items.append(item)
                        
                    except Exception as e:
                        logger.debug(f"Error parsing Zhihu link: {e}")
                        continue
                
                browser.close()
                
        except Exception as e:
            import traceback
            logger.error(f"Error fetching Zhihu following feed: {e}\n{traceback.format_exc()}")
        
        logger.info(f"Zhihu: fetched {len(items)} items from following feed")
        return items
