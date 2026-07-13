"""add meta andromeda backtest runs

Revision ID: 20260713_ma_backtest_runs
Revises: 20260710_ga4_item_category_rules
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260713_ma_backtest_runs"
down_revision = "20260710_ga4_item_category_rules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meta_andromeda_backtest_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="openrouter"),
        sa.Column("provider_model", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("sample_limit", sa.Integer(), nullable=True),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pairwise_ranking_accuracy", sa.Float(), nullable=True),
        sa.Column("mean_band_error", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result_summary", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_meta_andromeda_backtest_runs_status", "meta_andromeda_backtest_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_meta_andromeda_backtest_runs_status", table_name="meta_andromeda_backtest_runs")
    op.drop_table("meta_andromeda_backtest_runs")
