"""
Auth API Router - Account Status and Login Endpoints
"""
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from app.core.schemas import (
    LoginRequest, AuthStatusResponse, PlatformAccountResponse
)
from app.storage.database import get_db
from app.account.manager import AccountManager
from app.account.login_service import LoginService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status(db: Session = Depends(get_db)):
    """
    Get account status for all platforms.
    Shows which accounts are online/offline.
    """
    manager = AccountManager(db)
    status = manager.get_accounts_status()
    
    return AuthStatusResponse(
        accounts=[
            PlatformAccountResponse.model_validate(acc)
            for acc in status["accounts"]
        ],
        online_count=status["online_count"],
        offline_count=status["offline_count"]
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
