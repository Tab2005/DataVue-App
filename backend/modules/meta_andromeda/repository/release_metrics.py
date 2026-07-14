"""Release and backtest metric calculations."""

from ._shared import *  # noqa: F401,F403
from ._stats import _compute_pairwise_ranking_accuracy, _spearman_r

__all__ = [
    "ReleaseGateError",
    "_release_min_pairwise_accuracy",
    "_assert_release_gate",
    "_collect_release_metric_pairs",
    "compute_release_metrics",
    "list_release_metric_pairs",
    "_collect_backtest_metric_pairs",
    "compute_backtest_run_metrics",
    "MIN_IMPRESSIONS_FOR_ACCURACY",
    "MIN_OBSERVATION_WINDOW_DAYS",
]

class ReleaseGateError(ValueError):
    def __init__(self, code: str, message: str, status_code: int = 422, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
def _release_min_pairwise_accuracy() -> float:
    raw = os.getenv("META_ANDROMEDA_RELEASE_MIN_PAIRWISE_ACCURACY")
    if raw is None or raw == "":
        return DEFAULT_RELEASE_MIN_PAIRWISE_ACCURACY
    try:
        return float(raw)
    except ValueError:
        logger.warning(
            "[MetaAndromeda] Invalid META_ANDROMEDA_RELEASE_MIN_PAIRWISE_ACCURACY=%r; falling back to %.2f",
            raw,
            DEFAULT_RELEASE_MIN_PAIRWISE_ACCURACY,
        )
        return DEFAULT_RELEASE_MIN_PAIRWISE_ACCURACY
def _assert_release_gate(candidate: MetaAndromedaReleaseRecord, *, force: bool, note: str | None) -> dict:
    threshold = _release_min_pairwise_accuracy()
    accuracy = candidate.pairwise_ranking_accuracy
    gate_payload = {
        "threshold": threshold,
        "pairwise_ranking_accuracy": accuracy,
        "metrics_source": candidate.metrics_source,
        "forced": force,
    }
    if force:
        if not (note or "").strip():
            raise ReleaseGateError(
                "force_note_required",
                "Force approve requires a non-empty note for audit trail.",
                details=gate_payload,
            )
        return gate_payload
    if candidate.metrics_source != "computed":
        raise ReleaseGateError(
            "release_metrics_not_computed",
            "Release candidate has not been backtested with computed metrics yet. Run refresh/backtest before approval, or force with an audit note.",
            details=gate_payload,
        )
    if accuracy is None or float(accuracy) < threshold:
        raise ReleaseGateError(
            "release_accuracy_below_threshold",
            f"Release candidate pairwise ranking accuracy {accuracy} is below required threshold {threshold}.",
            details=gate_payload,
        )
    return gate_payload

# 小曝光廣告的 ROAS/CTR 噪音極大：spend=1、impressions=50 的廣告與 spend 十萬的廣告
# 不該同權重納入 accuracy 計算。門檻選擇 impressions（而非 spend）因跨帳戶/幣別可比。
MIN_IMPRESSIONS_FOR_ACCURACY = 1000
# 觀測期間過短（如 custom 窗口只選 1 天）統計噪音大，不納入 accuracy/校準集
MIN_OBSERVATION_WINDOW_DAYS = 3
def _collect_release_metric_pairs(db, model_version: str) -> list[dict]:
    """收集 `model_version` 的觀測素材 × AI 評分事件配對明細。

    compute_release_metrics()（聚合指標）與 list_release_metric_pairs()（明細端點，
    docs/32 任務 1.1）共用這一份配對邏輯，避免兩處篩選條件漂移導致
    sample_count 與明細筆數對不上。
    """
    observed_list = [
        obs for obs in db.query(MetaAndromedaObservedCreative).all()
        if float((obs.performance_snapshot or {}).get("spend", 0) or 0) > 0
    ]
    if not observed_list:
        return []

    label_thresholds = compute_label_thresholds(observed_list)
    band_score = {"low": 1, "mid": 2, "high": 3}
    pairs: list[dict] = []

    for obs in observed_list:
        pred = match_observed_to_prediction(db, obs)
        if not pred:
            continue
        pred_lineage = pred.lineage or {}
        if pred_lineage.get("scoring_purpose") == "backtest":
            continue
        if pred_lineage.get("registry_model_version") != model_version:
            continue
        if pred_lineage.get("scoring_mode") == "heuristic":
            continue

        real_band, label_detail = label_observed_band(obs.objective, obs.performance_snapshot, label_thresholds)
        pred_roas_eligible = (pred.roas_prediction or {}).get("eligible")
        if pred_roas_eligible is None:
            pred_roas_eligible = resolve_objective_group(obs.objective) not in NON_ROAS_GROUPS
        pred_band = pred.roas_band if pred_roas_eligible else None
        if pred_band is None or pred.overall_score is None or label_detail.get("value") is None:
            continue

        pairs.append({
            "observed_creative_id": obs.id,
            "score_event_id": pred.id,
            "ad_id": obs.ad_id,
            "ad_name": obs.ad_name,
            "asset_uri": obs.asset_uri,
            "media_url": obs.media_url,
            "media_type": obs.media_type,
            "objective": obs.objective,
            "observation_window_kind": obs.observation_window_kind,
            "overall_score": float(pred.overall_score),
            "pred_band": pred_band,
            "real_band": real_band,
            "band_gap": abs(band_score.get(pred_band, 1) - band_score.get(real_band, 1)),
            "label_metric": label_detail.get("metric"),
            "label_value": float(label_detail["value"]),
            "spend": float((obs.performance_snapshot or {}).get("spend", 0) or 0),
        })

    return pairs
def compute_release_metrics(db, model_version: str) -> dict:
    """Compute real pairwise ranking accuracy / mean band error for `model_version`
    from historical drift-matched pairs (ScoreEvent.lineage.registry_model_version),
    replacing the seed placeholder numbers release records shipped with (docs/19 P0-6).
    """
    pairs = _collect_release_metric_pairs(db, model_version)
    matched = len(pairs)
    if matched < 3:
        return {"status": "insufficient_data", "sample_count": matched}

    scores = [p["overall_score"] for p in pairs]
    perf_values = [p["label_value"] for p in pairs]
    total_error = float(sum(p["band_gap"] for p in pairs))

    return {
        "status": "computed",
        "sample_count": matched,
        "pairwise_ranking_accuracy": round(_compute_pairwise_ranking_accuracy(scores, perf_values), 4),
        "mean_band_error": round(total_error / matched, 4),
    }
def list_release_metric_pairs(db, model_version: str, *, sort: str = "mismatch", limit: int = 50) -> dict:
    """回傳 `model_version` 的配對明細（docs/32 任務 1.1），供人工歸因抽樣。

    sort:
    - "mismatch"（預設）：級距差大→小，同級距差內模型總分高→低，讓「高分低效」浮最上面。
    - "score_vs_perf"：模型總分高→低，並附實際成效排名 perf_rank（1 = 該批成效最好），
      方便肉眼檢視分數與成效的反相關。
    """
    pairs = _collect_release_metric_pairs(db, model_version)
    total = len(pairs)

    # perf_rank 依 label_metric 方向性一律以「值大 = 排名前」處理會誤導（CPC/CPL 越低越好），
    # 但配對明細以 dominant metric 為主的簡化排名已足夠人工抽樣使用；成本型指標另以
    # label_metric 欄位提示閱讀方向。
    by_perf = sorted(range(total), key=lambda i: pairs[i]["label_value"], reverse=True)
    for rank_pos, idx in enumerate(by_perf, start=1):
        pairs[idx]["perf_rank"] = rank_pos

    if sort == "score_vs_perf":
        pairs.sort(key=lambda p: p["overall_score"], reverse=True)
    else:
        pairs.sort(key=lambda p: (p["band_gap"], p["overall_score"]), reverse=True)

    return {
        "model_version": model_version,
        "sort": sort if sort in ("mismatch", "score_vs_perf") else "mismatch",
        "sample_count": total,
        "items": pairs[: max(1, limit)] if total else [],
    }
def _collect_backtest_metric_pairs(db, backtest_run_id: str) -> list[dict]:
    score_rows = [
        row for row in db.query(MetaAndromedaScoreEvent).all()
        if row.status == "completed"
        and (row.lineage or {}).get("scoring_purpose") == "backtest"
        and (row.lineage or {}).get("backtest_run_id") == backtest_run_id
        and (row.lineage or {}).get("scoring_mode") != "heuristic"
    ]
    if not score_rows:
        return []

    observed_ids = {
        (row.request_context or {}).get("observed_creative_id")
        for row in score_rows
        if (row.request_context or {}).get("observed_creative_id")
    }
    observed_by_id = {
        obs.id: obs for obs in db.query(MetaAndromedaObservedCreative)
        .filter(MetaAndromedaObservedCreative.id.in_(observed_ids))
        .all()
    } if observed_ids else {}
    observed_list = [observed_by_id[oid] for oid in observed_ids if oid in observed_by_id]
    if not observed_list:
        return []

    label_thresholds = compute_label_thresholds(observed_list)
    band_score = {"low": 1, "mid": 2, "high": 3}
    pairs: list[dict] = []
    for score in score_rows:
        obs_id = (score.request_context or {}).get("observed_creative_id")
        obs = observed_by_id.get(obs_id)
        if not obs:
            continue
        real_band, label_detail = label_observed_band(obs.objective, obs.performance_snapshot, label_thresholds)
        pred_band = score.roas_band
        if pred_band is None or score.overall_score is None or label_detail.get("value") is None:
            continue
        pairs.append({
            "observed_creative_id": obs.id,
            "score_event_id": score.id,
            "overall_score": float(score.overall_score),
            "pred_band": pred_band,
            "real_band": real_band,
            "band_gap": abs(band_score.get(pred_band, 1) - band_score.get(real_band, 1)),
            "label_value": float(label_detail["value"]),
        })
    return pairs
def compute_backtest_run_metrics(db, backtest_run_id: str) -> dict:
    pairs = _collect_backtest_metric_pairs(db, backtest_run_id)
    matched = len(pairs)
    if matched < 3:
        return {"status": "insufficient_data", "sample_count": matched}
    return {
        "status": "computed",
        "sample_count": matched,
        "pairwise_ranking_accuracy": _compute_pairwise_ranking_accuracy(
            [p["overall_score"] for p in pairs],
            [p["label_value"] for p in pairs],
        ),
        "mean_band_error": float(sum(p["band_gap"] for p in pairs)) / matched,
    }
