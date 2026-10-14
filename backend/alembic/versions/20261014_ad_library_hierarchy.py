"""ad library hierarchy & content tables (docs/74)

Revision ID: 20261014_ad_library_hierarchy
Revises: 20261014_ad_library_tables
Create Date: 2026-10-14 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20261014_ad_library_hierarchy"
down_revision = "20261014_ad_library_tables"
branch_labels = None
depends_on = None


ITEMS = "ad_library_items"
JOBS = "ad_library_refresh_jobs"
CAMPAIGNS = "ad_library_campaigns"
ADSETS = "ad_library_adsets"
CONTENTS = "ad_library_contents"
AD_CONTENTS = "ad_library_ad_contents"


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _existing_indexes(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _existing_columns(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _metric_and_seen_columns() -> list[sa.Column]:
    return [
        sa.Column("impressions", sa.BigInteger(), nullable=False),
        sa.Column("reach", sa.BigInteger(), nullable=False),
        sa.Column("clicks", sa.BigInteger(), nullable=False),
        sa.Column("spend", sa.Float(), nullable=False),
        sa.Column("ctr", sa.Float(), nullable=False),
        sa.Column("raw", sa.JSON(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("fetched_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, CAMPAIGNS):
        op.create_table(
            CAMPAIGNS,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("account_id", sa.String(length=64), nullable=False),
            sa.Column("campaign_id", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("objective", sa.String(length=64), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=True),
            sa.Column("effective_status", sa.String(length=32), nullable=True),
            sa.Column("buying_type", sa.String(length=32), nullable=True),
            sa.Column("bid_strategy", sa.String(length=64), nullable=True),
            sa.Column("smart_promotion_type", sa.String(length=64), nullable=True),
            sa.Column("daily_budget", sa.BigInteger(), nullable=True),
            sa.Column("lifetime_budget", sa.BigInteger(), nullable=True),
            sa.Column("budget_remaining", sa.BigInteger(), nullable=True),
            sa.Column("currency", sa.String(length=8), nullable=True),
            sa.Column("special_ad_categories", sa.JSON(), nullable=False),
            sa.Column("start_time", sa.DateTime(), nullable=True),
            sa.Column("stop_time", sa.DateTime(), nullable=True),
            sa.Column("created_time", sa.DateTime(), nullable=True),
            sa.Column("updated_time", sa.DateTime(), nullable=True),
            *_metric_and_seen_columns(),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("account_id", "campaign_id", name="uq_ad_library_campaigns_account_campaign"),
        )
        inspector = sa.inspect(bind)
    if "ix_ad_library_campaigns_account_id" not in _existing_indexes(inspector, CAMPAIGNS):
        op.create_index("ix_ad_library_campaigns_account_id", CAMPAIGNS, ["account_id"], unique=False)

    if not _table_exists(inspector, ADSETS):
        op.create_table(
            ADSETS,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("account_id", sa.String(length=64), nullable=False),
            sa.Column("adset_id", sa.String(length=64), nullable=False),
            sa.Column("campaign_id", sa.String(length=64), nullable=True),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=True),
            sa.Column("effective_status", sa.String(length=32), nullable=True),
            sa.Column("optimization_goal", sa.String(length=64), nullable=True),
            sa.Column("billing_event", sa.String(length=64), nullable=True),
            sa.Column("bid_strategy", sa.String(length=64), nullable=True),
            sa.Column("destination_type", sa.String(length=64), nullable=True),
            sa.Column("is_dynamic_creative", sa.Boolean(), nullable=True),
            sa.Column("bid_amount", sa.BigInteger(), nullable=True),
            sa.Column("daily_budget", sa.BigInteger(), nullable=True),
            sa.Column("lifetime_budget", sa.BigInteger(), nullable=True),
            sa.Column("budget_remaining", sa.BigInteger(), nullable=True),
            sa.Column("currency", sa.String(length=8), nullable=True),
            sa.Column("targeting", sa.JSON(), nullable=True),
            sa.Column("targeting_summary", sa.JSON(), nullable=False),
            sa.Column("promoted_object", sa.JSON(), nullable=True),
            sa.Column("attribution_spec", sa.JSON(), nullable=True),
            sa.Column("start_time", sa.DateTime(), nullable=True),
            sa.Column("end_time", sa.DateTime(), nullable=True),
            sa.Column("created_time", sa.DateTime(), nullable=True),
            sa.Column("updated_time", sa.DateTime(), nullable=True),
            *_metric_and_seen_columns(),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("account_id", "adset_id", name="uq_ad_library_adsets_account_adset"),
        )
        inspector = sa.inspect(bind)
    existing = _existing_indexes(inspector, ADSETS)
    if "ix_ad_library_adsets_account_id" not in existing:
        op.create_index("ix_ad_library_adsets_account_id", ADSETS, ["account_id"], unique=False)
    if "ix_ad_library_adsets_account_campaign" not in existing:
        op.create_index("ix_ad_library_adsets_account_campaign", ADSETS, ["account_id", "campaign_id"], unique=False)

    if not _table_exists(inspector, CONTENTS):
        op.create_table(
            CONTENTS,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("account_id", sa.String(length=64), nullable=False),
            sa.Column("kind", sa.String(length=20), nullable=False),
            sa.Column("fingerprint", sa.String(length=80), nullable=False),
            sa.Column("text_value", sa.Text(), nullable=True),
            sa.Column("image_hash", sa.String(length=64), nullable=True),
            sa.Column("video_id", sa.String(length=64), nullable=True),
            sa.Column("asset_id", sa.String(), nullable=True),
            sa.Column("first_seen_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("last_seen_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("account_id", "kind", "fingerprint", name="uq_ad_library_contents_account_kind_fp"),
        )
        inspector = sa.inspect(bind)
    if "ix_ad_library_contents_account_id" not in _existing_indexes(inspector, CONTENTS):
        op.create_index("ix_ad_library_contents_account_id", CONTENTS, ["account_id"], unique=False)

    if not _table_exists(inspector, AD_CONTENTS):
        op.create_table(
            AD_CONTENTS,
            sa.Column("item_id", sa.String(), nullable=False),
            sa.Column("content_id", sa.String(), nullable=False),
            sa.Column("position", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["item_id"], [f"{ITEMS}.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["content_id"], [f"{CONTENTS}.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("item_id", "content_id", "position"),
        )
        inspector = sa.inspect(bind)
    if "ix_ad_library_ad_contents_content_id" not in _existing_indexes(inspector, AD_CONTENTS):
        op.create_index("ix_ad_library_ad_contents_content_id", AD_CONTENTS, ["content_id"], unique=False)

    columns = _existing_columns(inspector, ITEMS)
    with op.batch_alter_table(ITEMS) as batch:
        if "copy_key" not in columns:
            batch.add_column(sa.Column("copy_key", sa.String(length=64), nullable=True))
        if "media_key" not in columns:
            batch.add_column(sa.Column("media_key", sa.String(length=64), nullable=True))
    inspector = sa.inspect(bind)
    existing = _existing_indexes(inspector, ITEMS)
    if "ix_ad_library_items_adset_copy" not in existing:
        op.create_index("ix_ad_library_items_adset_copy", ITEMS, ["account_id", "adset_id", "copy_key"], unique=False)
    if "ix_ad_library_items_adset_media" not in existing:
        op.create_index("ix_ad_library_items_adset_media", ITEMS, ["account_id", "adset_id", "media_key"], unique=False)

    columns = _existing_columns(inspector, JOBS)
    with op.batch_alter_table(JOBS) as batch:
        if "campaigns_fetched" not in columns:
            batch.add_column(sa.Column("campaigns_fetched", sa.Integer(), nullable=False, server_default="0"))
        if "adsets_fetched" not in columns:
            batch.add_column(sa.Column("adsets_fetched", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = _existing_columns(inspector, JOBS)
    with op.batch_alter_table(JOBS) as batch:
        for name in ("adsets_fetched", "campaigns_fetched"):
            if name in columns:
                batch.drop_column(name)

    existing = _existing_indexes(inspector, ITEMS)
    for name in ("ix_ad_library_items_adset_media", "ix_ad_library_items_adset_copy"):
        if name in existing:
            op.drop_index(name, table_name=ITEMS)
    columns = _existing_columns(inspector, ITEMS)
    with op.batch_alter_table(ITEMS) as batch:
        for name in ("media_key", "copy_key"):
            if name in columns:
                batch.drop_column(name)

    for table in (AD_CONTENTS, CONTENTS, ADSETS, CAMPAIGNS):
        if _table_exists(inspector, table):
            op.drop_table(table)
