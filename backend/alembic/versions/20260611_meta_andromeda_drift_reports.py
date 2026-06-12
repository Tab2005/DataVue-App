"""add meta andromeda drift reports

Revision ID: 20260611_meta_andromeda_drift_reports
Revises: 20260609_meta_andromeda_worker_observability
Create Date: 2026-06-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260611_meta_andromeda_drift_reports"
down_revision = "20260609_meta_andromeda_worker_observability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meta_andromeda_drift_reports",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("window_kind", sa.String(length=50), nullable=False),
        sa.Column("drift_status", sa.String(length=50), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False, server_default="info"),
        sa.Column("triggered_by", sa.String(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("report_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_meta_andromeda_drift_reports_window_kind",
        "meta_andromeda_drift_reports",
        ["window_kind"],
        unique=False,
    )
    op.create_index(
        "ix_meta_andromeda_drift_reports_drift_status",
        "meta_andromeda_drift_reports",
        ["drift_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_meta_andromeda_drift_reports_drift_status", table_name="meta_andromeda_drift_reports")
    op.drop_index("ix_meta_andromeda_drift_reports_window_kind", table_name="meta_andromeda_drift_reports")
    op.drop_table("meta_andromeda_drift_reports")
