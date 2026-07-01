"""consolidate_legacy_schema_patches

過去這些欄位/表僅由 core/startup.py::patch_database_schema()（執行期手動
ALTER TABLE / CREATE TABLE）與 database/__init__.py::init_db() 的 fail-safe
補丁建立，從未被納入 Alembic migration。任何「僅跑 alembic upgrade head」
從零建立的資料庫都會缺少這些欄位/表。

已用全新 SQLite 資料庫實測驗證，發現兩層問題：
  1. report_schedules、line_bindings、page_titles 三張表從未被任何
     migration 的 op.create_table() 建立，僅存在於 Base.metadata（ORM）
     與執行期補丁中。
  2. 403dfb0cfbd4_add_module_type_to_reports 對 page_titles / report_schedules
     使用 batch_alter_table（假設表已存在），在全新資料庫上會直接拋
     NoSuchTableError。

此 migration 補齊缺口，並插入在 403dfb0cfbd4 之前執行（見該檔案
down_revision 已改指向本 revision），讓全新資料庫也能單靠
`alembic upgrade head` 建出完整 schema，不再依賴執行期補丁。

已存在資料庫（表/欄位已由舊補丁建立過）：所有動作皆先檢查存在性，
確保重複套用時為 no-op，不會拋錯。

涵蓋項目：
  - report_schedules 表（原僅由 create_all() 建立）
  - line_bindings 表（原僅由 create_all() 建立）
  - page_titles 表（原僅由執行期補丁建立，403dfb0cfbd4 需要它已存在）
  - users: gsc_access_token / gsc_refresh_token / gsc_expires_at /
           zeabur_api_key / gemini_api_key / ai_provider / ai_model /
           line_user_id（含索引）
  - report_schedules.is_notify_line
  - weekly_reports.share_token（含唯一索引）
  - 附帶修復 20260223_p3_integrations_indexes.py 因分支合併順序問題，
    在全新資料庫上被 try/except 吞掉而從未真正建立的
    ix_user_module_access_composite 索引

Revision ID: 20260701_consolidate_legacy_patches
Revises: 20260331_merge_all_heads
Create Date: 2026-07-01
"""
from __future__ import annotations

import logging

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260701_consolidate_legacy_patches"
down_revision = "20260331_merge_all_heads"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.migration")


def _existing_columns(inspector, table_name: str) -> set[str]:
    if table_name not in inspector.get_table_names():
        return set()
    return {c["name"] for c in inspector.get_columns(table_name)}


def _existing_indexes(inspector, table_name: str) -> set[str]:
    if table_name not in inspector.get_table_names():
        return set()
    return {ix["name"] for ix in inspector.get_indexes(table_name)}


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # ── report_schedules 表（未曾被任何 migration 建立過）───────────────
    if "report_schedules" not in existing_tables:
        op.create_table(
            "report_schedules",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("ad_account_id", sa.String(), nullable=False),
            sa.Column("ad_account_name", sa.String(), nullable=True),
            sa.Column("selected_metrics", sa.Text(), nullable=False),
            sa.Column("breakdown", sa.String(), nullable=True),
            sa.Column("frequency", sa.String(), nullable=False),
            sa.Column("day_of_week", sa.String(), nullable=True),
            sa.Column("day_of_month", sa.String(), nullable=True),
            sa.Column("time_of_day", sa.String(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("team_id", sa.String(), sa.ForeignKey("teams.id"), nullable=True),
            sa.Column("last_run", sa.DateTime(), nullable=True),
            sa.Column("next_run", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_report_schedules_user_id"), "report_schedules", ["user_id"], unique=False
        )
        op.create_index(
            op.f("ix_report_schedules_team_id"), "report_schedules", ["team_id"], unique=False
        )
        existing_tables.append("report_schedules")

    # ── line_bindings 表（未曾被任何 migration 建立過）───────────────────
    if "line_bindings" not in existing_tables:
        op.create_table(
            "line_bindings",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("code", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_line_bindings_code"), "line_bindings", ["code"], unique=True)
        op.create_index(op.f("ix_line_bindings_user_id"), "line_bindings", ["user_id"], unique=False)
        existing_tables.append("line_bindings")

    # ── page_titles 表（原僅由執行期補丁建立，403dfb0cfbd4 需要它已存在）──
    # 刻意重現舊版執行期補丁的原始 schema（id 未強制 NOT NULL、url 為
    # inline UNIQUE 而非具名索引、fetched_at 為 TIMESTAMP）：
    # 403dfb0cfbd4 的 batch_alter_table 會接著把它調整為最終形態
    # （id NOT NULL、fetched_at → DateTime、具名 unique index），
    # 與歷史上真實環境（先由補丁建表、後由該 migration 調整）的路徑一致。
    if "page_titles" not in existing_tables:
        op.create_table(
            "page_titles",
            sa.Column("id", sa.String(), nullable=True),
            sa.Column("url", sa.String(), nullable=False, unique=True),
            sa.Column("title", sa.String(), nullable=True),
            sa.Column(
                "fetched_at", sa.TIMESTAMP(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        existing_tables.append("page_titles")

    # ── users: 舊版整合 Token / AI 設定欄位 ─────────────────────────────
    user_columns = _existing_columns(inspector, "users")
    user_patches = [
        ("gsc_access_token", sa.String()),
        ("gsc_refresh_token", sa.String()),
        ("gsc_expires_at", sa.DateTime()),
        ("zeabur_api_key", sa.String()),
        ("gemini_api_key", sa.String()),
        ("ai_provider", sa.String()),
        ("ai_model", sa.String()),
        ("line_user_id", sa.String()),
    ]
    with op.batch_alter_table("users", schema=None) as batch_op:
        for col_name, col_type in user_patches:
            if col_name not in user_columns:
                batch_op.add_column(sa.Column(col_name, col_type, nullable=True))

    if "line_user_id" not in user_columns and "ix_users_line_user_id" not in _existing_indexes(inspector, "users"):
        try:
            op.create_index("ix_users_line_user_id", "users", ["line_user_id"], unique=False)
        except Exception as exc:  # pragma: no cover - 防禦性，索引可能已存在
            logger.warning("ix_users_line_user_id 索引建立跳過：%s", exc)

    # ── report_schedules.is_notify_line ─────────────────────────────────
    schedule_columns = _existing_columns(inspector, "report_schedules")
    if "is_notify_line" not in schedule_columns:
        with op.batch_alter_table("report_schedules", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column("is_notify_line", sa.Boolean(), nullable=True, server_default=sa.false())
            )

    # ── weekly_reports.share_token ──────────────────────────────────────
    report_columns = _existing_columns(inspector, "weekly_reports")
    if "share_token" not in report_columns:
        with op.batch_alter_table("weekly_reports", schema=None) as batch_op:
            batch_op.add_column(sa.Column("share_token", sa.String(), nullable=True))
        try:
            op.create_index(
                "ix_weekly_reports_share_token", "weekly_reports", ["share_token"], unique=True
            )
        except Exception as exc:  # pragma: no cover - 防禦性，索引可能已存在
            logger.warning("ix_weekly_reports_share_token 索引建立跳過：%s", exc)

    # ── 附帶修復：ix_user_module_access_composite（見本檔案 docstring）──
    if "user_module_access" in existing_tables:
        if "ix_user_module_access_composite" not in _existing_indexes(inspector, "user_module_access"):
            try:
                op.create_index(
                    "ix_user_module_access_composite",
                    "user_module_access",
                    ["user_id", "team_id", "module_id"],
                    unique=False,
                )
            except Exception as exc:  # pragma: no cover - 防禦性，索引可能已存在
                logger.warning("ix_user_module_access_composite 索引建立跳過：%s", exc)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    report_columns = _existing_columns(inspector, "weekly_reports")
    if "share_token" in report_columns:
        with op.batch_alter_table("weekly_reports", schema=None) as batch_op:
            try:
                batch_op.drop_index("ix_weekly_reports_share_token")
            except Exception:  # pragma: no cover
                pass
            batch_op.drop_column("share_token")

    schedule_columns = _existing_columns(inspector, "report_schedules")
    if "is_notify_line" in schedule_columns:
        with op.batch_alter_table("report_schedules", schema=None) as batch_op:
            batch_op.drop_column("is_notify_line")

    user_columns = _existing_columns(inspector, "users")
    with op.batch_alter_table("users", schema=None) as batch_op:
        if "line_user_id" in user_columns:
            try:
                batch_op.drop_index("ix_users_line_user_id")
            except Exception:  # pragma: no cover
                pass
            batch_op.drop_column("line_user_id")
        for col_name in ("ai_model", "ai_provider", "gemini_api_key", "zeabur_api_key",
                         "gsc_expires_at", "gsc_refresh_token", "gsc_access_token"):
            if col_name in user_columns:
                batch_op.drop_column(col_name)

    if "page_titles" in inspector.get_table_names():
        # ix_page_titles_url 由下游的 403dfb0cfbd4 建立，downgrade 該
        # migration 時已一併移除，此處僅需 drop table。
        op.drop_table("page_titles")

    if "line_bindings" in inspector.get_table_names():
        op.drop_index(op.f("ix_line_bindings_user_id"), table_name="line_bindings")
        op.drop_index(op.f("ix_line_bindings_code"), table_name="line_bindings")
        op.drop_table("line_bindings")

    if "report_schedules" in inspector.get_table_names():
        op.drop_index(op.f("ix_report_schedules_team_id"), table_name="report_schedules")
        op.drop_index(op.f("ix_report_schedules_user_id"), table_name="report_schedules")
        op.drop_table("report_schedules")
