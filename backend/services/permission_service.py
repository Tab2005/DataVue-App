"""權限檢查服務"""
from typing import Optional, List
from sqlalchemy.orm import Session
from database import (
    Module, Permission, Role, RolePermission,
    UserModuleAccess, UserPermission, TeamMember, User
)


class PermissionService:
    """權限管理服務 - 處理模組存取和權限檢查"""
    
    def __init__(self, db: Session):
        self.db = db

    def check_module_access(
        self, user_id: str, module_key: str, team_id: Optional[str] = None
    ) -> bool:
        """
        檢查使用者是否可存取指定模組
        
        Args:
            user_id: 使用者 ID
            module_key: 模組 key (fb_ads, gsc, ga4)
            team_id: 團隊 ID (None = 個人工作區)
        
        Returns:
            bool: 是否有存取權
        """
        # 1. 檢查模組是否存在且啟用
        import sys
        print(f"[PERM DEBUG] check_module_access: user_id={user_id}, module_key={module_key}, team_id={team_id}", file=sys.stderr)
        
        module = self.db.query(Module).filter(
            Module.key == module_key, Module.enabled == True
        ).first()
        if not module:
            print(f"[PERM DEBUG] Module '{module_key}' not found or not enabled!", file=sys.stderr)
            return False
        
        print(f"[PERM DEBUG] Module found: id={module.id}, key={module.key}, enabled={module.enabled}", file=sys.stderr)

        # 2. 檢查 Super Admin - bypass 所有權限
        user = self.db.query(User).filter(User.id == user_id).first()
        print(f"[PERM DEBUG] User query result: user={user}, is_super_admin={user.is_super_admin if user else 'N/A'}", file=sys.stderr)
        
        if user and user.is_super_admin:
            print(f"[PERM DEBUG] Super Admin bypass - returning True", file=sys.stderr)
            return True

        # 3. 檢查 user_module_access 表
        # Handle NULL team_id correctly with is_(None) for SQLAlchemy
        query = self.db.query(UserModuleAccess).filter(
            UserModuleAccess.user_id == user_id,
            UserModuleAccess.module_id == module.id,
            UserModuleAccess.enabled == True
        )
        # Add team_id filter with proper NULL handling
        if team_id is None:
            query = query.filter(UserModuleAccess.team_id.is_(None))
        else:
            query = query.filter(UserModuleAccess.team_id == team_id)
        
        access = query.first()
        
        print(f"[PERM DEBUG] UserModuleAccess check: access={access}", file=sys.stderr)
        return access is not None


    def check_permission(
        self, user_id: str, permission_key: str, team_id: Optional[str] = None
    ) -> bool:
        """
        檢查使用者是否有指定權限
        
        權限檢查順序:
        1. Super Admin → 永遠通過
        2. 檢查 user_permissions 個別授權/撤銷
        3. 團隊工作區 → 檢查角色預設權限
        
        Args:
            user_id: 使用者 ID
            permission_key: 權限 key (如 fb_ads:analytics:view)
            team_id: 團隊 ID (None = 個人工作區)
        
        Returns:
            bool: 是否有權限
        """
        # 1. Super Admin bypass
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.is_super_admin:
            return True

        # 2. 取得權限 ID
        perm = self.db.query(Permission).filter(Permission.key == permission_key).first()
        if not perm:
            return False

        # 3. 檢查個別授權/撤銷 (最高優先級)
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

        # 5. 個人工作區 - 無特別設定則預設無權限
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
    ) -> bool:
        """
        授予使用者模組存取權
        
        Args:
            user_id: 使用者 ID
            module_key: 模組 key
            team_id: 團隊 ID (None = 個人工作區)
        
        Returns:
            bool: 是否成功
        """
        module = self.db.query(Module).filter(Module.key == module_key).first()
        if not module:
            return False

        existing = self.db.query(UserModuleAccess).filter(
            UserModuleAccess.user_id == user_id,
            UserModuleAccess.team_id == team_id,
            UserModuleAccess.module_id == module.id
        ).first()

        if existing:
            existing.enabled = True
        else:
            access = UserModuleAccess(
                user_id=user_id, 
                team_id=team_id, 
                module_id=module.id, 
                enabled=True
            )
            self.db.add(access)
        
        self.db.commit()
        return True

    def revoke_module_access(
        self, user_id: str, module_key: str, team_id: Optional[str] = None
    ) -> bool:
        """撤銷使用者模組存取權"""
        module = self.db.query(Module).filter(Module.key == module_key).first()
        if not module:
            return False

        existing = self.db.query(UserModuleAccess).filter(
            UserModuleAccess.user_id == user_id,
            UserModuleAccess.team_id == team_id,
            UserModuleAccess.module_id == module.id
        ).first()

        if existing:
            existing.enabled = False
            self.db.commit()
        
        return True

    def get_user_modules(self, user_id: str, team_id: Optional[str] = None) -> List[str]:
        """
        取得使用者可存取的模組列表
        
        Returns:
            List[str]: 模組 key 列表
        """
        # Super Admin 可存取所有啟用的模組
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.is_super_admin:
            modules = self.db.query(Module).filter(Module.enabled == True).all()
            return [m.key for m in modules]

        # 一般使用者 - 查詢 user_module_access
        access_list = self.db.query(UserModuleAccess).filter(
            UserModuleAccess.user_id == user_id,
            UserModuleAccess.team_id == team_id,
            UserModuleAccess.enabled == True
        ).all()

        return [a.module.key for a in access_list if a.module.enabled]

    def get_user_permissions(
        self, user_id: str, team_id: Optional[str] = None
    ) -> List[str]:
        """
        取得使用者的所有權限列表
        
        Returns:
            List[str]: 權限 key 列表
        """
        permissions = set()
        
        # Super Admin - 所有權限
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.is_super_admin:
            all_perms = self.db.query(Permission).all()
            return [p.key for p in all_perms]
        
        # 團隊工作區 - 角色權限
        if team_id:
            membership = self.db.query(TeamMember).filter(
                TeamMember.user_id == user_id,
                TeamMember.team_id == team_id
            ).first()
            if membership:
                role_key = f"team_{membership.role.value}"
                role = self.db.query(Role).filter(Role.key == role_key).first()
                if role:
                    role_perms = self.db.query(RolePermission).filter(
                        RolePermission.role_id == role.id
                    ).all()
                    for rp in role_perms:
                        permissions.add(rp.permission.key)
        
        # 個別授權
        user_perms = self.db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.team_id == team_id
        ).all()
        
        for up in user_perms:
            if up.granted:
                permissions.add(up.permission.key)
            else:
                permissions.discard(up.permission.key)
        
        return list(permissions)

    def grant_permission(
        self, 
        user_id: str, 
        permission_key: str, 
        team_id: Optional[str] = None,
        granted_by: Optional[str] = None
    ) -> bool:
        """授予使用者特定權限"""
        perm = self.db.query(Permission).filter(Permission.key == permission_key).first()
        if not perm:
            return False

        existing = self.db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.team_id == team_id,
            UserPermission.permission_id == perm.id
        ).first()

        if existing:
            existing.granted = True
            existing.granted_by = granted_by
        else:
            user_perm = UserPermission(
                user_id=user_id,
                team_id=team_id,
                permission_id=perm.id,
                granted=True,
                granted_by=granted_by
            )
            self.db.add(user_perm)
        
        self.db.commit()
        return True

    def revoke_permission(
        self, 
        user_id: str, 
        permission_key: str, 
        team_id: Optional[str] = None,
        granted_by: Optional[str] = None
    ) -> bool:
        """撤銷使用者特定權限"""
        perm = self.db.query(Permission).filter(Permission.key == permission_key).first()
        if not perm:
            return False

        existing = self.db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.team_id == team_id,
            UserPermission.permission_id == perm.id
        ).first()

        if existing:
            existing.granted = False
            existing.granted_by = granted_by
        else:
            user_perm = UserPermission(
                user_id=user_id,
                team_id=team_id,
                permission_id=perm.id,
                granted=False,
                granted_by=granted_by
            )
            self.db.add(user_perm)
        
        self.db.commit()
        return True
