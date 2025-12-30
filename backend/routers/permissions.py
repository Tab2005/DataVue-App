"""權限管理 API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database import SessionLocal, Module, Permission, Role, User
from dependencies import get_db, get_current_user
from services.permission_service import PermissionService

router = APIRouter(prefix="/api/permissions", tags=["Permissions"])


# ============================================
# Schemas
# ============================================

class ModuleOut(BaseModel):
    id: str
    key: str
    name: str
    icon: Optional[str] = None
    enabled: bool

    class Config:
        from_attributes = True


class PermissionOut(BaseModel):
    id: str
    key: str
    name: str
    category: Optional[str] = None

    class Config:
        from_attributes = True


class RoleOut(BaseModel):
    id: str
    key: str
    name: str
    scope: str

    class Config:
        from_attributes = True


class ModuleAccessRequest(BaseModel):
    user_id: str
    module_key: str
    team_id: Optional[str] = None


class PermissionGrantRequest(BaseModel):
    user_id: str
    permission_key: str
    team_id: Optional[str] = None


# ============================================
# 公開 API (所有使用者)
# ============================================

@router.get("/modules", response_model=List[ModuleOut])
async def list_modules(db: Session = Depends(get_db)):
    """列出所有啟用的模組"""
    return db.query(Module).filter(Module.enabled == True).order_by(Module.sort_order).all()


@router.get("/me/modules")
async def my_modules(
    team_id: Optional[str] = Query(None, description="團隊 ID (空=個人工作區)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得當前使用者可存取的模組"""
    service = PermissionService(db)
    modules = service.get_user_modules(user.id, team_id)
    return {"modules": modules, "team_id": team_id}


@router.get("/me/permissions")
async def my_permissions(
    team_id: Optional[str] = Query(None, description="團隊 ID"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得當前使用者的所有權限"""
    service = PermissionService(db)
    permissions = service.get_user_permissions(user.id, team_id)
    return {"permissions": permissions, "team_id": team_id}


@router.get("/me/check/{permission_key:path}")
async def check_my_permission(
    permission_key: str,
    team_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """檢查當前使用者是否有指定權限"""
    service = PermissionService(db)
    has_permission = service.check_permission(user.id, permission_key, team_id)
    return {
        "has_permission": has_permission, 
        "permission_key": permission_key,
        "team_id": team_id
    }


@router.get("/me/module/{module_key}")
async def check_my_module(
    module_key: str,
    team_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """檢查當前使用者是否可存取指定模組"""
    import sys
    print(f"[DEBUG] check_my_module called: user_id={user.id}, is_super_admin={user.is_super_admin}, module_key={module_key}, team_id={team_id}", file=sys.stderr)
    
    # DIRECT Super Admin bypass - highest priority
    if user.is_super_admin:
        print(f"[DEBUG] Super Admin detected, immediate bypass - returning has_access=True", file=sys.stderr)
        return {
            "has_access": True, 
            "module_key": module_key,
            "team_id": team_id,
            "debug_is_super_admin": True,
            "bypass_reason": "super_admin"
        }
    
    service = PermissionService(db)
    has_access = service.check_module_access(user.id, module_key, team_id)
    
    print(f"[DEBUG] check_my_module result: has_access={has_access}", file=sys.stderr)
    
    return {
        "has_access": has_access, 
        "module_key": module_key,
        "team_id": team_id,
        "debug_is_super_admin": user.is_super_admin
    }


# ============================================
# 管理 API (Super Admin / Team Admin)
# ============================================

@router.get("/admin/modules", response_model=List[ModuleOut])
async def admin_list_all_modules(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出所有模組（含停用）- Admin Only"""
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Admin required")
    return db.query(Module).order_by(Module.sort_order).all()


@router.get("/admin/permissions", response_model=List[PermissionOut])
async def admin_list_permissions(
    module_key: Optional[str] = Query(None, description="篩選模組"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出所有權限定義 - Admin Only"""
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Admin required")
    
    query = db.query(Permission)
    if module_key:
        module = db.query(Module).filter(Module.key == module_key).first()
        if module:
            query = query.filter(Permission.module_id == module.id)
    
    return query.all()


@router.get("/admin/roles", response_model=List[RoleOut])
async def admin_list_roles(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出所有角色 - Admin Only"""
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Admin required")
    return db.query(Role).all()


@router.post("/admin/grant-module")
async def admin_grant_module_access(
    request: ModuleAccessRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """授予使用者模組存取權 - Admin Only"""
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Admin required")
    
    service = PermissionService(db)
    success = service.grant_module_access(
        request.user_id, request.module_key, request.team_id
    )
    
    if success:
        return {"status": "granted", "module": request.module_key}
    else:
        raise HTTPException(status_code=400, detail="Module not found")


@router.post("/admin/revoke-module")
async def admin_revoke_module_access(
    request: ModuleAccessRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """撤銷使用者模組存取權 - Admin Only"""
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Admin required")
    
    service = PermissionService(db)
    success = service.revoke_module_access(
        request.user_id, request.module_key, request.team_id
    )
    
    return {"status": "revoked", "module": request.module_key}


@router.post("/admin/grant-permission")
async def admin_grant_permission(
    request: PermissionGrantRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """授予使用者特定權限 - Admin Only"""
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Admin required")
    
    service = PermissionService(db)
    success = service.grant_permission(
        request.user_id, request.permission_key, request.team_id, user.id
    )
    
    if success:
        return {"status": "granted", "permission": request.permission_key}
    else:
        raise HTTPException(status_code=400, detail="Permission not found")


@router.post("/admin/revoke-permission")
async def admin_revoke_permission(
    request: PermissionGrantRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """撤銷使用者特定權限 - Admin Only"""
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Admin required")
    
    service = PermissionService(db)
    success = service.revoke_permission(
        request.user_id, request.permission_key, request.team_id, user.id
    )
    
    return {"status": "revoked", "permission": request.permission_key}


@router.get("/admin/user/{user_id}/modules")
async def admin_get_user_modules(
    user_id: str,
    team_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查看指定使用者的模組存取權 - Admin Only"""
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Admin required")
    
    service = PermissionService(db)
    modules = service.get_user_modules(user_id, team_id)
    return {"user_id": user_id, "team_id": team_id, "modules": modules}


@router.get("/admin/user/{user_id}/permissions")
async def admin_get_user_permissions(
    user_id: str,
    team_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查看指定使用者的權限 - Admin Only"""
    if not user.is_super_admin:
        raise HTTPException(status_code=403, detail="Super Admin required")
    
    service = PermissionService(db)
    permissions = service.get_user_permissions(user_id, team_id)
    return {"user_id": user_id, "team_id": team_id, "permissions": permissions}
