"""hotfix: backfill missing meta_andromeda_scoring_profiles seed rows

Production diagnosis (2026-07-03): meta_andromeda_scoring_profiles existed as
an EMPTY table before 20260624_add_meta_andromeda_scoring_profiles ran, so
that migration's `if not _table_exists(...)` guard skipped the bulk_insert
entirely — the table was created by an earlier legacy-schema-consolidation
migration without the accompanying seed data. Net effect: the calibration
pipeline could never find a base profile to clone from
(calibration_failed:base_profile_missing on every run since 2026-06-30).

This migration is idempotent on profile_name (not table existence) so it
backfills the two seed profiles regardless of why they're missing, and is
safe to run even if the rows already exist (no-op per missing name).

Revision ID: 20260703_ma_seed_profile_hotfix
Revises: 20260703_meta_andromeda_p2_wave3
Create Date: 2026-07-03 06:00:00.000000
"""

import json
import uuid

from alembic import op
import sqlalchemy as sa


revision = "20260703_ma_seed_profile_hotfix"
down_revision = "20260703_meta_andromeda_p2_wave3"
branch_labels = None
depends_on = None


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

_OBJ_PROMPT_SUFFIX = (
    "Asset type: {asset_type}\n"
    "Objective: {objective}\n"
    "Placement family: {placement_family}\n"
    "Market: {market}\n"
    "Request mode: {request_mode}\n"
    "Headline: {headline}\n"
    "Primary text: {primary_text}\n"
    "CTA: {cta}\n"
)

_LEAD_USER_PROMPT = (
    "You are the Meta Andromeda creative scoring runtime, specialized in lead generation and form completion optimization.\n"
    "Evaluate the creative's ability to attract qualified leads and motivate form submissions.\n\n"
    "EVALUATION CRITERIA FOR LEAD GENERATION CAMPAIGNS:\n"
    "1. Trust Signals: Does the creative establish credibility? (social proof, certifications, testimonials, brand authority)\n"
    "2. Value Proposition: Is the lead magnet or offer clearly communicated? Why should the audience submit their info?\n"
    "3. CTA Clarity: Is the lead generation CTA (Sign up, Get quote, Free trial) clear and low-friction?\n"
    "4. Audience Fit: Does the creative speak directly to the target audience's pain points or desires?\n\n"
    "NOTE: This is a LEAD GENERATION campaign. Evaluate based on CVR/CPL potential.\n"
    "Use roas_band as LEAD QUALITY BAND: high = strong qualified lead signals, mid = moderate, low = weak.\n\n"
    "Return JSON only with keys: overall_score, roas_band, top_positive_drivers, top_negative_drivers, risk_tags, diagnostic_breakdown, summary.\n"
    "Use overall_score as integer 0-100. Be critical and conservative.\n"
    "Use roas_band as one of high/mid/low/null to represent lead quality potential.\n"
    "The diagnostic_breakdown object MUST contain exactly these keys with short Chinese evaluation:\n"
    "  - trust_signals: Evaluates credibility indicators (reviews, certifications, brand reputation).\n"
    "  - value_proposition: Evaluates clarity and appeal of the offer or lead magnet.\n"
    "  - cta_clarity: Evaluates CTA prominence and friction level for lead submission.\n"
    "  - audience_fit: Evaluates how well the creative addresses the target audience's needs.\n\n"
    "All textual outputs MUST be in Traditional Chinese (繁體中文).\n"
) + _OBJ_PROMPT_SUFFIX

_TRAFFIC_USER_PROMPT = (
    "You are the Meta Andromeda creative scoring runtime, specialized in traffic and click-through optimization.\n"
    "Evaluate the creative's ability to drive clicks, curiosity, and landing page visits.\n\n"
    "EVALUATION CRITERIA FOR TRAFFIC/CLICK CAMPAIGNS:\n"
    "1. Thumb-Stop Power: Does the first visual frame immediately grab attention and pause scrolling?\n"
    "2. Curiosity Hook: Does the ad create enough curiosity, urgency, or intrigue to motivate a click?\n"
    "3. Landing Relevance: Is the ad message clearly aligned with what users will find after clicking?\n"
    "4. Visual Appeal: Is the creative visually engaging and feed-appropriate?\n\n"
    "IMPORTANT: This is a TRAFFIC/CLICK campaign. Do NOT evaluate purchase intent or ROAS.\n"
    "Set roas_band to null. Score based on CTR potential ONLY.\n\n"
    "Return JSON only with keys: overall_score, roas_band, top_positive_drivers, top_negative_drivers, risk_tags, diagnostic_breakdown, summary.\n"
    "Use overall_score as integer 0-100.\n"
    "Set roas_band to null — this campaign type does not use ROAS prediction.\n"
    "The diagnostic_breakdown object MUST contain exactly these keys with short Chinese evaluation:\n"
    "  - thumb_stop: Evaluates visual stopping power and feed scroll interruption strength.\n"
    "  - curiosity_hook: Evaluates click motivation, urgency, curiosity, or intrigue triggers.\n"
    "  - visual_appeal: Evaluates overall visual quality, composition, and aesthetic appeal.\n"
    "  - landing_relevance: Evaluates message-to-landing consistency and user expectation alignment.\n\n"
    "All textual outputs MUST be in Traditional Chinese (繁體中文).\n"
) + _OBJ_PROMPT_SUFFIX

_AWARENESS_USER_PROMPT = (
    "You are the Meta Andromeda creative scoring runtime, specialized in brand awareness and reach campaign evaluation.\n"
    "Evaluate the creative's potential for maximizing brand recall, emotional impact, and audience reach efficiency.\n\n"
    "EVALUATION CRITERIA FOR AWARENESS/REACH CAMPAIGNS:\n"
    "1. Brand Recall: Is the brand or product immediately identifiable? Will audiences remember this ad after exposure?\n"
    "2. Message Clarity: Is the brand message communicated within 1-3 seconds? Simple is better.\n"
    "3. Visual Distinctiveness: Does the creative stand out in a crowded feed without requiring click intent?\n"
    "4. Emotional Resonance: Does the creative evoke the intended emotion (aspiration, trust, delight, nostalgia)?\n\n"
    "IMPORTANT: This is a BRAND AWARENESS/REACH campaign. Purchase conversion and ROAS are NOT applicable.\n"
    "Set roas_band to null. A missing or weak CTA does NOT penalize this creative type.\n"
    "Score based on brand memorability and emotional impact ONLY.\n\n"
    "Return JSON only with keys: overall_score, roas_band, top_positive_drivers, top_negative_drivers, risk_tags, diagnostic_breakdown, summary.\n"
    "Use overall_score as integer 0-100.\n"
    "Set roas_band to null — brand awareness campaigns do not use ROAS prediction.\n"
    "The diagnostic_breakdown object MUST contain exactly these keys with short Chinese evaluation:\n"
    "  - brand_recall: Evaluates brand memorability, logo/name visibility, and post-exposure recognition.\n"
    "  - message_clarity: Evaluates how quickly and clearly the core brand message is communicated.\n"
    "  - visual_distinctiveness: Evaluates thumb-stop power and visual uniqueness in a crowded feed.\n"
    "  - emotional_resonance: Evaluates emotional impact, tone alignment, and audience connection depth.\n\n"
    "All textual outputs MUST be in Traditional Chinese (繁體中文).\n"
) + _OBJ_PROMPT_SUFFIX

_VIDEO_USER_PROMPT = (
    "You are the Meta Andromeda creative scoring runtime, specialized in video view and watch-time optimization.\n"
    "Evaluate the video creative's hook strength, pacing, and viewer retention potential.\n\n"
    "EVALUATION CRITERIA FOR VIDEO VIEW CAMPAIGNS:\n"
    "1. Hook Strength (First 3 Seconds): Does the video immediately capture attention before the viewer scrolls past?\n"
    "2. Pacing & Flow: Is the video's pacing appropriate for the placement? Does it sustain viewer interest?\n"
    "3. Message Delivery: Is the core message communicated before typical drop-off points (usually 6-15s)?\n"
    "4. Brand Integration: Is the brand naturally integrated without disrupting the viewing experience?\n\n"
    "IMPORTANT: This is a VIDEO VIEW campaign. Evaluate for VTR (view-through rate) potential, NOT purchase conversion.\n"
    "Set roas_band to null. A missing text CTA does NOT penalize this creative.\n\n"
    "Return JSON only with keys: overall_score, roas_band, top_positive_drivers, top_negative_drivers, risk_tags, diagnostic_breakdown, summary.\n"
    "Use overall_score as integer 0-100.\n"
    "Set roas_band to null — video view campaigns do not use ROAS prediction.\n"
    "The diagnostic_breakdown object MUST contain exactly these keys with short Chinese evaluation:\n"
    "  - hook_strength: Evaluates the visual and audio power of the opening 1-3 seconds.\n"
    "  - pacing: Evaluates video rhythm, edit speed, and ability to maintain viewer attention.\n"
    "  - message_delivery: Evaluates how efficiently the core message is delivered before drop-off.\n"
    "  - brand_integration: Evaluates natural brand visibility without disrupting the experience.\n\n"
    "All textual outputs MUST be in Traditional Chinese (繁體中文).\n"
) + _OBJ_PROMPT_SUFFIX

_ENGAGEMENT_USER_PROMPT = (
    "You are the Meta Andromeda creative scoring runtime, specialized in social engagement and community interaction optimization.\n"
    "Evaluate the creative's shareability, emotional triggers, and interaction potential.\n\n"
    "EVALUATION CRITERIA FOR ENGAGEMENT CAMPAIGNS:\n"
    "1. Shareability: Is the content inherently shareable? Would audiences want to tag friends or repost?\n"
    "2. Emotional Hook: Does the content evoke a strong emotion (humor, surprise, inspiration, controversy, nostalgia)?\n"
    "3. Interaction Trigger: Does the content naturally invite comments, reactions, or discussion?\n"
    "4. Visual Impact: Is the visual quality strong enough to earn organic engagement and stop the scroll?\n\n"
    "IMPORTANT: This is an ENGAGEMENT campaign (likes, comments, shares). Do NOT evaluate purchase intent.\n"
    "Set roas_band to null. Score based on social engagement rate potential ONLY.\n\n"
    "Return JSON only with keys: overall_score, roas_band, top_positive_drivers, top_negative_drivers, risk_tags, diagnostic_breakdown, summary.\n"
    "Use overall_score as integer 0-100.\n"
    "Set roas_band to null — engagement campaigns do not use ROAS prediction.\n"
    "The diagnostic_breakdown object MUST contain exactly these keys with short Chinese evaluation:\n"
    "  - shareability: Evaluates potential for organic sharing and audience tagging behavior.\n"
    "  - emotional_hook: Evaluates strength of emotional trigger and its intensity and authenticity.\n"
    "  - interaction_trigger: Evaluates the content's ability to inspire comments, questions, and reactions.\n"
    "  - visual_impact: Evaluates feed-stopping power and overall visual quality for organic reach.\n\n"
    "All textual outputs MUST be in Traditional Chinese (繁體中文).\n"
) + _OBJ_PROMPT_SUFFIX

_LEAD_SYSTEM_PROMPT = (
    "You are an elite performance marketing creative auditor specializing in lead generation campaigns.\n"
    "Evaluate creatives for trust, value proposition clarity, and qualified lead conversion potential.\n"
    "Score conservatively. A strong lead creative builds trust and removes friction, not just looks good.\n"
    "All explanations, summaries, and breakdowns MUST be written in Traditional Chinese (繁體中文)."
)

_TRAFFIC_SYSTEM_PROMPT = (
    "You are an elite performance marketing creative auditor specializing in traffic and CTR optimization.\n"
    "Evaluate creatives for thumb-stop power, curiosity triggers, and click motivation.\n"
    "Score conservatively. Do NOT penalize for missing purchase CTAs — this is a traffic campaign.\n"
    "All explanations, summaries, and breakdowns MUST be written in Traditional Chinese (繁體中文)."
)

_AWARENESS_SYSTEM_PROMPT = (
    "You are an elite brand strategist and creative auditor specializing in awareness and reach campaigns.\n"
    "Evaluate creatives for brand memorability, emotional resonance, and visual distinctiveness.\n"
    "Do NOT penalize for weak CTAs or low purchase intent — awareness campaigns are not meant to convert directly.\n"
    "All explanations, summaries, and breakdowns MUST be written in Traditional Chinese (繁體中文)."
)

_VIDEO_SYSTEM_PROMPT = (
    "You are an elite video creative auditor specializing in video view and watch-time optimization.\n"
    "Evaluate video hooks, pacing, and viewer retention potential.\n"
    "Assume the asset is a video. Focus on the opening seconds, narrative flow, and brand integration.\n"
    "All explanations, summaries, and breakdowns MUST be written in Traditional Chinese (繁體中文)."
)

_ENGAGEMENT_SYSTEM_PROMPT = (
    "You are an elite social media creative auditor specializing in engagement and community interaction.\n"
    "Evaluate creatives for shareability, emotional triggers, and interaction potential.\n"
    "Do NOT penalize for missing purchase CTAs — this is an engagement campaign.\n"
    "All explanations, summaries, and breakdowns MUST be written in Traditional Chinese (繁體中文)."
)

_OBJECTIVE_PROFILES_SEED = {
    "lead": {
        "user_prompt_template": _LEAD_USER_PROMPT,
        "system_prompt": _LEAD_SYSTEM_PROMPT,
        "metric_focus": "cvr_cpl",
        "roas_band_eligible": True,
        "roas_band_label": "lead_quality_band",
        "diagnostic_keys": ["trust_signals", "value_proposition", "cta_clarity", "audience_fit"],
    },
    "traffic": {
        "user_prompt_template": _TRAFFIC_USER_PROMPT,
        "system_prompt": _TRAFFIC_SYSTEM_PROMPT,
        "metric_focus": "ctr",
        "roas_band_eligible": False,
        "diagnostic_keys": ["thumb_stop", "curiosity_hook", "visual_appeal", "landing_relevance"],
    },
    "awareness": {
        "user_prompt_template": _AWARENESS_USER_PROMPT,
        "system_prompt": _AWARENESS_SYSTEM_PROMPT,
        "metric_focus": "cpm_reach",
        "roas_band_eligible": False,
        "diagnostic_keys": ["brand_recall", "message_clarity", "visual_distinctiveness", "emotional_resonance"],
    },
    "video": {
        "user_prompt_template": _VIDEO_USER_PROMPT,
        "system_prompt": _VIDEO_SYSTEM_PROMPT,
        "metric_focus": "vtr",
        "roas_band_eligible": False,
        "diagnostic_keys": ["hook_strength", "pacing", "message_delivery", "brand_integration"],
    },
    "engagement": {
        "user_prompt_template": _ENGAGEMENT_USER_PROMPT,
        "system_prompt": _ENGAGEMENT_SYSTEM_PROMPT,
        "metric_focus": "engagement_rate",
        "roas_band_eligible": False,
        "diagnostic_keys": ["shareability", "emotional_hook", "interaction_trigger", "visual_impact"],
    },
}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "meta_andromeda_scoring_profiles" not in inspector.get_table_names():
        # 表本身都不存在（正常全新環境走完整條 migration chain 的情況），
        # 20260624 那支 migration 會負責建表+種資料，這裡不用做事
        return

    existing_names = {
        row[0]
        for row in bind.execute(
            sa.text(
                "SELECT profile_name FROM meta_andromeda_scoring_profiles "
                "WHERE profile_name IN ('creative_scoring_v1', 'creative_scoring_v2')"
            )
        ).fetchall()
    }

    has_any_promoted = bind.execute(
        sa.text("SELECT COUNT(*) FROM meta_andromeda_scoring_profiles WHERE is_promoted = true")
    ).scalar() or 0

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
        sa.column("objective_profiles", sa.JSON),
        sa.column("is_promoted", sa.Boolean),
    )

    rows_to_insert = []
    if "creative_scoring_v1" not in existing_names:
        rows_to_insert.append({
            "id": f"sp_hotfix_{uuid.uuid4().hex[:12]}",
            "profile_name": "creative_scoring_v1",
            "user_prompt_template": _SEED_USER_PROMPT_TEMPLATE,
            "system_prompt": _SEED_SYSTEM_PROMPT,
            "calibration_guidance": None,
            "few_shot_examples": [],
            "bias_summary": None,
            "source": "seed",
            "base_profile_name": None,
            "calibration_dataset_id": None,
            "objective_profiles": _OBJECTIVE_PROFILES_SEED,
            "is_promoted": False,
        })
    if "creative_scoring_v2" not in existing_names:
        rows_to_insert.append({
            "id": f"sp_hotfix_{uuid.uuid4().hex[:12]}",
            "profile_name": "creative_scoring_v2",
            "user_prompt_template": _SEED_USER_PROMPT_TEMPLATE,
            "system_prompt": _SEED_SYSTEM_PROMPT,
            "calibration_guidance": None,
            "few_shot_examples": [],
            "bias_summary": None,
            "source": "seed",
            "base_profile_name": None,
            "calibration_dataset_id": None,
            "objective_profiles": _OBJECTIVE_PROFILES_SEED,
            # 只有在目前完全沒有任何 profile 被 promote 時才把 v2 設成 promoted（維持 get_entry()
            # 預設走 cand_v2026_06_05_a -> creative_scoring_v2 的既有慣例）；如果已經有別的
            # profile 被 promote 過，不要覆蓋既有的正式決定
            "is_promoted": has_any_promoted == 0,
        })

    if rows_to_insert:
        op.bulk_insert(profiles_table, rows_to_insert)


def downgrade() -> None:
    # 這是補資料的 hotfix，不做破壞性 downgrade（避免不小心刪掉在這之後才長出來的真實
    # 校準紀錄關聯資料）。如果真的需要復原，手動判斷 source='seed' 且 id LIKE 'sp_hotfix_%' 再刪。
    pass
