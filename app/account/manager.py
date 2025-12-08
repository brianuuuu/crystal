"""
Account Manager - Account CRUD and Cookie Management
"""
from typing import List, Optional, Dict, Any
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
