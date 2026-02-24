# backend/database/models/permission.py
"""
權限管理系統 ORM 模型（Phase 2）。
包含 Module、Permission、Role、RolePermission、UserModuleAccess、UserPermission。
"""

import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, text
from sqlalchemy.orm import relationship

from database.base import Base


class Module(Base):
    """系統模組定義（FB Ads, GSC, GA4 等）"""
    __tablename__ = "modules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(50), unique=True, nullable=False)   # 'fb_ads', 'gsc', 'ga4'
    name = Column(String(100), nullable=False)              # '廣告管理', '搜尋管理'
    description = Column(String, nullable=True)
    icon = Column(String(50), nullable=True)                # Emoji or icon class
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
    category = Column(String(50), nullable=True)            # 'feature', 'admin', 'api'
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    module = relationship("Module", backref="permissions")


class Role(Base):
    """角色定義（系統/團隊層級）"""
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(50), unique=True, nullable=False)   # 'team_owner', 'team_admin'
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    scope = Column(String(20), nullable=False)              # 'system', 'team', 'personal'
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
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)   # NULL = 個人工作區
    module_id = Column(String, ForeignKey("modules.id"), nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    user = relationship("User", backref="module_access")
    team = relationship("Team")
    module = relationship("Module")


class UserPermission(Base):
    """使用者-權限關聯（細緻化授予/撤銷）"""
    __tablename__ = "user_permissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    permission_id = Column(String, ForeignKey("permissions.id"), nullable=False)
    granted = Column(Boolean, default=True)                 # TRUE=授予, FALSE=撤銷
    granted_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))
    granted_by = Column(String, ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id], backref="custom_permissions")
    permission = relationship("Permission")
