"""ga4 insights tables (docs/22 wave 1)

Revision ID: 20260710_ga4_insights_tables
Revises: 20260708_contribution_snapshot_ai_summary
Create Date: 2026-07-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260710_ga4_insights_tables"
down_revision = "20260708_contribution_snapshot_ai_summary"
branch_labels = None
depends_on = None


SNAPSHOTS = "ga4_insights_snapshots"
RULES = "ga4_anomaly_rules"
EVENTS = "ga4_anomaly_events"


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _existing_indexes(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, SNAPSHOTS):
        op.create_table(
            SNAPSHOTS,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("property_id", sa.String(length=50), nullable=False),
            sa.Column("kind", sa.String(length=30), nullable=False),
            sa.Column("date", sa.String(length=10), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("ai_summary", sa.Text(), nullable=True),
            sa.Column("ai_summary_generated_at", sa.DateTime(), nullable=True),
            sa.Column("fetched_by", sa.String(), nullable=True),
            sa.Column("fetched_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["fetched_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("property_id", "kind", "date", name="uq_ga4_insights_snapshots_property_kind_date"),
        )
        inspector = sa.inspect(bind)
    existing = _existing_indexes(inspector, SNAPSHOTS) if _table_exists(inspector, SNAPSHOTS) else set()
    if "ix_ga4_insights_snapshots_property_id" not in existing:
        op.create_index("ix_ga4_insights_snapshots_property_id", SNAPSHOTS, ["property_id"], unique=False)

    if not _table_exists(inspector, RULES):
        op.create_table(
            RULES,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("property_id", sa.String(length=50), nullable=False),
            sa.Column("metric_key", sa.String(length=50), nullable=False),
            sa.Column("sensitivity", sa.String(length=10), nullable=False, server_default="medium"),
            sa.Column("check_frequency", sa.String(length=20), nullable=False, server_default="hourly"),
            sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("notify_line", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("notify_email", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("cooldown_hours", sa.Integer(), nullable=False, server_default="6"),
            sa.Column("created_by", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = sa.inspect(bind)
    existing = _existing_indexes(inspector, RULES) if _table_exists(inspector, RULES) else set()
    if "ix_ga4_anomaly_rules_property_id" not in existing:
        op.create_index("ix_ga4_anomaly_rules_property_id", RULES, ["property_id"], unique=False)

    if not _table_exists(inspector, EVENTS):
        op.create_table(
            EVENTS,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("rule_id", sa.String(), nullable=False),
            sa.Column("severity", sa.String(length=10), nullable=False),
            sa.Column("direction", sa.String(length=10), nullable=False),
            sa.Column("observed_value", sa.Float(), nullable=False),
            sa.Column("expected_low", sa.Float(), nullable=False),
            sa.Column("expected_high", sa.Float(), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("notified_channels", sa.JSON(), nullable=False),
            sa.Column("acknowledged_by", sa.String(), nullable=True),
            sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["acknowledged_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["rule_id"], ["ga4_anomaly_rules.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = sa.inspect(bind)
    existing = _existing_indexes(inspector, EVENTS) if _table_exists(inspector, EVENTS) else set()
    if "ix_ga4_anomaly_events_rule_id" not in existing:
        op.create_index("ix_ga4_anomaly_events_rule_id", EVENTS, ["rule_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _table_exists(inspector, EVENTS):
        if "ix_ga4_anomaly_events_rule_id" in _existing_indexes(inspector, EVENTS):
            op.drop_index("ix_ga4_anomaly_events_rule_id", table_name=EVENTS)
        op.drop_table(EVENTS)
    inspector = sa.inspect(bind)
    if _table_exists(inspector, RULES):
        if "ix_ga4_anomaly_rules_property_id" in _existing_indexes(inspector, RULES):
            op.drop_index("ix_ga4_anomaly_rules_property_id", table_name=RULES)
        op.drop_table(RULES)
    inspector = sa.inspect(bind)
    if _table_exists(inspector, SNAPSHOTS):
        if "ix_ga4_insights_snapshots_property_id" in _existing_indexes(inspector, SNAPSHOTS):
            op.drop_index("ix_ga4_insights_snapshots_property_id", table_name=SNAPSHOTS)
        op.drop_table(SNAPSHOTS)
