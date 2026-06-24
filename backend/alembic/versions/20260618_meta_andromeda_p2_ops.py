"""meta andromeda p2 operational tables and indexes

Revision ID: 20260618_meta_andromeda_p2_ops
Revises: 20260618_meta_andromeda_observed_creatives
Create Date: 2026-06-18 18:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260618_meta_andromeda_p2_ops"
down_revision = "20260618_meta_andromeda_observed_creatives"
branch_labels = None
depends_on = None


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, "meta_andromeda_calibration_datasets"):
        op.create_table(
            "meta_andromeda_calibration_datasets",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("window_kind", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("label_policy_version", sa.String(length=50), nullable=False),
            sa.Column("since", sa.String(length=40), nullable=True),
            sa.Column("until", sa.String(length=40), nullable=True),
            sa.Column("excluded_observed_ids", sa.JSON(), nullable=False),
            sa.Column("synced_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("summary", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_meta_andromeda_calibration_datasets_window_kind",
            "meta_andromeda_calibration_datasets",
            ["window_kind"],
            unique=False,
        )
        op.create_index(
            "ix_meta_andromeda_calibration_datasets_status",
            "meta_andromeda_calibration_datasets",
            ["status"],
            unique=False,
        )

    inspector = sa.inspect(bind)
    if not _table_exists(inspector, "meta_andromeda_calibration_items"):
        op.create_table(
            "meta_andromeda_calibration_items",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("dataset_id", sa.String(), nullable=False),
            sa.Column("observed_creative_id", sa.String(), nullable=False),
            sa.Column("score_event_id", sa.String(), nullable=False),
            sa.Column("asset_uri", sa.String(), nullable=True),
            sa.Column("objective", sa.String(length=50), nullable=True),
            sa.Column("market", sa.String(length=20), nullable=False),
            sa.Column("placement_family", sa.String(length=50), nullable=False),
            sa.Column("prediction_band", sa.String(length=20), nullable=False),
            sa.Column("observed_band", sa.String(length=20), nullable=False),
            sa.Column("error", sa.Float(), nullable=False),
            sa.Column("performance_snapshot", sa.JSON(), nullable=False),
            sa.Column("label_policy_version", sa.String(length=50), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.ForeignKeyConstraint(["dataset_id"], ["meta_andromeda_calibration_datasets.id"]),
            sa.ForeignKeyConstraint(["observed_creative_id"], ["meta_andromeda_observed_creatives.id"]),
            sa.ForeignKeyConstraint(["score_event_id"], ["meta_andromeda_score_events.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_meta_andromeda_calibration_items_dataset_id",
            "meta_andromeda_calibration_items",
            ["dataset_id"],
            unique=False,
        )
        op.create_index(
            "ix_meta_andromeda_calibration_items_observed_creative_id",
            "meta_andromeda_calibration_items",
            ["observed_creative_id"],
            unique=False,
        )
        op.create_index(
            "ix_meta_andromeda_calibration_items_score_event_id",
            "meta_andromeda_calibration_items",
            ["score_event_id"],
            unique=False,
        )
        op.create_index(
            "ix_meta_andromeda_calibration_items_asset_uri",
            "meta_andromeda_calibration_items",
            ["asset_uri"],
            unique=False,
        )

    inspector = sa.inspect(bind)
    score_indexes = _index_names(inspector, "meta_andromeda_score_events")
    score_columns = _column_names(inspector, "meta_andromeda_score_events")
    if "ix_meta_andromeda_score_events_status_reviewed_created_at" not in score_indexes:
        if "reviewed" in score_columns and "created_at" in score_columns:
            op.create_index(
                "ix_meta_andromeda_score_events_status_reviewed_created_at",
                "meta_andromeda_score_events",
                ["status", "reviewed", "created_at"],
                unique=False,
            )
    if "ix_meta_andromeda_score_events_status_queued_at" not in score_indexes:
        if "queued_at" in score_columns:
            op.create_index(
                "ix_meta_andromeda_score_events_status_queued_at",
                "meta_andromeda_score_events",
                ["status", "queued_at"],
                unique=False,
            )
    if "ix_meta_andromeda_score_events_asset_uri_status_completed_at" not in score_indexes:
        if "asset_uri" in score_columns and "completed_at" in score_columns:
            op.create_index(
                "ix_meta_andromeda_score_events_asset_uri_status_completed_at",
                "meta_andromeda_score_events",
                ["asset_uri", "status", "completed_at"],
                unique=False,
            )

    worker_indexes = _index_names(inspector, "meta_andromeda_worker_events")
    if "ix_meta_andromeda_worker_events_score_event_id_created_at" not in worker_indexes:
        op.create_index(
            "ix_meta_andromeda_worker_events_score_event_id_created_at",
            "meta_andromeda_worker_events",
            ["score_event_id", "created_at"],
            unique=False,
        )

    dead_letter_indexes = _index_names(inspector, "meta_andromeda_dead_letters")
    if "ix_meta_andromeda_dead_letters_score_event_id_created_at" not in dead_letter_indexes:
        op.create_index(
            "ix_meta_andromeda_dead_letters_score_event_id_created_at",
            "meta_andromeda_dead_letters",
            ["score_event_id", "created_at"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "meta_andromeda_dead_letters"):
        if "ix_meta_andromeda_dead_letters_score_event_id_created_at" in _index_names(inspector, "meta_andromeda_dead_letters"):
            op.drop_index("ix_meta_andromeda_dead_letters_score_event_id_created_at", table_name="meta_andromeda_dead_letters")
    if _table_exists(inspector, "meta_andromeda_worker_events"):
        if "ix_meta_andromeda_worker_events_score_event_id_created_at" in _index_names(inspector, "meta_andromeda_worker_events"):
            op.drop_index("ix_meta_andromeda_worker_events_score_event_id_created_at", table_name="meta_andromeda_worker_events")
    if _table_exists(inspector, "meta_andromeda_score_events"):
        score_indexes = _index_names(inspector, "meta_andromeda_score_events")
        if "ix_meta_andromeda_score_events_asset_uri_status_completed_at" in score_indexes:
            op.drop_index("ix_meta_andromeda_score_events_asset_uri_status_completed_at", table_name="meta_andromeda_score_events")
        if "ix_meta_andromeda_score_events_status_queued_at" in score_indexes:
            op.drop_index("ix_meta_andromeda_score_events_status_queued_at", table_name="meta_andromeda_score_events")
        if "ix_meta_andromeda_score_events_status_reviewed_created_at" in score_indexes:
            op.drop_index("ix_meta_andromeda_score_events_status_reviewed_created_at", table_name="meta_andromeda_score_events")

    if _table_exists(inspector, "meta_andromeda_calibration_items"):
        item_indexes = _index_names(inspector, "meta_andromeda_calibration_items")
        for index_name in (
            "ix_meta_andromeda_calibration_items_asset_uri",
            "ix_meta_andromeda_calibration_items_score_event_id",
            "ix_meta_andromeda_calibration_items_observed_creative_id",
            "ix_meta_andromeda_calibration_items_dataset_id",
        ):
            if index_name in item_indexes:
                op.drop_index(index_name, table_name="meta_andromeda_calibration_items")
        op.drop_table("meta_andromeda_calibration_items")

    if _table_exists(inspector, "meta_andromeda_calibration_datasets"):
        dataset_indexes = _index_names(inspector, "meta_andromeda_calibration_datasets")
        for index_name in (
            "ix_meta_andromeda_calibration_datasets_status",
            "ix_meta_andromeda_calibration_datasets_window_kind",
        ):
            if index_name in dataset_indexes:
                op.drop_index(index_name, table_name="meta_andromeda_calibration_datasets")
        op.drop_table("meta_andromeda_calibration_datasets")
