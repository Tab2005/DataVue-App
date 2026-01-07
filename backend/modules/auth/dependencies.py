"""
Auth Module - Dependencies
認證相關的 FastAPI 依賴注入

此模組從 dependencies.py 抽取出來，提供可複用的認證依賴。

使用方式:
    from modules.auth.dependencies import get_current_user, require_admin
    
    @router.get("/api/data")
    async def get_data(user: User = Depends(get_current_user)):
        return {"user": user.email}
"""

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
import sys
import traceback

from database import SessionLocal, User, UserRole, UserStatus, Team, TeamMember

# HTTP Bearer 認證方案
security = HTTPBearer()


def get_google_client_id() -> str:
    """取得 Google Client ID（可被覆寫以支援測試）"""
    return os.getenv("GOOGLE_CLIENT_ID", "")


def get_db():
    """資料庫 Session 依賴"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_google_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    驗證 Google OAuth Token，回傳 Token 內的用戶資訊。
    
    Returns:
        dict: 包含 sub (Google ID), email, name 等欄位
    
    Raises:
        HTTPException: 401 如果 Token 無效
    """
    token = credentials.credentials
    client_id = get_google_client_id()
    
    try:
        print(f"DEBUG: Verifying Google Token: {token[:10]}...", file=sys.stderr)
        id_info = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            client_id,
            clock_skew_in_seconds=60
        )
        print(f"DEBUG: Token Verified. User: {id_info.get('email')}", file=sys.stderr)
        return id_info
    except Exception as e:
        print(f"Token Verification Error: {type(e).__name__}: {e}", file=sys.stderr)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication Error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    id_info: dict = Depends(verify_google_token), 
    db = Depends(get_db)
) -> User:
    """
    根據 Google Token 取得或自動註冊資料庫中的 User 物件。
    
    功能:
    - 自動註冊新用戶
    - 同步 Email/Name 到資料庫
    - 首位用戶自動成為 Super Admin
    - 緊急恢復模式：當 DB 無 Super Admin 時可透過環境變數恢復
    
    Returns:
        User: 資料庫中的用戶物件
    """
    try:
        google_id = id_info['sub']
        email = id_info.get('email')
        name = id_info.get('name')
        user = db.query(User).filter(User.google_id == google_id).first()
        
        if not user:
            print(f"DEBUG: User {google_id} not found. Auto-Registering...", file=sys.stderr)
            
            # 第一位用戶成為 Admin
            user_count = db.query(User).count()
            new_role = UserRole.ADMIN if user_count == 0 else UserRole.VIEWER
            
            user = User(
                google_id=google_id, 
                email=email,
                name=name,
                role=new_role,
                status=UserStatus.ACTIVE,
                is_super_admin=(user_count == 0)
            )
            
            # 環境變數強制 Super Admin
            super_admin_email = os.getenv("SUPER_ADMIN_EMAIL")
            if super_admin_email and email:
                if super_admin_email.strip().lower() == email.strip().lower():
                    print(f"🔒 SUPER_ADMIN_EMAIL match! Promoting {email}", file=sys.stderr)
                    user.is_super_admin = True
                    user.role = UserRole.ADMIN
            
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Auto-Registered: {name} ({email}) as {new_role}", file=sys.stderr)
            
            # 授予預設模組權限
            _grant_default_modules(db, user)
        else:
            # 更新 Profile
            if user.email != email or user.name != name:
                user.email = email
                user.name = name
            
            # 緊急恢復：如果 DB 沒有任何 Super Admin
            if not user.is_super_admin:
                _check_emergency_recovery(db, user, email)
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        print(f"CRITICAL ERROR in get_current_user: {str(e)}", file=sys.stderr)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Login Failed: {str(e)}"
        )


def _grant_default_modules(db, user: User):
    """授予新用戶預設模組權限"""
    try:
        from database import Module, UserModuleAccess
        for module_key in ["fb_ads", "gsc"]:
            module = db.query(Module).filter(Module.key == module_key).first()
            if module:
                existing = db.query(UserModuleAccess).filter(
                    UserModuleAccess.user_id == user.id,
                    UserModuleAccess.module_id == module.id,
                    UserModuleAccess.team_id.is_(None)
                ).first()
                if not existing:
                    access = UserModuleAccess(
                        user_id=user.id,
                        module_id=module.id,
                        team_id=None,
                        enabled=True
                    )
                    db.add(access)
        db.commit()
        print(f"✅ Granted default modules to {user.email}", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ Failed to grant default modules: {e}", file=sys.stderr)
        db.rollback()


def _check_emergency_recovery(db, user: User, email: str):
    """緊急恢復：當 DB 無 Super Admin 時"""
    has_any_super_admin = db.query(User).filter(User.is_super_admin == True).count() > 0
    
    if not has_any_super_admin:
        super_admin_email = os.getenv("SUPER_ADMIN_EMAIL")
        if super_admin_email and email:
            allowed_emails = [e.strip().lower() for e in super_admin_email.split(",")]
            if email.strip().lower() in allowed_emails:
                print(f"🚨 [EMERGENCY] Restoring {email} as Super Admin...", file=sys.stderr)
                user.is_super_admin = True
                user.role = UserRole.ADMIN
                db.commit()
                db.refresh(user)


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """確保用戶狀態為 ACTIVE"""
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """確保用戶為 Admin 或 Super Admin"""
    if current_user.is_super_admin:
        return current_user
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin privileges required"
        )
    return current_user


def get_super_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """確保用戶為 Super Admin"""
    if not current_user.is_super_admin:
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
    驗證用戶是否為團隊成員，回傳 Team 物件。
    
    Args:
        x_team_id: HTTP Header 中的團隊 ID
    
    Returns:
        Team 物件，或 None 如果未指定團隊
    """
    if not x_team_id:
        return None

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


# ============================================================
# Permission Check Dependencies
# ============================================================

def require_permission(permission_key: str):
    """
    依賴工廠：檢查用戶是否擁有特定權限。
    
    Usage:
        @router.get("/api/endpoint")
        async def endpoint(_: bool = Depends(require_permission("fb_ads:analytics:view"))):
            ...
    """
    def permission_checker(
        user: User = Depends(get_current_user),
        db = Depends(get_db)
    ):
        if user.is_super_admin:
            return True
        
        from services.permission_service import PermissionService
        service = PermissionService(db)
        
        if not service.check_permission(user.id, permission_key, None):
            raise HTTPException(
                status_code=403, 
                detail=f"Permission denied: {permission_key}"
            )
        return True
    
    return permission_checker


def require_module(module_key: str):
    """
    依賴工廠：檢查用戶是否有模組存取權。
    
    Usage:
        @router.get("/api/gsc/data")
        async def gsc_data(_: bool = Depends(require_module("gsc"))):
            ...
    """
    def module_checker(
        user: User = Depends(get_current_user),
        db = Depends(get_db)
    ):
        if user.is_super_admin:
            return True
        
        from services.permission_service import PermissionService
        service = PermissionService(db)
        
        if not service.check_module_access(user.id, module_key, None):
            raise HTTPException(
                status_code=403, 
                detail=f"Module access denied: {module_key}"
            )
        return True
    
    return module_checker


def require_super_admin():
    """
    依賴工廠：要求 Super Admin 權限。
    
    Usage:
        @router.delete("/api/admin/users/{user_id}")
        async def delete_user(_: bool = Depends(require_super_admin())):
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
