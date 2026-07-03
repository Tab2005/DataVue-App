"""meta andromeda scoring-loop P0 wave 1: label policy table + calibration item thresholds

Revision ID: 20260703_meta_andromeda_p0_wave1
Revises: 20260630_meta_andromeda_objective_profiles
Create Date: 2026-07-03 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260703_meta_andromeda_p0_wave1"
down_revision = "20260630_meta_andromeda_objective_profiles"
branch_labels = None
depends_on = None


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = {c["name"] for c in inspector.get_columns("meta_andromeda_calibration_items")}
    if "label_thresholds" not in columns:
        op.add_column(
            "meta_andromeda_calibration_items",
            sa.Column("label_thresholds", sa.JSON(), nullable=True),
        )

    if not _table_exists(inspector, "meta_andromeda_label_policies"):
        op.create_table(
            "meta_andromeda_label_policies",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("scope_key", sa.String(length=120), nullable=False),
            sa.Column("window_kind", sa.String(length=50), nullable=False),
            sa.Column("label_policy_version", sa.String(length=50), nullable=False),
            sa.Column("roas_low", sa.Float(), nullable=True),
            sa.Column("roas_high", sa.Float(), nullable=True),
            sa.Column("roas_method", sa.String(length=30), nullable=True),
            sa.Column("roas_sample_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("ctr_low", sa.Float(), nullable=True),
            sa.Column("ctr_high", sa.Float(), nullable=True),
            sa.Column("ctr_sample_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("cpc_low", sa.Float(), nullable=True),
            sa.Column("cpc_high", sa.Float(), nullable=True),
            sa.Column("cpc_sample_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("cvr_low", sa.Float(), nullable=True),
            sa.Column("cvr_high", sa.Float(), nullable=True),
            sa.Column("cvr_sample_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("cpl_low", sa.Float(), nullable=True),
            sa.Column("cpl_high", sa.Float(), nullable=True),
            sa.Column("cpl_sample_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("effective_from", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_meta_andromeda_label_policies_scope_key",
            "meta_andromeda_label_policies",
            ["scope_key"],
            unique=False,
        )
        op.create_index(
            "ix_meta_andromeda_label_policies_window_kind",
            "meta_andromeda_label_policies",
            ["window_kind"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "meta_andromeda_label_policies"):
        for idx in ("ix_meta_andromeda_label_policies_window_kind", "ix_meta_andromeda_label_policies_scope_key"):
            idxs = {i["name"] for i in inspector.get_indexes("meta_andromeda_label_policies")}
            if idx in idxs:
                op.drop_index(idx, table_name="meta_andromeda_label_policies")
        op.drop_table("meta_andromeda_label_policies")

    columns = {c["name"] for c in inspector.get_columns("meta_andromeda_calibration_items")}
    if "label_thresholds" in columns:
        op.drop_column("meta_andromeda_calibration_items", "label_thresholds")
