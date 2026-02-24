"""add_user_integrations_and_composite_indexes

Revision ID: 20260223_p3_integrations_indexes
Revises: fe8441e71f69
Create Date: 2026-02-23

實作項目：
  5.1 — 新增 user_integrations 表（UserIntegration 模型）
  5.2 — 新增複合索引至高頻查詢路徑
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime
import logging

logger = logging.getLogger("alembic.migration")

# revision identifiers
revision = "20260223_p3_integrations_indexes"
down_revision = "fe8441e71f69"
branch_labels = None
depends_on = None


# ─────────────────────────────────────────────────────────────────────────────
# 5.1 UserIntegration 表結構
# ─────────────────────────────────────────────────────────────────────────────

def upgrade() -> None:
    # ── 5.1：建立 user_integrations 表 ───────────────────────────────────
    op.create_table(
        "user_integrations",
        sa.Column("id", sa.String(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.String(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expiry", sa.DateTime(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint(
            "user_id", "provider",
            name="uq_user_integration_provider",
        ),
    )

    # 主要查詢複合索引
    op.create_index(
        "ix_user_integrations_lookup",
        "user_integrations",
        ["user_id", "provider"],
        unique=True,
    )

    # ── 注意：Token 資料遷移已移至 20260224_fix_integrations_migration_compat.py ──
    # 原本此處使用 SQLite 專用的 randomblob() / hex() / json_object() 函式，
    # 在 PostgreSQL 環境執行會失敗。已改由新腳本使用 Python uuid 模組跨方言相容處理。

    # ── 5.2：新增高頻查詢複合索引 ────────────────────────────────────────
    # 注意：此腳本的 down_revision 指向 fe8441e71f69（早於 20260106_add_permissions_tables）。
    # 在全新 DB 升級時，user_module_access 等表可能尚未建立；
    # 使用 try/except 保護，確保在 merge 後的補充執行中可正常建立索引。

    # user_module_access：常以 (user_id, team_id, module_id) 三欄查詢
    try:
        op.create_index(
            "ix_user_module_access_composite",
            "user_module_access",
            ["user_id", "team_id", "module_id"],
            unique=False,
        )
    except Exception as e:
        logger.warning("ix_user_module_access_composite 索引建立跳過（表可能尚未存在或索引已存在）：%s", e)

    # team_members：依 user_id 反查所有團隊
    try:
        op.create_index(
            "ix_team_members_user_id",
            "team_members",
            ["user_id"],
            unique=False,
        )
    except Exception as e:
        logger.warning("ix_team_members_user_id 索引建立跳過：%s", e)

    # saved_views：使用者在特定團隊的所有視圖
    try:
        op.create_index(
            "ix_saved_views_user_team",
            "saved_views",
            ["user_id", "team_id"],
            unique=False,
        )
    except Exception as e:
        logger.warning("ix_saved_views_user_team 索引建立跳過：%s", e)


def downgrade() -> None:
    # 5.2 索引回滾
    op.drop_index("ix_saved_views_user_team", table_name="saved_views")
    op.drop_index("ix_team_members_user_id", table_name="team_members")
    op.drop_index("ix_user_module_access_composite", table_name="user_module_access")

    # 5.1 資料表回滾
    op.drop_index("ix_user_integrations_lookup", table_name="user_integrations")
    op.drop_table("user_integrations")
