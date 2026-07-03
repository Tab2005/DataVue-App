"""meta andromeda scoring-loop P1 wave 2: label policy per-metric method + calibration item split

Revision ID: 20260703_meta_andromeda_p1_wave2
Revises: 20260703_meta_andromeda_p0_wave1
Create Date: 2026-07-03 01:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260703_meta_andromeda_p1_wave2"
down_revision = "20260703_meta_andromeda_p0_wave1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    lp_columns = {c["name"] for c in inspector.get_columns("meta_andromeda_label_policies")}
    for col in ("ctr_method", "cpc_method", "cvr_method", "cpl_method"):
        if col not in lp_columns:
            op.add_column(
                "meta_andromeda_label_policies",
                sa.Column(col, sa.String(length=30), nullable=True),
            )

    item_columns = {c["name"] for c in inspector.get_columns("meta_andromeda_calibration_items")}
    if "split" not in item_columns:
        op.add_column(
            "meta_andromeda_calibration_items",
            sa.Column("split", sa.String(length=20), nullable=True),
        )
    if "baseline_overall_score" not in item_columns:
        op.add_column(
            "meta_andromeda_calibration_items",
            sa.Column("baseline_overall_score", sa.Integer(), nullable=True),
        )

    profile_columns = {c["name"] for c in inspector.get_columns("meta_andromeda_scoring_profiles")}
    if "promotion_baseline" not in profile_columns:
        op.add_column(
            "meta_andromeda_scoring_profiles",
            sa.Column("promotion_baseline", sa.JSON(), nullable=True),
        )
    if "consecutive_degraded_periods" not in profile_columns:
        op.add_column(
            "meta_andromeda_scoring_profiles",
            sa.Column("consecutive_degraded_periods", sa.Integer(), nullable=False, server_default="0"),
        )
    if "demoted_at" not in profile_columns:
        op.add_column(
            "meta_andromeda_scoring_profiles",
            sa.Column("demoted_at", sa.DateTime(), nullable=True),
        )
    if "demoted_reason" not in profile_columns:
        op.add_column(
            "meta_andromeda_scoring_profiles",
            sa.Column("demoted_reason", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    profile_columns = {c["name"] for c in inspector.get_columns("meta_andromeda_scoring_profiles")}
    for col in ("demoted_reason", "demoted_at", "consecutive_degraded_periods", "promotion_baseline"):
        if col in profile_columns:
            op.drop_column("meta_andromeda_scoring_profiles", col)

    item_columns = {c["name"] for c in inspector.get_columns("meta_andromeda_calibration_items")}
    if "baseline_overall_score" in item_columns:
        op.drop_column("meta_andromeda_calibration_items", "baseline_overall_score")
    if "split" in item_columns:
        op.drop_column("meta_andromeda_calibration_items", "split")

    lp_columns = {c["name"] for c in inspector.get_columns("meta_andromeda_label_policies")}
    for col in ("ctr_method", "cpc_method", "cvr_method", "cpl_method"):
        if col in lp_columns:
            op.drop_column("meta_andromeda_label_policies", col)
