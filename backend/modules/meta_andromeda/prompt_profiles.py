"""Prompt profile loading and cache invalidation for Meta Andromeda runtime."""

import json
import logging
import threading
import time

from .cache_invalidation import publish_invalidation, register_invalidation_handler

logger = logging.getLogger(__name__)

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

_DIAGNOSTIC_SCORE_FORMAT_INSTRUCTION = (
    "\n\nOUTPUT FORMAT REQUIREMENT for diagnostic_breakdown: each key's value MUST be a JSON "
    'object {"score": <integer 0-100>, "reasoning": "<one short sentence in Traditional Chinese>"}, '
    "never a plain string. The score is your own independent numeric sub-rating for that "
    "dimension (may differ from overall_score) and is used for downstream statistical calibration."
)



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
