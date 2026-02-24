from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any, Optional
import logging
import sys
import os
from database import User, Team, TeamMember, Module, UserModuleAccess, UserRole
from dependencies import get_super_admin, get_db, get_current_user
from schemas import UserResponse, TeamResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["Super Admin"],
    dependencies=[Depends(get_super_admin)]
)

@router.get("/stats")
def get_system_stats(db: Session = Depends(get_db)):
    user_count = db.query(User).count()
    team_count = db.query(Team).count()
    return {
        "user_count": user_count,
        "team_count": team_count
    }

@router.get("/users", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    # Return all users, newest first
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users

@router.get("/teams", response_model=List[TeamResponse])
def get_all_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).order_by(Team.created_at.desc()).all()
    return teams

@router.delete("/users/{user_id}")
def delete_user_force(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete associated data if needed, or rely on cascade
    db.delete(user)
    db.commit()
    return {"message": f"User {user.email} deleted"}


# ============================================
# 緊急修復端點 (不需要 Super Admin 權限，使用 Secret Key)
# ============================================

emergency_router = APIRouter(
    prefix="/api/emergency",
    tags=["Emergency"]
)

@emergency_router.post("/fix-super-admin")
def emergency_fix_super_admin(
    x_emergency_key: Optional[str] = Header(None, alias="X-Emergency-Key"),
    db: Session = Depends(get_db)
):
    """
    緊急修復超級管理員權限
    
    需要設定 X-Emergency-Key header，值必須等於 ENCRYPTION_KEY 環境變數的前 32 字元
    """
    import sys
    
    # 驗證 Emergency Key
    encryption_key = os.getenv("ENCRYPTION_KEY", "")
    expected_key = encryption_key[:32] if encryption_key else None
    
    if not expected_key:
        raise HTTPException(status_code=500, detail="Server not configured properly (missing ENCRYPTION_KEY)")
    
    if not x_emergency_key or x_emergency_key != expected_key:
        logger.warning("[SECURITY] Emergency fix attempt with invalid key")
        raise HTTPException(status_code=403, detail="Invalid emergency key")
    
    # 取得 SUPER_ADMIN_EMAIL
    super_admin_email = os.getenv("SUPER_ADMIN_EMAIL", "").strip()
    if not super_admin_email:
        raise HTTPException(status_code=400, detail="SUPER_ADMIN_EMAIL environment variable not set")
    
    emails = [e.strip().lower() for e in super_admin_email.split(",") if e.strip()]
    if not emails:
        raise HTTPException(status_code=400, detail="No valid emails in SUPER_ADMIN_EMAIL")
    
    results = []
    
    for email in emails:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            results.append({
                "email": email,
                "status": "not_found",
                "message": "User not found - will be set on first login"
            })
            continue
        
        changes = []
        
        # 設定 is_super_admin
        if not user.is_super_admin:
            user.is_super_admin = True
            changes.append("set is_super_admin=True")
        
        # 設定 role
        if user.role != UserRole.ADMIN:
            user.role = UserRole.ADMIN
            changes.append("set role=ADMIN")
        
        # 確保有所有模組存取權限
        modules = db.query(Module).all()
        for module in modules:
            access = db.query(UserModuleAccess).filter(
                UserModuleAccess.user_id == user.id,
                UserModuleAccess.module_id == module.id,
                UserModuleAccess.team_id.is_(None)
            ).first()
            
            if not access:
                access = UserModuleAccess(
                    user_id=user.id,
                    module_id=module.id,
                    team_id=None,
                    enabled=True
                )
                db.add(access)
                changes.append(f"granted {module.key}")
            elif not access.enabled:
                access.enabled = True
                changes.append(f"enabled {module.key}")
        
        results.append({
            "email": email,
            "status": "fixed" if changes else "no_change",
            "changes": changes,
            "is_super_admin": user.is_super_admin,
            "role": str(user.role)
        })
    
    db.commit()
    
    logger.info(f"[EMERGENCY] Super admin fix completed: {results}")
    
    return {
        "success": True,
        "results": results
    }


@emergency_router.get("/diagnose")
def emergency_diagnose(
    x_emergency_key: Optional[str] = Header(None, alias="X-Emergency-Key"),
    db: Session = Depends(get_db)
):
    """
    診斷權限狀態
    """
    # 驗證 Emergency Key
    encryption_key = os.getenv("ENCRYPTION_KEY", "")
    expected_key = encryption_key[:32] if encryption_key else None
    
    if not expected_key:
        raise HTTPException(status_code=500, detail="Server not configured properly")
    
    if not x_emergency_key or x_emergency_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid emergency key")
    
    # 收集診斷資訊
    users = db.query(User).all()
    modules = db.query(Module).all()
    
    user_info = []
    for u in users:
        accesses = db.query(UserModuleAccess).filter(
            UserModuleAccess.user_id == u.id,
            UserModuleAccess.team_id.is_(None)
        ).all()
        
        module_access = {}
        for a in accesses:
            module = db.query(Module).filter(Module.id == a.module_id).first()
            if module:
                module_access[module.key] = a.enabled
        
        user_info.append({
            "id": u.id,
            "email": u.email,
            "is_super_admin": u.is_super_admin,
            "role": str(u.role),
            "module_access": module_access
        })
    
    return {
        "env": {
            "SUPER_ADMIN_EMAIL": os.getenv("SUPER_ADMIN_EMAIL", "(not set)"),
            "DATABASE_URL": "PostgreSQL" if "postgresql" in os.getenv("DATABASE_URL", "").lower() else "SQLite"
        },
        "modules": [{"key": m.key, "name": m.name, "enabled": m.enabled} for m in modules],
        "users": user_info
    }

