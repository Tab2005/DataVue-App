from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session
from database import User, Team
from dependencies import get_db
from auth import TokenManager
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.security import verify_google_token_and_get_sub

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

security = HTTPBearer()

# 速率限制（由 limiter.py 初始化）
from limiter import limiter


def _get_google_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """從 Bearer Token 提取並驗證 Google User ID（sub）"""
    try:
        return verify_google_token_and_get_sub(credentials.credentials)
    except ValueError as e:
        logger.error(f"Google Token Verification Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {e}"
        )

class ExchangeRequest(BaseModel):
    app_id: str
    app_secret: str
    short_token: str
    team_id: Optional[str] = None

@router.post("/exchange-token")
@limiter.limit("10/minute")
def exchange_token_endpoint(
    request: Request,
    body: ExchangeRequest,
    user_id: str = Depends(_get_google_user_id)
):
    """Exchange short-lived token for long-lived token."""
    success, message = TokenManager.exchange_for_long_lived_token(
        body.app_id, 
        body.app_secret, 
        body.short_token,
        user_id,
        team_id=body.team_id
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@router.get("/token-status")
@limiter.limit("30/minute")
def get_token_status(
    request: Request,
    db: Session = Depends(get_db),
    team_id: Optional[str] = None,
    user_id: str = Depends(_get_google_user_id)
):
    """Check the expiration status of the user's OR team's Facebook token."""
    try:
        target = None
        if team_id:
            target = db.query(Team).filter(Team.id == team_id).first()
        else:
            target = db.query(User).filter(User.google_id == user_id).first()
        
        token_exists = False
        if target and hasattr(target, 'fb_access_token') and target.fb_access_token:
            token_exists = len(str(target.fb_access_token)) > 10
        
        if not target or not target.token_expires_at:
            return {
                "expires_at": None,
                "days_remaining": None,
                "is_expired": False,
                "token_exists": token_exists
            }
        
        now = datetime.now(timezone.utc)
        expires_at = target.token_expires_at
        
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
             
        delta = expires_at - now
        days_remaining = delta.days
        
        return {
            "expires_at": expires_at.isoformat(),
            "days_remaining": days_remaining,
            "is_expired": days_remaining < 0,
            "token_exists": token_exists
        }
    except Exception as e:
        logger.error(f"Token Status Error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
