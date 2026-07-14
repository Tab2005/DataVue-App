"""Pure statistics helpers for Meta Andromeda repository."""

from ._shared import *  # noqa: F401,F403

__all__ = [
    "_window_days",
    "_dedupe_observed_by_ad_id",
    "_compute_pairwise_ranking_accuracy",
    "_average_rank",
    "_spearman_r",
    "_spearman_r_weighted",
    "_classify_period_state",
    "_METRIC_LABEL",
    "_TRANSITION_MESSAGES",
]

def _window_days(start_str: str | None, end_str: str | None) -> int | None:
    try:
        start = date.fromisoformat((start_str or "")[:10])
        end = date.fromisoformat((end_str or "")[:10])
        return (end - start).days + 1
    except (TypeError, ValueError):
        return None
def _dedupe_observed_by_ad_id(observed_list: list) -> tuple[list, int]:
    """Collapse duplicate ObservedCreative rows sharing the same ad_id within one
    drift report batch (e.g. a 'custom' window's interval-overlap query can match
    both a last_7d and a last_30d row for the same ad). Keeps the highest-spend
    row, tie-broken by the longer observation window."""
    best_by_ad: dict[str, object] = {}
    for obs in observed_list:
        spend = float((obs.performance_snapshot or {}).get("spend", 0) or 0)
        current = best_by_ad.get(obs.ad_id)
        if current is None:
            best_by_ad[obs.ad_id] = obs
            continue
        current_spend = float((current.performance_snapshot or {}).get("spend", 0) or 0)
        if spend > current_spend:
            best_by_ad[obs.ad_id] = obs
        elif spend == current_spend:
            current_days = _window_days(current.observation_window_start, current.observation_window_end) or 0
            new_days = _window_days(obs.observation_window_start, obs.observation_window_end) or 0
            if new_days > current_days:
                best_by_ad[obs.ad_id] = obs
    deduped = list(best_by_ad.values())
    return deduped, len(observed_list) - len(deduped)
def _compute_pairwise_ranking_accuracy(scores: list[float], perf: list[float]) -> float:
    """Fraction of concordant pairs: how often a higher overall_score also has a
    higher primary-metric value. Pairs tied on either dimension are excluded from
    the denominator (standard convention for pairwise/Kendall-style concordance)."""
    n = len(scores)
    concordant = 0
    total = 0
    for i in range(n):
        for j in range(i + 1, n):
            if scores[i] == scores[j] or perf[i] == perf[j]:
                continue
            total += 1
            if (scores[i] - scores[j]) * (perf[i] - perf[j]) > 0:
                concordant += 1
    return concordant / total if total else 0.0
def _average_rank(values: list[float]) -> list[float]:
    """Tie-aware average ranking: tied values share the mean of their tied rank positions."""
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return ranks
def _spearman_r(x: list[float], y: list[float]) -> float:
    """Spearman rank correlation between two equal-length lists. Returns 0.0 if n < 3.

    Uses tie-aware average ranking (ties share the mean of their tied rank
    positions) and computes rho as the Pearson correlation of the ranks.
    Without ties this is mathematically identical to the classic
    1 - 6*sum(d^2)/(n*(n^2-1)) shortcut; with ties (common here since AI
    scores cluster on a handful of integers) the shortcut formula is biased
    and this is the textbook-correct generalization.
    """
    n = len(x)
    if n < 3:
        return 0.0

    rx, ry = _average_rank(x), _average_rank(y)
    mean_rx = sum(rx) / n
    mean_ry = sum(ry) / n
    cov = sum((rx[i] - mean_rx) * (ry[i] - mean_ry) for i in range(n))
    var_x = sum((r - mean_rx) ** 2 for r in rx)
    var_y = sum((r - mean_ry) ** 2 for r in ry)
    denom = (var_x * var_y) ** 0.5
    return cov / denom if denom else 0.0
def _spearman_r_weighted(x: list[float], y: list[float], weights: list[float]) -> float:
    """Spend-weighted Spearman rho: weighted Pearson correlation on tie-aware ranks.

    Supplementary metric alongside the unweighted rho — large-budget creatives
    matter more for ranking quality in practice, but this doesn't replace the
    primary ρ used for drift verdicts (a handful of high-spend ads shouldn't
    single-handedly flip the health status).
    """
    n = len(x)
    if n < 3 or sum(weights) <= 0:
        return 0.0

    rx, ry = _average_rank(x), _average_rank(y)
    total_w = sum(weights)
    mean_rx = sum(w * r for w, r in zip(weights, rx)) / total_w
    mean_ry = sum(w * r for w, r in zip(weights, ry)) / total_w
    cov = sum(w * (rx[i] - mean_rx) * (ry[i] - mean_ry) for i, w in enumerate(weights))
    var_x = sum(w * (rx[i] - mean_rx) ** 2 for i, w in enumerate(weights))
    var_y = sum(w * (ry[i] - mean_ry) ** 2 for i, w in enumerate(weights))
    denom = (var_x * var_y) ** 0.5
    return cov / denom if denom else 0.0


_METRIC_LABEL: dict[str, str] = {
    "roas":             "ROAS",
    "cvr":              "CVR",
    "cpl":              "CPL",
    "cpa":              "CPA",
    "ctr":              "CTR",
    "cpc":              "CPC",
    "fallback_traffic": "CTR/CPC",
}

_TRANSITION_MESSAGES: dict[tuple[str, str], str] = {
    ("market_driven",    "creative_critical"): "市場護航期結束，創意品質重新成為關鍵差異因子。建議積極優化素材，高分素材加速擴量，低分素材快速汰換。",
    ("market_driven",    "needs_review"):      "市場護航期結束且整體表現轉弱。建議系統性檢視：受眾定向精準度、出價策略、素材是否已疲乏。",
    ("market_driven",    "dual_advantage"):    "創意影響力明顯提升，進入雙重有利期。建議把握時機擴大預算規模，維持高品質素材供應節奏。",
    ("dual_advantage",   "market_driven"):     "創意影響力下滑，整體表現現由市場/定向因素主導。勿過度依賴創意優化，優先鞏固定向與競價策略。",
    ("dual_advantage",   "creative_critical"): "整體績效下滑但創意仍是關鍵差異因子。維持創意優化投入，高分素材積極保量避免縮量。",
    ("dual_advantage",   "needs_review"):      "雙重有利期結束，表現全面走弱。建議系統性檢視所有影響因子，避免繼續擴量。",
    ("creative_critical","dual_advantage"):    "市場環境改善，創意品質持續有效，進入雙重有利期。可適度擴大預算並維持高品質素材供應。",
    ("creative_critical","market_driven"):     "市場環境好轉拉動整體表現，但創意影響力相對下降。優先鞏固定向與競價優勢，創意達標即可。",
    ("creative_critical","needs_review"):      "創意影響力也開始弱化，整體陷入全面檢視狀態。建議優先排查根本問題再考慮調整投放策略。",
    ("needs_review",     "creative_critical"): "創意品質開始發揮影響力，從全面檢視期進入創意突圍階段。持續優化高分素材，快速汰換低分素材。",
    ("needs_review",     "market_driven"):     "市場/定向因素開始拉動整體表現，從全面檢視期逐步回穩。鞏固定向與競價優勢，謹慎恢復預算。",
    ("needs_review",     "dual_advantage"):    "強勁復甦，直接進入雙重有利期。建議積極擴量並保持當前創意策略。",
}
def _classify_period_state(spearman_r: float, perf_is_high: bool, dominant_metric: str) -> dict:
    metric_label = _METRIC_LABEL.get(dominant_metric, dominant_metric.upper())
    creative_is_effective = spearman_r >= 0.30

    if perf_is_high and creative_is_effective:
        state, label = "dual_advantage", "雙重有利"
        recommendation = (
            f"創意品質與市場環境同步有利（ρ={spearman_r:.3f}），"
            f"{metric_label} 整體表現佳且與創意評分正相關。"
            "維持現有創意策略，可考慮擴大投放預算。"
        )
    elif perf_is_high and not creative_is_effective:
        state, label = "market_driven", "市場護航"
        recommendation = (
            f"整體 {metric_label} 由市場/定向/競價因素拉高（ρ={spearman_r:.3f}），"
            "創意品質影響力偏弱。優先鞏固受眾定向與競價策略；"
            "創意達標即可，勿過度投資創意優化。"
        )
    elif not perf_is_high and creative_is_effective:
        state, label = "creative_critical", "創意突圍"
        recommendation = (
            f"市場環境困難，創意品質是主要差異因子（ρ={spearman_r:.3f}）。"
            f"積極擴量高分素材，快速汰換低分素材，"
            "創意優化的投資報酬率在此階段最高。"
        )
    else:
        state, label = "needs_review", "全面檢視"
        recommendation = (
            f"創意品質與整體 {metric_label} 同步偏弱（ρ={spearman_r:.3f}），"
            "需系統性檢視：產品競爭力、受眾定向精準度、出價策略、素材是否已疲乏。"
        )

    return {
        "state": state,
        "label": label,
        "creative_is_effective": creative_is_effective,
        "perf_is_high": perf_is_high,
        "dominant_metric": dominant_metric,
        "creative_explained_variance": round(spearman_r ** 2, 4),
        "recommendation": recommendation,
    }
