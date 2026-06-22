"""add meta andromeda worker observability tables

Revision ID: 20260609_meta_andromeda_worker_observability
Revises: 20260608_meta_andromeda_workflow_tables
Create Date: 2026-06-09 09:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260609_meta_andromeda_worker_observability"
down_revision = "20260608_meta_andromeda_workflow_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meta_andromeda_worker_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("score_event_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("queue_host", sa.String(length=50), nullable=False),
        sa.Column("runtime_job_id", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("event_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["score_event_id"], ["meta_andromeda_score_events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_meta_andromeda_worker_events_event_type"), "meta_andromeda_worker_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_meta_andromeda_worker_events_runtime_job_id"), "meta_andromeda_worker_events", ["runtime_job_id"], unique=False)
    op.create_index(op.f("ix_meta_andromeda_worker_events_score_event_id"), "meta_andromeda_worker_events", ["score_event_id"], unique=False)

    op.create_table(
        "meta_andromeda_dead_letters",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("score_event_id", sa.String(), nullable=False),
        sa.Column("queue_host", sa.String(length=50), nullable=False),
        sa.Column("runtime_job_id", sa.String(length=120), nullable=True),
        sa.Column("final_error_message", sa.Text(), nullable=False),
        sa.Column("failure_stage", sa.String(length=50), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("dead_letter_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["score_event_id"], ["meta_andromeda_score_events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_meta_andromeda_dead_letters_runtime_job_id"), "meta_andromeda_dead_letters", ["runtime_job_id"], unique=False)
    op.create_index(op.f("ix_meta_andromeda_dead_letters_score_event_id"), "meta_andromeda_dead_letters", ["score_event_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_meta_andromeda_dead_letters_score_event_id"), table_name="meta_andromeda_dead_letters")
    op.drop_index(op.f("ix_meta_andromeda_dead_letters_runtime_job_id"), table_name="meta_andromeda_dead_letters")
    op.drop_table("meta_andromeda_dead_letters")
    op.drop_index(op.f("ix_meta_andromeda_worker_events_score_event_id"), table_name="meta_andromeda_worker_events")
    op.drop_index(op.f("ix_meta_andromeda_worker_events_runtime_job_id"), table_name="meta_andromeda_worker_events")
    op.drop_index(op.f("ix_meta_andromeda_worker_events_event_type"), table_name="meta_andromeda_worker_events")
    op.drop_table("meta_andromeda_worker_events")
