# 權限管理系統 - Phase 2 & 3 實作指南

**專案**: DataVue  
**版本**: v2.0 權限系統  
**日期**: 2025-12-29  
**注意**: 本地端測試，不推送至 Git

---

## 實作順序

```
Step 1: 資料庫 Models (database.py)
  ↓
Step 2: 初始資料 Seeding
  ↓
Step 3: 權限檢查 Service
  ↓
Step 4: API Endpoints
  ↓
Step 5: 前端 Hooks & 路由守衛
  ↓
Step 6: 管理介面 UI
```

---

## Step 1: 資料庫 Models

在 `backend/database.py` 新增以下 Models：

### 1.1 新增 Models

```python
# ============================================
# 權限管理系統 Models (Phase 2)
# ============================================

class Module(Base):
    """系統模組定義（FB Ads, GSC, GA4 等）"""
    __tablename__ = "modules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(50), unique=True, nullable=False)  # 'fb_ads', 'gsc', 'ga4'
    name = Column(String(100), nullable=False)  # '廣告管理', '搜尋管理'
    description = Column(String, nullable=True)
    icon = Column(String(50), nullable=True)  # Emoji or icon class
    enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))


class Permission(Base):
    """權限定義（模組:功能:動作）"""
    __tablename__ = "permissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    module_id = Column(String, ForeignKey("modules.id"), nullable=False)
    key = Column(String(100), unique=True, nullable=False)  # 'fb_ads:analytics:view'
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    category = Column(String(50), nullable=True)  # 'feature', 'admin', 'api'
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    module = relationship("Module", backref="permissions")


class Role(Base):
    """角色定義（系統/團隊層級）"""
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(50), unique=True, nullable=False)  # 'team_owner', 'team_admin'
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    scope = Column(String(20), nullable=False)  # 'system', 'team', 'personal'
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))


class RolePermission(Base):
    """角色-權限關聯"""
    __tablename__ = "role_permissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id = Column(String, ForeignKey("roles.id"), nullable=False)
    permission_id = Column(String, ForeignKey("permissions.id"), nullable=False)

    role = relationship("Role", backref="role_permissions")
    permission = relationship("Permission")


class UserModuleAccess(Base):
    """使用者-模組存取權"""
    __tablename__ = "user_module_access"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)  # NULL = 個人工作區
    module_id = Column(String, ForeignKey("modules.id"), nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    user = relationship("User", backref="module_access")
    team = relationship("Team")
    module = relationship("Module")


class UserPermission(Base):
    """使用者-權限關聯（細緻化授權/撤銷）"""
    __tablename__ = "user_permissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    permission_id = Column(String, ForeignKey("permissions.id"), nullable=False)
    granted = Column(Boolean, default=True)  # TRUE=授予, FALSE=撤銷
    granted_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))
    granted_by = Column(String, ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id], backref="custom_permissions")
    permission = relationship("Permission")
```

### 1.2 測試指令

```bash
# 本地端測試 - 重新建立資料表
cd backend
python -c "from database import init_db; init_db()"
```

---

## Step 2: 初始資料 Seeding

建立 `backend/seeds/permission_seeds.py`：

```python
"""權限系統初始資料"""

MODULES = [
    {"key": "fb_ads", "name": "FB Ads 廣告管理", "icon": "📊", "sort_order": 1},
    {"key": "gsc", "name": "Google Search Console", "icon": "🔍", "sort_order": 2},
    {"key": "ga4", "name": "Google Analytics 4", "icon": "📈", "sort_order": 3, "enabled": False},
]

PERMISSIONS = {
    "fb_ads": [
        {"key": "fb_ads:analytics:view", "name": "數據查看", "category": "feature"},
        {"key": "fb_ads:account:manage", "name": "帳號管理", "category": "admin"},
        {"key": "fb_ads:report:generate", "name": "報表生成", "category": "feature"},
        {"key": "fb_ads:view:create", "name": "新增視角", "category": "feature"},
        {"key": "fb_ads:view:edit", "name": "編輯視角", "category": "feature"},
        {"key": "fb_ads:ai:use", "name": "AI 分析師", "category": "feature"},
    ],
    "gsc": [
        {"key": "gsc:site:connect", "name": "連接站點", "category": "admin"},
        {"key": "gsc:analytics:view", "name": "數據查看", "category": "feature"},
        {"key": "gsc:keyword:view", "name": "關鍵字分析", "category": "feature"},
        {"key": "gsc:page:view", "name": "頁面分析", "category": "feature"},
        {"key": "gsc:trend:view", "name": "趨勢分析", "category": "feature"},
    ],
    "ga4": [
        {"key": "ga4:property:connect", "name": "連接屬性", "category": "admin"},
        {"key": "ga4:analytics:view", "name": "數據查看", "category": "feature"},
    ],
}

ROLES = [
    {"key": "team_owner", "name": "團隊擁有者", "scope": "team"},
    {"key": "team_admin", "name": "團隊管理員", "scope": "team"},
    {"key": "team_member", "name": "團隊成員", "scope": "team"},
    {"key": "team_viewer", "name": "團隊檢視者", "scope": "team"},
]

# 角色預設權限矩陣
ROLE_PERMISSIONS = {
    "team_owner": ["*"],  # 全部權限
    "team_admin": [
        "fb_ads:analytics:view", "fb_ads:account:manage", "fb_ads:report:generate",
        "fb_ads:view:create", "fb_ads:view:edit", "fb_ads:ai:use",
        "gsc:site:connect", "gsc:analytics:view", "gsc:keyword:view",
        "gsc:page:view", "gsc:trend:view",
    ],
    "team_member": [
        "fb_ads:analytics:view", "fb_ads:report:generate",
        "fb_ads:view:create", "fb_ads:view:edit", "fb_ads:ai:use",
        "gsc:analytics:view", "gsc:keyword:view", "gsc:page:view", "gsc:trend:view",
    ],
    "team_viewer": [
        "fb_ads:analytics:view", "fb_ads:report:generate",
        "gsc:analytics:view", "gsc:keyword:view", "gsc:page:view", "gsc:trend:view",
    ],
}
```

### Seeding 執行腳本

建立 `backend/seed_permissions.py`：

```python
"""執行權限系統初始資料 Seeding"""
from database import SessionLocal, Module, Permission, Role, RolePermission
from seeds.permission_seeds import MODULES, PERMISSIONS, ROLES, ROLE_PERMISSIONS

def seed_permissions():
    db = SessionLocal()
    try:
        # 1. Seed Modules
        module_map = {}
        for m in MODULES:
            existing = db.query(Module).filter(Module.key == m["key"]).first()
            if not existing:
                module = Module(**m)
                db.add(module)
                db.flush()
                module_map[m["key"]] = module.id
                print(f"✅ Created module: {m['key']}")
            else:
                module_map[m["key"]] = existing.id
                print(f"⏭️ Module exists: {m['key']}")

        # 2. Seed Permissions
        permission_map = {}
        for module_key, perms in PERMISSIONS.items():
            for p in perms:
                existing = db.query(Permission).filter(Permission.key == p["key"]).first()
                if not existing:
                    perm = Permission(
                        module_id=module_map[module_key],
                        **p
                    )
                    db.add(perm)
                    db.flush()
                    permission_map[p["key"]] = perm.id
                    print(f"  ✅ Created permission: {p['key']}")
                else:
                    permission_map[p["key"]] = existing.id

        # 3. Seed Roles
        role_map = {}
        for r in ROLES:
            existing = db.query(Role).filter(Role.key == r["key"]).first()
            if not existing:
                role = Role(**r)
                db.add(role)
                db.flush()
                role_map[r["key"]] = role.id
                print(f"✅ Created role: {r['key']}")
            else:
                role_map[r["key"]] = existing.id

        # 4. Seed Role Permissions
        for role_key, perms in ROLE_PERMISSIONS.items():
            role_id = role_map.get(role_key)
            if not role_id:
                continue
            
            if perms == ["*"]:
                # 全部權限
                perms = list(permission_map.keys())
            
            for perm_key in perms:
                perm_id = permission_map.get(perm_key)
                if not perm_id:
                    continue
                existing = db.query(RolePermission).filter(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == perm_id
                ).first()
                if not existing:
                    rp = RolePermission(role_id=role_id, permission_id=perm_id)
                    db.add(rp)

        db.commit()
        print("\n🎉 Permission seeding completed!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_permissions()
```

### 執行 Seeding

```bash
cd backend
python seed_permissions.py
```

---

## Step 3: 權限檢查 Service

建立 `backend/services/permission_service.py`：

```python
"""權限檢查服務"""
from typing import Optional, List
from sqlalchemy.orm import Session
from database import (
    Module, Permission, Role, RolePermission,
    UserModuleAccess, UserPermission, TeamMember, User
)


class PermissionService:
    def __init__(self, db: Session):
        self.db = db

    def check_module_access(
        self, user_id: str, module_key: str, team_id: Optional[str] = None
    ) -> bool:
        """檢查使用者是否可存取指定模組"""
        # 1. 檢查模組是否存在且啟用
        module = self.db.query(Module).filter(
            Module.key == module_key, Module.enabled == True
        ).first()
        if not module:
            return False

        # 2. 檢查 Super Admin
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.is_super_admin:
            return True

        # 3. 檢查 user_module_access
        access = self.db.query(UserModuleAccess).filter(
            UserModuleAccess.user_id == user_id,
            UserModuleAccess.team_id == team_id,
            UserModuleAccess.module_id == module.id,
            UserModuleAccess.enabled == True
        ).first()
        
        return access is not None

    def check_permission(
        self, user_id: str, permission_key: str, team_id: Optional[str] = None
    ) -> bool:
        """檢查使用者是否有指定權限"""
        # 1. Super Admin bypass
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.is_super_admin:
            return True

        # 2. 取得權限 ID
        perm = self.db.query(Permission).filter(Permission.key == permission_key).first()
        if not perm:
            return False

        # 3. 檢查個別授權/撤銷
        user_perm = self.db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.team_id == team_id,
            UserPermission.permission_id == perm.id
        ).first()
        
        if user_perm:
            return user_perm.granted

        # 4. 團隊工作區 - 檢查角色預設權限
        if team_id:
            membership = self.db.query(TeamMember).filter(
                TeamMember.user_id == user_id,
                TeamMember.team_id == team_id
            ).first()
            if membership:
                role_key = f"team_{membership.role.value}"
                return self._role_has_permission(role_key, perm.id)

        # 5. 個人工作區 - 預設允許基本權限
        # (可根據訂閱方案調整)
        return False

    def _role_has_permission(self, role_key: str, permission_id: str) -> bool:
        """檢查角色是否有指定權限"""
        role = self.db.query(Role).filter(Role.key == role_key).first()
        if not role:
            return False
        
        rp = self.db.query(RolePermission).filter(
            RolePermission.role_id == role.id,
            RolePermission.permission_id == permission_id
        ).first()
        return rp is not None

    def grant_module_access(
        self, user_id: str, module_key: str, team_id: Optional[str] = None
    ):
        """授予模組存取權"""
        module = self.db.query(Module).filter(Module.key == module_key).first()
        if not module:
            raise ValueError(f"Module {module_key} not found")

        existing = self.db.query(UserModuleAccess).filter(
            UserModuleAccess.user_id == user_id,
            UserModuleAccess.team_id == team_id,
            UserModuleAccess.module_id == module.id
        ).first()

        if existing:
            existing.enabled = True
        else:
            access = UserModuleAccess(
                user_id=user_id, team_id=team_id, module_id=module.id, enabled=True
            )
            self.db.add(access)
        
        self.db.commit()

    def get_user_modules(self, user_id: str, team_id: Optional[str] = None) -> List[str]:
        """取得使用者可存取的模組列表"""
        # Super Admin
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.is_super_admin:
            return [m.key for m in self.db.query(Module).filter(Module.enabled == True).all()]

        access_list = self.db.query(UserModuleAccess).filter(
            UserModuleAccess.user_id == user_id,
            UserModuleAccess.team_id == team_id,
            UserModuleAccess.enabled == True
        ).all()

        return [a.module.key for a in access_list if a.module.enabled]
```

---

## Step 4: API Endpoints

建立 `backend/routers/permissions.py`：

```python
"""權限管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database import SessionLocal, Module, Permission, User
from auth import get_current_user
from services.permission_service import PermissionService

router = APIRouter(prefix="/api/permissions", tags=["permissions"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Schemas ---
class ModuleOut(BaseModel):
    id: str
    key: str
    name: str
    icon: Optional[str]
    enabled: bool

    class Config:
        from_attributes = True

class PermissionOut(BaseModel):
    id: str
    key: str
    name: str
    category: Optional[str]

    class Config:
        from_attributes = True

# --- Endpoints ---
@router.get("/modules", response_model=List[ModuleOut])
async def list_modules(db: Session = Depends(get_db)):
    """列出所有啟用的模組"""
    return db.query(Module).filter(Module.enabled == True).order_by(Module.sort_order).all()

@router.get("/me/modules")
async def my_modules(
    team_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得當前使用者可存取的模組"""
    service = PermissionService(db)
    modules = service.get_user_modules(user.id, team_id)
    return {"modules": modules}

@router.get("/me/check/{permission_key}")
async def check_my_permission(
    permission_key: str,
    team_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """檢查當前使用者是否有指定權限"""
    service = PermissionService(db)
    has_permission = service.check_permission(user.id, permission_key, team_id)
    return {"has_permission": has_permission, "permission_key": permission_key}
```

### 註冊 Router

在 `backend/main.py` 加入：

```python
from routers import permissions

app.include_router(permissions.router)
```

---

## Step 5: 權限檢查 Decorator

在 `backend/dependencies.py` 新增：

```python
from functools import wraps
from fastapi import HTTPException, Depends
from database import SessionLocal
from services.permission_service import PermissionService
from auth import get_current_user

def require_permission(permission_key: str):
    """權限檢查 Decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('user') or kwargs.get('current_user')
            db = kwargs.get('db')
            team_id = kwargs.get('team_id')
            
            if not user or not db:
                raise HTTPException(status_code=401, detail="Unauthorized")
            
            service = PermissionService(db)
            if not service.check_permission(user.id, permission_key, team_id):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {permission_key}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_module(module_key: str):
    """模組存取檢查 Decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('user') or kwargs.get('current_user')
            db = kwargs.get('db')
            team_id = kwargs.get('team_id')
            
            if not user or not db:
                raise HTTPException(status_code=401, detail="Unauthorized")
            
            service = PermissionService(db)
            if not service.check_module_access(user.id, module_key, team_id):
                raise HTTPException(
                    status_code=403,
                    detail=f"Module access denied: {module_key}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## Step 6: 本地端測試

### 測試流程

```bash
# 1. 確保在 backend 目錄
cd backend

# 2. 啟動資料庫（重建 tables）
python -c "from database import init_db; init_db()"

# 3. 執行 Seeding
python seed_permissions.py

# 4. 啟動後端
python main.py

# 5. 測試 API（另開終端機）
curl http://localhost:8000/api/permissions/modules
```

### 預期輸出

```json
[
  {"id": "...", "key": "fb_ads", "name": "FB Ads 廣告管理", "icon": "📊", "enabled": true},
  {"id": "...", "key": "gsc", "name": "Google Search Console", "icon": "🔍", "enabled": true}
]
```

---

## 下一步：Phase 3 管理介面

Phase 2 完成後，再進行 Phase 3：
1. 超級管理員後台 - 模組/權限管理
2. 團隊權限配置頁面
3. 前端權限 Hooks
