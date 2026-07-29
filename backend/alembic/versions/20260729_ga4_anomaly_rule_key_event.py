"""ga4 anomaly rules key_event column (docs/52)

Revision ID: 20260729_ga4_anomaly_rule_key_event
Revises: 20260727_ga4_channel_group_rules
Create Date: 2026-07-29 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_ga4_anomaly_rule_key_event"
down_revision = "20260727_ga4_channel_group_rules"
branch_labels = None
depends_on = None


TABLE = "ga4_anomaly_rules"
COLUMN = "key_event"


def _existing_columns(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if COLUMN not in _existing_columns(inspector, TABLE):
        op.add_column(TABLE, sa.Column(COLUMN, sa.String(length=80), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if COLUMN in _existing_columns(inspector, TABLE):
        op.drop_column(TABLE, COLUMN)
