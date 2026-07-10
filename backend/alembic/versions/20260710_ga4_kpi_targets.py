"""ga4 kpi targets table (docs/22 wave 3)

Revision ID: 20260710_ga4_kpi_targets
Revises: 20260710_ga4_insights_tables
Create Date: 2026-07-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260710_ga4_kpi_targets"
down_revision = "20260710_ga4_insights_tables"
branch_labels = None
depends_on = None


TARGETS = "ga4_kpi_targets"


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _existing_indexes(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, TARGETS):
        op.create_table(
            TARGETS,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("property_id", sa.String(length=50), nullable=False),
            sa.Column("metric_key", sa.String(length=50), nullable=False),
            sa.Column("period_type", sa.String(length=10), nullable=False),
            sa.Column("period_key", sa.String(length=10), nullable=False),
            sa.Column("target_value", sa.Float(), nullable=False),
            sa.Column("created_by", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "property_id", "metric_key", "period_type", "period_key",
                name="uq_ga4_kpi_targets_property_metric_period",
            ),
        )
        inspector = sa.inspect(bind)
    existing = _existing_indexes(inspector, TARGETS) if _table_exists(inspector, TARGETS) else set()
    if "ix_ga4_kpi_targets_property_id" not in existing:
        op.create_index("ix_ga4_kpi_targets_property_id", TARGETS, ["property_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _table_exists(inspector, TARGETS):
        if "ix_ga4_kpi_targets_property_id" in _existing_indexes(inspector, TARGETS):
            op.drop_index("ix_ga4_kpi_targets_property_id", table_name=TARGETS)
        op.drop_table(TARGETS)
