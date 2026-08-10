from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session
from database import User, Team
from dependencies import get_db
from modules.auth.service import TokenManager
from services.integration_service import (
    get_user_integration,
    get_decrypted_access_token,
)
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
    """
    查詢目前使用者或指定團隊的 Facebook Token 狀態。

    查詢優先順序：
    1. 若提供 team_id → 查詢 Team 表的 fb_access_token / token_expires_at
    2. 若無 team_id → 先查 UserIntegration 表；若無則 fallback 到 User 表舊欄位
    """
    try:
        token_exists = False
        expires_at = None
        is_expired = True
        days_remaining = None

        if team_id:
            # 查詢團隊 Token（存在 Team 表）
            team = db.query(Team).filter(Team.id == team_id).first()
            if team and team.fb_access_token:
                token_exists = True
                expires_at = team.token_expires_at
        else:
            # 先從 google_id 解析出 User UUID（UserIntegration 使用 UUID，非 google sub）
            user = db.query(User).filter(User.google_id == user_id).first()
            if user:
                # 1. 優先查詢新版 UserIntegration 表（使用 User UUID）
                integration = get_user_integration(db, user.id, "facebook")
                if integration and integration.access_token:
                    token_exists = True
                    expires_at = integration.token_expiry
                # 2. Fallback：查詢舊版 User 表欄位
                elif user.fb_access_token:
                    token_exists = True
                    expires_at = user.token_expires_at

        if expires_at:
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            delta = expires_at - now
            days_remaining = delta.days
            is_expired = days_remaining < 0
        elif token_exists:
            # Token 存在但無過期時間，視為有效
            is_expired = False

        return {
            "token_exists": token_exists,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "days_remaining": days_remaining,
            "is_expired": is_expired,
            "provider": "facebook",
        }
    except Exception as e:
        logger.error(f"Token Status Error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
