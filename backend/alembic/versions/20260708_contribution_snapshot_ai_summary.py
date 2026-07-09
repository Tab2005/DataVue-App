"""docs/21 task 2.3: contribution_snapshots 新增 AI 白話解讀欄位

為 contribution_snapshots 追加 2 欄：
  - ai_summary             : Text, nullable  — AI 生成的 Markdown 白話解讀
  - ai_summary_generated_at: DateTime, nullable — 解讀生成時間（持久化後即不重打）

回滾時僅刪除這 2 欄，保留既有資料。

Revision ID: 20260708_contribution_snapshot_ai_summary
Revises: 20260707_ma_non_roas_band_enable
Create Date: 2026-07-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260708_contribution_snapshot_ai_summary"
down_revision = "20260707_ma_non_roas_band_enable"
branch_labels = None
depends_on = None


SNAPSHOTS_TABLE = "contribution_snapshots"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if SNAPSHOTS_TABLE not in inspector.get_table_names():
        # 表不存在時不做事（降級鏈上可能還沒到 20260706；典型僅在
        # fresh DB 直接從此 migration 之後 head 起步才會發生，但屬
        # 異常路徑。與既有 migration 慣例一致：缺表時 silently skip）
        return
    existing = {c["name"] for c in inspector.get_columns(SNAPSHOTS_TABLE)}
    if "ai_summary" not in existing:
        op.add_column(
            SNAPSHOTS_TABLE,
            sa.Column("ai_summary", sa.Text(), nullable=True),
        )
    if "ai_summary_generated_at" not in existing:
        op.add_column(
            SNAPSHOTS_TABLE,
            sa.Column("ai_summary_generated_at", sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if SNAPSHOTS_TABLE not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns(SNAPSHOTS_TABLE)}
    if "ai_summary_generated_at" in existing:
        op.drop_column(SNAPSHOTS_TABLE, "ai_summary_generated_at")
    if "ai_summary" in existing:
        op.drop_column(SNAPSHOTS_TABLE, "ai_summary")
