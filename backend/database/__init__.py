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
from database.models.report import WeeklyReport, ReportSchedule
from database.models.line_binding import LineBinding
from database.models.meta_andromeda import (
    MetaAndromedaAsset,
    MetaAndromedaScoreEvent,
    MetaAndromedaFeedbackEvent,
    MetaAndromedaReleaseRecord,
    MetaAndromedaReleaseEvent,
    MetaAndromedaWorkerEvent,
    MetaAndromedaDeadLetter,
)

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
    "WeeklyReport",
    "ReportSchedule",
    "LineBinding",
    "MetaAndromedaAsset",
    "MetaAndromedaScoreEvent",
    "MetaAndromedaFeedbackEvent",
    "MetaAndromedaReleaseRecord",
    "MetaAndromedaReleaseEvent",
    "MetaAndromedaWorkerEvent",
    "MetaAndromedaDeadLetter",
    # 初始化函式
    "init_db",
]


def init_db():
    """
    初始化資料庫 schema。
    開發模式（DEBUG_MODE=true）使用 create_all() 快速建表；
    生產環境依賴 Alembic 遷移管理，但加入緊急降級機制（Fail-safe）。
    """
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    if DEBUG_MODE:
        logger.info("Dev Mode detected: Running Base.metadata.create_all().")
        Base.metadata.create_all(bind=engine)
        return

    # 生產環境：先檢查核心新表是否存在 (e.g. weekly_reports)
    # 若缺失則嘗試補足，確保功能不中斷
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        required_tables = ["user_integrations", "weekly_reports", "report_schedules", "line_bindings"]
        missing = [t for t in required_tables if t not in existing_tables]
        
        if missing:
            logger.warning(f"Production safety check: Tables {missing} are missing! Running emergency create_all...")
            # create_all 僅會建立「不存在」的表，對現有資料安全
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Missing tables created successfully.")
        else:
            logger.info("Production Mode: Verified all required tables exist.")
            
        # ── 欄位檢查 (Fail-safe for adding columns to existing tables) ──
        user_columns = [c["name"] for c in inspector.get_columns("users")]
        if "line_user_id" not in user_columns:
            logger.warning("Production safety check: Column 'line_user_id' missing in 'users' table! Adding it...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN line_user_id VARCHAR"))
                conn.commit()
            logger.info("✅ Column 'line_user_id' added successfully.")

        # ── 欄位檢查 (ReportSchedule) ──
        schedule_columns = [c["name"] for c in inspector.get_columns("report_schedules")]
        if "is_notify_line" not in schedule_columns:
            logger.warning("Production safety check: Column 'is_notify_line' missing in 'report_schedules'! Adding it...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE report_schedules ADD COLUMN is_notify_line BOOLEAN DEFAULT FALSE"))
                conn.commit()
            logger.info("✅ Column 'is_notify_line' added successfully.")

    except Exception as e:
        logger.error(f"Fail-safe table check failed: {e}. Falling back to normal flow.")

    logger.info("Production initialization completed.")
