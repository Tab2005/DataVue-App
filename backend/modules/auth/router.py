"""
Auth Module - Router
認證相關的 API 端點

此模組提供用戶認證和 Token 狀態相關的 API。

使用方式:
    from modules.auth.router import router as auth_router
    app.include_router(auth_router, prefix="/api/auth")
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone

from database import User, Team, TeamMember
from .dependencies import get_db, get_current_user, get_current_active_user
from .service import TokenManager

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)


# ============================================================
# User Profile Endpoints
# ============================================================

@router.get("/me")
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    取得當前用戶的基本資訊。
    
    Returns:
        用戶 ID、Email、Name、角色、Super Admin 狀態等
    """
    return {
        "id": current_user.id,
        "google_id": current_user.google_id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role.value if current_user.role else None,
        "status": current_user.status.value if current_user.status else None,
        "is_super_admin": current_user.is_super_admin,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
    }


@router.get("/token-status")
def get_token_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    team_id: Optional[str] = None
):
    """
    取得用戶或團隊的 Facebook Token 狀態。
    
    Args:
        team_id: 如果指定，檢查團隊 Token；否則檢查個人 Token
        
    Returns:
        Token 是否已設定、是否過期、過期時間等
    """
    if team_id:
        # 檢查團隊 Token
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # 檢查用戶是否為團隊成員
        is_member = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id
        ).first()
        
        if not is_member and not current_user.is_super_admin:
            raise HTTPException(status_code=403, detail="Not a member of this team")
        
        has_token = bool(team.fb_access_token)
        expires_at = team.token_expires_at
        target_name = team.name
        target_type = "team"
    else:
        # 檢查個人 Token
        has_token = bool(current_user.fb_access_token)
        expires_at = current_user.token_expires_at
        target_name = current_user.name or current_user.email
        target_type = "user"
    
    # 計算過期狀態
    is_expired = False
    expires_in_days = None
    
    if expires_at:
        now = datetime.now(timezone.utc)
        # 確保 expires_at 有時區資訊
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        is_expired = expires_at < now
        if not is_expired:
            delta = expires_at - now
            expires_in_days = delta.days
    
    return {
        "type": target_type,
        "name": target_name,
        "has_token": has_token,
        "is_expired": is_expired,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "expires_in_days": expires_in_days
    }


@router.get("/ai-settings")
def get_ai_settings(
    current_user: User = Depends(get_current_user)
):
    """
    取得當前用戶的 AI 設定。
    
    Returns:
        AI 提供者、模型、是否已設定 API Key 等
    """
    settings = TokenManager.get_ai_settings(current_user.google_id)
    if not settings:
        return {
            "ai_provider": "zeabur",
            "ai_model": "deepseek/deepseek-v4-flash",
            "has_zeabur_key": False,
            "has_gemini_key": False,
            "has_openrouter_key": False,
        }
    return settings
