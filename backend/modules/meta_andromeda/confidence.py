"""Confidence and self-consistency helpers for Meta Andromeda runtime."""

import logging
from collections import Counter

from core.config import settings

logger = logging.getLogger(__name__)
VALID_ROAS_BANDS = {"high", "mid", "low"}



def _clip(value: str | None, limit: int = 140) -> str:
    if not value:
        return ""
    return value.strip()[:limit]



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
