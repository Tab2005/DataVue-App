"""docs/23: enable predicted band for non-ROAS objective groups

The 20260630 migration seeded objective_profiles with roas_band_eligible=False
for traffic/awareness/video/engagement, telling the AI to always set
roas_band=null. docs/23 reverses that: these groups now produce a comparable
predicted band (CTR potential / brand recall / VTR potential / engagement
rate potential) so the review-queue detail page can show prediction-vs-actual
matching for them just like conversion/lead.

Pure data update — no schema change. Idempotent on JSON content: only writes
when the stored roas_band_eligible flag is False, so re-running on a DB that
already has the new value is a no-op (we use json_set/jsonb_set under
SQLite/PostgreSQL respectively rather than blindly overwriting).

Revision ID: 20260707_ma_non_roas_band_enable
Revises: 20260706_contribution_module_tables
Create Date: 2026-07-07 00:00:00.000000
"""

import json

from alembic import op
import sqlalchemy as sa


revision = "20260707_ma_non_roas_band_enable"
down_revision = "20260706_contribution_module_tables"
branch_labels = None
depends_on = None


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

# prompts mirror _DEFAULT_OBJECTIVE_PROFILES in backend/modules/meta_andromeda/runtime.py
# (docs/23: "保留既有『不評估購買意圖/CTA 不扣分』等既有正確規則，只是額外加一條『輸出
# 可比對的 band』"). If runtime.py hardcoded defaults are ever edited, this seed needs to
# follow or the two will drift.
_TRAFFIC_USER_PROMPT = (
    "You are the Meta Andromeda creative scoring runtime, specialized in traffic and click-through optimization.\n"
    "Evaluate the creative's ability to drive clicks, curiosity, and landing page visits.\n\n"
    "EVALUATION CRITERIA FOR TRAFFIC/CLICK CAMPAIGNS:\n"
    "1. Thumb-Stop Power: Does the first visual frame immediately grab attention and pause scrolling?\n"
    "2. Curiosity Hook: Does the ad create enough curiosity, urgency, or intrigue to motivate a click?\n"
    "3. Landing Relevance: Is the ad message clearly aligned with what users will find after clicking?\n"
    "4. Visual Appeal: Is the creative visually engaging and feed-appropriate?\n\n"
    "IMPORTANT: This is a TRAFFIC/CLICK campaign. Do NOT evaluate purchase intent or ROAS.\n"
    "Do NOT penalize for missing purchase CTAs — this is a traffic campaign.\n\n"
    "Use roas_band as CTR POTENTIAL BAND: high = expected strong click-through, mid = moderate, low = weak.\n\n"
    "Return JSON only with keys: overall_score, roas_band, top_positive_drivers, top_negative_drivers, risk_tags, diagnostic_breakdown, summary.\n"
    "Use overall_score as integer 0-100.\n"
    "Use roas_band as one of high/mid/low/null to represent click-through potential (not ROAS).\n"
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
    "Do NOT penalize for weak CTAs or low purchase intent — awareness campaigns are not meant to convert directly.\n"
    "Score based on brand memorability and emotional impact.\n\n"
    "Use roas_band as BRAND RECALL POTENTIAL BAND: high = expected strong brand memorability, mid = moderate, low = weak.\n\n"
    "Return JSON only with keys: overall_score, roas_band, top_positive_drivers, top_negative_drivers, risk_tags, diagnostic_breakdown, summary.\n"
    "Use overall_score as integer 0-100.\n"
    "Use roas_band as one of high/mid/low/null to represent brand recall potential (not ROAS).\n"
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
    "Do NOT penalize for missing text CTAs — video view campaigns are about retention, not click action.\n\n"
    "Use roas_band as VTR POTENTIAL BAND: high = expected strong watch-through, mid = moderate, low = weak.\n\n"
    "Return JSON only with keys: overall_score, roas_band, top_positive_drivers, top_negative_drivers, risk_tags, diagnostic_breakdown, summary.\n"
    "Use overall_score as integer 0-100.\n"
    "Use roas_band as one of high/mid/low/null to represent VTR potential (not ROAS).\n"
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
    "Do NOT penalize for missing purchase CTAs — engagement is about social interaction, not conversion.\n\n"
    "Use roas_band as ENGAGEMENT RATE POTENTIAL BAND: high = expected strong interaction volume, mid = moderate, low = weak.\n\n"
    "Return JSON only with keys: overall_score, roas_band, top_positive_drivers, top_negative_drivers, risk_tags, diagnostic_breakdown, summary.\n"
    "Use overall_score as integer 0-100.\n"
    "Use roas_band as one of high/mid/low/null to represent social engagement rate potential (not ROAS).\n"
    "The diagnostic_breakdown object MUST contain exactly these keys with short Chinese evaluation:\n"
    "  - shareability: Evaluates potential for organic sharing and audience tagging behavior.\n"
    "  - emotional_hook: Evaluates strength of emotional trigger and its intensity and authenticity.\n"
    "  - interaction_trigger: Evaluates the content's ability to inspire comments, questions, and reactions.\n"
    "  - visual_impact: Evaluates feed-stopping power and overall visual quality for organic reach.\n\n"
    "All textual outputs MUST be in Traditional Chinese (繁體中文).\n"
) + _OBJ_PROMPT_SUFFIX

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

_NEW_OBJECTIVE_PROFILE_FRAGMENTS = {
    "traffic": {
        "user_prompt_template": _TRAFFIC_USER_PROMPT,
        "system_prompt": _TRAFFIC_SYSTEM_PROMPT,
        "metric_focus": "ctr",
        "roas_band_eligible": True,
        "diagnostic_keys": ["thumb_stop", "curiosity_hook", "visual_appeal", "landing_relevance"],
    },
    "awareness": {
        "user_prompt_template": _AWARENESS_USER_PROMPT,
        "system_prompt": _AWARENESS_SYSTEM_PROMPT,
        "metric_focus": "cpm_reach",
        "roas_band_eligible": True,
        "diagnostic_keys": ["brand_recall", "message_clarity", "visual_distinctiveness", "emotional_resonance"],
    },
    "video": {
        "user_prompt_template": _VIDEO_USER_PROMPT,
        "system_prompt": _VIDEO_SYSTEM_PROMPT,
        "metric_focus": "vtr",
        "roas_band_eligible": True,
        "diagnostic_keys": ["hook_strength", "pacing", "message_delivery", "brand_integration"],
    },
    "engagement": {
        "user_prompt_template": _ENGAGEMENT_USER_PROMPT,
        "system_prompt": _ENGAGEMENT_SYSTEM_PROMPT,
        "metric_focus": "engagement_rate",
        "roas_band_eligible": True,
        "diagnostic_keys": ["shareability", "emotional_hook", "interaction_trigger", "visual_impact"],
    },
}

# Pre-upgrade shape (what the DB currently holds per group, used for downgrade
# restoration): mirrors the seed values from 20260630 / 20260703_ma_seed_profile_hotfix
_PRE_UPGRADE_FRAGMENTS = {
    "traffic": {
        "user_prompt_template": _TRAFFIC_USER_PROMPT.replace(
            "Use roas_band as CTR POTENTIAL BAND: high = expected strong click-through, mid = moderate, low = weak.",
            "Set roas_band to null. Score based on CTR potential ONLY.",
        ).replace(
            "Do NOT penalize for missing purchase CTAs — this is a traffic campaign.",
            "Set roas_band to null — this campaign type does not use ROAS prediction.",
        ).replace(
            "Use roas_band as one of high/mid/low/null to represent click-through potential (not ROAS).",
            "Set roas_band to null — this campaign type does not use ROAS prediction.",
        ),
        "system_prompt": _TRAFFIC_SYSTEM_PROMPT,
        "metric_focus": "ctr",
        "roas_band_eligible": False,
        "diagnostic_keys": ["thumb_stop", "curiosity_hook", "visual_appeal", "landing_relevance"],
    },
    "awareness": {
        "user_prompt_template": _AWARENESS_USER_PROMPT.replace(
            "Use roas_band as BRAND RECALL POTENTIAL BAND: high = expected strong brand memorability, mid = moderate, low = weak.",
            "Set roas_band to null. Score based on brand memorability and emotional impact ONLY.",
        ).replace(
            "Do NOT penalize for weak CTAs or low purchase intent — awareness campaigns are not meant to convert directly.",
            "Set roas_band to null — brand awareness campaigns do not use ROAS prediction.",
        ).replace(
            "Use roas_band as one of high/mid/low/null to represent brand recall potential (not ROAS).",
            "Set roas_band to null — brand awareness campaigns do not use ROAS prediction.",
        ),
        "system_prompt": _AWARENESS_SYSTEM_PROMPT,
        "metric_focus": "cpm_reach",
        "roas_band_eligible": False,
        "diagnostic_keys": ["brand_recall", "message_clarity", "visual_distinctiveness", "emotional_resonance"],
    },
    "video": {
        "user_prompt_template": _VIDEO_USER_PROMPT.replace(
            "Use roas_band as VTR POTENTIAL BAND: high = expected strong watch-through, mid = moderate, low = weak.",
            "Set roas_band to null — video view campaigns do not use ROAS prediction.",
        ).replace(
            "Do NOT penalize for missing text CTAs — video view campaigns are about retention, not click action.",
            "Set roas_band to null. A missing text CTA does NOT penalize this creative.",
        ).replace(
            "Use roas_band as one of high/mid/low/null to represent VTR potential (not ROAS).",
            "Set roas_band to null — video view campaigns do not use ROAS prediction.",
        ),
        "system_prompt": _VIDEO_SYSTEM_PROMPT,
        "metric_focus": "vtr",
        "roas_band_eligible": False,
        "diagnostic_keys": ["hook_strength", "pacing", "message_delivery", "brand_integration"],
    },
    "engagement": {
        "user_prompt_template": _ENGAGEMENT_USER_PROMPT.replace(
            "Use roas_band as ENGAGEMENT RATE POTENTIAL BAND: high = expected strong interaction volume, mid = moderate, low = weak.",
            "Set roas_band to null. Score based on social engagement rate potential ONLY.",
        ).replace(
            "Do NOT penalize for missing purchase CTAs — engagement is about social interaction, not conversion.",
            "Set roas_band to null — engagement campaigns do not use ROAS prediction.",
        ).replace(
            "Use roas_band as one of high/mid/low/null to represent social engagement rate potential (not ROAS).",
            "Set roas_band to null — engagement campaigns do not use ROAS prediction.",
        ),
        "system_prompt": _ENGAGEMENT_SYSTEM_PROMPT,
        "metric_focus": "engagement_rate",
        "roas_band_eligible": False,
        "diagnostic_keys": ["shareability", "emotional_hook", "interaction_trigger", "visual_impact"],
    },
}


def _apply_objective_profile_update(fragments: dict, *, only_when_old: bool) -> None:
    """Walk every scoring-profile row and replace the per-group entries inside
    the objective_profiles JSON column. only_when_old=True is for upgrade (only
    touch rows that still have roas_band_eligible=False for these groups, so
    re-running on an already-upgraded DB is a no-op). only_when_old=False is for
    downgrade (always write the pre-upgrade shape, in case someone hand-edited
    a row to a different intermediate state)."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "meta_andromeda_scoring_profiles" not in inspector.get_table_names():
        return

    rows = bind.execute(
        sa.text("SELECT id, objective_profiles FROM meta_andromeda_scoring_profiles")
    ).fetchall()

    for row_id, current in rows:
        if not current:
            # Row exists with NULL objective_profiles — should not happen for
            # the seed paths, but be defensive: write a complete JSON from scratch
            new_payload = dict(fragments)
        else:
            try:
                parsed = json.loads(current) if isinstance(current, str) else current
            except (TypeError, ValueError):
                parsed = {}
            if not isinstance(parsed, dict):
                parsed = {}
            new_payload = dict(parsed)
            for group, fragment in fragments.items():
                if only_when_old:
                    old_fragment = parsed.get(group) or {}
                    if isinstance(old_fragment, dict) and old_fragment.get("roas_band_eligible") is True:
                        # already upgraded, skip
                        continue
                new_payload[group] = fragment
        bind.execute(
            sa.text(
                "UPDATE meta_andromeda_scoring_profiles "
                "SET objective_profiles = :val WHERE id = :id"
            ),
            {"val": json.dumps(new_payload), "id": row_id},
        )


def upgrade() -> None:
    _apply_objective_profile_update(_NEW_OBJECTIVE_PROFILE_FRAGMENTS, only_when_old=True)


def downgrade() -> None:
    _apply_objective_profile_update(_PRE_UPGRADE_FRAGMENTS, only_when_old=False)
