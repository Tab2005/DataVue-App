from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import SessionLocal, User, UserRole, UserStatus, Team, TeamMember
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
import sys
import traceback

from functools import lru_cache
import logging

# Configure Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reuse the existing security scheme
security = HTTPBearer()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@lru_cache(maxsize=128)
def _verify_token_cached(token: str):
    """Internal helper to verify token with caching."""
    return id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=60)

def verify_google_token_basic(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Basic verification that returns the full Google Token Info (ID, Email, Name).
    Uses LRU cache to reduce latency and redundant API calls.
    """
    token = credentials.credentials
    try:
        logger.debug(f"Verifying Google Token: {token[:10]}...")
        
        # Use cached verification
        id_info = _verify_token_cached(token)
        
        email = id_info.get('email', 'unknown')
        masked_email = f"{email[:3]}***@{email.split('@')[-1]}" if '@' in email else email
        logger.info(f"Token Verified. User: {masked_email}")
        return id_info
    except Exception as e:
        logger.error(f"Token Verification Critical Error: {type(e).__name__}: {e}")
        # CRITICAL: We must ensure this raises a standard HTTPException that CORS middleware can handle
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
    Fetch the full User object from DB based on the verified Google ID.
    Syncs basic profile info (Email, Name) from Google Token.
    """
    try:
        google_id = id_info['sub']
        email = id_info.get('email')
        name = id_info.get('name')
        user = db.query(User).filter(User.google_id == google_id).first()
        
        if not user:
            print(f"DEBUG: User {google_id} not found. Auto-Registering...", file=sys.stderr)
            
            # Check if this is the FIRST user ever (Global Super Admin candidate)
            user_count = db.query(User).count()
            new_role = UserRole.ADMIN if user_count == 0 else UserRole.VIEWER
            
            user = User(
                google_id=google_id, 
                email=email,
                name=name,
                role=new_role,
                status=UserStatus.ACTIVE,
                is_super_admin=(user_count == 0) # First user is Super Admin
            )
            
            # [Security hardening] Check Environment Variable for Forced Super Admin
            # This ensures that even if the DB is not empty, the owner can reclaim Super Admin status
            super_admin_email = os.getenv("SUPER_ADMIN_EMAIL")
            if super_admin_email and email and super_admin_email.strip().lower() == email.strip().lower():
                print(f"🔒 SUPER_ADMIN_EMAIL match detected! Promoting {email} to Super Admin.", file=sys.stderr)
                user.is_super_admin = True
                user.role = UserRole.ADMIN # Ensure they are also an Admin
            
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Auto-Registered: {name} ({email}) as {new_role}", file=sys.stderr)
            
            # Grant default modules to new user (fb_ads, gsc)
            try:
                from database import Module, UserModuleAccess
                for module_key in ["fb_ads", "gsc"]:
                    module = db.query(Module).filter(Module.key == module_key).first()
                    if module:
                        # Check if access already exists to prevent IntegrityError
                        # Use .is_(None) for proper NULL comparison in SQLAlchemy
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
                masked_email = f"{email[:3]}***@{email.split('@')[-1]}" if email and '@' in email else "unknown"
                print(f"✅ Granted default modules (fb_ads, gsc) to {masked_email}", file=sys.stderr)
            except Exception as mod_err:
                print(f"⚠️ Failed to grant default modules: {mod_err}", file=sys.stderr)
                db.rollback()  # Rollback on error to prevent transaction issues


        else:
            # Auto-Update Profile if missing or changed
            if user.email != email or user.name != name:
                 user.email = email
                 user.name = name
                 # Not committing updates to avoid write-conflicts
            
            # [ENHANCED SUPER ADMIN SYNC]
            # 每次登入時檢查 SUPER_ADMIN_EMAIL 環境變數
            # 確保環境變數中指定的用戶始終擁有超級管理員權限
            
            if not user.is_super_admin:
                super_admin_email = os.getenv("SUPER_ADMIN_EMAIL")
                if super_admin_email and email:
                    # 支援逗號分隔的多個 Email
                    allowed_emails = [e.strip().lower() for e in super_admin_email.split(",")]
                    if email.strip().lower() in allowed_emails:
                        masked_email = f"{email[:3]}***@{email.split('@')[-1]}" if email and '@' in email else "unknown"
                        print(f"🔒 [SUPER_ADMIN_SYNC] Restoring Super Admin status for {masked_email}...", file=sys.stderr)
                        user.is_super_admin = True
                        user.role = UserRole.ADMIN
                        
                        # 同時確保有所有模組的存取權限
                        try:
                            from database import Module, UserModuleAccess
                            modules = db.query(Module).all()
                            for module in modules:
                                existing_access = db.query(UserModuleAccess).filter(
                                    UserModuleAccess.user_id == user.id,
                                    UserModuleAccess.module_id == module.id,
                                    UserModuleAccess.team_id.is_(None)
                                ).first()
                                if not existing_access:
                                    access = UserModuleAccess(
                                        user_id=user.id,
                                        module_id=module.id,
                                        team_id=None,
                                        enabled=True
                                    )
                                    db.add(access)
                                elif not existing_access.enabled:
                                    existing_access.enabled = True
                        except Exception as mod_err:
                            print(f"⚠️ Failed to sync module access: {mod_err}", file=sys.stderr)
                        
                        db.commit()
                        db.refresh(user)
                        print(f"✅ [SUPER_ADMIN_SYNC] {email} restored as Super Admin with all modules.", file=sys.stderr)
        
        print(f"DEBUG: Returning user {user.email}, is_super_admin={user.is_super_admin}, role={user.role}", file=sys.stderr)
        return user
    except Exception as e:
        print(f"CRITICAL ERROR in get_current_user: {str(e)}", file=sys.stderr, flush=True)
        try:
             with open("debug_auth.log", "w", encoding="utf-8") as f:
                 f.write(f"Auth Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}")
        except:
            pass
        # Raise as 401/400 to break the 500 loop
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Login Logic Failed: {str(e)}"
        )

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.status != UserStatus.ACTIVE:
        print(f"DEBUG: User {current_user.google_id} is INACTIVE", file=sys.stderr)
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    # Allow Super Admin to bypass specific role checks
    if current_user.is_super_admin:
        return current_user

    print(f"DEBUG: Checking Admin Privileges for {current_user.google_id}. Role: {current_user.role}", file=sys.stderr)
    if current_user.role != UserRole.ADMIN:
        print(f"Access Denied: User is not ADMIN", file=sys.stderr)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_super_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_super_admin:
        print(f"Access Denied: User {current_user.email} is NOT Super Admin", file=sys.stderr)
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

