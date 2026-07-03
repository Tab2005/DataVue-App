"""
Meta Andromeda Module - statistical confidence calibration (docs/20 task 3.1 / P2-4).

Fits an isotonic (PAVA) mapping from the AI provider's own overall_score to an
empirically observed "this band prediction turned out correct" hit rate, using
MetaAndromedaCalibrationItem history (both correct and incorrect pairs, per the
wave-2 P1-5 change that started syncing error=0 items too). This replaces
runtime._compute_confidence()'s hand-written formula (base + completeness*w)
with a number that means what it claims — a calibrated probability — while
falling back to the old formula when there isn't enough history to fit yet.
"""

import logging
import threading

from .cache_invalidation import publish_invalidation, register_invalidation_handler

logger = logging.getLogger(__name__)

MIN_ITEMS_FOR_FIT = 30
N_BUCKETS = 10
GLOBAL_SCOPE = "global"

_confidence_cache: dict[str, dict] = {}
_confidence_cache_lock = threading.Lock()


def _pava(values: list[float], weights: list[float]) -> list[float]:
    """Pool Adjacent Violators Algorithm: the weighted-least-squares, non-decreasing
    step function closest to `values`. Standard isotonic regression fit."""
    n = len(values)
    if n == 0:
        return []
    # stack of [weighted_mean, total_weight, start_idx, end_idx]
    stack: list[list[float]] = []
    for i in range(n):
        block = [values[i], weights[i], i, i]
        stack.append(block)
        while len(stack) > 1 and stack[-2][0] > stack[-1][0]:
            b = stack.pop()
            a = stack.pop()
            merged_w = a[1] + b[1]
            merged_v = (a[0] * a[1] + b[0] * b[1]) / merged_w if merged_w else 0.0
            stack.append([merged_v, merged_w, a[2], b[3]])

    result = [0.0] * n
    for value, _weight, start, end in stack:
        for i in range(start, end + 1):
            result[i] = value
    return result


def fit_confidence_calibration(db, scope_key: str = GLOBAL_SCOPE) -> dict:
    """Fit (or refit) the calibration mapping from all synced CalibrationItems
    and persist it. Call this after sync_calibration_dataset grows the item
    pool — it's pure Python over at most a few hundred rows, cheap enough to
    run synchronously (no LLM calls, unlike the profile-calibration pipeline)."""
    from database.models.meta_andromeda import MetaAndromedaCalibrationItem, MetaAndromedaConfidenceCalibration

    items = (
        db.query(MetaAndromedaCalibrationItem)
        .filter(MetaAndromedaCalibrationItem.baseline_overall_score.isnot(None))
        .all()
    )
    if len(items) < MIN_ITEMS_FOR_FIT:
        return {"status": "skipped", "reason": "insufficient_items", "item_count": len(items)}

    bucket_hits = [0] * N_BUCKETS
    bucket_total = [0] * N_BUCKETS
    for item in items:
        score = max(0, min(int(item.baseline_overall_score), 100))
        bucket = min(score * N_BUCKETS // 100, N_BUCKETS - 1)
        bucket_total[bucket] += 1
        if item.prediction_band == item.observed_band:
            bucket_hits[bucket] += 1

    raw_rates: list[float] = []
    weights: list[float] = []
    for i in range(N_BUCKETS):
        if bucket_total[i] > 0:
            raw_rates.append(bucket_hits[i] / bucket_total[i])
            weights.append(float(bucket_total[i]))
        else:
            # 空桶：用 0 權重丟給 PAVA，它會被相鄰有資料的桶合併吸收，不會拉低整體擬合
            raw_rates.append(0.5)
            weights.append(0.0)

    calibrated_rates = _pava(raw_rates, weights)
    bucket_boundaries = [round(i * 100 / N_BUCKETS, 1) for i in range(N_BUCKETS + 1)]

    payload = {
        "bucket_boundaries": bucket_boundaries,
        "bucket_rates": [round(r, 4) for r in calibrated_rates],
        "bucket_sample_counts": bucket_total,
        "total_items": len(items),
    }

    existing = (
        db.query(MetaAndromedaConfidenceCalibration)
        .filter(MetaAndromedaConfidenceCalibration.scope_key == scope_key)
        .first()
    )
    if existing:
        existing.calibration_data = payload
        existing.item_count = len(items)
        db.add(existing)
    else:
        import uuid

        db.add(
            MetaAndromedaConfidenceCalibration(
                id=f"ma_cc_{uuid.uuid4().hex[:12]}",
                scope_key=scope_key,
                calibration_data=payload,
                item_count=len(items),
            )
        )
    db.commit()
    invalidate_confidence_cache(scope_key)

    logger.info(
        "[CalibrationStats] Fitted confidence calibration for scope '%s' from %d items: rates=%s",
        scope_key, len(items), payload["bucket_rates"],
    )
    return {"status": "fitted", **payload}


def predict_confidence(overall_score: int, scope_key: str = GLOBAL_SCOPE) -> float | None:
    """Return the calibrated confidence for this overall_score, or None if no
    fit exists yet (caller should fall back to the hand-written formula)."""
    with _confidence_cache_lock:
        mapping = _confidence_cache.get(scope_key)

    if mapping is None:
        try:
            from database import SessionLocal
            from database.models.meta_andromeda import MetaAndromedaConfidenceCalibration

            db = SessionLocal()
            try:
                row = (
                    db.query(MetaAndromedaConfidenceCalibration)
                    .filter(MetaAndromedaConfidenceCalibration.scope_key == scope_key)
                    .first()
                )
                if row is None:
                    return None
                mapping = row.calibration_data or {}
                with _confidence_cache_lock:
                    _confidence_cache[scope_key] = mapping
            finally:
                db.close()
        except Exception as exc:
            logger.warning("[CalibrationStats] Failed to load confidence calibration '%s': %s", scope_key, exc)
            return None

    rates = mapping.get("bucket_rates") or []
    if not rates:
        return None
    score = max(0, min(int(overall_score), 100))
    bucket = min(score * len(rates) // 100, len(rates) - 1)
    return max(0.05, min(float(rates[bucket]), 0.98))


def _invalidate_confidence_cache_local(scope_key: str | None = None) -> None:
    with _confidence_cache_lock:
        if scope_key is None:
            _confidence_cache.clear()
        else:
            _confidence_cache.pop(scope_key, None)


def invalidate_confidence_cache(scope_key: str | None = None) -> None:
    """Clear this process's cache and notify sibling workers via Redis pub/sub
    (P2-7) so a freshly-refit calibration propagates immediately instead of
    each worker only picking it up after its own next sync_calibration_dataset call."""
    publish_invalidation("confidence_calibration", scope_key)


register_invalidation_handler("confidence_calibration", _invalidate_confidence_cache_local)
