"""Heuristic scoring fallback for Meta Andromeda runtime."""

from uuid import uuid4

from .confidence import _build_multimodal_user_content, _clip, _compute_confidence
from .labeling import LABEL_POLICY_VERSION
from .model_registry import MetaAndromedaModelEntry
from .objective_routing import is_roas_band_eligible, resolve_objective_group



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
