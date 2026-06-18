"""add meta andromeda observed creatives

Revision ID: 20260618_meta_andromeda_observed_creatives
Revises: 46c781526b51
Create Date: 2026-06-18 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260618_meta_andromeda_observed_creatives"
down_revision = "46c781526b51"
branch_labels = None
depends_on = None

TABLE_NAME = "meta_andromeda_observed_creatives"
INDEX_DEFINITIONS = (
    ("ix_meta_andromeda_observed_creatives_asset_uri", ["asset_uri"]),
    ("ix_meta_andromeda_observed_creatives_source_platform", ["source_platform"]),
    ("ix_meta_andromeda_observed_creatives_source_account_id", ["source_account_id"]),
    ("ix_meta_andromeda_observed_creatives_campaign_id", ["campaign_id"]),
    ("ix_meta_andromeda_observed_creatives_adset_id", ["adset_id"]),
    ("ix_meta_andromeda_observed_creatives_ad_id", ["ad_id"]),
    ("ix_meta_andromeda_observed_creatives_observation_window_kind", ["observation_window_kind"]),
)


def _existing_indexes(inspector: sa.Inspector) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(TABLE_NAME)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if TABLE_NAME not in inspector.get_table_names():
        op.create_table(
            TABLE_NAME,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("asset_id", sa.String(), nullable=True),
            sa.Column("asset_uri", sa.String(), nullable=True),
            sa.Column("source_platform", sa.String(length=50), nullable=False),
            sa.Column("source_account_id", sa.String(length=120), nullable=False),
            sa.Column("campaign_id", sa.String(length=120), nullable=True),
            sa.Column("adset_id", sa.String(length=120), nullable=True),
            sa.Column("ad_id", sa.String(length=120), nullable=False),
            sa.Column("ad_name", sa.String(), nullable=True),
            sa.Column("objective", sa.String(length=50), nullable=True),
            sa.Column("placement_family", sa.String(length=50), nullable=False),
            sa.Column("market", sa.String(length=20), nullable=False),
            sa.Column("primary_text", sa.Text(), nullable=True),
            sa.Column("headline", sa.Text(), nullable=True),
            sa.Column("cta", sa.String(length=100), nullable=True),
            sa.Column("media_url", sa.String(), nullable=True),
            sa.Column("media_type", sa.String(length=20), nullable=False, server_default="unknown"),
            sa.Column("performance_snapshot", sa.JSON(), nullable=False),
            sa.Column("observation_window_kind", sa.String(length=50), nullable=False),
            sa.Column("observation_window_start", sa.String(length=40), nullable=False),
            sa.Column("observation_window_end", sa.String(length=40), nullable=False),
            sa.Column("source_fetched_at", sa.String(length=40), nullable=False),
            sa.Column("lineage", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.ForeignKeyConstraint(["asset_id"], ["meta_andromeda_assets.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = sa.inspect(bind)

    existing_indexes = _existing_indexes(inspector)
    for index_name, columns in INDEX_DEFINITIONS:
        if index_name not in existing_indexes:
            op.create_index(index_name, TABLE_NAME, columns, unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if TABLE_NAME not in inspector.get_table_names():
        return

    existing_indexes = _existing_indexes(inspector)
    for index_name, _ in reversed(INDEX_DEFINITIONS):
        if index_name in existing_indexes:
            op.drop_index(index_name, table_name=TABLE_NAME)
    op.drop_table(TABLE_NAME)
