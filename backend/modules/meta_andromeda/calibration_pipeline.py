"""
Meta Andromeda Calibration Pipeline
分析校準資料集的偏差模式，並自動生成修正版 Scoring Profile。
"""

import logging
import uuid
from datetime import datetime, timezone

from database.models.meta_andromeda import MetaAndromedaCalibrationItem, MetaAndromedaScoringProfile

logger = logging.getLogger(__name__)

MIN_ITEMS_FOR_CALIBRATION = 10

_BIAS_GUIDANCE = {
    "over_predict": (
        "CALIBRATION NOTE: Recent performance data shows a systematic tendency to over-predict ROAS bands. "
        "Apply stricter thresholds for HIGH classification — require multiple strong positive signals with no significant risk tags. "
        "When visual hierarchy is strong but CTA or copy is mediocre, default to MID rather than HIGH. "
        "Err on the side of conservative scoring."
    ),
    "under_predict": (
        "CALIBRATION NOTE: Recent performance data shows a systematic tendency to under-predict ROAS bands. "
        "Do not be overly conservative. "
        "If a creative shows clear visual focus, compelling CTA, and on-brand messaging that is consistent with the target market, "
        "lean toward MID or HIGH even if minor imperfections exist. "
        "Only assign LOW when there are clear structural weaknesses."
    ),
    "mixed": (
        "CALIBRATION NOTE: Recent performance data shows inconsistent prediction patterns with no dominant bias direction. "
        "Pay close attention to the diagnostic_breakdown scores — ensure that visual_appeal, copywriting, "
        "cta_clarity, and relevance are evaluated independently and consistently. "
        "Do not let one strong dimension override weaknesses in others."
    ),
}


def analyze_dataset_bias(db, dataset_id: str) -> dict:
    items = (
        db.query(MetaAndromedaCalibrationItem)
        .filter(MetaAndromedaCalibrationItem.dataset_id == dataset_id)
        .all()
    )

    total_items = len(items)
    if total_items == 0:
        return {
            "total_items": 0,
            "min_samples_met": False,
            "dominant_bias": "mixed",
            "confusion_matrix": {},
            "over_predict_count": 0,
            "under_predict_count": 0,
            "worst_examples": [],
        }

    band_order = {"low": 1, "mid": 2, "high": 3}
    over_predict = 0
    under_predict = 0
    confusion: dict[str, dict[str, int]] = {}
    worst: list[dict] = []

    for item in items:
        obs = item.observed_band
        pred = item.prediction_band
        confusion.setdefault(obs, {})
        confusion[obs][pred] = confusion[obs].get(pred, 0) + 1

        obs_val = band_order.get(obs, 2)
        pred_val = band_order.get(pred, 2)
        if pred_val > obs_val:
            over_predict += 1
        elif pred_val < obs_val:
            under_predict += 1

        if item.error >= 2:
            snap = item.performance_snapshot or {}
            worst.append({
                "prediction_band": pred,
                "observed_band": obs,
                "headline": (item.score_event.request_context or {}).get("headline", "") if item.score_event else "",
                "primary_text": (item.score_event.request_context or {}).get("primary_text", "") if item.score_event else "",
                "error": item.error,
                "roas": snap.get("roas"),
            })

    worst.sort(key=lambda x: x["error"], reverse=True)
    worst = worst[:3]

    if over_predict > under_predict * 1.5:
        dominant_bias = "over_predict"
    elif under_predict > over_predict * 1.5:
        dominant_bias = "under_predict"
    else:
        dominant_bias = "mixed"

    return {
        "total_items": total_items,
        "min_samples_met": total_items >= MIN_ITEMS_FOR_CALIBRATION,
        "dominant_bias": dominant_bias,
        "confusion_matrix": confusion,
        "over_predict_count": over_predict,
        "under_predict_count": under_predict,
        "worst_examples": worst,
    }


def _format_few_shot_block(examples: list[dict]) -> str:
    if not examples:
        return ""
    lines = ["\n\nCALIBRATION EXAMPLES (cases where prior predictions were wrong):"]
    for i, ex in enumerate(examples, 1):
        pred = ex.get("prediction_band", "?")
        obs = ex.get("observed_band", "?")
        headline = str(ex.get("headline") or "")[:80]
        roas = ex.get("roas")
        roas_str = f" (actual ROAS: {roas:.2f})" if roas is not None else ""
        lines.append(
            f"  Example {i}: Model predicted '{pred}' but actual performance was '{obs}'{roas_str}. "
            f"Headline: '{headline}'. "
            f"Lesson: Be more careful when evaluating similar creatives."
        )
    return "\n".join(lines)


def generate_calibrated_profile(db, dataset_id: str, base_profile_name: str) -> str | None:
    bias = analyze_dataset_bias(db, dataset_id)

    if not bias["min_samples_met"]:
        logger.info(
            "[CalibrationPipeline] Dataset %s has only %d items (< %d). Skipping profile generation.",
            dataset_id,
            bias["total_items"],
            MIN_ITEMS_FOR_CALIBRATION,
        )
        return None

    base_profile = (
        db.query(MetaAndromedaScoringProfile)
        .filter(MetaAndromedaScoringProfile.profile_name == base_profile_name)
        .first()
    )
    if base_profile is None:
        logger.warning(
            "[CalibrationPipeline] Base profile '%s' not found. Skipping calibration.",
            base_profile_name,
        )
        return None

    new_profile_name = f"{base_profile_name}_cal_{dataset_id[:8]}"
    if db.query(MetaAndromedaScoringProfile).filter(
        MetaAndromedaScoringProfile.profile_name == new_profile_name
    ).first():
        logger.info("[CalibrationPipeline] Profile '%s' already exists. Skipping.", new_profile_name)
        return new_profile_name

    calibration_guidance = _BIAS_GUIDANCE[bias["dominant_bias"]]
    few_shot_examples = bias["worst_examples"]

    new_profile = MetaAndromedaScoringProfile(
        id=f"sp_{uuid.uuid4().hex[:12]}",
        profile_name=new_profile_name,
        user_prompt_template=base_profile.user_prompt_template,
        system_prompt=base_profile.system_prompt,
        calibration_guidance=calibration_guidance,
        few_shot_examples=few_shot_examples,
        bias_summary=bias,
        source="calibration_auto",
        base_profile_name=base_profile_name,
        calibration_dataset_id=dataset_id,
        is_promoted=False,
    )
    db.add(new_profile)
    db.commit()

    logger.info(
        "[CalibrationPipeline] Generated new profile '%s' from dataset %s (bias=%s, items=%d).",
        new_profile_name,
        dataset_id,
        bias["dominant_bias"],
        bias["total_items"],
    )
    return new_profile_name
