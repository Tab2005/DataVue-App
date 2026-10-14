"""ad library dynamic creative asset insights (docs/74 phase 3)

Revision ID: 20261014_ad_library_asset_insights
Revises: 20261014_ad_library_hierarchy
Create Date: 2026-10-14 21:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20261014_ad_library_asset_insights"
down_revision = "20261014_ad_library_hierarchy"
branch_labels = None
depends_on = None


TABLE = "ad_library_asset_insights"
JOBS = "ad_library_refresh_jobs"


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _existing_indexes(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _existing_columns(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, TABLE):
        op.create_table(
            TABLE,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("account_id", sa.String(length=64), nullable=False),
            sa.Column("ad_id", sa.String(length=64), nullable=False),
            sa.Column("content_id", sa.String(), nullable=False),
            sa.Column("kind", sa.String(length=20), nullable=False),
            sa.Column("fb_asset_id", sa.String(length=64), nullable=True),
            sa.Column("impressions", sa.BigInteger(), nullable=False),
            sa.Column("reach", sa.BigInteger(), nullable=False),
            sa.Column("clicks", sa.BigInteger(), nullable=False),
            sa.Column("spend", sa.Float(), nullable=False),
            sa.Column("fetched_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["content_id"], ["ad_library_contents.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "account_id", "ad_id", "content_id", name="uq_ad_library_asset_insights_account_ad_content"
            ),
        )
        inspector = sa.inspect(bind)
    existing = _existing_indexes(inspector, TABLE)
    if "ix_ad_library_asset_insights_account_id" not in existing:
        op.create_index("ix_ad_library_asset_insights_account_id", TABLE, ["account_id"], unique=False)
    if "ix_ad_library_asset_insights_content_id" not in existing:
        op.create_index("ix_ad_library_asset_insights_content_id", TABLE, ["content_id"], unique=False)

    if "asset_insights_ads" not in _existing_columns(inspector, JOBS):
        with op.batch_alter_table(JOBS) as batch:
            batch.add_column(sa.Column("asset_insights_ads", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "asset_insights_ads" in _existing_columns(inspector, JOBS):
        with op.batch_alter_table(JOBS) as batch:
            batch.drop_column("asset_insights_ads")
    if _table_exists(inspector, TABLE):
        op.drop_table(TABLE)
