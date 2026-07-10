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

from database.engine import (
    engine,
    SessionLocal,
    get_db,
    check_db_connection,
    DATABASE_URL,
)
from database.base import Base
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
    MetaAndromedaObservedCreative,
    MetaAndromedaScoreEvent,
    MetaAndromedaFeedbackEvent,
    MetaAndromedaReleaseRecord,
    MetaAndromedaReleaseEvent,
    MetaAndromedaWorkerEvent,
    MetaAndromedaDeadLetter,
)
from database.models.contribution import (
    ContributionDailyMetric,
    ContributionCampaignGroup,
    ContributionSnapshot,
)
from database.models.ga4_insights import (
    GA4InsightsSnapshot,
    GA4AnomalyRule,
    GA4AnomalyEvent,
)

logger = logging.getLogger(__name__)

__all__ = [
    "engine", "SessionLocal", "get_db", "check_db_connection", "DATABASE_URL",
    "Base",
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
    "MetaAndromedaObservedCreative",
    "MetaAndromedaScoreEvent",
    "MetaAndromedaFeedbackEvent",
    "MetaAndromedaReleaseRecord",
    "MetaAndromedaReleaseEvent",
    "MetaAndromedaWorkerEvent",
    "MetaAndromedaDeadLetter",
    "ContributionDailyMetric",
    "ContributionCampaignGroup",
    "ContributionSnapshot",
    "GA4InsightsSnapshot",
    "GA4AnomalyRule",
    "GA4AnomalyEvent",
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

    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        required_tables = [
            "user_integrations",
            "weekly_reports",
            "report_schedules",
            "line_bindings",
            "meta_andromeda_assets",
            "meta_andromeda_observed_creatives",
            "meta_andromeda_score_events",
            "meta_andromeda_feedback_events",
            "meta_andromeda_release_records",
            "meta_andromeda_release_events",
            "meta_andromeda_worker_events",
            "meta_andromeda_dead_letters",
            "meta_andromeda_drift_reports",
            "contribution_daily_metrics",
            "contribution_campaign_groups",
            "contribution_snapshots",
            "ga4_insights_snapshots",
            "ga4_anomaly_rules",
            "ga4_anomaly_events",
        ]
        missing = [t for t in required_tables if t not in existing_tables]

        if missing:
            if engine.dialect.name == "sqlite":
                logger.warning(f"Production safety check: Tables {missing} are missing! Running emergency create_all on SQLite...")
                Base.metadata.create_all(bind=engine)
                logger.info("✅ Missing tables created successfully via SQLite fallback.")
            else:
                logger.warning(
                    f"Production safety check: PostgreSQL tables {missing} are missing. "
                    "Skipping emergency create_all to prevent Alembic DuplicateTable conflict. "
                    "Schema upgrades must be managed via 'run_migration.py' (alembic upgrade head)."
                )
        else:
            logger.info("Production Mode: Verified all required tables exist.")
    except Exception as e:
        logger.error(f"Fail-safe table check failed: {e}. Falling back to normal flow.")

    logger.info("Production initialization completed.")