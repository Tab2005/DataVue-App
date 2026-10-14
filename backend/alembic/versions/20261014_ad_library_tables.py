"""ad library tables (docs/73)

Revision ID: 20261014_ad_library_tables
Revises: 20260905_drop_zeabur_api_key
Create Date: 2026-10-14 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20261014_ad_library_tables"
down_revision = "20260905_drop_zeabur_api_key"
branch_labels = None
depends_on = None


ITEMS = "ad_library_items"
JOBS = "ad_library_refresh_jobs"


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _existing_indexes(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, ITEMS):
        op.create_table(
            ITEMS,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("account_id", sa.String(length=64), nullable=False),
            sa.Column("ad_id", sa.String(length=64), nullable=False),
            sa.Column("ad_name", sa.String(), nullable=True),
            sa.Column("campaign_id", sa.String(length=64), nullable=True),
            sa.Column("campaign_name", sa.String(), nullable=True),
            sa.Column("adset_id", sa.String(length=64), nullable=True),
            sa.Column("adset_name", sa.String(), nullable=True),
            sa.Column("objective", sa.String(length=64), nullable=True),
            sa.Column("effective_status", sa.String(length=32), nullable=True),
            sa.Column("page_id", sa.String(length=64), nullable=True),
            sa.Column("media_type", sa.String(length=20), nullable=False),
            sa.Column("primary_texts", sa.JSON(), nullable=False),
            sa.Column("headlines", sa.JSON(), nullable=False),
            sa.Column("descriptions", sa.JSON(), nullable=False),
            sa.Column("cta_types", sa.JSON(), nullable=False),
            sa.Column("link_url", sa.Text(), nullable=True),
            sa.Column("media", sa.JSON(), nullable=False),
            sa.Column("preview_link", sa.Text(), nullable=True),
            sa.Column("search_text", sa.Text(), nullable=True),
            sa.Column("impressions", sa.BigInteger(), nullable=False),
            sa.Column("reach", sa.BigInteger(), nullable=False),
            sa.Column("clicks", sa.BigInteger(), nullable=False),
            sa.Column("spend", sa.Float(), nullable=False),
            sa.Column("ctr", sa.Float(), nullable=False),
            sa.Column("ad_created_at", sa.DateTime(), nullable=True),
            sa.Column("ad_updated_at", sa.DateTime(), nullable=True),
            sa.Column("first_seen_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("last_seen_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("fetched_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("account_id", "ad_id", name="uq_ad_library_items_account_ad"),
        )
        inspector = sa.inspect(bind)

    existing = _existing_indexes(inspector, ITEMS)
    if "ix_ad_library_items_account_id" not in existing:
        op.create_index("ix_ad_library_items_account_id", ITEMS, ["account_id"], unique=False)
    if "ix_ad_library_items_effective_status" not in existing:
        op.create_index("ix_ad_library_items_effective_status", ITEMS, ["effective_status"], unique=False)

    if not _table_exists(inspector, JOBS):
        op.create_table(
            JOBS,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("account_id", sa.String(length=64), nullable=False),
            sa.Column("team_id", sa.String(), nullable=True),
            sa.Column("requested_by", sa.String(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("ads_fetched", sa.Integer(), nullable=False),
            sa.Column("media_stored", sa.Integer(), nullable=False),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
            sa.ForeignKeyConstraint(["requested_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = sa.inspect(bind)

    existing = _existing_indexes(inspector, JOBS)
    if "ix_ad_library_refresh_jobs_account_id" not in existing:
        op.create_index("ix_ad_library_refresh_jobs_account_id", JOBS, ["account_id"], unique=False)
    if "ix_ad_library_refresh_jobs_status" not in existing:
        op.create_index("ix_ad_library_refresh_jobs_status", JOBS, ["status"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _table_exists(inspector, JOBS):
        op.drop_table(JOBS)
    if _table_exists(inspector, ITEMS):
        op.drop_table(ITEMS)
