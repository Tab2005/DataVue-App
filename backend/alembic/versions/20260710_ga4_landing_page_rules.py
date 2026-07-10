"""ga4 landing page rules table (docs/22 wave 5)

Revision ID: 20260710_ga4_landing_page_rules
Revises: 20260710_ga4_kpi_targets
Create Date: 2026-07-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260710_ga4_landing_page_rules"
down_revision = "20260710_ga4_kpi_targets"
branch_labels = None
depends_on = None


RULES = "ga4_landing_page_rules"


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _existing_indexes(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, RULES):
        op.create_table(
            RULES,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("property_id", sa.String(length=50), nullable=False),
            sa.Column("category", sa.String(length=20), nullable=False),
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
    existing = _existing_indexes(inspector, RULES) if _table_exists(inspector, RULES) else set()
    if "ix_ga4_landing_page_rules_property_id" not in existing:
        op.create_index("ix_ga4_landing_page_rules_property_id", RULES, ["property_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _table_exists(inspector, RULES):
        if "ix_ga4_landing_page_rules_property_id" in _existing_indexes(inspector, RULES):
            op.drop_index("ix_ga4_landing_page_rules_property_id", table_name=RULES)
        op.drop_table(RULES)
