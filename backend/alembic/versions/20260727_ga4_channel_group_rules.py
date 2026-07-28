"""ga4 channel group rules table (docs/44)

Revision ID: 20260727_ga4_channel_group_rules
Revises: 20260727_ga4_insights_share_token
Create Date: 2026-07-27 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260727_ga4_channel_group_rules"
down_revision = "20260727_ga4_insights_share_token"
branch_labels = None
depends_on = None


TABLE = "ga4_channel_group_rules"


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _existing_indexes(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, TABLE):
        op.create_table(
            TABLE,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("property_id", sa.String(length=50), nullable=False),
            sa.Column("channel_dimension", sa.String(length=30), nullable=False),
            sa.Column("group_label", sa.String(length=100), nullable=False),
            sa.Column("match_type", sa.String(length=10), nullable=False),
            sa.Column("pattern", sa.String(length=200), nullable=False),
            sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_by", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = sa.inspect(bind)

    existing = _existing_indexes(inspector, TABLE) if _table_exists(inspector, TABLE) else set()
    if "ix_ga4_channel_group_rules_property_id" not in existing:
        op.create_index("ix_ga4_channel_group_rules_property_id", TABLE, ["property_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _table_exists(inspector, TABLE):
        if "ix_ga4_channel_group_rules_property_id" in _existing_indexes(inspector, TABLE):
            op.drop_index("ix_ga4_channel_group_rules_property_id", table_name=TABLE)
        op.drop_table(TABLE)
