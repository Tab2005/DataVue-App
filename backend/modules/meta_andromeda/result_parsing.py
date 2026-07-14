"""Provider result parsing and validation helpers for Meta Andromeda runtime."""

import json
import logging
import re
from uuid import uuid4

from .confidence import VALID_ROAS_BANDS, _build_multimodal_user_content, _compute_confidence
from .labeling import LABEL_POLICY_VERSION
from .model_registry import MetaAndromedaModelEntry

logger = logging.getLogger(__name__)



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
