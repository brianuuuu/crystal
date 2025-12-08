"""
Auth API Router - Account Status and Login Endpoints
"""
import asyncio
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger
from pydantic import BaseModel

from app.core.schemas import (
    LoginRequest, AuthStatusResponse, PlatformAccountResponse
)
from app.storage.database import get_db
from app.account.manager import AccountManager, check_account_health
from app.account.login_service import LoginService, manual_login
from app.config.settings import beijing_now


router = APIRouter(prefix="/auth", tags=["auth"])


class ManualLoginRequest(BaseModel):
    """Request body for manual login."""
    platform: str
    timeout: int = 120


class AccountHealthStatus(BaseModel):
    """Health status for a single account."""
    account_id: int
    platform: str
    username: str
    login_status: str
    is_healthy: bool
    health_error: Optional[str] = None
    last_login_at: Optional[str] = None
    checked_at: Optional[str] = None  # Health check timestamp


class AuthStatusWithHealthResponse(BaseModel):
    """Auth status response with health check results."""
    accounts: List[AccountHealthStatus]
    online_count: int
    offline_count: int


@router.get("/status", response_model=AuthStatusWithHealthResponse)
async def get_auth_status(db: Session = Depends(get_db)):
    """
    Get account status for all platforms with health check.
    Shows which accounts are online/offline and their current health status.
    """
    manager = AccountManager(db)
    accounts = manager.get_all_accounts()
    
    # Perform health check for each account with cookies
    health_results = []
    for acc in accounts:
        is_healthy = False
        health_error = None
        
        if acc.cookies:
            is_healthy, health_error = await check_account_health(acc)
            
            # Sync login_status with health check result
            if is_healthy and acc.login_status != "online":
                manager.update_login_success(acc.id, acc.cookies)
                acc.login_status = "online"
            elif not is_healthy and acc.login_status == "online":
                manager.set_offline(acc.id)
                acc.login_status = "offline"
        
        health_results.append(AccountHealthStatus(
            account_id=acc.id,
            platform=acc.platform,
            username=acc.username,
            login_status=acc.login_status,
            is_healthy=is_healthy,
            health_error=health_error,
            last_login_at=acc.last_login_at.isoformat() if acc.last_login_at else None,
            checked_at=beijing_now().isoformat()
        ))
    
    online_count = sum(1 for r in health_results if r.is_healthy)
    offline_count = len(health_results) - online_count
    
    return AuthStatusWithHealthResponse(
        accounts=health_results,
        online_count=online_count,
        offline_count=offline_count
    )


@router.post("/manual-login")
async def manual_login_endpoint(
    request: ManualLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Perform manual login for a platform account.
    
    Opens a visible browser window for user to login manually
    (via QR code scan or credentials). Cookies are automatically
    detected and saved when login succeeds.
    """
    manager = AccountManager(db)
    
    logger.info(f"Starting manual login for {request.platform}")
    
    try:
        success, cookies, error = await manual_login(
            platform=request.platform,
            timeout=request.timeout
        )
        
        if success:
            # Create account or update existing
            # For manual login, we use a placeholder username
            account = manager.create_or_update_account(
                platform=request.platform,
                username=f"{request.platform}_user",
                login_type="manual",
                cookies=cookies
            )
            return {
                "success": True,
                "message": "Manual login successful",
                "account_id": account.id
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Manual login failed: {error}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Manual login error: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Manual login error: {error_msg}"
        )


@router.post("/login")
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Perform simulated login for a platform account.
    
    Uses Playwright to automate the login process.
    """
    manager = AccountManager(db)
    login_service = LoginService()
    
    # Create or get account
    account = manager.create_or_update_account(
        platform=request.platform,
        username=request.username,
        login_type=request.login_type
    )
    
    # Attempt login
    logger.info(f"Attempting login for {request.platform}/{request.username}")
    
    try:
        success, cookies, error = await login_service.login(
            platform=request.platform,
            username=request.username,
            password=request.password,
            login_type=request.login_type
        )
        
        if success:
            manager.update_login_success(account.id, cookies)
            return {
                "success": True,
                "message": "Login successful",
                "account_id": account.id
            }
        else:
            manager.update_login_failure(account.id, error)
            raise HTTPException(
                status_code=400,
                detail=f"Login failed: {error}"
            )
            
    except Exception as e:
        error_msg = str(e)
        manager.update_login_failure(account.id, error_msg)
        raise HTTPException(
            status_code=500,
            detail=f"Login error: {error_msg}"
        )


@router.post("/logout/{account_id}")
async def logout(
    account_id: int,
    db: Session = Depends(get_db)
):
    """Set account to offline status."""
    manager = AccountManager(db)
    account = manager.set_offline(account_id)
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {
        "success": True,
        "message": "Logged out successfully"
    }


@router.post("/verify/{account_id}")
async def verify_cookies(
    account_id: int,
    db: Session = Depends(get_db)
):
    """Verify if stored cookies are still valid."""
    manager = AccountManager(db)
    login_service = LoginService()
    
    account = manager.repo.get_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if not account.cookies:
        return {
            "valid": False,
            "message": "No cookies stored"
        }
    
    valid, error = await login_service.login_with_cookies(
        platform=account.platform,
        cookies=account.cookies
    )
    
    if valid:
        return {
            "valid": True,
            "message": "Cookies are valid"
        }
    else:
        manager.set_offline(account_id)
        return {
            "valid": False,
            "message": error or "Cookies expired"
        }
