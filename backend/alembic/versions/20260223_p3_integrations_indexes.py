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

    # ── 遷移現有 Token 資料（Facebook）────────────────────────────────────
    # 注意：僅遷移 fb_access_token 不為 NULL 的使用者
    # refresh_token 與 extra_data（app_id, app_secret）一併遷移
    op.execute("""
        INSERT INTO user_integrations
            (id, user_id, provider, access_token, refresh_token, token_expiry,
             extra_data, created_at)
        SELECT
            lower(hex(randomblob(4))) || '-'
                || lower(hex(randomblob(2))) || '-'
                || lower(hex(randomblob(2))) || '-'
                || lower(hex(randomblob(2))) || '-'
                || lower(hex(randomblob(6))),
            id,
            'facebook',
            fb_access_token,
            NULL,
            token_expires_at,
            json_object(
                'app_id',    COALESCE(fb_app_id, ''),
                'app_secret', COALESCE(fb_app_secret, '')
            ),
            CURRENT_TIMESTAMP
        FROM users
        WHERE fb_access_token IS NOT NULL
    """)

    # 遷移 GSC Token
    op.execute("""
        INSERT INTO user_integrations
            (id, user_id, provider, access_token, refresh_token, token_expiry,
             extra_data, created_at)
        SELECT
            lower(hex(randomblob(4))) || '-'
                || lower(hex(randomblob(2))) || '-'
                || lower(hex(randomblob(2))) || '-'
                || lower(hex(randomblob(2))) || '-'
                || lower(hex(randomblob(6))),
            id,
            'gsc',
            gsc_access_token,
            gsc_refresh_token,
            gsc_expires_at,
            '{}',
            CURRENT_TIMESTAMP
        FROM users
        WHERE gsc_access_token IS NOT NULL
    """)

    # 遷移 GA4 Token
    op.execute("""
        INSERT INTO user_integrations
            (id, user_id, provider, access_token, refresh_token, token_expiry,
             extra_data, created_at)
        SELECT
            lower(hex(randomblob(4))) || '-'
                || lower(hex(randomblob(2))) || '-'
                || lower(hex(randomblob(2))) || '-'
                || lower(hex(randomblob(2))) || '-'
                || lower(hex(randomblob(6))),
            id,
            'ga4',
            ga4_access_token,
            ga4_refresh_token,
            ga4_expires_at,
            '{}',
            CURRENT_TIMESTAMP
        FROM users
        WHERE ga4_access_token IS NOT NULL
    """)

    # 遷移 Zeabur AI Key
    op.execute("""
        INSERT INTO user_integrations
            (id, user_id, provider, access_token, refresh_token, token_expiry,
             extra_data, created_at)
        SELECT
            lower(hex(randomblob(4))) || '-'
                || lower(hex(randomblob(2))) || '-'
                || lower(hex(randomblob(2))) || '-'
                || lower(hex(randomblob(2))) || '-'
                || lower(hex(randomblob(6))),
            id,
            'ai_zeabur',
            zeabur_api_key,
            NULL,
            NULL,
            json_object(
                'ai_provider', COALESCE(ai_provider, 'zeabur'),
                'ai_model', COALESCE(ai_model, 'gemini-2.5-flash')
            ),
            CURRENT_TIMESTAMP
        FROM users
        WHERE zeabur_api_key IS NOT NULL
    """)

    # 遷移 Gemini AI Key
    op.execute("""
        INSERT INTO user_integrations
            (id, user_id, provider, access_token, refresh_token, token_expiry,
             extra_data, created_at)
        SELECT
            lower(hex(randomblob(4))) || '-'
                || lower(hex(randomblob(2))) || '-'
                || lower(hex(randomblob(2))) || '-'
                || lower(hex(randomblob(2))) || '-'
                || lower(hex(randomblob(6))),
            id,
            'ai_gemini',
            gemini_api_key,
            NULL,
            NULL,
            json_object(
                'ai_model', COALESCE(ai_model, 'gemini-2.5-flash')
            ),
            CURRENT_TIMESTAMP
        FROM users
        WHERE gemini_api_key IS NOT NULL
    """)

    # ── 5.2：新增高頻查詢複合索引 ────────────────────────────────────────

    # user_module_access：常以 (user_id, team_id, module_id) 三欄查詢
    op.create_index(
        "ix_user_module_access_composite",
        "user_module_access",
        ["user_id", "team_id", "module_id"],
        unique=False,
    )

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
    op.drop_index("ix_saved_views_user_team", table_name="saved_views")
    op.drop_index("ix_team_members_user_id", table_name="team_members")
    op.drop_index("ix_user_module_access_composite", table_name="user_module_access")

    # 5.1 資料表回滾
    op.drop_index("ix_user_integrations_lookup", table_name="user_integrations")
    op.drop_table("user_integrations")
