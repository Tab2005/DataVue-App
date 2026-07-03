"""meta andromeda scoring-loop wave 3: confidence calibration table + diagnostic scores + model registry table

Revision ID: 20260703_meta_andromeda_p2_wave3
Revises: 20260703_meta_andromeda_p1_wave2
Create Date: 2026-07-03 02:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260703_meta_andromeda_p2_wave3"
down_revision = "20260703_meta_andromeda_p1_wave2"
branch_labels = None
depends_on = None


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    item_columns = {c["name"] for c in inspector.get_columns("meta_andromeda_calibration_items")}
    if "diagnostic_scores" not in item_columns:
        op.add_column(
            "meta_andromeda_calibration_items",
            sa.Column("diagnostic_scores", sa.JSON(), nullable=True),
        )

    release_columns = {c["name"] for c in inspector.get_columns("meta_andromeda_release_records")}
    if "metrics_source" not in release_columns:
        op.add_column(
            "meta_andromeda_release_records",
            sa.Column("metrics_source", sa.String(length=20), nullable=False, server_default="seed"),
        )
    if "metrics_sample_count" not in release_columns:
        op.add_column(
            "meta_andromeda_release_records",
            sa.Column("metrics_sample_count", sa.Integer(), nullable=True),
        )

    if not _table_exists(inspector, "meta_andromeda_confidence_calibrations"):
        op.create_table(
            "meta_andromeda_confidence_calibrations",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("scope_key", sa.String(length=120), nullable=False),
            sa.Column("calibration_data", sa.JSON(), nullable=False),
            sa.Column("item_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("fitted_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("scope_key"),
        )
        op.create_index(
            "ix_meta_andromeda_confidence_calibrations_scope_key",
            "meta_andromeda_confidence_calibrations",
            ["scope_key"],
            unique=True,
        )

    if not _table_exists(inspector, "meta_andromeda_model_registry_entries"):
        op.create_table(
            "meta_andromeda_model_registry_entries",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("model_version", sa.String(length=100), nullable=False),
            sa.Column("provider", sa.String(length=50), nullable=False),
            sa.Column("provider_model", sa.String(length=200), nullable=False),
            sa.Column("scoring_profile", sa.String(length=120), nullable=False),
            sa.Column("feature_manifest_id", sa.String(length=100), nullable=False),
            sa.Column("release_channel", sa.String(length=30), nullable=False),
            sa.Column("source_of_truth", sa.String(length=120), nullable=False),
            sa.Column("is_current_production", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("model_version"),
        )
        op.create_index(
            "ix_meta_andromeda_model_registry_entries_model_version",
            "meta_andromeda_model_registry_entries",
            ["model_version"],
            unique=True,
        )
        op.create_index(
            "ix_meta_andromeda_model_registry_entries_is_current_production",
            "meta_andromeda_model_registry_entries",
            ["is_current_production"],
            unique=False,
        )

        registry_table = sa.table(
            "meta_andromeda_model_registry_entries",
            sa.column("id", sa.String),
            sa.column("model_version", sa.String),
            sa.column("provider", sa.String),
            sa.column("provider_model", sa.String),
            sa.column("scoring_profile", sa.String),
            sa.column("feature_manifest_id", sa.String),
            sa.column("release_channel", sa.String),
            sa.column("source_of_truth", sa.String),
            sa.column("is_current_production", sa.Boolean),
        )
        # 種子資料對齊現有 model_registry.py 的硬編碼清單，落地到 DB 後兩者同步
        op.bulk_insert(registry_table, [
            {
                "id": "mr_seed_prod_20260528",
                "model_version": "prod_v2026_05_28",
                "provider": "openrouter",
                "provider_model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
                "scoring_profile": "creative_scoring_v1",
                "feature_manifest_id": "fm_prod_20260528",
                "release_channel": "production",
                "source_of_truth": "datavue.meta_andromeda.registry",
                "is_current_production": False,
            },
            {
                "id": "mr_seed_prod_20260512",
                "model_version": "prod_v2026_05_12",
                "provider": "heuristic",
                "provider_model": "heuristic://creative_scoring_v0",
                "scoring_profile": "creative_scoring_v0",
                "feature_manifest_id": "fm_prod_20260512",
                "release_channel": "superseded",
                "source_of_truth": "datavue.meta_andromeda.registry",
                "is_current_production": False,
            },
            {
                "id": "mr_seed_cand_20260605_a",
                "model_version": "cand_v2026_06_05_a",
                "provider": "openrouter",
                "provider_model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
                "scoring_profile": "creative_scoring_v2",
                "feature_manifest_id": "fm_cand_20260605_a",
                "release_channel": "candidate",
                "source_of_truth": "datavue.meta_andromeda.registry",
                # 目前實際生效版本（見 core/config.py 預設值），落地時標記為 current_production
                "is_current_production": True,
            },
            {
                "id": "mr_seed_cand_20260604_b",
                "model_version": "cand_v2026_06_04_b",
                "provider": "openrouter",
                "provider_model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
                "scoring_profile": "creative_scoring_v1",
                "feature_manifest_id": "fm_cand_20260604_b",
                "release_channel": "candidate",
                "source_of_truth": "datavue.meta_andromeda.registry",
                "is_current_production": False,
            },
            {
                "id": "mr_seed_candidate_v0",
                "model_version": "candidate_v0",
                "provider": "heuristic",
                "provider_model": "heuristic://creative_scoring_v0",
                "scoring_profile": "creative_scoring_v0",
                "feature_manifest_id": "fm_candidate_v0",
                "release_channel": "local_fallback",
                "source_of_truth": "datavue.meta_andromeda.registry",
                "is_current_production": False,
            },
        ])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "meta_andromeda_model_registry_entries"):
        for idx in (
            "ix_meta_andromeda_model_registry_entries_is_current_production",
            "ix_meta_andromeda_model_registry_entries_model_version",
        ):
            idxs = {i["name"] for i in inspector.get_indexes("meta_andromeda_model_registry_entries")}
            if idx in idxs:
                op.drop_index(idx, table_name="meta_andromeda_model_registry_entries")
        op.drop_table("meta_andromeda_model_registry_entries")

    if _table_exists(inspector, "meta_andromeda_confidence_calibrations"):
        idxs = {i["name"] for i in inspector.get_indexes("meta_andromeda_confidence_calibrations")}
        if "ix_meta_andromeda_confidence_calibrations_scope_key" in idxs:
            op.drop_index(
                "ix_meta_andromeda_confidence_calibrations_scope_key",
                table_name="meta_andromeda_confidence_calibrations",
            )
        op.drop_table("meta_andromeda_confidence_calibrations")

    item_columns = {c["name"] for c in inspector.get_columns("meta_andromeda_calibration_items")}
    if "diagnostic_scores" in item_columns:
        op.drop_column("meta_andromeda_calibration_items", "diagnostic_scores")

    release_columns = {c["name"] for c in inspector.get_columns("meta_andromeda_release_records")}
    if "metrics_sample_count" in release_columns:
        op.drop_column("meta_andromeda_release_records", "metrics_sample_count")
    if "metrics_source" in release_columns:
        op.drop_column("meta_andromeda_release_records", "metrics_source")
