"""
Account Manager - Account CRUD and Cookie Management
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from loguru import logger

from app.core.models import PlatformAccount, LoginStatus
from app.storage.repositories import AccountRepository


class AccountManager:
    """Manager for platform account operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = AccountRepository(db)
    
    def get_all_accounts(self) -> List[PlatformAccount]:
        """Get all platform accounts."""
        return self.repo.get_all()
    
    def get_accounts_status(self) -> Dict[str, Any]:
        """Get account status summary."""
        accounts = self.repo.get_all()
        online_count = sum(1 for a in accounts if a.login_status == LoginStatus.ONLINE.value)
        offline_count = len(accounts) - online_count
        
        return {
            "accounts": accounts,
            "online_count": online_count,
            "offline_count": offline_count
        }
    
    def get_account_by_platform(self, platform: str) -> Optional[PlatformAccount]:
        """Get active account for a platform."""
        return self.repo.get_active_by_platform(platform)
    
    def get_cookies(self, platform: str) -> Optional[Dict]:
        """Get cookies for active account on platform."""
        account = self.get_account_by_platform(platform)
        if account and account.cookies:
            return account.cookies
        return None
    
    def create_or_update_account(
        self,
        platform: str,
        username: str,
        login_type: str = "cookie",
        cookies: Dict = None
    ) -> PlatformAccount:
        """Create new account or update existing one."""
        existing = self.repo.get_by_platform_username(platform, username)
        
        if existing:
            logger.info(f"Updating existing account: {platform}/{username}")
            return self.repo.update(
                existing.id,
                login_type=login_type,
                cookies=cookies,
                login_status=LoginStatus.ONLINE.value if cookies else existing.login_status
            )
        else:
            logger.info(f"Creating new account: {platform}/{username}")
            return self.repo.create(
                platform=platform,
                username=username,
                login_type=login_type,
                cookies=cookies,
                login_status=LoginStatus.ONLINE.value if cookies else LoginStatus.OFFLINE.value
            )
    
    def update_login_success(
        self,
        account_id: int,
        cookies: Dict
    ) -> Optional[PlatformAccount]:
        """Update account after successful login."""
        logger.info(f"Login success for account ID: {account_id}")
        return self.repo.update_login_status(
            account_id,
            status=LoginStatus.ONLINE.value,
            cookies=cookies
        )
    
    def update_login_failure(
        self,
        account_id: int,
        error: str
    ) -> Optional[PlatformAccount]:
        """Update account after login failure."""
        logger.warning(f"Login failed for account ID: {account_id}, error: {error}")
        return self.repo.update_login_status(
            account_id,
            status=LoginStatus.ERROR.value,
            error=error
        )
    
    def set_offline(self, account_id: int) -> Optional[PlatformAccount]:
        """Set account to offline status."""
        return self.repo.update_login_status(
            account_id,
            status=LoginStatus.OFFLINE.value
        )
    
    def deactivate_account(self, account_id: int) -> Optional[PlatformAccount]:
        """Deactivate an account."""
        return self.repo.update(account_id, is_active=False)


# Health check URLs for each platform (use main pages that require login)
HEALTH_CHECK_URLS = {
    "xueqiu": "https://xueqiu.com/",
    "weibo": "https://weibo.com/",
    "zhihu": "https://www.zhihu.com/",
}

# Required cookies for each platform to consider logged in
REQUIRED_COOKIES = {
    "xueqiu": ["xq_a_token"],
    "weibo": ["SUB", "SUBP"],
    "zhihu": ["z_c0"],
}


async def check_account_health(account: PlatformAccount) -> Tuple[bool, Optional[str]]:
    """
    Verify if stored cookies are still valid by fetching the main page.
    
    Health check logic:
    - Check if required cookies exist
    - Fetch main page and verify 200 OK with HTML content
    
    Args:
        account: PlatformAccount instance with cookies
    
    Returns:
        Tuple of (is_healthy, error_message)
    """
    import httpx
    
    platform = account.platform
    
    if platform not in HEALTH_CHECK_URLS:
        return False, f"Unsupported platform: {platform}"
    
    if not account.cookies:
        return False, "No cookies stored"
    
    cookies = account.cookies
    
    # Check if required cookies exist
    required = REQUIRED_COOKIES.get(platform, [])
    has_required = any(k in cookies for k in required)
    if not has_required:
        return False, f"Missing required cookies: {required}"
    
    url = HEALTH_CHECK_URLS[platform]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, cookies=cookies, headers=headers)
            
            # Check for successful response
            if response.status_code == 200:
                html = response.text
                # Basic check: HTML should contain <html> tag and be reasonably long
                if "<html" in html.lower() and len(html) > 1000:
                    return True, None
                else:
                    return False, f"Invalid HTML response (len={len(html)})"
            elif response.status_code in (401, 403):
                return False, f"Auth failed: {response.status_code}"
            else:
                return False, f"Health check failed: {response.status_code}"
            
    except httpx.TimeoutException:
        return False, "Health check timed out"
    except Exception as e:
        logger.error(f"Health check error for {platform}: {e}")
        return False, f"Health check error: {str(e)}"
