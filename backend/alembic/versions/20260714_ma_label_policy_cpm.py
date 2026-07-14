"""meta andromeda: add cpm columns to label policy (AWARENESS uses CPM, not CTR/CPC)

Revision ID: 20260714_ma_label_policy_cpm
Revises: 20260713_ma_backtest_runs
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260714_ma_label_policy_cpm"
down_revision = "20260713_ma_backtest_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    lp_columns = {c["name"] for c in inspector.get_columns("meta_andromeda_label_policies")}
    if "cpm_low" not in lp_columns:
        op.add_column("meta_andromeda_label_policies", sa.Column("cpm_low", sa.Float(), nullable=True))
    if "cpm_high" not in lp_columns:
        op.add_column("meta_andromeda_label_policies", sa.Column("cpm_high", sa.Float(), nullable=True))
    if "cpm_method" not in lp_columns:
        op.add_column("meta_andromeda_label_policies", sa.Column("cpm_method", sa.String(length=30), nullable=True))
    if "cpm_sample_count" not in lp_columns:
        op.add_column(
            "meta_andromeda_label_policies",
            sa.Column("cpm_sample_count", sa.Integer(), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    lp_columns = {c["name"] for c in inspector.get_columns("meta_andromeda_label_policies")}
    for col in ("cpm_sample_count", "cpm_method", "cpm_high", "cpm_low"):
        if col in lp_columns:
            op.drop_column("meta_andromeda_label_policies", col)
