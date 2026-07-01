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
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "user_integrations" not in existing_tables:
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
    # 在全新 DB 升級時，user_module_access 尚未建立。
    #
    # 2026-07-01 修復：原本這裡對三個 create_index 都包了 try/except 想做
    # 「表可能不存在就跳過」的防呆，這在 SQLite 上恰好能繼續往下跑，但在
    # PostgreSQL 上一旦某條語句失敗，整個交易會被標記為 aborted，後續所有
    # 語句（包含其他兩個原本會成功的索引、以及 Alembic 自動更新
    # alembic_version 的 UPDATE）都會連帶失敗，整支 migration 直接中止。
    # 已用全新 PostgreSQL 18 資料庫實測重現並確認此修復可解決。
    #
    # user_module_access 在此時間點確定尚未建立（由 20260106_add_permissions_tables
    # 之後才建立），故直接移除這個必定失敗的嘗試；改由
    # 20260701_consolidate_legacy_schema_patches.py 在該表確定存在後補建此索引。
    # team_members（0001 建立）與 saved_views（230a10d75894 建立）在此時間點
    # 都已確定存在，故改為直接呼叫，不再需要防呆。

    # team_members：依 user_id 反查所有團隊
    op.create_index(
        "ix_team_members_user_id",
        "team_members",
        ["user_id"],
        unique=False,
    )

    # saved_views：使用者在特定團隊的所有視圖
    op.create_index(
        "ix_saved_views_user_team",
        "saved_views",
        ["user_id", "team_id"],
        unique=False,
    )


def downgrade() -> None:
    # 5.2 索引回滾
    # 注意：ix_user_module_access_composite 已改由
    # 20260701_consolidate_legacy_schema_patches.py 建立，此處不再處理。
    op.drop_index("ix_saved_views_user_team", table_name="saved_views")
    op.drop_index("ix_team_members_user_id", table_name="team_members")

    # 5.1 資料表回滾
    op.drop_index("ix_user_integrations_lookup", table_name="user_integrations")
    op.drop_table("user_integrations")
