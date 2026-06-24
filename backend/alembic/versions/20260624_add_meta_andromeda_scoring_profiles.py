"""add meta_andromeda_scoring_profiles table

Revision ID: 20260624_add_meta_andromeda_scoring_profiles
Revises: 20260618_meta_andromeda_p2_ops
Create Date: 2026-06-24 00:00:00.000000
"""

import json
from alembic import op
import sqlalchemy as sa


revision = "20260624_add_meta_andromeda_scoring_profiles"
down_revision = "20260618_meta_andromeda_p2_ops"
branch_labels = None
depends_on = None


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


_SEED_USER_PROMPT_TEMPLATE = (
    "You are the Meta Andromeda creative scoring runtime, an expert in mobile ad conversion optimization (CRO) and ad design.\n"
    "Analyze both the provided ad image (via image_url) and the text metadata details to evaluate the overall performance.\n\n"
    "CRITICAL EVALUATION CRITERIA:\n"
    "1. Visual Focus & Hierarchy: Is the product/subject clear? Is the background clean and supportive?\n"
    "2. Text Ratio & Legibility: Are copy elements in the image readable? Is the text-to-image ratio balanced (avoiding overloaded text)?\n"
    "3. CTA Prominence: Is there a clear visual CTA in the image, and does it align with the text CTA?\n"
    "4. Relevance & Consistency: Does the visual style connect tightly with the Headline and Primary text?\n\n"
    "Return JSON only with keys: overall_score, roas_band, top_positive_drivers, "
    "top_negative_drivers, risk_tags, diagnostic_breakdown, summary.\n"
    "Use overall_score as integer 0-100. Be critical and conservative—do not give high scores (>80) unless the creative is truly premium and highly optimized.\n"
    "Use roas_band as one of high/mid/low/null.\n"
    "The diagnostic_breakdown object MUST contain exactly these keys with short Chinese evaluation:\n"
    "  - visual_appeal: Evaluates composition, focal point, and aesthetics.\n"
    "  - copywriting: Evaluates headline and primary text persuasiveness.\n"
    "  - cta_clarity: Evaluates CTA prominence and action clarity.\n"
    "  - relevance: Evaluates the consistency between the image and texts.\n\n"
    "All textual outputs (summary, top_positive_drivers, top_negative_drivers, diagnostic_breakdown values) MUST be in Traditional Chinese (繁體中文).\n"
    "Asset type: {asset_type}\n"
    "Objective: {objective}\n"
    "Placement family: {placement_family}\n"
    "Market: {market}\n"
    "Request mode: {request_mode}\n"
    "Headline: {headline}\n"
    "Primary text: {primary_text}\n"
    "CTA: {cta}\n"
)

_SEED_SYSTEM_PROMPT = (
    "You are an elite performance marketing creative auditor. Score ad creatives conservatively based on CRO best practices.\n"
    "Always inspect the image details if available. Give objective, realistic scores. Do not sugarcoat.\n"
    "All explanations, summaries, and breakdowns MUST be written in Traditional Chinese (繁體中文)."
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, "meta_andromeda_scoring_profiles"):
        op.create_table(
            "meta_andromeda_scoring_profiles",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("profile_name", sa.String(), nullable=False),
            sa.Column("user_prompt_template", sa.Text(), nullable=False),
            sa.Column("system_prompt", sa.Text(), nullable=False),
            sa.Column("calibration_guidance", sa.Text(), nullable=True),
            sa.Column("few_shot_examples", sa.JSON(), nullable=False),
            sa.Column("bias_summary", sa.JSON(), nullable=True),
            sa.Column("source", sa.String(length=30), nullable=False, server_default="seed"),
            sa.Column("base_profile_name", sa.String(), nullable=True),
            sa.Column("calibration_dataset_id", sa.String(), nullable=True),
            sa.Column("is_promoted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("promoted_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.ForeignKeyConstraint(
                ["calibration_dataset_id"],
                ["meta_andromeda_calibration_datasets.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("profile_name"),
        )
        op.create_index(
            "ix_meta_andromeda_scoring_profiles_profile_name",
            "meta_andromeda_scoring_profiles",
            ["profile_name"],
            unique=True,
        )
        op.create_index(
            "ix_meta_andromeda_scoring_profiles_is_promoted",
            "meta_andromeda_scoring_profiles",
            ["is_promoted"],
            unique=False,
        )

        # Seed existing profiles
        profiles_table = sa.table(
            "meta_andromeda_scoring_profiles",
            sa.column("id", sa.String),
            sa.column("profile_name", sa.String),
            sa.column("user_prompt_template", sa.Text),
            sa.column("system_prompt", sa.Text),
            sa.column("calibration_guidance", sa.Text),
            sa.column("few_shot_examples", sa.JSON),
            sa.column("bias_summary", sa.JSON),
            sa.column("source", sa.String),
            sa.column("base_profile_name", sa.String),
            sa.column("calibration_dataset_id", sa.String),
            sa.column("is_promoted", sa.Boolean),
        )
        op.bulk_insert(profiles_table, [
            {
                "id": "sp_seed_v1_000000",
                "profile_name": "creative_scoring_v1",
                "user_prompt_template": _SEED_USER_PROMPT_TEMPLATE,
                "system_prompt": _SEED_SYSTEM_PROMPT,
                "calibration_guidance": None,
                "few_shot_examples": json.dumps([]),
                "bias_summary": None,
                "source": "seed",
                "base_profile_name": None,
                "calibration_dataset_id": None,
                "is_promoted": False,
            },
            {
                "id": "sp_seed_v2_000000",
                "profile_name": "creative_scoring_v2",
                "user_prompt_template": _SEED_USER_PROMPT_TEMPLATE,
                "system_prompt": _SEED_SYSTEM_PROMPT,
                "calibration_guidance": None,
                "few_shot_examples": json.dumps([]),
                "bias_summary": None,
                "source": "seed",
                "base_profile_name": None,
                "calibration_dataset_id": None,
                "is_promoted": True,
            },
        ])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "meta_andromeda_scoring_profiles"):
        for idx in ("ix_meta_andromeda_scoring_profiles_is_promoted",
                    "ix_meta_andromeda_scoring_profiles_profile_name"):
            idxs = {i["name"] for i in inspector.get_indexes("meta_andromeda_scoring_profiles")}
            if idx in idxs:
                op.drop_index(idx, table_name="meta_andromeda_scoring_profiles")
        op.drop_table("meta_andromeda_scoring_profiles")
