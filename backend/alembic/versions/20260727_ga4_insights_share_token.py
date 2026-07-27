"""ga4 insights snapshots share_token column (docs/39)

Revision ID: 20260727_ga4_insights_share_token
Revises: 20260714_ma_label_policy_cpm
Create Date: 2026-07-27 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260727_ga4_insights_share_token"
down_revision = "20260714_ma_label_policy_cpm"
branch_labels = None
depends_on = None


TABLE = "ga4_insights_snapshots"
COLUMN = "share_token"
INDEX = "ix_ga4_insights_snapshots_share_token"


def _existing_columns(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {col["name"] for col in inspector.get_columns(table_name)}


def _existing_indexes(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if COLUMN not in _existing_columns(inspector, TABLE):
        op.add_column(TABLE, sa.Column(COLUMN, sa.String(length=64), nullable=True))
        inspector = sa.inspect(bind)

    if INDEX not in _existing_indexes(inspector, TABLE):
        op.create_index(INDEX, TABLE, [COLUMN], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if INDEX in _existing_indexes(inspector, TABLE):
        op.drop_index(INDEX, table_name=TABLE)
    if COLUMN in _existing_columns(inspector, TABLE):
        op.drop_column(TABLE, COLUMN)
