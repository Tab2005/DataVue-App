"""
Meta Andromeda Module - Runtime adapter
"""

import asyncio
import json
import logging
import re
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from uuid import uuid4

from core.config import settings
from .cache_invalidation import publish_invalidation, register_invalidation_handler
from .model_registry import MetaAndromedaModelEntry, model_registry
from .objective_routing import is_roas_band_eligible, resolve_objective_group
from .labeling import LABEL_POLICY_VERSION


logger = logging.getLogger(__name__)
VALID_ROAS_BANDS = {"high", "mid", "low"}

# TTL 作為多 worker 快取失效的底線：即使 Redis pub/sub 通知因故沒送達（worker 啟動時機、
# 網路抖動等），5 分鐘後也會自動視為過期重新查 DB，不會無限期卡在舊 prompt
_PROMPT_CACHE_TTL_SECONDS = 300
_prompt_profile_cache: dict[str, tuple[dict, float]] = {}
_profile_cache_lock = threading.Lock()

_FALLBACK_USER_PROMPT_TEMPLATE = (
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

_FALLBACK_SYSTEM_PROMPT = (
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

# 附加於每個 objective_group prompt 之後（統一在 render 時 append，而非逐一改寫每份 prompt
# template），要求 diagnostic_breakdown 每個維度輸出結構化數值分數，供統計校準層使用
_DIAGNOSTIC_SCORE_FORMAT_INSTRUCTION = (
    "\n\nOUTPUT FORMAT REQUIREMENT for diagnostic_breakdown: each key's value MUST be a JSON "
    'object {"score": <integer 0-100>, "reasoning": "<one short sentence in Traditional Chinese>"}, '
    "never a plain string. The score is your own independent numeric sub-rating for that "
    "dimension (may differ from overall_score) and is used for downstream statistical calibration."
)

# OpenRouter/OpenAI-style structured-output schema (docs/20 P2-2). Not every model routed
# through OpenRouter honors response_format, so this is tried first and callers must fall
# back to the existing regex-based _extract_json_payload() path on any failure — never assume
# a model actually obeys the schema.
_SCORE_RESPONSE_JSON_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "meta_andromeda_creative_score",
        "strict": False,
        "schema": {
            "type": "object",
            "properties": {
                "overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "roas_band": {"type": ["string", "null"], "enum": ["high", "mid", "low", None]},
                "top_positive_drivers": {"type": "array", "items": {"type": "string"}},
                "top_negative_drivers": {"type": "array", "items": {"type": "string"}},
                "risk_tags": {"type": "array", "items": {"type": "string"}},
                "diagnostic_breakdown": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "score": {"type": "integer", "minimum": 0, "maximum": 100},
                            "reasoning": {"type": "string"},
                        },
                    },
                },
                "summary": {"type": "string"},
            },
            "required": ["overall_score", "summary"],
        },
    },
}

_DEFAULT_OBJECTIVE_PROFILES: dict[str, dict] = {
    "lead": {
        "user_prompt_template": (
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
        ) + _OBJ_PROMPT_SUFFIX,
        "system_prompt": (
            "You are an elite performance marketing creative auditor specializing in lead generation campaigns.\n"
            "Evaluate creatives for trust, value proposition clarity, and qualified lead conversion potential.\n"
            "Score conservatively. A strong lead creative builds trust and removes friction, not just looks good.\n"
            "All explanations, summaries, and breakdowns MUST be written in Traditional Chinese (繁體中文)."
        ),
        "metric_focus": "cvr_cpl",
        "roas_band_eligible": True,
    },
    "traffic": {
        "user_prompt_template": (
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
        ) + _OBJ_PROMPT_SUFFIX,
        "system_prompt": (
            "You are an elite performance marketing creative auditor specializing in traffic and CTR optimization.\n"
            "Evaluate creatives for thumb-stop power, curiosity triggers, and click motivation.\n"
            "Score conservatively. Do NOT penalize for missing purchase CTAs — this is a traffic campaign.\n"
            "All explanations, summaries, and breakdowns MUST be written in Traditional Chinese (繁體中文)."
        ),
        "metric_focus": "ctr",
        "roas_band_eligible": True,
    },
    "awareness": {
        "user_prompt_template": (
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
        ) + _OBJ_PROMPT_SUFFIX,
        "system_prompt": (
            "You are an elite brand strategist and creative auditor specializing in awareness and reach campaigns.\n"
            "Evaluate creatives for brand memorability, emotional resonance, and visual distinctiveness.\n"
            "Do NOT penalize for weak CTAs or low purchase intent — awareness campaigns are not meant to convert directly.\n"
            "All explanations, summaries, and breakdowns MUST be written in Traditional Chinese (繁體中文)."
        ),
        "metric_focus": "cpm_reach",
        "roas_band_eligible": True,
    },
    "video": {
        "user_prompt_template": (
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
        ) + _OBJ_PROMPT_SUFFIX,
        "system_prompt": (
            "You are an elite video creative auditor specializing in video view and watch-time optimization.\n"
            "Evaluate video hooks, pacing, and viewer retention potential.\n"
            "Assume the asset is a video. Focus on the opening seconds, narrative flow, and brand integration.\n"
            "All explanations, summaries, and breakdowns MUST be written in Traditional Chinese (繁體中文)."
        ),
        "metric_focus": "vtr",
        "roas_band_eligible": True,
    },
    "engagement": {
        "user_prompt_template": (
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
        ) + _OBJ_PROMPT_SUFFIX,
        "system_prompt": (
            "You are an elite social media creative auditor specializing in engagement and community interaction.\n"
            "Evaluate creatives for shareability, emotional triggers, and interaction potential.\n"
            "Do NOT penalize for missing purchase CTAs — this is an engagement campaign.\n"
            "All explanations, summaries, and breakdowns MUST be written in Traditional Chinese (繁體中文)."
        ),
        "metric_focus": "engagement_rate",
        "roas_band_eligible": True,
    },
}


def _load_scoring_profile(profile_name: str, *, ignore_promoted: bool = False) -> dict:
    """Load a scoring profile's prompt content.

    By default the globally promoted profile wins regardless of profile_name
    (matches production scoring behavior). Pass ignore_promoted=True to force
    loading the exact named profile — used by the holdout backtest, which must
    evaluate the CANDIDATE profile in isolation even if a different profile is
    currently promoted.
    """
    cache_key = f"__exact__{profile_name}" if ignore_promoted else profile_name
    with _profile_cache_lock:
        cached = _prompt_profile_cache.get(cache_key)
        if cached is not None:
            value, cached_at = cached
            if time.monotonic() - cached_at < _PROMPT_CACHE_TTL_SECONDS:
                return value
            del _prompt_profile_cache[cache_key]

    try:
        from database import SessionLocal
        from database.models.meta_andromeda import MetaAndromedaScoringProfile
        db = SessionLocal()
        try:
            if ignore_promoted:
                row = db.query(MetaAndromedaScoringProfile).filter(
                    MetaAndromedaScoringProfile.profile_name == profile_name
                ).first()
            else:
                # Prefer the globally promoted profile; fall back to named profile
                row = (
                    db.query(MetaAndromedaScoringProfile)
                    .filter(MetaAndromedaScoringProfile.is_promoted == True)  # noqa: E712
                    .first()
                ) or db.query(MetaAndromedaScoringProfile).filter(
                    MetaAndromedaScoringProfile.profile_name == profile_name
                ).first()
            if row is not None:
                few_shot_raw = row.few_shot_examples
                if isinstance(few_shot_raw, str):
                    try:
                        few_shot_raw = json.loads(few_shot_raw)
                    except Exception:
                        few_shot_raw = []
                if not isinstance(few_shot_raw, list):
                    few_shot_raw = []
                profile = {
                    "user_prompt_template": row.user_prompt_template,
                    "system_prompt": row.system_prompt,
                    "calibration_guidance": row.calibration_guidance or "",
                    "few_shot_examples": few_shot_raw,
                    "objective_profiles": row.objective_profiles or {},
                    # 實際被載入的 profile 名稱：可能因 is_promoted 全域覆蓋而與呼叫方傳入的
                    # profile_name（registry 設定值）不同，lineage 必須記這個，校準前後 ρ 才可歸因
                    "resolved_profile_name": row.profile_name,
                }
                with _profile_cache_lock:
                    _prompt_profile_cache[cache_key] = (profile, time.monotonic())
                logger.info("[MetaAndromeda] Loaded scoring profile '%s' from DB.", profile_name)
                return profile
        finally:
            db.close()
    except Exception as exc:
        logger.warning("[MetaAndromeda] Could not load profile '%s' from DB: %s. Using fallback.", profile_name, exc)

    fallback = {
        "user_prompt_template": _FALLBACK_USER_PROMPT_TEMPLATE,
        "system_prompt": _FALLBACK_SYSTEM_PROMPT,
        "calibration_guidance": "",
        "few_shot_examples": [],
        "objective_profiles": {},
        "resolved_profile_name": None,
    }
    with _profile_cache_lock:
        _prompt_profile_cache[cache_key] = (fallback, time.monotonic())
    return fallback


def _resolve_active_profile(base_profile: dict, objective_group: str) -> dict:
    """Merge base profile with objective-group-specific overrides.

    Priority: DB objective_profiles → hardcoded _DEFAULT_OBJECTIVE_PROFILES → base (conversion) profile.
    """
    db_obj_profiles = base_profile.get("objective_profiles") or {}
    db_override = db_obj_profiles.get(objective_group) or {}
    hardcoded = _DEFAULT_OBJECTIVE_PROFILES.get(objective_group) or {}

    # For each field, prefer DB override → hardcoded default → base profile
    user_prompt = (
        db_override.get("user_prompt_template")
        or hardcoded.get("user_prompt_template")
        or base_profile["user_prompt_template"]
    )
    system_prompt = (
        db_override.get("system_prompt")
        or hardcoded.get("system_prompt")
        or base_profile["system_prompt"]
    )
    calibration_guidance = (
        db_override.get("calibration_guidance")
        or hardcoded.get("calibration_guidance")
        or base_profile.get("calibration_guidance")
        or ""
    )
    few_shot_examples = (
        db_override.get("few_shot_examples")
        or hardcoded.get("few_shot_examples")
        or base_profile.get("few_shot_examples")
        or []
    )
    # For roas_band_eligible: DB takes precedence; then hardcoded default; then True (conversion default)
    if "roas_band_eligible" in db_override:
        roas_band_eligible = bool(db_override["roas_band_eligible"])
    elif "roas_band_eligible" in hardcoded:
        roas_band_eligible = bool(hardcoded["roas_band_eligible"])
    else:
        roas_band_eligible = True

    metric_focus = db_override.get("metric_focus") or hardcoded.get("metric_focus") or "roas"

    return {
        "user_prompt_template": user_prompt,
        "system_prompt": system_prompt,
        "calibration_guidance": calibration_guidance,
        "few_shot_examples": few_shot_examples,
        "metric_focus": metric_focus,
        "roas_band_eligible": roas_band_eligible,
        "resolved_profile_name": base_profile.get("resolved_profile_name"),
    }


def _invalidate_prompt_cache_local(profile_name: str | None = None) -> None:
    with _profile_cache_lock:
        if profile_name is None:
            _prompt_profile_cache.clear()
            logger.info("[MetaAndromeda] Prompt profile cache fully cleared.")
        else:
            _prompt_profile_cache.pop(profile_name, None)
            _prompt_profile_cache.pop(f"__exact__{profile_name}", None)
            logger.info("[MetaAndromeda] Prompt profile cache cleared for '%s'.", profile_name)


def invalidate_prompt_cache(profile_name: str | None = None) -> None:
    """Clear this process's prompt cache and notify other workers via Redis
    pub/sub (docs/20 P2-7) — a promote/approve handled by one worker must not
    leave sibling workers serving the old prompt until their TTL happens to expire."""
    publish_invalidation("prompt_profile", profile_name)


register_invalidation_handler("prompt_profile", _invalidate_prompt_cache_local)


def resolve_openrouter_api_key_for_asset(db_session, asset_id: str | None) -> str | None:
    """Look up the OpenRouter API key belonging to whoever uploaded this asset — the
    same per-user, DB-stored key resolution MetaAndromedaRuntime.generate_score_result
    uses for live scoring — falling back to the raw OPENROUTER_API_KEY env var.

    Any code path that talks to OpenRouter directly (calibration_pipeline.py's LLM
    guidance generator and holdout backtest scorer both did this) MUST go through here
    instead of reading settings.OPENROUTER_API_KEY alone: in deployments where the
    working key lives per-user in the DB rather than as a container env var, that
    shortcut makes every such call fail with "OpenRouter client is not configured"
    (2026-07-03 incident: broke the holdout backtest — 0/22 items scored — and silently
    degraded LLM calibration-guidance generation to its hardcoded template fallback).
    """
    if asset_id:
        try:
            from database.models.meta_andromeda import MetaAndromedaAsset
            from database.models.user import User
            from modules.auth.service import TokenManager

            asset = db_session.query(MetaAndromedaAsset).filter(MetaAndromedaAsset.id == asset_id).first()
            if asset and asset.uploaded_by:
                user = db_session.query(User).filter(User.id == asset.uploaded_by).first()
                if user and user.google_id:
                    db_key = TokenManager.get_ai_api_key(user.google_id, provider="openrouter")
                    if db_key:
                        return db_key
        except Exception as exc:
            logger.warning(
                "[MetaAndromeda] Failed to resolve per-user OpenRouter key for asset %s: %s",
                asset_id, exc,
            )
    return settings.OPENROUTER_API_KEY


def _clip(value: str | None, limit: int = 140) -> str:
    if not value:
        return ""
    return value.strip()[:limit]


def _strip_reasoning_blocks(text: str) -> str:
    """Strip <think>...</think> and <thinking>...</thinking> blocks from reasoning model output."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()


def _extract_json_payload(raw_text: str) -> dict:
    if not raw_text or not raw_text.strip():
        logger.error("[MetaAndromeda] Raw text from AI provider is empty.")
        raise ValueError("API returned an empty response.")

    candidate = _strip_reasoning_blocks(raw_text).strip()
    if not candidate:
        logger.error("[MetaAndromeda] Response was empty after stripping reasoning blocks. Raw: %r", raw_text[:200])
        raise ValueError("API returned only reasoning blocks with no JSON payload.")

    if "```" in candidate:
        block_match = re.search(r"```(?:json)?\s*(.*?)\s*```", candidate, re.DOTALL)
        if block_match:
            candidate = block_match.group(1).strip()
        else:
            candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
            candidate = re.sub(r"\s*```$", "", candidate).strip()

    try:
        result = json.loads(candidate)
        # Reasoning models sometimes double-encode JSON (return a JSON string containing another JSON)
        if isinstance(result, str):
            logger.warning("[MetaAndromeda] Parsed JSON is a string, attempting double-decode. Value: %r", result[:200])
            result = json.loads(result)
        if not isinstance(result, dict):
            raise ValueError(f"AI response parsed to {type(result).__name__}, expected dict.")
        return result
    except json.JSONDecodeError as e:
        logger.warning("[MetaAndromeda] Failed to parse JSON directly: %s. Attempting regex extract. Candidate: %r", e, candidate)
        match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if not match:
            logger.error("[MetaAndromeda] Regex extraction failed. No braces found in text: %r", raw_text)
            raise ValueError(f"AI response is not valid JSON. Raw: {raw_text[:200]}") from e
        try:
            result = json.loads(match.group(0))
            if not isinstance(result, dict):
                raise ValueError(f"Regex-extracted JSON is {type(result).__name__}, expected dict.")
            return result
        except json.JSONDecodeError as inner_e:
            # Last resort: try to repair truncated JSON by closing unclosed braces/brackets
            truncated = match.group(0)
            open_braces = truncated.count('{') - truncated.count('}')
            open_brackets = truncated.count('[') - truncated.count(']')
            repaired = truncated.rstrip().rstrip(',').rstrip('"').rstrip("'")
            if open_brackets > 0:
                repaired += ']' * open_brackets
            if open_braces > 0:
                repaired += '}' * open_braces
            try:
                result = json.loads(repaired)
                if isinstance(result, dict):
                    logger.warning("[MetaAndromeda] Repaired truncated JSON (open_braces=%d, open_brackets=%d).", open_braces, open_brackets)
                    return result
            except json.JSONDecodeError:
                pass
            logger.error("[MetaAndromeda] Failed to parse extracted braces text: %r. Error: %s", match.group(0), inner_e)
            raise ValueError(f"AI response JSON structure is broken. Extracted: {match.group(0)[:200]}") from inner_e


def _normalize_string_list(value, field_name: str, *, limit: int | None = None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [item.strip() for item in re.split(r"[,;\n]+", value) if item.strip()]
    if not isinstance(value, (list, tuple)):
        logger.warning("[MetaAndromeda] %s is %s, expected list — coercing to empty list.", field_name, type(value).__name__)
        return []
    normalized = [str(item).strip() for item in value if str(item).strip()]
    return normalized[:limit] if limit is not None else normalized


def _normalize_diagnostic_breakdown(value) -> tuple[dict[str, str], dict[str, int]]:
    """Returns (display_dict, numeric_scores_dict).

    display_dict keeps the existing "score: reasoning" string shape so the
    public API contract (diagnostic_breakdown: dict[str, str]) and frontend
    review-queue display are unchanged. numeric_scores_dict extracts the raw
    0-100 sub-score per dimension (when the model returned one) for the
    statistical confidence-calibration layer — this is the "數值化
    diagnostic_breakdown" from docs/20 task 3.1, done without breaking the
    existing string-shaped API.
    """
    if value is None:
        return {}, {}
    if not isinstance(value, dict):
        logger.warning("[MetaAndromeda] diagnostic_breakdown is %s, expected dict — returning empty.", type(value).__name__)
        return {}, {}
    display: dict[str, str] = {}
    numeric: dict[str, int] = {}
    for key, item in value.items():
        if isinstance(item, dict):
            score = item.get("score", "")
            reasoning = item.get("reasoning", "")
            display[str(key)] = f"{score}: {reasoning}".strip(": ") if (score or reasoning) else ""
            try:
                score_int = int(score)
                if 0 <= score_int <= 100:
                    numeric[str(key)] = score_int
            except (TypeError, ValueError):
                pass
        else:
            display[str(key)] = str(item)
    return display, numeric


def _build_multimodal_user_content(prompt: str, score_payload: dict) -> list[dict]:
    user_content = [{"type": "text", "text": prompt}]
    request_context = score_payload.get("request_context", {})
    image_url = (
        request_context.get("asset_public_url")
        or request_context.get("preview_url")
        or request_context.get("asset_source_url")
        or score_payload.get("preview_url")
        or score_payload.get("asset_uri")
    )
    if score_payload.get("asset_type") == "image" and isinstance(image_url, str):
        normalized_url = image_url.strip()
        if normalized_url.startswith(("http://", "https://", "data:image/")):
            user_content.append({"type": "image_url", "image_url": {"url": normalized_url}})
    elif score_payload.get("asset_type") == "video":
        keyframe_urls = request_context.get("video_keyframe_urls")
        if isinstance(keyframe_urls, list):
            for url in keyframe_urls:
                if isinstance(url, str) and url.startswith(("http://", "https://", "data:image/")):
                    user_content.append({"type": "image_url", "image_url": {"url": url}})
    return user_content


def _compute_signal_completeness(score_payload: dict) -> tuple[float, dict]:
    request_context = score_payload.get("request_context", {})
    components = {
        "headline": 1.0 if _clip(request_context.get("headline")) else 0.0,
        "primary_text": 1.0 if _clip(request_context.get("primary_text")) else 0.0,
        "cta": 1.0 if _clip(request_context.get("cta")) else 0.0,
        "image_signal": 1.0 if any(part.get("type") == "image_url" for part in _build_multimodal_user_content("", score_payload)[1:]) else 0.0,
        "objective": 1.0 if _clip(request_context.get("objective") or score_payload.get("objective")) else 0.0,
        "placement_family": 1.0 if _clip(request_context.get("placement_family") or score_payload.get("placement_family")) else 0.0,
        "market": 1.0 if _clip(request_context.get("market") or score_payload.get("market")) else 0.0,
    }
    completeness = sum(components.values()) / len(components)
    return completeness, components


def _compute_confidence(
    score_payload: dict,
    *,
    scoring_mode: str,
    used_multimodal: bool,
    fallback_reason: str | None = None,
    overall_score: int | None = None,
    video_not_inspected: bool = False,
) -> tuple[float | None, dict]:
    if score_payload.get("request_mode") == "diagnostic_only":
        return None, {"reason": "diagnostic_only_request"}

    completeness, components = _compute_signal_completeness(score_payload)
    base = 0.42 if scoring_mode == "heuristic" else 0.58
    formula_confidence = base + completeness * (0.26 if scoring_mode == "heuristic" else 0.24)
    if used_multimodal:
        formula_confidence += 0.06
    if fallback_reason:
        formula_confidence -= 0.12
    if video_not_inspected:
        # 沒看過影片內容等於盲評，遠比「訊號不完整」嚴重——原本 image_signal 分量只讓
        # completeness 少掉 ~0.03-0.06，不足以反映這件事，這裡直接大幅扣減
        formula_confidence -= 0.2
    formula_confidence = max(0.18, min(round(formula_confidence, 4), 0.92))

    # 用歷史 CalibrationItem（prediction_band vs observed_band）擬合出的經驗機率取代手寫公式，
    # 讓 confidence 真的代表「這個 band 判斷過去有多常猜對」而非只是訊號完整度的代理指標。
    # 資料不足或尚未擬合時優雅退回原本的公式，避免冷啟動期間報錯或無意義輸出。影片盲評的情況
    # 不查經驗校準表——那張表主要是用「有看過內容」的樣本擬合的，用在盲評案例上會虛報信心。
    calibration_method = "hand_written_formula"
    calibrated_confidence = None
    if scoring_mode == "ai" and overall_score is not None and not fallback_reason and not video_not_inspected:
        try:
            from .calibration_stats import predict_confidence
            calibrated_confidence = predict_confidence(overall_score)
            if calibrated_confidence is not None:
                calibration_method = "empirical_isotonic"
        except Exception as exc:
            logger.debug("[MetaAndromeda] Confidence calibration lookup failed: %s", exc)

    final_confidence = calibrated_confidence if calibrated_confidence is not None else formula_confidence
    return final_confidence, {
        "signal_completeness": round(completeness, 4),
        "components": components,
        "used_multimodal": used_multimodal,
        "fallback": bool(fallback_reason),
        "video_not_inspected": video_not_inspected,
        "calibration_method": calibration_method,
        "formula_confidence": formula_confidence,
    }


def _validate_provider_result(
    parsed: dict,
    score_payload: dict,
    registry_entry: MetaAndromedaModelEntry,
    *,
    roas_band_eligible: bool = True,
    objective_group: str = "conversion",
    prompt_profile_used: str | None = None,
) -> dict:
    is_diagnostic_only_request = score_payload.get("request_mode") == "diagnostic_only"
    roas_applicable = roas_band_eligible and not is_diagnostic_only_request
    prediction_mode = "diagnostic_plus_roas" if roas_applicable else "diagnostic_only"

    raw_score = parsed.get("overall_score")
    if raw_score is None:
        raise ValueError("provider_missing_overall_score")
    try:
        overall_score = int(raw_score)
    except (TypeError, ValueError) as exc:
        raise ValueError("provider_invalid_overall_score") from exc
    if overall_score < 0 or overall_score > 100:
        raise ValueError("provider_invalid_overall_score")

    used_multimodal = len(_build_multimodal_user_content("", score_payload)) > 1
    # 影片素材沒能附上 keyframes（ffmpeg 不存在/抽取失敗）等於盲評：模型只能靠文案判斷，
    # 這比「訊號不完整」嚴重得多，必須額外扣減 confidence 並在 risk_tags 明確標出
    video_not_inspected = score_payload.get("asset_type") == "video" and not used_multimodal
    confidence, confidence_detail = _compute_confidence(
        score_payload,
        scoring_mode="ai",
        used_multimodal=used_multimodal,
        overall_score=overall_score,
        video_not_inspected=video_not_inspected,
    )

    roas_band = parsed.get("roas_band")
    if not roas_applicable:
        roas_band = None
    elif roas_band is not None:
        roas_band = str(roas_band).lower().strip()
        if roas_band not in VALID_ROAS_BANDS:
            raise ValueError("provider_invalid_roas_band")

    top_positive_drivers = _normalize_string_list(parsed.get("top_positive_drivers"), "top_positive_drivers", limit=3)
    top_negative_drivers = _normalize_string_list(parsed.get("top_negative_drivers"), "top_negative_drivers", limit=3)
    risk_tags = _normalize_string_list(parsed.get("risk_tags"), "risk_tags")
    if video_not_inspected and "video_content_not_inspected" not in risk_tags:
        risk_tags.append("video_content_not_inspected")
    diagnostic_breakdown, diagnostic_scores = _normalize_diagnostic_breakdown(parsed.get("diagnostic_breakdown"))
    summary = str(parsed.get("summary") or "Scored by OpenRouter-backed Meta Andromeda runtime.").strip()

    if is_diagnostic_only_request:
        roas_unavailable_reason = "diagnostic only request"
    elif not roas_band_eligible:
        roas_unavailable_reason = f"not applicable for {objective_group} campaigns"
    else:
        roas_unavailable_reason = None

    return {
        "status": "completed",
        "prediction_mode": prediction_mode,
        "overall_score": overall_score,
        "roas_band": roas_band,
        "model_version": registry_entry.model_version,
        "feature_manifest_id": registry_entry.feature_manifest_id,
        "error_message": None,
        "diagnostic_breakdown": diagnostic_breakdown,
        "roas_prediction": {
            "eligible": roas_applicable,
            "band": roas_band,
            "confidence": confidence,
            "reason_if_unavailable": roas_unavailable_reason,
        },
        "risk_tags": risk_tags,
        "top_positive_drivers": top_positive_drivers,
        "top_negative_drivers": top_negative_drivers,
        "explanations": {
            "summary": summary,
            "top_positive_drivers": top_positive_drivers,
            "top_risks": top_negative_drivers,
            "diagnostic_evidence": {
                "provider": registry_entry.provider,
                "provider_model": registry_entry.provider_model,
                "objective": score_payload.get("objective", "purchase"),
                "objective_group": objective_group,
                "placement_family": score_payload.get("placement_family", "all"),
                "confidence_detail": confidence_detail,
            },
        },
        "lineage": {
            "source_ingest_batch_id": f"runtime_batch_{uuid4().hex[:6]}",
            "feature_manifest_id": registry_entry.feature_manifest_id,
            "registry_model_version": registry_entry.model_version,
            "registry_provider": registry_entry.provider,
            "provider_model": registry_entry.provider_model,
            "registry_profile": registry_entry.scoring_profile,
            "registry_source": registry_entry.source_of_truth,
            "prompt_profile_used": prompt_profile_used or "hardcoded_fallback",
            "scoring_mode": "ai",
            "objective_group": objective_group,
            "label_policy_version": LABEL_POLICY_VERSION,
            "diagnostic_scores": diagnostic_scores,
        },
    }


def _resolve_self_consistency_sample_count(score_payload: dict) -> int:
    """Self-consistency (N-sample, take the median) is only worth the extra API
    cost/latency for "high value" scoring: observation-triggered re-scoring
    (事後補評) and holdout backtests — not interactive Score Lab uploads, which
    stay single-sample to keep cost/latency predictable for a human waiting
    on the result (docs/20 P2-2)."""
    if not settings.META_ANDROMEDA_SELF_CONSISTENCY_ENABLED:
        return 1
    request_context = score_payload.get("request_context", {})
    if not isinstance(request_context, dict):
        return 1
    origin = request_context.get("origin")
    is_backtest = bool(request_context.get("is_backtest"))
    if origin == "analytics" or is_backtest:
        return settings.META_ANDROMEDA_SELF_CONSISTENCY_SAMPLES
    return 1


def _median_int(values: list[int]) -> int:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return ordered[mid]
    return round((ordered[mid - 1] + ordered[mid]) / 2)


def _majority_vote_band(bands: list[str | None]) -> str | None:
    votes = [b for b in bands if b in VALID_ROAS_BANDS]
    if not votes:
        return None
    counts = Counter(votes)
    top_count = max(counts.values())
    tied = sorted(b for b, c in counts.items() if c == top_count)
    if len(tied) == 1:
        return tied[0]
    # 平票時取中間值（mid 若在候選內優先，否則取 band_order 排序後的中位者），避免用字母順序
    # 這種跟語意無關的方式決定 high 還是 low
    band_order = {"low": 1, "mid": 2, "high": 3}
    tied_sorted = sorted(tied, key=lambda b: band_order[b])
    return tied_sorted[len(tied_sorted) // 2]


def _aggregate_self_consistency_samples(samples: list[dict]) -> dict:
    """Merge N independently-parsed provider responses into one: median
    overall_score, majority-vote roas_band, and textual fields (diagnostic
    breakdown/drivers/summary) taken from whichever sample's overall_score is
    closest to the median — averaging text doesn't make sense, but picking the
    most "representative" sample's prose does."""
    if len(samples) == 1:
        return samples[0]

    scores = [int(s.get("overall_score", 0)) for s in samples]
    median_score = _median_int(scores)
    bands = [s.get("roas_band") for s in samples]
    majority_band = _majority_vote_band(bands)

    representative = min(samples, key=lambda s: abs(int(s.get("overall_score", 0)) - median_score))
    merged = dict(representative)
    merged["overall_score"] = median_score
    merged["roas_band"] = majority_band
    merged["_self_consistency"] = {
        "sample_count": len(samples),
        "scores": scores,
        "bands": bands,
    }
    return merged


class BaseScoringProvider:
    async def score(self, score_payload: dict, registry_entry: MetaAndromedaModelEntry) -> dict:
        raise NotImplementedError


class HeuristicScoringProvider(BaseScoringProvider):
    async def score(self, score_payload: dict, registry_entry: MetaAndromedaModelEntry) -> dict:
        forced_delay_ms = int(score_payload.get("request_context", {}).get("forced_delay_ms") or 0)
        if forced_delay_ms > 0:
            await asyncio.sleep(forced_delay_ms / 1000)
        if score_payload.get("request_context", {}).get("force_failure"):
            raise RuntimeError("forced_runtime_failure")
        return build_heuristic_score_result(score_payload, registry_entry)


class OpenRouterScoringProvider(BaseScoringProvider):
    def __init__(self, api_key: str | None = None, force_profile_name: str | None = None):
        self.api_key = api_key
        # 回測用：強制使用指定 profile_name，忽略 is_promoted 全域覆蓋，
        # 才能在別的 profile 已上線時仍獨立評估候選 profile
        self.force_profile_name = force_profile_name

    def _build_prompt(self, score_payload: dict, registry_entry: MetaAndromedaModelEntry) -> dict:
        request_context = score_payload.get("request_context", {})
        if not isinstance(request_context, dict):
            request_context = {}
        request_mode = score_payload.get("request_mode", "auto")

        if self.force_profile_name:
            base_profile = _load_scoring_profile(self.force_profile_name, ignore_promoted=True)
        else:
            base_profile = _load_scoring_profile(registry_entry.scoring_profile)
        objective_group = resolve_objective_group(score_payload.get("objective"))
        active_profile = _resolve_active_profile(base_profile, objective_group)
        _fmt = {
            "asset_type": score_payload.get("asset_type", "image"),
            "objective": score_payload.get("objective", "purchase"),
            "placement_family": score_payload.get("placement_family", "all"),
            "market": score_payload.get("market", "TW"),
            "request_mode": request_mode,
            "headline": _clip(request_context.get("headline")),
            "primary_text": _clip(request_context.get("primary_text")),
            "cta": _clip(request_context.get("cta")),
        }
        prompt = active_profile["user_prompt_template"].format_map(_fmt)
        prompt += _DIAGNOSTIC_SCORE_FORMAT_INSTRUCTION
        if active_profile.get("calibration_guidance"):
            prompt += f"\n\n{active_profile['calibration_guidance']}"
        few_shot_examples = active_profile.get("few_shot_examples")
        few_shot_image_blocks: list[dict] = []
        if few_shot_examples and isinstance(few_shot_examples, list):
            from .calibration_pipeline import format_few_shot_content
            few_shot_text, few_shot_image_blocks = format_few_shot_content(few_shot_examples)
            prompt += few_shot_text
        system_prompt = active_profile["system_prompt"]
        user_content = _build_multimodal_user_content(prompt, score_payload)
        # few-shot 圖片附加在主素材圖片之後，讓模型能實際「看到」校準範例，而非只靠文字描述
        user_content.extend(few_shot_image_blocks)
        return {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "user_content": user_content,
            "active_profile": active_profile,
            "objective_group": objective_group,
        }

    @staticmethod
    async def _call_provider_once(
        client,
        prompt: str,
        system_prompt: str,
        user_content,
        registry_entry: MetaAndromedaModelEntry,
        *,
        use_structured_output: bool,
    ) -> dict:
        """One full attempt (with its own rate-limit retry loop), returning the
        parsed JSON payload. use_structured_output tries response_format=
        json_schema first (P2-2) as a fast pre-attempt — any failure there
        (model doesn't support it, malformed response, ...) falls through to
        the existing, already-battle-tested regex-parsed retry loop unchanged.
        """
        import openai

        if use_structured_output:
            try:
                raw = await asyncio.to_thread(
                    client.generate_content,
                    prompt,
                    registry_entry.provider_model,
                    system_prompt,
                    0.2,
                    8192,
                    settings.META_ANDROMEDA_SCORE_TIMEOUT_SECONDS,
                    user_content,
                    _SCORE_RESPONSE_JSON_SCHEMA,
                )
                if raw and raw.strip():
                    return _extract_json_payload(raw)
            except Exception as exc:
                logger.info(
                    "[MetaAndromeda] Structured output attempt failed (%s), falling back to regex-parsed prompt.",
                    exc,
                )

        raw = None
        max_retries = 3
        backoff = 2.0
        for attempt in range(max_retries):
            try:
                raw = await asyncio.to_thread(
                    client.generate_content,
                    prompt,
                    registry_entry.provider_model,
                    system_prompt,
                    0.2,
                    8192,
                    settings.META_ANDROMEDA_SCORE_TIMEOUT_SECONDS,
                    user_content,
                )
                if not raw or not raw.strip():
                    if attempt < max_retries - 1:
                        sleep_time = backoff * (2 ** attempt)
                        logger.warning(
                            "[MetaAndromeda] OpenRouter returned empty response. Retrying in %.1fs... (Attempt %d/%d)",
                            sleep_time, attempt + 1, max_retries,
                        )
                        await asyncio.sleep(sleep_time)
                        continue
                break
            except Exception as e:
                is_rate_limit = False
                if isinstance(e, openai.RateLimitError):
                    is_rate_limit = True
                elif hasattr(e, "status_code") and e.status_code == 429:
                    is_rate_limit = True
                elif "429" in str(e) or "resource_exhausted" in str(e).lower() or "exhausted" in str(e).lower() or "rate_limit" in str(e).lower():
                    is_rate_limit = True

                if is_rate_limit and attempt < max_retries - 1:
                    sleep_time = backoff * (2 ** attempt)
                    logger.warning(
                        "[MetaAndromeda] OpenRouter 429 Rate Limit hit. Retrying in %.1fs... (Attempt %d/%d)",
                        sleep_time,
                        attempt + 1,
                        max_retries
                    )
                    await asyncio.sleep(sleep_time)
                else:
                    raise
        return _extract_json_payload(raw)

    async def score(self, score_payload: dict, registry_entry: MetaAndromedaModelEntry) -> dict:
        from services.ai.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key=self.api_key)
        if client.client is None:
            raise RuntimeError("OpenRouter client is not configured")

        built = self._build_prompt(score_payload, registry_entry)
        prompt = built["prompt"]
        system_prompt = built["system_prompt"]
        user_content = built["user_content"]
        active_profile = built["active_profile"]
        objective_group = built["objective_group"]

        sample_count = _resolve_self_consistency_sample_count(score_payload)
        use_structured_output = settings.META_ANDROMEDA_STRUCTURED_OUTPUT_ENABLED

        if sample_count <= 1:
            parsed = await self._call_provider_once(
                client, prompt, system_prompt, user_content, registry_entry,
                use_structured_output=use_structured_output,
            )
        else:
            # 依序取樣（非併發）：避免對本來就嚴格限流的 provider 一次炸出 N 倍請求，
            # 用延遲換取穩定性——這類請求本來就是背景非互動流程，不急著在幾秒內回應
            samples = []
            for i in range(sample_count):
                try:
                    sample = await self._call_provider_once(
                        client, prompt, system_prompt, user_content, registry_entry,
                        use_structured_output=use_structured_output,
                    )
                    samples.append(sample)
                except Exception as exc:
                    logger.warning(
                        "[MetaAndromeda] Self-consistency sample %d/%d failed: %s",
                        i + 1, sample_count, exc,
                    )
            if not samples:
                raise RuntimeError("self_consistency_all_samples_failed")
            parsed = _aggregate_self_consistency_samples(samples)

        return _validate_provider_result(
            parsed,
            score_payload,
            registry_entry,
            roas_band_eligible=active_profile.get("roas_band_eligible", True),
            objective_group=objective_group,
            prompt_profile_used=active_profile.get("resolved_profile_name"),
        )


def build_heuristic_score_result(score_payload: dict, registry_entry: MetaAndromedaModelEntry, fallback_reason: str | None = None) -> dict:
    asset_type = score_payload["asset_type"]
    objective = score_payload.get("objective", "purchase")
    request_mode = score_payload.get("request_mode", "auto")
    placement_family = score_payload.get("placement_family", "all")
    request_context = score_payload.get("request_context", {})
    objective_group = resolve_objective_group(objective)
    roas_band_eligible = is_roas_band_eligible(objective_group)
    is_diagnostic_only_request = request_mode == "diagnostic_only"
    roas_applicable = roas_band_eligible and not is_diagnostic_only_request
    prediction_mode = "diagnostic_plus_roas" if roas_applicable else "diagnostic_only"

    score = 56 if asset_type == "image" else 52
    if objective_group == "conversion":
        score += 3
    elif objective_group == "lead":
        score += 2
    if _clip(request_context.get("headline")):
        score += 8
    else:
        score -= 5
    if _clip(request_context.get("primary_text")):
        score += 8
    else:
        score -= 6
    if _clip(request_context.get("cta")):
        score += 10
    elif objective_group in {"awareness", "video"}:
        pass  # CTA not required for these groups
    else:
        score -= 5
    if placement_family in {"feed", "stories"}:
        score += 4
    if not _clip(request_context.get("headline")) and not _clip(request_context.get("primary_text")) and not _clip(request_context.get("cta")):
        score -= 8
    score = max(24, min(score, 88))

    used_multimodal = len(_build_multimodal_user_content("", score_payload)) > 1
    confidence, confidence_detail = _compute_confidence(
        score_payload,
        scoring_mode="heuristic",
        used_multimodal=used_multimodal,
        fallback_reason=fallback_reason,
    )

    if roas_applicable:
        if score >= 80:
            roas_band = "high"
        elif score >= 66:
            roas_band = "mid"
        else:
            roas_band = "low"
    else:
        roas_band = None

    top_positive_drivers = []
    if _clip(request_context.get("cta")) and objective_group not in {"awareness", "video"}:
        top_positive_drivers.append("明確的行動呼籲 (CTA)")
    if _clip(request_context.get("headline")):
        top_positive_drivers.append("包含廣告標題")
    if placement_family in {"feed", "stories"}:
        top_positive_drivers.append("版位適配良好")
    if not top_positive_drivers:
        top_positive_drivers.append("基礎素材完整度良好")

    top_negative_drivers = []
    if not _clip(request_context.get("headline")):
        top_negative_drivers.append("缺少廣告標題")
    if not _clip(request_context.get("primary_text")):
        top_negative_drivers.append("缺少主要文字")
    if fallback_reason:
        top_negative_drivers.append("已啟用 AI 執行期備用方案")
    if not top_negative_drivers:
        top_negative_drivers.append("細部調整需人工審核")

    risk_tags = ["heuristic_runtime"]
    if fallback_reason:
        risk_tags.append("provider_fallback")

    if objective_group == "awareness":
        diagnostic_breakdown = {
            "brand_recall": "good" if _clip(request_context.get("headline")) else "needs_work",
            "message_clarity": "good" if _clip(request_context.get("primary_text")) else "needs_work",
            "visual_distinctiveness": "good" if asset_type == "image" else "neutral",
            "emotional_resonance": "neutral",
        }
    elif objective_group == "traffic":
        diagnostic_breakdown = {
            "thumb_stop": "good" if asset_type == "image" else "neutral",
            "curiosity_hook": "good" if _clip(request_context.get("headline")) else "needs_work",
            "visual_appeal": "good" if asset_type == "image" else "neutral",
            "landing_relevance": "good" if _clip(request_context.get("primary_text")) else "needs_work",
        }
    elif objective_group == "video":
        diagnostic_breakdown = {
            "hook_strength": "good" if asset_type == "video" else "neutral",
            "pacing": "neutral",
            "message_delivery": "good" if _clip(request_context.get("headline")) else "needs_work",
            "brand_integration": "good" if _clip(request_context.get("primary_text")) else "neutral",
        }
    elif objective_group == "lead":
        diagnostic_breakdown = {
            "trust_signals": "good" if _clip(request_context.get("primary_text")) else "needs_work",
            "value_proposition": "good" if _clip(request_context.get("headline")) else "needs_work",
            "cta_clarity": "clear" if _clip(request_context.get("cta")) else "missing",
            "audience_fit": "neutral",
        }
    elif objective_group == "engagement":
        diagnostic_breakdown = {
            "shareability": "neutral",
            "emotional_hook": "good" if _clip(request_context.get("primary_text")) else "needs_work",
            "interaction_trigger": "good" if _clip(request_context.get("headline")) else "neutral",
            "visual_impact": "good" if asset_type == "image" else "neutral",
        }
    else:  # conversion
        diagnostic_breakdown = {
            "hook_strength": "good" if _clip(request_context.get("headline")) else "needs_work",
            "cta_presence": "clear" if _clip(request_context.get("cta")) else "missing",
            "placement_fit": "good" if placement_family in {"feed", "stories"} else "neutral",
        }

    if is_diagnostic_only_request:
        roas_unavailable_reason = "diagnostic only request"
    elif not roas_band_eligible:
        roas_unavailable_reason = f"not applicable for {objective_group} campaigns"
    else:
        roas_unavailable_reason = None

    return {
        "status": "completed",
        "prediction_mode": prediction_mode,
        "overall_score": score,
        "roas_band": roas_band,
        "model_version": registry_entry.model_version,
        "feature_manifest_id": registry_entry.feature_manifest_id,
        "error_message": None,
        "diagnostic_breakdown": diagnostic_breakdown,
        "roas_prediction": {
            "eligible": roas_applicable,
            "band": roas_band,
            "confidence": confidence,
            "reason_if_unavailable": roas_unavailable_reason,
        },
        "risk_tags": risk_tags,
        "top_positive_drivers": top_positive_drivers[:3],
        "top_negative_drivers": top_negative_drivers[:3],
        "explanations": {
            "summary": "由 DataVue 註冊表支援的啟發式執行程序完成評分。",
            "top_positive_drivers": top_positive_drivers[:3],
            "top_risks": top_negative_drivers[:3],
            "diagnostic_evidence": {
                "provider": registry_entry.provider,
                "provider_model": registry_entry.provider_model,
                "objective": objective,
                "objective_group": objective_group,
                "placement_family": placement_family,
                "confidence_detail": confidence_detail,
            },
        },
        "lineage": {
            "source_ingest_batch_id": f"runtime_batch_{uuid4().hex[:6]}",
            "feature_manifest_id": registry_entry.feature_manifest_id,
            "registry_model_version": registry_entry.model_version,
            "registry_provider": registry_entry.provider,
            "provider_model": registry_entry.provider_model,
            "registry_profile": registry_entry.scoring_profile,
            "registry_source": registry_entry.source_of_truth,
            "prompt_profile_used": None,
            "scoring_mode": "heuristic",
            "objective_group": objective_group,
            "fallback_reason": fallback_reason or "",
            "label_policy_version": LABEL_POLICY_VERSION,
            "diagnostic_scores": {},
        },
    }


class MetaAndromedaRuntimeAdapter:
    """Registry-backed runtime adapter for queued score processing."""

    @staticmethod
    def build_score_submission(payload: dict) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "score_event_id": f"ma_evt_{now.strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:4]}",
            "status": "queued",
            "runtime_job_id": None,
            "created_at": now,
            "queued_at": now,
            "started_at": None,
            "completed_at": None,
            "failed_at": None,
            "updated_at": now,
            "asset_uri": payload["asset_uri"],
            "asset_type": payload["asset_type"],
            "asset_id": payload.get("asset_id"),
            "preview_url": None,
            "request_mode": payload.get("request_mode", "auto"),
            "objective": payload.get("objective", "purchase"),
            "placement_family": payload.get("placement_family", "all"),
            "market": payload.get("market", "TW"),
            "prediction_mode": None,
            "overall_score": None,
            "roas_band": None,
            "model_version": None,
            "reviewed": False,
            "feedback_count": 0,
            "latest_feedback_decision": None,
            "feature_manifest_id": None,
            "error_message": None,
            "attempt_count": 0,
            "diagnostic_breakdown": {},
            "roas_prediction": None,
            "risk_tags": [],
            "top_positive_drivers": [],
            "top_negative_drivers": [],
            "explanations": None,
            "lineage": {},
            "request_context": {
                "origin": "score_lab",
                "headline": payload.get("headline"),
                "primary_text": payload.get("primary_text"),
                "cta": payload.get("cta"),
                "objective": payload.get("objective", "purchase"),
                "placement_family": payload.get("placement_family", "all"),
                "market": payload.get("market", "TW"),
                "request_mode": payload.get("request_mode", "auto"),
            },
        }

    @staticmethod
    def _prepare_asset_context(score_payload: dict) -> str | None:
        """同步阻塞版本的素材準備：DB 查詢上傳者金鑰、讀檔/S3 下載、base64 編碼、
        ffmpeg keyframe 抽取。這些全是阻塞 I/O，必須透過 asyncio.to_thread 呼叫，
        不可直接 await（否則會卡住 FastAPI 的 event loop，見 docs/24 Wave 1）。

        直接 mutate score_payload["request_context"]；回傳素材上傳者自己的
        OpenRouter API 金鑰（若有）。
        """
        db_key = None
        asset_id = score_payload.get("asset_id")
        if not asset_id:
            return db_key

        try:
            from database import SessionLocal
            from database.models.meta_andromeda import MetaAndromedaAsset
            from database.models.user import User
            from modules.auth.service import TokenManager

            db_session = SessionLocal()
            try:
                asset = db_session.query(MetaAndromedaAsset).filter(MetaAndromedaAsset.id == asset_id).first()
                if asset and asset.uploaded_by:
                    user = db_session.query(User).filter(User.id == asset.uploaded_by).first()
                    if user and user.google_id:
                        db_key = TokenManager.get_ai_api_key(user.google_id, provider="openrouter")
                if asset:
                    request_context = score_payload.setdefault("request_context", {})
                    request_context.setdefault("asset_public_url", asset.public_url)
                    request_context.setdefault("asset_source_url", asset.asset_uri)

                    # 若為內部儲存協議，將其轉為 Base64 Data URI 直接傳送給 AI
                    if asset.asset_uri.startswith("storage://") and asset.asset_type == "image":
                        try:
                            import base64
                            from pathlib import Path

                            if asset.storage_backend == "filesystem":
                                storage_root = Path(settings.META_ANDROMEDA_STORAGE_ROOT)
                                safe_path = (storage_root / asset.storage_key).resolve()
                                if safe_path.relative_to(storage_root.resolve()) and safe_path.exists():
                                    file_bytes = safe_path.read_bytes()
                                    mime = "image/png"
                                    if asset.source_filename.lower().endswith((".jpg", ".jpeg")):
                                        mime = "image/jpeg"
                                    elif asset.source_filename.lower().endswith(".webp"):
                                        mime = "image/webp"
                                    elif asset.source_filename.lower().endswith(".gif"):
                                        mime = "image/gif"
                                    base64_str = base64.b64encode(file_bytes).decode("utf-8")
                                    request_context["asset_public_url"] = f"data:{mime};base64,{base64_str}"

                            elif asset.storage_backend == "s3_compatible":
                                from .storage import storage_adapter
                                client = storage_adapter._build_s3_client()
                                bucket = settings.META_ANDROMEDA_STORAGE_S3_BUCKET
                                response = client.get_object(Bucket=bucket, Key=asset.storage_key)
                                file_bytes = response['Body'].read()
                                mime = response.get('ContentType', 'image/png')
                                base64_str = base64.b64encode(file_bytes).decode("utf-8")
                                request_context["asset_public_url"] = f"data:{mime};base64,{base64_str}"
                        except Exception as parse_exc:
                            logger.error(f"[MetaAndromeda] Base64 encoding failed for asset {asset_id}: {parse_exc}")

                    # 影片素材：抽 keyframes 多圖傳入，讓模型能實際「看到」內容而非只憑文案盲評。
                    # 任何失敗（ffmpeg 不存在、檔案損毀、逾時）都優雅退化為空列表，之後在
                    # _validate_provider_result 標記 video_content_not_inspected 並顯著調降 confidence。
                    elif asset.asset_uri.startswith("storage://") and asset.asset_type == "video":
                        try:
                            from .video_utils import extract_video_keyframes_base64

                            video_bytes = None
                            if asset.storage_backend == "filesystem":
                                from pathlib import Path
                                storage_root = Path(settings.META_ANDROMEDA_STORAGE_ROOT)
                                safe_path = (storage_root / asset.storage_key).resolve()
                                if safe_path.relative_to(storage_root.resolve()) and safe_path.exists():
                                    video_bytes = safe_path.read_bytes()
                            elif asset.storage_backend == "s3_compatible":
                                from .storage import storage_adapter
                                client = storage_adapter._build_s3_client()
                                bucket = settings.META_ANDROMEDA_STORAGE_S3_BUCKET
                                response = client.get_object(Bucket=bucket, Key=asset.storage_key)
                                video_bytes = response['Body'].read()

                            if video_bytes:
                                keyframe_urls = extract_video_keyframes_base64(video_bytes)
                                if keyframe_urls:
                                    request_context["video_keyframe_urls"] = keyframe_urls
                        except Exception as parse_exc:
                            logger.warning(f"[MetaAndromeda] Video keyframe extraction failed for asset {asset_id}: {parse_exc}")
            finally:
                db_session.close()
        except Exception as e:
            logger.error(f"[MetaAndromeda] Failed to retrieve DB API key for asset {asset_id}: {e}")

        return db_key

    @staticmethod
    async def generate_score_result(score_payload: dict) -> dict:
        """Run registry-backed scoring with optional AI provider fallback."""
        registry_entry = model_registry.get_entry()
        provider_name = registry_entry.provider

        # 素材準備（DB 查詢、讀檔、base64、S3 下載、ffmpeg 抽幀）是同步阻塞 I/O，
        # 丟到 thread 執行避免卡住 event loop（docs/24 Wave 1）。
        db_key = await asyncio.to_thread(
            MetaAndromedaRuntimeAdapter._prepare_asset_context, score_payload
        )

        openrouter_key = db_key or settings.OPENROUTER_API_KEY

        logger.debug(
            "[MetaAndromeda] generate_score_result. DB Key present: %s, OPENROUTER_API_KEY len: %s, provider_override: %s",
            bool(db_key),
            len(openrouter_key) if openrouter_key else 0,
            settings.META_ANDROMEDA_SCORING_PROVIDER
        )

        if settings.META_ANDROMEDA_SCORING_PROVIDER == "heuristic":
            provider_name = "heuristic"
        elif settings.META_ANDROMEDA_SCORING_PROVIDER == "openrouter":
            provider_name = "openrouter"
        else:
            has_any_openrouter_key = bool(openrouter_key) or bool(settings.OPENROUTER_API_KEY)
            if provider_name == "openrouter" and not has_any_openrouter_key:
                provider_name = "heuristic"

        provider: BaseScoringProvider
        if provider_name == "openrouter":
            provider = OpenRouterScoringProvider(api_key=openrouter_key)
        else:
            provider = HeuristicScoringProvider()

        try:
            return await provider.score(score_payload, registry_entry)
        except Exception as exc:
            logger.warning("Meta Andromeda scoring provider failed: %s", exc, exc_info=True)
            if not settings.META_ANDROMEDA_SCORING_ALLOW_FALLBACK:
                raise
            fallback_entry = model_registry.get_entry("candidate_v0")
            err_detail = str(exc).replace("\n", " ")
            return build_heuristic_score_result(
                score_payload,
                fallback_entry,
                fallback_reason=f"{provider_name}:{type(exc).__name__} ({err_detail[:120]})",
            )


runtime_adapter = MetaAndromedaRuntimeAdapter()
