"""ad library ai analyses (docs/75)

Revision ID: 20261014_ad_library_ai_analyses
Revises: 20261014_ad_library_asset_insights
Create Date: 2026-10-14 22:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20261014_ad_library_ai_analyses"
down_revision = "20261014_ad_library_asset_insights"
branch_labels = None
depends_on = None


TABLE = "ad_library_ai_analyses"
INDEX = "ix_ad_library_ai_analyses_account_campaign"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if TABLE not in inspector.get_table_names():
        op.create_table(
            TABLE,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("account_id", sa.String(length=64), nullable=False),
            sa.Column("campaign_id", sa.String(length=64), nullable=False),
            sa.Column("requested_by", sa.String(), nullable=False),
            sa.Column("model", sa.String(length=128), nullable=False),
            sa.Column("context_hash", sa.String(length=64), nullable=False),
            sa.Column("context_chars", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["requested_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = sa.inspect(bind)
    if INDEX not in {i["name"] for i in inspector.get_indexes(TABLE)}:
        op.create_index(INDEX, TABLE, ["account_id", "campaign_id", "created_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    if TABLE in sa.inspect(bind).get_table_names():
        op.drop_table(TABLE)
