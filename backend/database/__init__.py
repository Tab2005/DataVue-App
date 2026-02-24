# backend/database/__init__.py
"""
資料庫套件的公開 API。
從此處匯入所有模型與資料庫工具，維持向後相容性。

原先的 database.py（324 行）已拆分為：
  database/base.py        — DeclarativeBase
  database/engine.py      — 引擎、SessionLocal、get_db
  database/models/user.py       — User, UserRole, UserStatus
  database/models/team.py       — Team, TeamMember, TeamInvite
  database/models/view.py       — SavedView, PageTitle
  database/models/permission.py — Module, Permission, Role, RolePermission,
                                  UserModuleAccess, UserPermission
"""

import os
import logging

# ── 引擎 & Session ────────────────────────────────────────────────────────
from database.engine import (
    engine,
    SessionLocal,
    get_db,
    check_db_connection,
    DATABASE_URL,
)

# ── 聲明基底 ──────────────────────────────────────────────────────────────
from database.base import Base

# ── 模型 ─────────────────────────────────────────────────────────────────
from database.models.user import User, UserRole, UserStatus
from database.models.team import Team, TeamMember, TeamInvite
from database.models.view import SavedView, PageTitle
from database.models.permission import (
    Module,
    Permission,
    Role,
    RolePermission,
    UserModuleAccess,
    UserPermission,
)
from database.models.integration import UserIntegration

logger = logging.getLogger(__name__)

__all__ = [
    # 引擎 & Session
    "engine", "SessionLocal", "get_db", "check_db_connection", "DATABASE_URL",
    # Base
    "Base",
    # 模型
    "User", "UserRole", "UserStatus",
    "Team", "TeamMember", "TeamInvite",
    "SavedView", "PageTitle",
    "Module", "Permission", "Role", "RolePermission",
    "UserModuleAccess", "UserPermission",
    "UserIntegration",
    # 初始化函式
    "init_db",
]


def init_db():
    """
    初始化資料庫 schema。
    開發模式（DEBUG_MODE=true）使用 create_all() 快速建表；
    生產環境依賴 Alembic 遷移管理。
    """
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    if DEBUG_MODE:
        logger.info("Dev Mode detected: Running Base.metadata.create_all().")
        Base.metadata.create_all(bind=engine)
    else:
        logger.info("Production Mode detected: Skipping metadata.create_all() (Use migrations).")
