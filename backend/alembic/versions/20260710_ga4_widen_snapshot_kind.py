"""widen ga4_insights_snapshots.kind to String(80) (docs/22 wave 5)

Revision ID: 20260710_ga4_widen_snapshot_kind
Revises: 20260710_ga4_landing_page_rules
Create Date: 2026-07-10 00:00:01.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260710_ga4_widen_snapshot_kind"
down_revision = "20260710_ga4_landing_page_rules"
branch_labels = None
depends_on = None


TABLE = "ga4_insights_snapshots"


def upgrade() -> None:
    # 無損 ALTER：只放寬長度上限，不動既有資料。用 batch_alter_table 相容
    # SQLite（測試用，SQLite 不支援直接 ALTER COLUMN）與 PostgreSQL（生產）。
    with op.batch_alter_table(TABLE, schema=None) as batch_op:
        batch_op.alter_column(
            "kind", type_=sa.String(length=80), existing_type=sa.String(length=30), existing_nullable=False
        )


def downgrade() -> None:
    with op.batch_alter_table(TABLE, schema=None) as batch_op:
        batch_op.alter_column(
            "kind", type_=sa.String(length=30), existing_type=sa.String(length=80), existing_nullable=False
        )
