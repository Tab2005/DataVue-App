from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import SessionLocal, User, UserRole, UserStatus, Team, TeamMember
import os
import logging

# Configure Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 統一 Token 驗證（core/security.py）
from core.security import verify_google_token

# Reuse the existing security scheme
security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_google_token_basic(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    驗證 Google ID Token 並返回完整的 id_info 字典。
    Token 快取由 core/security.py 的 TTLCache 統一管理（5 分鐘）。
    """
    token = credentials.credentials
    try:
        logger.debug(f"Verifying Google Token: {token[:10]}...")
        id_info = verify_google_token(token)
        email = id_info.get('email', 'unknown')
        masked_email = f"{email[:3]}***@{email.split('@')[-1]}" if '@' in email else email
        logger.info(f"Token Verified. User: {masked_email}")
        return id_info
    except ValueError as e:
        logger.error(f"Token Verification Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication Error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    id_info: dict = Depends(verify_google_token_basic), 
    db = Depends(get_db)
) -> User:
    """
    FastAPI 依賴注入：驗證 Token 並返回當前使用者。
    
    職責：
    1. 取得或建立使用者記錄
    2. 同步 Super Admin 狀態
    3. 首次登入時授予預設模組

    Raises:
        HTTPException 400: 登入邏輯失敗
    """
    from services.user_service import get_or_create_user, sync_super_admin_status, grant_default_module_access

    try:
        user, is_new = get_or_create_user(
            db=db,
            google_id=id_info["sub"],
            email=id_info.get("email", ""),
            name=id_info.get("name", ""),
            picture=id_info.get("picture", ""),
        )

        sync_super_admin_status(db=db, user=user)

        if is_new:
            grant_default_module_access(db=db, user=user)

        masked_email = f"{user.email[:3]}***@{user.email.split('@')[-1]}" if user.email and '@' in user.email else "unknown"
        logger.debug(f"[Auth] Authenticated: {masked_email}, super_admin={user.is_super_admin}, role={user.role}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Auth] get_current_user 失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Login Logic Failed: {str(e)}"
        )

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.status != UserStatus.ACTIVE:
        logger.warning(f"[Auth] User {current_user.google_id} is INACTIVE")
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    # Allow Super Admin to bypass specific role checks
    if current_user.is_super_admin:
        return current_user

    logger.debug(f"[Auth] Checking Admin Privileges for {current_user.google_id}. Role: {current_user.role}")
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"[Auth] Access Denied: User is not ADMIN")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_super_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_super_admin:
        logger.warning(f"[Auth] Access Denied: User {current_user.email} is NOT Super Admin")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Super Admin privileges required"
        )
    return current_user

def get_current_team(
    x_team_id: str = Header(None),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
) -> Team:
    """
    Validates that the user is a member of the requested Team ID (via Header).
    returns the Team object if valid.
    """
    if not x_team_id:
        # If no team header, we might return None or Default Team?
        # For strict multi-tenant, we should require it, OR return None and let endpoint decide.
        return None

    # Verify Membership
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == x_team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if not membership and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    team = db.query(Team).filter(Team.id == x_team_id).first()
    if not team:
         raise HTTPException(status_code=404, detail="Team not found")
         
    return team


# ==================================================
# Permission Check Dependencies
# ==================================================

from typing import Callable, Optional
from functools import wraps

def require_permission(permission_key: str, team_id_param: str = None):
    """
    Dependency factory that checks if the current user has a specific permission.
    
    Usage:
        @app.get("/api/some-endpoint")
        async def endpoint(
            user: User = Depends(get_current_user),
            _: bool = Depends(require_permission("fb_ads:analytics:view"))
        ):
            ...
    """
    def permission_checker(
        user: User = Depends(get_current_user),
        db = Depends(get_db)
    ):
        from services.permission_service import PermissionService
        
        # Super Admin bypass
        if user.is_super_admin:
            return True
        
        service = PermissionService(db)
        has_permission = service.check_permission(user.id, permission_key, None)
        
        if not has_permission:
            raise HTTPException(
                status_code=403, 
                detail=f"Permission denied: {permission_key}"
            )
        return True
    
    return permission_checker


def require_module(module_key: str):
    """
    Dependency factory that checks if the current user has access to a module.
    
    Usage:
        @app.get("/api/gsc/data")
        async def gsc_data(
            user: User = Depends(get_current_user),
            _: bool = Depends(require_module("gsc"))
        ):
            ...
    """
    def module_checker(
        user: User = Depends(get_current_user),
        db = Depends(get_db)
    ):
        from services.permission_service import PermissionService
        
        # Super Admin bypass
        if user.is_super_admin:
            return True
        
        service = PermissionService(db)
        has_access = service.check_module_access(user.id, module_key, None)
        
        if not has_access:
            raise HTTPException(
                status_code=403, 
                detail=f"Module access denied: {module_key}. Please upgrade your plan."
            )
        return True
    
    return module_checker


def require_super_admin():
    """
    Dependency that requires the current user to be a Super Admin.
    
    Usage:
        @app.delete("/api/admin/users/{user_id}")
        async def delete_user(
            user_id: str,
            _: bool = Depends(require_super_admin())
        ):
            ...
    """
    def admin_checker(user: User = Depends(get_current_user)):
        if not user.is_super_admin:
            raise HTTPException(
                status_code=403, 
                detail="Super Admin access required"
            )
        return True
    
    return admin_checker

