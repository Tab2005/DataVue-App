"""fb ads analytics ai snapshots (docs/58)

Revision ID: 20260731_fb_ads_analytics_ai_snapshots
Revises: 20260729_ga4_anomaly_rule_key_event
Create Date: 2026-07-31 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260731_fb_ads_analytics_ai_snapshots"
down_revision = "20260729_ga4_anomaly_rule_key_event"
branch_labels = None
depends_on = None


TABLE = "fb_ads_analytics_ai_snapshots"


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
            sa.Column("account_id", sa.String(length=64), nullable=False),
            sa.Column("team_id", sa.String(), nullable=True),
            sa.Column("level", sa.String(length=20), nullable=False),
            sa.Column("date_since", sa.String(length=10), nullable=False),
            sa.Column("date_until", sa.String(length=10), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("ai_summary", sa.Text(), nullable=True),
            sa.Column("ai_summary_generated_at", sa.DateTime(), nullable=True),
            sa.Column("share_token", sa.String(length=64), nullable=True),
            sa.Column("created_by", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = sa.inspect(bind)

    existing = _existing_indexes(inspector, TABLE) if _table_exists(inspector, TABLE) else set()
    if "ix_fb_ads_analytics_ai_snapshots_account_id" not in existing:
        op.create_index("ix_fb_ads_analytics_ai_snapshots_account_id", TABLE, ["account_id"], unique=False)
    if "ix_fb_ads_analytics_ai_snapshots_share_token" not in existing:
        op.create_index("ix_fb_ads_analytics_ai_snapshots_share_token", TABLE, ["share_token"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _table_exists(inspector, TABLE):
        op.drop_table(TABLE)
