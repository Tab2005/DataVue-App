"""add meta andromeda workflow tables

Revision ID: 20260608_meta_andromeda_workflow_tables
Revises: 403dfb0cfbd4
Create Date: 2026-06-08 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260608_meta_andromeda_workflow_tables"
down_revision = "403dfb0cfbd4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meta_andromeda_assets",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("asset_uri", sa.String(), nullable=False),
        sa.Column("storage_backend", sa.String(length=50), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("asset_type", sa.String(length=20), nullable=False),
        sa.Column("source_filename", sa.String(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=128), nullable=False),
        sa.Column("upload_status", sa.String(length=50), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("public_url", sa.String(), nullable=True),
        sa.Column("uploaded_by", sa.String(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_meta_andromeda_assets_asset_uri"), "meta_andromeda_assets", ["asset_uri"], unique=True)

    op.create_table(
        "meta_andromeda_score_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("runtime_job_id", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("queued_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("asset_uri", sa.String(), nullable=False),
        sa.Column("asset_type", sa.String(length=20), nullable=False),
        sa.Column("asset_id", sa.String(), nullable=True),
        sa.Column("preview_url", sa.String(), nullable=True),
        sa.Column("request_mode", sa.String(length=50), nullable=False),
        sa.Column("objective", sa.String(length=50), nullable=False),
        sa.Column("placement_family", sa.String(length=50), nullable=False),
        sa.Column("market", sa.String(length=20), nullable=False),
        sa.Column("prediction_mode", sa.String(length=50), nullable=True),
        sa.Column("overall_score", sa.Integer(), nullable=True),
        sa.Column("roas_band", sa.String(length=50), nullable=True),
        sa.Column("model_version", sa.String(length=100), nullable=True),
        sa.Column("reviewed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("feedback_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("latest_feedback_decision", sa.String(length=50), nullable=True),
        sa.Column("feature_manifest_id", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("diagnostic_breakdown", sa.JSON(), nullable=False),
        sa.Column("roas_prediction", sa.JSON(), nullable=True),
        sa.Column("risk_tags", sa.JSON(), nullable=False),
        sa.Column("top_positive_drivers", sa.JSON(), nullable=False),
        sa.Column("top_negative_drivers", sa.JSON(), nullable=False),
        sa.Column("explanations", sa.JSON(), nullable=True),
        sa.Column("lineage", sa.JSON(), nullable=False),
        sa.Column("request_context", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["meta_andromeda_assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_meta_andromeda_score_events_runtime_job_id"), "meta_andromeda_score_events", ["runtime_job_id"], unique=False)

    op.create_table(
        "meta_andromeda_feedback_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("score_event_id", sa.String(), nullable=False),
        sa.Column("reviewer_id", sa.String(), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["score_event_id"], ["meta_andromeda_score_events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_meta_andromeda_feedback_events_score_event_id"), "meta_andromeda_feedback_events", ["score_event_id"], unique=False)

    op.create_table(
        "meta_andromeda_release_records",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("record_kind", sa.String(length=50), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=False),
        sa.Column("release_status", sa.String(length=50), nullable=False),
        sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("approved_at", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("pairwise_ranking_accuracy", sa.Float(), nullable=False),
        sa.Column("mean_band_error", sa.Float(), nullable=False),
        sa.Column("promotion_gate_summary", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_meta_andromeda_release_records_model_version"), "meta_andromeda_release_records", ["model_version"], unique=False)
    op.create_index(op.f("ix_meta_andromeda_release_records_record_kind"), "meta_andromeda_release_records", ["record_kind"], unique=False)

    op.create_table(
        "meta_andromeda_release_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_meta_andromeda_release_events_model_version"), "meta_andromeda_release_events", ["model_version"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_meta_andromeda_release_events_model_version"), table_name="meta_andromeda_release_events")
    op.drop_table("meta_andromeda_release_events")
    op.drop_index(op.f("ix_meta_andromeda_release_records_record_kind"), table_name="meta_andromeda_release_records")
    op.drop_index(op.f("ix_meta_andromeda_release_records_model_version"), table_name="meta_andromeda_release_records")
    op.drop_table("meta_andromeda_release_records")
    op.drop_index(op.f("ix_meta_andromeda_feedback_events_score_event_id"), table_name="meta_andromeda_feedback_events")
    op.drop_table("meta_andromeda_feedback_events")
    op.drop_index(op.f("ix_meta_andromeda_score_events_runtime_job_id"), table_name="meta_andromeda_score_events")
    op.drop_table("meta_andromeda_score_events")
    op.drop_index(op.f("ix_meta_andromeda_assets_asset_uri"), table_name="meta_andromeda_assets")
    op.drop_table("meta_andromeda_assets")
