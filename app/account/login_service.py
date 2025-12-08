"""
Login Service - Playwright-based Simulated Login
"""
import asyncio
from typing import Dict, Optional, Tuple
from loguru import logger

from app.config import settings


class LoginService:
    """Service for simulated login using Playwright."""
    
    # Platform login URLs
    LOGIN_URLS = {
        "weibo": "https://passport.weibo.com/sso/signin",
        "zhihu": "https://www.zhihu.com",
        "xueqiu": "https://xueqiu.com",
    }
    
    async def login(
        self,
        platform: str,
        username: str,
        password: str = None,
        login_type: str = "password"
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Perform simulated login for a platform.
        
        Returns:
            Tuple of (success, cookies_dict, error_message)
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return False, None, "Playwright not installed. Run: pip install playwright && playwright install chromium"
        
        if platform not in self.LOGIN_URLS:
            return False, None, f"Unsupported platform: {platform}"
        
        login_url = self.LOGIN_URLS[platform]
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=settings.HEADLESS)
                context = await browser.new_context()
                page = await context.new_page()
                
                logger.info(f"Starting login for {platform}: {username}")
                await page.goto(login_url, timeout=settings.BROWSER_TIMEOUT)
                
                # Platform-specific login logic
                if platform == "weibo":
                    success, error = await self._login_weibo(page, username, password)
                elif platform == "zhihu":
                    success, error = await self._login_zhihu(page, username, password)
                elif platform == "xueqiu":
                    success, error = await self._login_xueqiu(page, username, password)
                else:
                    success, error = False, "Platform login not implemented"
                
                if success:
                    # Extract cookies
                    cookies = await context.cookies()
                    cookies_dict = {c["name"]: c["value"] for c in cookies}
                    logger.info(f"Login successful for {platform}: {username}")
                    await browser.close()
                    return True, cookies_dict, None
                else:
                    await browser.close()
                    return False, None, error
                    
        except Exception as e:
            error_msg = f"Login error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    async def _login_weibo(self, page, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """Weibo login implementation."""
        try:
            # Wait for login form
            await page.wait_for_selector('input[name="username"]', timeout=10000)
            
            # Fill in credentials
            await page.fill('input[name="username"]', username)
            await page.fill('input[name="password"]', password)
            
            # Click login button
            await page.click('button[type="submit"]')
            
            # Wait for redirect or error
            await asyncio.sleep(3)
            
            # Check if login successful (redirected to home)
            if "weibo.com" in page.url and "passport" not in page.url:
                return True, None
            else:
                return False, "Login failed - check credentials or captcha required"
                
        except Exception as e:
            return False, str(e)
    
    async def _login_zhihu(self, page, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """Zhihu login implementation."""
        try:
            # Switch to password login tab if needed
            pwd_tab = page.locator('div[role="tab"]:has-text("密码登录")')
            if await pwd_tab.count() > 0:
                await pwd_tab.click()
                await asyncio.sleep(1)
            
            # Fill in credentials
            await page.fill('input[name="username"]', username)
            await page.fill('input[name="password"]', password)
            
            # Click login button
            await page.click('button[type="submit"]')
            
            await asyncio.sleep(3)
            
            # Check if login successful
            if "/signin" not in page.url:
                return True, None
            else:
                return False, "Login failed - check credentials or captcha required"
                
        except Exception as e:
            return False, str(e)
    
    async def _login_xueqiu(self, page, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """Xueqiu login implementation."""
        try:
            # Click login button to open modal
            login_btn = page.locator('a:has-text("登录")')
            if await login_btn.count() > 0:
                await login_btn.click()
                await asyncio.sleep(1)
            
            # Wait for login modal
            await page.wait_for_selector('input[name="username"]', timeout=10000)
            
            # Fill in credentials
            await page.fill('input[name="username"]', username)
            await page.fill('input[name="password"]', password)
            
            # Click login button
            await page.click('button:has-text("登录")')
            
            await asyncio.sleep(3)
            
            # Check if login successful
            user_menu = page.locator('.user-name, .nav__user')
            if await user_menu.count() > 0:
                return True, None
            else:
                return False, "Login failed - check credentials or captcha required"
                
        except Exception as e:
            return False, str(e)
    
    async def login_with_cookies(
        self,
        platform: str,
        cookies: Dict
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify login with existing cookies.
        
        Returns:
            Tuple of (valid, error_message)
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return False, "Playwright not installed"
        
        base_urls = {
            "weibo": settings.WEIBO_BASE_URL,
            "zhihu": settings.ZHIHU_BASE_URL,
            "xueqiu": settings.XUEQIU_BASE_URL,
        }
        
        if platform not in base_urls:
            return False, f"Unsupported platform: {platform}"
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                
                # Set cookies
                cookie_list = [
                    {"name": k, "value": v, "domain": base_urls[platform].split("//")[1], "path": "/"}
                    for k, v in cookies.items()
                ]
                await context.add_cookies(cookie_list)
                
                # Navigate to check login status
                page = await context.new_page()
                await page.goto(base_urls[platform], timeout=settings.BROWSER_TIMEOUT)
                
                # Platform-specific login check
                is_logged_in = await self._check_logged_in(page, platform)
                
                await browser.close()
                
                if is_logged_in:
                    return True, None
                else:
                    return False, "Cookies expired or invalid"
                    
        except Exception as e:
            return False, str(e)
    
    async def _check_logged_in(self, page, platform: str) -> bool:
        """Check if currently logged in on platform."""
        try:
            if platform == "weibo":
                # Check for user menu
                return await page.locator('.gn_name, .woo-box-item-inlineBlock').count() > 0
            elif platform == "zhihu":
                # Check for user avatar
                return await page.locator('.AppHeader-profile, .Avatar').count() > 0
            elif platform == "xueqiu":
                # Check for user menu
                return await page.locator('.user-name, .nav__user').count() > 0
            return False
        except:
            return False


# Sync wrapper for use in non-async contexts
def sync_login(platform: str, username: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """Synchronous wrapper for login."""
    service = LoginService()
    return asyncio.run(service.login(platform, username, password))


# Platform-specific cookie keys for login detection
PLATFORM_COOKIE_KEYS = {
    "xueqiu": ["xq_a_token"],
    "weibo": ["SUB", "SUBP"],
    "zhihu": ["z_c0"],
}



async def manual_login(
    platform: str,
    timeout: int = 120,
    poll_interval: int = 2
) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Open a visible browser for manual login with cookie polling.
    
    Uses sync Playwright API wrapped in thread executor to avoid
    Windows asyncio subprocess issues.
    """
    import concurrent.futures
    
    # Run sync version in thread pool to avoid Windows asyncio subprocess issues
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool,
            _sync_manual_login_impl,
            platform,
            timeout,
            poll_interval
        )
    return result


def _sync_manual_login_impl(
    platform: str,
    timeout: int = 120,
    poll_interval: int = 2
) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Synchronous implementation of manual login.
    Opens a visible browser for user to manually complete login.
    """
    import time
    
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, None, "Playwright not installed. Run: pip install playwright && playwright install chromium"
    
    login_urls = LoginService.LOGIN_URLS
    
    if platform not in login_urls:
        return False, None, f"Unsupported platform: {platform}"
    
    if platform not in PLATFORM_COOKIE_KEYS:
        return False, None, f"No cookie detection configured for: {platform}"
    
    login_url = login_urls[platform]
    required_cookies = PLATFORM_COOKIE_KEYS[platform]
    
    logger.info(f"Starting manual login for {platform}")
    logger.info(f"Please complete login in the browser window. Timeout: {timeout}s")
    
    try:
        with sync_playwright() as p:
            # Launch visible browser
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            page.goto(login_url, timeout=30000)
            
            # Poll for cookies
            start_time = time.time()
            
            while True:
                elapsed = time.time() - start_time
                
                if elapsed >= timeout:
                    browser.close()
                    return False, None, f"Login timeout after {timeout} seconds"
                
                # Check cookies
                cookies = context.cookies()
                cookie_names = {c["name"] for c in cookies}
                
                # Check if any required cookie is present
                found_cookie = any(key in cookie_names for key in required_cookies)
                
                if found_cookie:
                    # Login detected, save all cookies
                    cookies_dict = {c["name"]: c["value"] for c in cookies}
                    logger.info(f"Login successful for {platform}. Found required cookies.")
                    browser.close()
                    return True, cookies_dict, None
                
                # Wait before next poll
                time.sleep(poll_interval)
                
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        error_msg = f"Manual login error: {str(e) or 'Unknown error'}"
        logger.error(f"{error_msg}\n{error_detail}")
        return False, None, error_msg


def sync_manual_login(platform: str, timeout: int = 120) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """Synchronous wrapper for manual login."""
    return _sync_manual_login_impl(platform, timeout)

