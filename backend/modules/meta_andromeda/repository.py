"""
Meta Andromeda Module - DB-backed repository
"""

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import math
import statistics
from sqlalchemy.orm import Session

from database.models.meta_andromeda import (
    MetaAndromedaAsset,
    MetaAndromedaCalibrationDataset,
    MetaAndromedaCalibrationItem,
    MetaAndromedaDeadLetter,
    MetaAndromedaDriftReport,
    MetaAndromedaFeedbackEvent,
    MetaAndromedaObservedCreative,
    MetaAndromedaReleaseEvent,
    MetaAndromedaReleaseRecord,
    MetaAndromedaScoreEvent,
    MetaAndromedaScoringProfile,
    MetaAndromedaWorkerEvent,
)
from .model_registry import model_registry


TERMINAL_SCORE_STATUSES = {"completed", "failed"}
LABEL_POLICY_VERSION = "ma_label_policy_v1"


def _objective_key(value: str | None) -> str:
    return (value or "").strip().lower()


_ROAS_FALLBACK_LOW = 3.0
_ROAS_FALLBACK_HIGH = 6.0

# 流量/互動/知名度廣告 objective 關鍵詞清單
# 這類廣告不追求購買轉換，ROAS 永遠為 0，應改用 CTR/CPC 評估
_TRAFFIC_OBJECTIVE_TOKENS = (
    "traffic", "engagement", "awareness", "reach", "video",
    "outcome_traffic", "outcome_engagement", "outcome_awareness",
    # 舊帳號代碼相容
    "link_clicks", "post_engagement", "page_likes",
    "brand_awareness", "video_views",
)


def _is_traffic_objective(objective_key: str) -> bool:
    return any(token in objective_key for token in _TRAFFIC_OBJECTIVE_TOKENS)


def _spearman_r(x: list[float], y: list[float]) -> float:
    """Spearman rank correlation between two equal-length lists. Returns 0.0 if n < 3."""
    n = len(x)
    if n < 3:
        return 0.0

    def _rank(values: list[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: values[i])
        ranks = [0.0] * n
        for pos, idx in enumerate(order):
            ranks[idx] = float(pos + 1)
        return ranks

    rx, ry = _rank(x), _rank(y)
    d_sq = sum((rx[i] - ry[i]) ** 2 for i in range(n))
    denom = n * (n * n - 1)
    return 1.0 - (6.0 * d_sq / denom) if denom else 0.0


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


def _resolve_observed_band(
    objective: str | None,
    performance_snapshot: dict | None,
    roas_thresholds: tuple[float, float] | None = None,
    ctr_thresholds: tuple[float, float] | None = None,
    cpc_thresholds: tuple[float, float] | None = None,
) -> tuple[str, dict]:
    snapshot = performance_snapshot or {}
    objective_key = _objective_key(objective)

    # 潛在客戶廣告：CVR / CPL 評估
    if any(token in objective_key for token in ("lead", "cpl")):
        cvr = snapshot.get("cvr")
        if cvr is not None:
            value = float(cvr)
            if value >= 0.08:
                return "high", {"metric": "cvr", "value": value}
            if value >= 0.03:
                return "mid", {"metric": "cvr", "value": value}
            return "low", {"metric": "cvr", "value": value}
        cpl = snapshot.get("cpl")
        if cpl is not None:
            value = float(cpl)
            if value <= 150:
                return "high", {"metric": "cpl", "value": value}
            if value <= 350:
                return "mid", {"metric": "cpl", "value": value}
            return "low", {"metric": "cpl", "value": value}

    # 流量 / 互動 / 知名度廣告：CTR 或 CPC 評估（ROAS 對此類廣告無意義）
    if _is_traffic_objective(objective_key):
        ctr = snapshot.get("ctr")
        if ctr is not None and ctr_thresholds:
            value = float(ctr)
            low_t, high_t = ctr_thresholds
            if value >= high_t:
                return "high", {"metric": "ctr", "value": value}
            if value >= low_t:
                return "mid", {"metric": "ctr", "value": value}
            return "low", {"metric": "ctr", "value": value}

        cpc = snapshot.get("cpc")
        if cpc is not None and cpc_thresholds and float(cpc) > 0:
            value = float(cpc)
            # cpc_thresholds = (P67, P33)：CPC 越低越好，P33 側 → "high"
            low_t, high_t = cpc_thresholds
            if value <= high_t:
                return "high", {"metric": "cpc", "value": value}
            if value <= low_t:
                return "mid", {"metric": "cpc", "value": value}
            return "low", {"metric": "cpc", "value": value}

        return "low", {"metric": "fallback_traffic", "value": None}

    # 轉換廣告（預設）：ROAS 評估
    roas = snapshot.get("roas")
    if roas is not None:
        value = float(roas)
        low_threshold, high_threshold = roas_thresholds if roas_thresholds else (_ROAS_FALLBACK_LOW, _ROAS_FALLBACK_HIGH)
        if value < low_threshold:
            return "low", {"metric": "roas", "value": value}
        if value < high_threshold:
            return "mid", {"metric": "roas", "value": value}
        return "high", {"metric": "roas", "value": value}

    cpa = snapshot.get("cpa")
    if cpa is not None:
        value = float(cpa)
        if value <= 120:
            return "high", {"metric": "cpa", "value": value}
        if value <= 300:
            return "mid", {"metric": "cpa", "value": value}
        return "low", {"metric": "cpa", "value": value}

    return "low", {"metric": "fallback", "value": None}


SEED_REVIEW_QUEUE = [
    {
        "id": "ma_evt_20260605_001",
        "status": "completed",
        "runtime_job_id": "ma_score_ma_evt_20260605_001",
        "created_at": datetime(2026, 6, 5, 9, 15, tzinfo=timezone.utc),
        "queued_at": datetime(2026, 6, 5, 9, 15, tzinfo=timezone.utc),
        "started_at": datetime(2026, 6, 5, 9, 15, 10, tzinfo=timezone.utc),
        "completed_at": datetime(2026, 6, 5, 9, 18, tzinfo=timezone.utc),
        "failed_at": None,
        "updated_at": datetime(2026, 6, 5, 9, 18, tzinfo=timezone.utc),
        "asset_uri": "storage://meta-andromeda/assets/creative_001.png",
        "asset_type": "image",
        "asset_id": "creative_001",
        "preview_url": None,
        "request_mode": "diagnostic_plus_roas",
        "objective": "purchase",
        "placement_family": "feed",
        "market": "TW",
        "prediction_mode": "diagnostic_plus_roas",
        "overall_score": 82,
        "roas_band": "high",
        "model_version": "candidate_v0",
        "reviewed": False,
        "feedback_count": 0,
        "latest_feedback_decision": None,
        "feature_manifest_id": "fm_001",
        "error_message": None,
        "attempt_count": 1,
        "diagnostic_breakdown": {
            "hook_strength": "strong",
            "cta_presence": "clear",
            "placement_fit": "good",
        },
        "roas_prediction": {
            "eligible": True,
            "band": "high",
            "confidence": 0.74,
            "reason_if_unavailable": None,
        },
        "risk_tags": ["text_density_watch"],
        "top_positive_drivers": ["strong opening hook", "clear CTA", "offer visibility"],
        "top_negative_drivers": ["text density slightly high"],
        "explanations": {
            "summary": "Creative is ready for reviewer inspection with strong purchase intent signals.",
            "top_positive_drivers": ["strong opening hook", "clear CTA", "offer visibility"],
            "top_risks": ["text density slightly high"],
            "diagnostic_evidence": {
                "headline": "限時優惠訊號清楚",
                "cta": "立即購買明確",
            },
        },
        "lineage": {
            "source_ingest_batch_id": "seed_batch_001",
            "feature_manifest_id": "fm_001",
        },
        "request_context": {},
    },
    {
        "id": "ma_evt_20260605_002",
        "status": "completed",
        "runtime_job_id": "ma_score_ma_evt_20260605_002",
        "created_at": datetime(2026, 6, 5, 8, 40, tzinfo=timezone.utc),
        "queued_at": datetime(2026, 6, 5, 8, 40, tzinfo=timezone.utc),
        "started_at": datetime(2026, 6, 5, 8, 40, 15, tzinfo=timezone.utc),
        "completed_at": datetime(2026, 6, 5, 8, 43, tzinfo=timezone.utc),
        "failed_at": None,
        "updated_at": datetime(2026, 6, 5, 8, 43, tzinfo=timezone.utc),
        "asset_uri": "storage://meta-andromeda/assets/creative_002.mp4",
        "asset_type": "video",
        "asset_id": "creative_002",
        "preview_url": None,
        "request_mode": "diagnostic_plus_roas",
        "objective": "lead",
        "placement_family": "reels",
        "market": "TW",
        "prediction_mode": "diagnostic_plus_roas",
        "overall_score": 61,
        "roas_band": "mid",
        "model_version": "candidate_v0",
        "reviewed": True,
        "feedback_count": 1,
        "latest_feedback_decision": "revise",
        "feature_manifest_id": "fm_002",
        "error_message": None,
        "attempt_count": 1,
        "diagnostic_breakdown": {
            "hook_strength": "medium",
            "cta_presence": "moderate",
            "placement_fit": "good",
        },
        "roas_prediction": {
            "eligible": True,
            "band": "mid",
            "confidence": 0.63,
            "reason_if_unavailable": None,
        },
        "risk_tags": ["hook_not_sharp_enough", "offer_visibility"],
        "top_positive_drivers": ["good reel pacing", "clean branding"],
        "top_negative_drivers": ["hook not sharp enough", "offer visibility can improve"],
        "explanations": {
            "summary": "Creative is usable but likely needs revision before release.",
            "top_positive_drivers": ["good reel pacing", "clean branding"],
            "top_risks": ["hook not sharp enough", "offer visibility can improve"],
            "diagnostic_evidence": {
                "video_pacing": "節奏穩定",
                "offer": "優惠露出偏晚",
            },
        },
        "lineage": {
            "source_ingest_batch_id": "seed_batch_002",
            "feature_manifest_id": "fm_002",
        },
        "request_context": {},
    },
    {
        "id": "ma_evt_20260605_003",
        "status": "queued",
        "runtime_job_id": "ma_score_ma_evt_20260605_003",
        "created_at": datetime(2026, 6, 5, 8, 5, tzinfo=timezone.utc),
        "queued_at": datetime(2026, 6, 5, 8, 5, tzinfo=timezone.utc),
        "started_at": None,
        "completed_at": None,
        "failed_at": None,
        "updated_at": datetime(2026, 6, 5, 8, 5, tzinfo=timezone.utc),
        "asset_uri": "storage://meta-andromeda/assets/creative_003.png",
        "asset_type": "image",
        "asset_id": "creative_003",
        "preview_url": None,
        "request_mode": "auto",
        "objective": "purchase",
        "placement_family": "stories",
        "market": "TW",
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
        "request_context": {},
    },
]

SEED_FEEDBACK = [
    {
        "id": "fb_evt_001",
        "score_event_id": "ma_evt_20260605_002",
        "reviewer_id": "reviewer_01",
        "decision": "revise",
        "reason_codes": ["hook_soft", "offer_late"],
        "comment": "Hook 可再更直接，優惠露出還可以提早。",
        "created_at": datetime(2026, 6, 5, 8, 55, tzinfo=timezone.utc),
    }
]

SEED_RELEASE_RECORDS = [
    {
        "record_kind": "current_production",
        "model_version": "prod_v2026_05_28",
        "release_status": "production",
        "approved_by": "operator_01",
        "approved_at": "2026-05-28T09:30:00Z",
        "created_at": "2026-05-28T09:30:00Z",
        "pairwise_ranking_accuracy": 0.74,
        "mean_band_error": 0.19,
        "promotion_gate_summary": None,
    },
    {
        "record_kind": "previous_production",
        "model_version": "prod_v2026_05_12",
        "release_status": "superseded",
        "approved_by": "operator_01",
        "approved_at": "2026-05-12T08:20:00Z",
        "created_at": "2026-05-12T08:20:00Z",
        "pairwise_ranking_accuracy": 0.69,
        "mean_band_error": 0.23,
        "promotion_gate_summary": None,
    },
    {
        "record_kind": "candidate",
        "model_version": "cand_v2026_06_05_a",
        "release_status": "candidate",
        "approved_by": None,
        "approved_at": None,
        "created_at": "2026-06-05T07:00:00Z",
        "pairwise_ranking_accuracy": 0.78,
        "mean_band_error": 0.17,
        "promotion_gate_summary": {
            "sample_size_ok": True,
            "beats_naive_baseline": True,
            "not_worse_than_production": True,
            "calibration_ok": True,
        },
    },
    {
        "record_kind": "candidate",
        "model_version": "cand_v2026_06_04_b",
        "release_status": "candidate",
        "approved_by": None,
        "approved_at": None,
        "created_at": "2026-06-04T15:10:00Z",
        "pairwise_ranking_accuracy": 0.71,
        "mean_band_error": 0.21,
        "promotion_gate_summary": {
            "sample_size_ok": True,
            "beats_naive_baseline": True,
            "not_worse_than_production": False,
            "calibration_ok": True,
        },
    },
]

SEED_RELEASE_EVENTS = [
    {
        "action": "approve",
        "model_version": "prod_v2026_05_28",
        "actor": "operator_01",
        "created_at": "2026-05-28T09:30:00Z",
        "note": "Promoted after holdout metrics cleared all gates.",
    },
    {
        "action": "rollback",
        "model_version": "prod_v2026_05_12",
        "actor": "operator_02",
        "created_at": "2026-05-13T10:05:00Z",
        "note": "Rolled back due to calibration anomaly.",
    },
]

SEED_DRIFT_REPORTS = [
    {
        "window_kind": "last_24h",
        "drift_status": "stable",
        "summary": "Seed baseline shows no material drift in the initial DataVue bootstrap window.",
        "severity": "info",
        "triggered_by": "system_seed",
        "note": "Bootstrap drift baseline for Meta Andromeda monitoring.",
        "report_payload": {
            "score_total": 3,
            "completed_total": 2,
            "failed_total": 0,
            "dead_letter_total": 0,
            "retrying_total": 0,
            "high_ratio": 0.5,
            "mid_ratio": 0.5,
            "low_ratio": 0.0,
        },
    },
]


class MetaAndromedaRepository:
    def ensure_seed_data(self, db: Session):
        if db.query(MetaAndromedaScoreEvent).count() == 0:
            for item in SEED_REVIEW_QUEUE:
                asset = db.query(MetaAndromedaAsset).filter(MetaAndromedaAsset.id == item["asset_id"]).first()
                if asset is None:
                    asset = MetaAndromedaAsset(
                        id=item["asset_id"],
                        asset_uri=item["asset_uri"],
                        storage_backend="seed",
                        storage_key=f"seed/{item['asset_id']}",
                        asset_type=item["asset_type"],
                        source_filename=f"{item['asset_id']}.{ 'png' if item['asset_type'] == 'image' else 'mp4'}",
                        checksum_sha256=f"seed_{item['asset_id']}",
                        upload_status="seeded",
                        file_size_bytes=0,
                        public_url=None,
                        uploaded_by=None,
                        uploaded_at=item["created_at"],
                    )
                    db.add(asset)

                db.add(MetaAndromedaScoreEvent(**item))

            for item in SEED_FEEDBACK:
                db.add(MetaAndromedaFeedbackEvent(**item))

        if db.query(MetaAndromedaReleaseRecord).count() == 0:
            for item in SEED_RELEASE_RECORDS:
                db.add(MetaAndromedaReleaseRecord(**item))

        if db.query(MetaAndromedaReleaseEvent).count() == 0:
            for item in SEED_RELEASE_EVENTS:
                db.add(MetaAndromedaReleaseEvent(**item))

        if db.query(MetaAndromedaDriftReport).count() == 0:
            for item in SEED_DRIFT_REPORTS:
                db.add(MetaAndromedaDriftReport(**item))

        db.commit()

    @staticmethod
    def _score_to_list_item(score: MetaAndromedaScoreEvent) -> dict:
        rc = MetaAndromedaRepository._safe_json_dict(score.request_context)
        return {
            "score_event_id": score.id,
            "status": score.status,
            "runtime_job_id": score.runtime_job_id,
            "created_at": score.created_at,
            "queued_at": score.queued_at,
            "started_at": score.started_at,
            "completed_at": score.completed_at,
            "failed_at": score.failed_at,
            "updated_at": score.updated_at,
            "asset_uri": score.asset_uri,
            "asset_type": score.asset_type,
            "asset_id": score.asset_id,
            "preview_url": score.preview_url,
            "request_mode": score.request_mode,
            "objective": score.objective,
            "placement_family": score.placement_family,
            "market": score.market,
            "prediction_mode": score.prediction_mode,
            "overall_score": score.overall_score,
            "roas_band": score.roas_band,
            "model_version": score.model_version,
            "reviewed": score.reviewed,
            "feedback_count": score.feedback_count,
            "latest_feedback_decision": score.latest_feedback_decision,
            "feature_manifest_id": score.feature_manifest_id,
            "error_message": score.error_message,
            "attempt_count": score.attempt_count,
            "source": "analytics" if rc.get("observed_creative_id") else "score_lab",
        }

    @staticmethod
    def _safe_json_dict(value) -> dict:
        """Safely coerce a DB JSON column value to a Python dict."""
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            import json as _json
            try:
                parsed = _json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
        return {}

    @staticmethod
    def _score_to_detail(score: MetaAndromedaScoreEvent) -> dict:
        payload = MetaAndromedaRepository._score_to_list_item(score)
        payload.update(
            {
                "diagnostic_breakdown": score.diagnostic_breakdown or {},
                "roas_prediction": score.roas_prediction,
                "risk_tags": score.risk_tags or [],
                "top_positive_drivers": score.top_positive_drivers or [],
                "top_negative_drivers": score.top_negative_drivers or [],
                "explanations": score.explanations,
                "lineage": score.lineage or {},
                "request_context": MetaAndromedaRepository._safe_json_dict(score.request_context),
            }
        )
        return payload

    @staticmethod
    def _worker_event_to_dict(event: MetaAndromedaWorkerEvent) -> dict:
        return {
            "worker_event_id": event.id,
            "score_event_id": event.score_event_id,
            "event_type": event.event_type,
            "queue_host": event.queue_host,
            "runtime_job_id": event.runtime_job_id,
            "status": event.status,
            "attempt_count": event.attempt_count,
            "message": event.message,
            "event_payload": deepcopy(event.event_payload or {}),
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }

    @staticmethod
    def _dead_letter_to_dict(dead_letter: MetaAndromedaDeadLetter) -> dict:
        return {
            "dead_letter_id": dead_letter.id,
            "score_event_id": dead_letter.score_event_id,
            "queue_host": dead_letter.queue_host,
            "runtime_job_id": dead_letter.runtime_job_id,
            "final_error_message": dead_letter.final_error_message,
            "failure_stage": dead_letter.failure_stage,
            "attempt_count": dead_letter.attempt_count,
            "dead_letter_payload": deepcopy(dead_letter.dead_letter_payload or {}),
            "created_at": dead_letter.created_at.isoformat() if dead_letter.created_at else None,
        }

    @staticmethod
    def _drift_report_to_dict(report: MetaAndromedaDriftReport) -> dict:
        return {
            "drift_report_id": report.id,
            "window_kind": report.window_kind,
            "drift_status": report.drift_status,
            "summary": report.summary,
            "severity": report.severity,
            "triggered_by": report.triggered_by,
            "note": report.note,
            "report_payload": deepcopy(report.report_payload or {}),
            "created_at": report.created_at.isoformat() if report.created_at else None,
        }

    def list_review_queue(self, db: Session, status=None, has_observation=None, roas_band=None, limit=25, page=1, search=None, source=None):
        from sqlalchemy import or_
        query = db.query(MetaAndromedaScoreEvent)
        if status:
            query = query.filter(MetaAndromedaScoreEvent.status == status)
        if roas_band:
            query = query.filter(MetaAndromedaScoreEvent.roas_band == roas_band)
        if source == "analytics":
            query = query.filter(
                MetaAndromedaScoreEvent.request_context["observed_creative_id"].isnot(None)
            )
        elif source == "score_lab":
            query = query.filter(
                MetaAndromedaScoreEvent.request_context["observed_creative_id"].is_(None)
            )
        if has_observation is True:
            cal_exists = (
                db.query(MetaAndromedaCalibrationItem.score_event_id)
                .filter(MetaAndromedaCalibrationItem.score_event_id == MetaAndromedaScoreEvent.id)
                .correlate(MetaAndromedaScoreEvent)
                .exists()
            )
            query = query.filter(cal_exists)
        elif has_observation is False:
            cal_exists = (
                db.query(MetaAndromedaCalibrationItem.score_event_id)
                .filter(MetaAndromedaCalibrationItem.score_event_id == MetaAndromedaScoreEvent.id)
                .correlate(MetaAndromedaScoreEvent)
                .exists()
            )
            query = query.filter(~cal_exists)
        if search:
            pat = f"%{search}%"
            ad_name_match = (
                db.query(MetaAndromedaCalibrationItem.score_event_id)
                .join(MetaAndromedaObservedCreative, MetaAndromedaCalibrationItem.observed_creative_id == MetaAndromedaObservedCreative.id)
                .filter(MetaAndromedaObservedCreative.ad_name.ilike(pat))
                .filter(MetaAndromedaCalibrationItem.score_event_id == MetaAndromedaScoreEvent.id)
                .correlate(MetaAndromedaScoreEvent)
                .exists()
            )
            query = query.filter(
                or_(
                    MetaAndromedaScoreEvent.id.ilike(pat),
                    MetaAndromedaScoreEvent.objective.ilike(pat),
                    MetaAndromedaScoreEvent.placement_family.ilike(pat),
                    MetaAndromedaScoreEvent.market.ilike(pat),
                    ad_name_match,
                )
            )
        total = query.count()
        page = max(1, page)
        offset = (page - 1) * limit
        total_pages = max(1, math.ceil(total / limit))
        rows = query.order_by(MetaAndromedaScoreEvent.created_at.desc()).offset(offset).limit(limit).all()
        cal_ids: set[str] = set()
        if rows:
            matched = (
                db.query(MetaAndromedaCalibrationItem.score_event_id)
                .filter(MetaAndromedaCalibrationItem.score_event_id.in_([r.id for r in rows]))
                .all()
            )
            cal_ids = {m.score_event_id for m in matched}
        ad_name_map: dict[str, str] = {}
        if cal_ids:
            obs_rows = (
                db.query(MetaAndromedaCalibrationItem.score_event_id, MetaAndromedaObservedCreative.ad_name)
                .join(MetaAndromedaObservedCreative, MetaAndromedaCalibrationItem.observed_creative_id == MetaAndromedaObservedCreative.id)
                .filter(MetaAndromedaCalibrationItem.score_event_id.in_(cal_ids))
                .all()
            )
            ad_name_map = {row.score_event_id: row.ad_name for row in obs_rows if row.ad_name}
        items = []
        for row in rows:
            item = self._score_to_list_item(row)
            item["has_observation"] = row.id in cal_ids
            item["ad_name"] = ad_name_map.get(row.id)
            items.append(item)
        return {
            "items": items,
            "summary": {
                "total": total,
                "page": page,
                "total_pages": total_pages,
                "page_size": limit,
                "status_filter": status,
                "roas_band_filter": roas_band,
                "has_observation_filter": has_observation,
            },
        }

    def get_review_queue_detail(self, db: Session, score_event_id: str):
        row = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.id == score_event_id).first()
        if row is None:
            raise KeyError(score_event_id)
        detail = self._score_to_detail(row)
        cal_item = (
            db.query(MetaAndromedaCalibrationItem)
            .filter(MetaAndromedaCalibrationItem.score_event_id == score_event_id)
            .first()
        )
        if cal_item:
            obs = (
                db.query(MetaAndromedaObservedCreative)
                .filter(MetaAndromedaObservedCreative.id == cal_item.observed_creative_id)
                .first()
            )
            detail["observation"] = {
                "prediction_band": cal_item.prediction_band,
                "observed_band": cal_item.observed_band,
                "error": cal_item.error,
                "performance_snapshot": deepcopy(cal_item.performance_snapshot or {}),
                "ad_name": obs.ad_name if obs else None,
                "ad_id": obs.ad_id if obs else None,
                "observation_window_kind": obs.observation_window_kind if obs else None,
                "observation_window_start": obs.observation_window_start if obs else None,
                "observation_window_end": obs.observation_window_end if obs else None,
            }
        else:
            # 若此 ScoreEvent 由成效分析匯入自動建立，request_context 會帶有 observed_creative_id
            # 直接從 ObservedCreative 取得實際成效，不必等 CalibrationItem 同步
            rc = self._safe_json_dict(row.request_context)
            linked_obs_id = rc.get("observed_creative_id")
            obs = None
            if linked_obs_id:
                obs = (
                    db.query(MetaAndromedaObservedCreative)
                    .filter(MetaAndromedaObservedCreative.id == linked_obs_id)
                    .first()
                )
            if obs and obs.performance_snapshot and float((obs.performance_snapshot or {}).get("spend", 0) or 0) > 0:
                pred_band = row.roas_band or "low"
                real_band, _ = _resolve_observed_band(obs.objective, obs.performance_snapshot)
                _band_score = {"low": 1, "mid": 2, "high": 3}
                err = abs(_band_score.get(pred_band, 1) - _band_score.get(real_band, 1))
                detail["observation"] = {
                    "prediction_band": pred_band,
                    "observed_band": real_band,
                    "error": float(err),
                    "performance_snapshot": deepcopy(obs.performance_snapshot or {}),
                    "ad_name": obs.ad_name,
                    "ad_id": obs.ad_id,
                    "observation_window_kind": obs.observation_window_kind,
                    "observation_window_start": obs.observation_window_start,
                    "observation_window_end": obs.observation_window_end,
                }
            else:
                detail["observation"] = None
        return detail

    def get_monitoring_summary(self, db: Session):
        score_rows = db.query(MetaAndromedaScoreEvent).all()
        total = len(score_rows)
        completed_rows = [row for row in score_rows if row.status == "completed"]
        queued = sum(1 for row in score_rows if row.status == "queued")
        failed = sum(1 for row in score_rows if row.status == "failed")
        retrying = sum(1 for row in score_rows if row.attempt_count > 1)
        completed = len(completed_rows)
        observed_total = db.query(MetaAndromedaObservedCreative).count()
        observed_with_asset = (
            db.query(MetaAndromedaObservedCreative)
            .filter(
                (MetaAndromedaObservedCreative.asset_id.isnot(None))
                | (MetaAndromedaObservedCreative.asset_uri.isnot(None))
            )
            .count()
        )
        feedback_events = db.query(MetaAndromedaFeedbackEvent).count()
        worker_events = (
            db.query(MetaAndromedaWorkerEvent)
            .order_by(MetaAndromedaWorkerEvent.created_at.desc())
            .limit(10)
            .all()
        )
        dead_letters = (
            db.query(MetaAndromedaDeadLetter)
            .order_by(MetaAndromedaDeadLetter.created_at.desc())
            .limit(5)
            .all()
        )
        drift_reports = (
            db.query(MetaAndromedaDriftReport)
            .order_by(MetaAndromedaDriftReport.created_at.desc())
            .limit(5)
            .all()
        )
        latest_calibration = (
            db.query(MetaAndromedaCalibrationDataset)
            .order_by(MetaAndromedaCalibrationDataset.created_at.desc())
            .first()
        )
        def _to_naive(dt: datetime) -> datetime | None:
            if dt is None:
                return None
            if dt.tzinfo is not None:
                return dt.replace(tzinfo=None)
            return dt

        latency_samples = []
        queue_markers = []
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for row in score_rows:
            queued_at_naive = _to_naive(row.queued_at)
            started_at_naive = _to_naive(row.started_at)
            completed_at_naive = _to_naive(row.completed_at)
            failed_at_naive = _to_naive(row.failed_at)

            if queued_at_naive:
                queue_markers.append((queued_at_naive, 1))
                queue_end = started_at_naive or completed_at_naive or failed_at_naive or now
                if queue_end:
                    queue_markers.append((queue_end, -1))
            if queued_at_naive and (completed_at_naive or failed_at_naive):
                latency_ms = int(((completed_at_naive or failed_at_naive) - queued_at_naive).total_seconds() * 1000)
                latency_samples.append(max(0, latency_ms))

        queue_markers.sort(key=lambda item: (item[0], -item[1]))
        current_depth = 0
        peak_depth = 0
        for _, delta in queue_markers:
            current_depth += delta
            peak_depth = max(peak_depth, current_depth)

        latency_samples.sort()
        if latency_samples:
            p95_index = max(0, min(len(latency_samples) - 1, math.ceil(len(latency_samples) * 0.95) - 1))
            latency_metrics = {
                "avg": int(sum(latency_samples) / len(latency_samples)),
                "p95": latency_samples[p95_index],
                "max": latency_samples[-1],
            }
        else:
            latency_metrics = {"avg": 0, "p95": 0, "max": 0}

        active_alerts = [
            {
                "severity": report.severity,
                "code": f"drift_{report.drift_status}",
                "message": report.summary,
                "drift_report_id": report.id,
                "window_kind": report.window_kind,
            }
            for report in drift_reports
            if report.drift_status not in ("stable", "healthy")
        ]

        # Phase 5: 象限切換告警
        if len(drift_reports) >= 2:
            _latest_diag = (drift_reports[0].report_payload or {}).get("period_diagnosis") or {}
            _prev_diag   = (drift_reports[1].report_payload or {}).get("period_diagnosis") or {}
            _latest_state = _latest_diag.get("state")
            _prev_state   = _prev_diag.get("state")
            if _latest_state and _prev_state and _latest_state != _prev_state:
                _latest_label = _latest_diag.get("label", _latest_state)
                _prev_label   = _prev_diag.get("label", _prev_state)
                _transition_msg = _TRANSITION_MESSAGES.get(
                    (_prev_state, _latest_state),
                    "投放環境象限發生切換，請留意是否需要調整投放策略。",
                )
                active_alerts.insert(0, {
                    "severity": "medium",
                    "code": "period_state_transition",
                    "message": f"【象限切換】{_prev_label} → {_latest_label}。{_transition_msg}",
                    "from_state": _prev_state,
                    "to_state": _latest_state,
                })
        latest_drift_payload = deepcopy(drift_reports[0].report_payload) if drift_reports else {}
        latest_matched = int(latest_drift_payload.get("total_matched") or 0)
        latest_observed = int(latest_drift_payload.get("total_observed") or 0)
        latest_calibration_candidates = int(latest_drift_payload.get("calibration_candidate_total") or 0)
        return {
            "jobs": {
                "score-request": {
                    "queued_total": total,
                    "completed_total": completed,
                    "failure_total": failed,
                    "queue_depth": {"current": queued, "peak": peak_depth},
                    "latency_ms": latency_metrics,
                }
            },
            "observation_pipeline": {
                "observed_total": observed_total,
                "latest_observed_total": latest_observed,
                "observed_with_asset": observed_with_asset,
                "latest_matched_total": latest_matched,
                "latest_match_rate": round(latest_matched / latest_observed, 4) if latest_observed > 0 else 0.0,
                "latest_calibration_candidate_total": latest_calibration_candidates,
                "latest_calibration_synced_total": latest_calibration.synced_count if latest_calibration else 0,
                "latest_calibration_status": latest_calibration.status if latest_calibration else "not_started",
                "latest_calibration_dataset_id": latest_calibration.id if latest_calibration else None,
            },
            "worker_host": {
                "recent_events": [self._worker_event_to_dict(item) for item in worker_events],
                "dead_letters": [self._dead_letter_to_dict(item) for item in dead_letters],
                "dead_letter_count": db.query(MetaAndromedaDeadLetter).count(),
            },
            "prediction_distribution": {
                "high": db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.roas_band == "high").count(),
                "mid": db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.roas_band == "mid").count(),
                "low": db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.roas_band == "low").count(),
            },
            "active_alerts": active_alerts,
            "latest_drift_reports": [self._drift_report_to_dict(item) for item in drift_reports],
            "notes": [
                f"Score events persisted in DataVue DB: {total}",
                f"Observed creatives persisted in DataVue DB: {observed_total} (observation pipeline only)",
                f"Feedback events persisted in DataVue DB: {feedback_events}",
                f"Retry-involved score events: {retrying}",
                f"Calibration label policy version: {LABEL_POLICY_VERSION}",
                f"Active scoring registry target: {model_registry.get_entry().model_version}",
                "Observation pipeline metrics exclude manual Score Lab uploads unless they are explicitly matched by a drift report.",
                "Monitoring timeline and drift trigger are now available from the shared DataVue host.",
            ],
        }

    def get_score_event_timeline(self, db: Session, score_event_id: str):
        score = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.id == score_event_id).first()
        if score is None:
            raise KeyError(score_event_id)

        worker_events = (
            db.query(MetaAndromedaWorkerEvent)
            .filter(MetaAndromedaWorkerEvent.score_event_id == score_event_id)
            .order_by(MetaAndromedaWorkerEvent.created_at.asc())
            .all()
        )
        dead_letters = (
            db.query(MetaAndromedaDeadLetter)
            .filter(MetaAndromedaDeadLetter.score_event_id == score_event_id)
            .order_by(MetaAndromedaDeadLetter.created_at.asc())
            .all()
        )
        feedback = (
            db.query(MetaAndromedaFeedbackEvent)
            .filter(MetaAndromedaFeedbackEvent.score_event_id == score_event_id)
            .order_by(MetaAndromedaFeedbackEvent.created_at.asc())
            .all()
        )
        return {
            "score_event": self._score_to_detail(score),
            "worker_events": [self._worker_event_to_dict(item) for item in worker_events],
            "dead_letters": [self._dead_letter_to_dict(item) for item in dead_letters],
            "feedback": [
                {
                    "feedback_event_id": item.id,
                    "score_event_id": item.score_event_id,
                    "reviewer_id": item.reviewer_id,
                    "decision": item.decision,
                    "reason_codes": item.reason_codes or [],
                    "comment": item.comment,
                    "created_at": item.created_at.isoformat(),
                }
                for item in feedback
            ],
        }

    def create_drift_report(
        self,
        db: Session,
        window_kind: str,
        triggered_by: str | None = None,
        note: str | None = None,
        since: str | None = None,
        until: str | None = None,
        account_id: str | None = None,
    ):
        # 1. 撈取該窗口的所有 Observed Creative (改用區間重疊比對，避免因時區或邊界跨天導致資料遺漏)
        if window_kind == "custom" and since and until:
            range_str = f"[{since} ~ {until}]"
            note = f"{note} {range_str}" if note else range_str
            q = db.query(MetaAndromedaObservedCreative).filter(
                MetaAndromedaObservedCreative.observation_window_end >= since,
                MetaAndromedaObservedCreative.observation_window_start <= until,
            )
        else:
            q = db.query(MetaAndromedaObservedCreative).filter(
                MetaAndromedaObservedCreative.observation_window_kind == window_kind,
            )
        if account_id:
            q = q.filter(MetaAndromedaObservedCreative.source_account_id == account_id)
        # 排除 spend=0 的記錄（未實際投放），避免污染 Spearman 相關計算
        observed_list = [
            obs for obs in q.all()
            if float((obs.performance_snapshot or {}).get("spend", 0) or 0) > 0
        ]
        
        matched_pairs = []
        correct_count = 0
        total_error = 0.0

        # 區間映射字典
        band_score = {"low": 1, "mid": 2, "high": 3}

        # 動態 ROAS 門檻：只從轉換廣告（非流量/互動/知名度）計算 P33/P67
        # 排除流量廣告，避免大量 ROAS=0 拉低分位數；樣本 < 5 時回退固定門檻
        _roas_values = sorted(
            float(obs.performance_snapshot["roas"])
            for obs in observed_list
            if obs.performance_snapshot
            and obs.performance_snapshot.get("roas") is not None
            and not _is_traffic_objective(_objective_key(obs.objective))
        )
        if len(_roas_values) >= 5:
            _p33 = _roas_values[int(len(_roas_values) * 0.33)]
            _p67 = _roas_values[int(len(_roas_values) * 0.67)]
            roas_thresholds: tuple[float, float] | None = (_p33, _p67)
            roas_threshold_method = "percentile_p33_p67"
        else:
            roas_thresholds = None
            roas_threshold_method = "fixed_fallback"

        # 動態 CTR/CPC 門檻：只從流量/互動/知名度廣告計算 P33/P67；樣本 < 5 時不設門檻
        _traffic_obs = [
            obs for obs in observed_list
            if _is_traffic_objective(_objective_key(obs.objective))
        ]
        ctr_thresholds: tuple[float, float] | None = None
        cpc_thresholds: tuple[float, float] | None = None
        _ctr_values = sorted(
            float(obs.performance_snapshot["ctr"])
            for obs in _traffic_obs
            if obs.performance_snapshot and obs.performance_snapshot.get("ctr")
        )
        if len(_ctr_values) >= 5:
            ctr_thresholds = (
                _ctr_values[int(len(_ctr_values) * 0.33)],
                _ctr_values[int(len(_ctr_values) * 0.67)],
            )
        _cpc_values = sorted(
            float(obs.performance_snapshot["cpc"])
            for obs in _traffic_obs
            if obs.performance_snapshot
            and obs.performance_snapshot.get("cpc")
            and float(obs.performance_snapshot["cpc"]) > 0
        )
        if len(_cpc_values) >= 5:
            # CPC 越低越好：P67（貴的那側）作為 Low/Mid 邊界，P33（便宜的那側）作為 Mid/High 邊界
            cpc_thresholds = (
                _cpc_values[int(len(_cpc_values) * 0.67)],
                _cpc_values[int(len(_cpc_values) * 0.33)],
            )

        # 2. 逐筆進行 Prediction 匹配與比對
        for obs in observed_list:
            pred = None
            
            # 優先嘗試透過 asset.checksum_sha256 進行匹配 (避免因重新下載/上傳而產生的隨機 UUID asset_uri 不一致問題)
            if obs.asset and obs.asset.checksum_sha256:
                # 撈出所有 checksum 相同的 assets
                sibling_assets = db.query(MetaAndromedaAsset.id).filter(
                    MetaAndromedaAsset.checksum_sha256 == obs.asset.checksum_sha256
                ).all()
                sibling_asset_ids = [a[0] for a in sibling_assets] if sibling_assets else []
                
                if sibling_asset_ids:
                    pred = (
                        db.query(MetaAndromedaScoreEvent)
                        .filter(
                            MetaAndromedaScoreEvent.asset_id.in_(sibling_asset_ids),
                            MetaAndromedaScoreEvent.status == "completed"
                        )
                        .order_by(MetaAndromedaScoreEvent.completed_at.desc())
                        .first()
                    )
            
            # 若無 checksum 或沒配到，則 Fallback 使用傳統的 asset_uri 精確匹配
            if not pred and obs.asset_uri:
                pred = (
                    db.query(MetaAndromedaScoreEvent)
                    .filter(
                        MetaAndromedaScoreEvent.asset_uri == obs.asset_uri,
                        MetaAndromedaScoreEvent.status == "completed"
                    )
                    .order_by(MetaAndromedaScoreEvent.completed_at.desc())
                    .first()
                )
                
            if not pred:
                continue
                
            # 提取真實成效 Band（依 objective 路由至對應指標，使用本批次動態門檻）
            real_band, label_detail = _resolve_observed_band(
                obs.objective,
                obs.performance_snapshot,
                roas_thresholds,
                ctr_thresholds=ctr_thresholds,
                cpc_thresholds=cpc_thresholds,
            )
            real_roas = obs.performance_snapshot.get("roas", 0.0) if obs.performance_snapshot else 0.0
                
            pred_band = pred.roas_band or "low"
            
            is_match = (pred_band == real_band)
            if is_match:
                correct_count += 1
                
            # 計算 MAE 誤差 (數值距離)
            err = abs(band_score.get(pred_band, 1) - band_score.get(real_band, 1))
            total_error += err
            
            real_spend = float((obs.performance_snapshot or {}).get("spend", 0) or 0)
            matched_pairs.append({
                "id": obs.id,
                "ad_id": obs.ad_id,
                "ad_name": obs.ad_name,
                "prediction_band": pred_band,
                "observed_band": real_band,
                "real_roas": real_roas,
                "real_spend": real_spend,
                "overall_score": pred.overall_score,
                "primary_metric": label_detail["metric"],
                "primary_metric_value": label_detail["value"],
                "error": err,
                "label_policy_version": LABEL_POLICY_VERSION,
                "label_metric": label_detail["metric"],
            })
            
        # 3. 計算統計指標
        total_matched = len(matched_pairs)
        accuracy = correct_count / total_matched if total_matched > 0 else 0.0
        mae = total_error / total_matched if total_matched > 0 else 0.0
        calibration_candidate_total = sum(1 for item in matched_pairs if item["error"] > 0)

        # Spearman ρ：AI overall_score 排名 vs 主指標排名的相關性
        # 以各廣告的 primary_metric 判斷帳戶類型（purchase→ROAS, lead→CVR/CPL, 其他→CPA）
        # 混合 objective 帳戶以最多筆的指標群組為主
        _metric_counter = Counter(
            p["primary_metric"] for p in matched_pairs
            if p.get("primary_metric") and p.get("primary_metric_value") is not None
        )
        dominant_metric = _metric_counter.most_common(1)[0][0] if _metric_counter else "roas"
        metric_distribution = dict(_metric_counter)

        _eligible = [
            p for p in matched_pairs
            if p.get("primary_metric") == dominant_metric
            and p.get("primary_metric_value") is not None
            and p.get("overall_score") is not None
        ]
        _scores = [float(p["overall_score"])        for p in _eligible]
        _perf   = [float(p["primary_metric_value"]) for p in _eligible]
        spearman_r = _spearman_r(_scores, _perf) if len(_scores) >= 3 else 0.0

        # 主指標分布（用於象限判定的 P50 基準）
        _perf_all = sorted(
            float(p["primary_metric_value"]) for p in matched_pairs
            if p.get("primary_metric") == dominant_metric
            and p.get("primary_metric_value") is not None
        )
        perf_median = _perf_all[len(_perf_all) // 2] if _perf_all else 0.0
        perf_std = statistics.stdev(_perf_all) if len(_perf_all) >= 2 else 0.0
        perf_is_high = perf_median >= (sum(_perf_all) / len(_perf_all)) if _perf_all else False

        period_diagnosis = _classify_period_state(spearman_r, perf_is_high, dominant_metric)
        metric_label = _METRIC_LABEL.get(dominant_metric, dominant_metric.upper())

        # 4. 判定漂移健康度（主判據：Spearman ρ；輔助資訊：accuracy/MAE）
        if total_matched < 5:
            drift_status = "insufficient_data"
            severity = "info"

            total_observed = len(observed_list)
            obs_with_asset = sum(1 for obs in observed_list if obs.asset_id or obs.asset_uri)
            total_completed_scores = db.query(MetaAndromedaScoreEvent).filter(
                MetaAndromedaScoreEvent.status == "completed"
            ).count()
            total_failed_scores = db.query(MetaAndromedaScoreEvent).filter(
                MetaAndromedaScoreEvent.status == "failed"
            ).count()
            total_pending_scores = db.query(MetaAndromedaScoreEvent).filter(
                MetaAndromedaScoreEvent.status.in_(["queued", "started", "processing"])
            ).count()

            summary = (
                f"數據量不足 (僅成功匹配 {total_matched} 筆)。"
                f"診斷：區間內匯入廣告 {total_observed} 筆，"
                f"其中 {obs_with_asset} 筆具有素材檔案。"
                f"Prediction / ScoreEvent 累積統計：{total_completed_scores} 筆已完成，"
                f"{total_failed_scores} 筆失敗，{total_pending_scores} 筆處理/排隊中。"
                "請確認素材是否已在評分工作台完成評估，或確認背景任務與 AI 服務是否正常運作。"
            )
        elif spearman_r >= 0.30:
            drift_status = "healthy"
            severity = "info"
            summary = (
                f"模型排名能力穩定 (ρ={spearman_r:.3f}, Accuracy: {accuracy:.1%})，"
                f"創意評分與實際 {metric_label} 排名具正相關，"
                f"投放狀態：{period_diagnosis['label']}。"
            )
        elif spearman_r >= 0.10:
            drift_status = "warning"
            severity = "medium"
            summary = (
                f"模型排名能力偏弱 (ρ={spearman_r:.3f}, Accuracy: {accuracy:.1%})，"
                f"創意評分與 {metric_label} 排名相關性不足，"
                f"投放狀態：{period_diagnosis['label']}。請密切關注。"
            )
        else:
            drift_status = "drifted"
            severity = "high"
            summary = (
                f"模型排名能力已失效 (ρ={spearman_r:.3f}, Accuracy: {accuracy:.1%})，"
                f"創意評分無法有效預測相對 {metric_label} 表現，建議進行資料校準。"
            )
    
        # 5. 寫入資料庫
        report = MetaAndromedaDriftReport(
            window_kind=window_kind,
            drift_status=drift_status,
            summary=summary,
            severity=severity,
            triggered_by=triggered_by,
            note=note,
            report_payload={
                "total_observed": len(observed_list),
                "total_matched": total_matched,
                "match_rate": round(total_matched / len(observed_list), 4) if observed_list else 0.0,
                "obs_with_asset": sum(1 for obs in observed_list if obs.asset_id or obs.asset_uri),
                "total_completed_scores": db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.status == "completed").count(),
                "total_failed_scores": db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.status == "failed").count(),
                "total_pending_scores": db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.status.in_(["queued", "started", "processing"])).count(),
                "accuracy": round(accuracy, 4),
                "mae": round(mae, 4),
                "spearman_r": round(spearman_r, 4),
                "dominant_metric": dominant_metric,
                "metric_distribution": metric_distribution,
                "perf_median": round(perf_median, 4),
                "perf_std": round(perf_std, 4),
                "period_diagnosis": period_diagnosis,
                "calibration_candidate_total": calibration_candidate_total,
                "label_policy_version": LABEL_POLICY_VERSION,
                "roas_band_thresholds": {
                    "low_below": round(roas_thresholds[0], 2) if roas_thresholds else _ROAS_FALLBACK_LOW,
                    "high_above": round(roas_thresholds[1], 2) if roas_thresholds else _ROAS_FALLBACK_HIGH,
                    "method": roas_threshold_method,
                    "sample_count": len(_roas_values),
                },
                "ctr_band_thresholds": {
                    "low_below": round(ctr_thresholds[0], 4) if ctr_thresholds else None,
                    "high_above": round(ctr_thresholds[1], 4) if ctr_thresholds else None,
                    "sample_count": len(_ctr_values),
                },
                "cpc_band_thresholds": {
                    "low_above": round(cpc_thresholds[0], 2) if cpc_thresholds else None,
                    "high_below": round(cpc_thresholds[1], 2) if cpc_thresholds else None,
                    "sample_count": len(_cpc_values),
                },
                "traffic_ad_total": len(_traffic_obs),
                "matched_details": matched_pairs,
                "since": since,
                "until": until,
                "account_id": account_id,
            }
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        
        return self._drift_report_to_dict(report)

    def get_release_overview(self, db: Session):
        # 若資料表為空，主動執行一次種子數據播種
        if db.query(MetaAndromedaReleaseRecord).count() == 0:
            try:
                self.ensure_seed_data(db)
            except Exception as e:
                logger.error("[MetaAndromeda] Auto-seeding on release overview request failed: %s", e)

        records = db.query(MetaAndromedaReleaseRecord).all()
        
        # 安全獲取 record，避免 StopIteration 導致 500 錯誤
        current = next((item for item in records if item.record_kind == "current_production"), None)
        previous = next((item for item in records if item.record_kind == "previous_production"), None)
        candidates = [item for item in records if item.record_kind == "candidate"]
        history = db.query(MetaAndromedaReleaseEvent).order_by(MetaAndromedaReleaseEvent.created_at.desc()).all()
        latest_calibration = (
            db.query(MetaAndromedaCalibrationDataset)
            .order_by(MetaAndromedaCalibrationDataset.created_at.desc())
            .first()
        )
        
        # 回傳 dict 封裝與預設備用 fallback
        current_dict = self._release_record_to_dict(current) if current else {
            "model_version": "prod_v2026_05_28",
            "release_status": "production",
            "approved_by": "system",
            "approved_at": "",
            "pairwise_ranking_accuracy": 0.85,
            "mean_band_error": 0.15,
        }
        previous_dict = self._release_record_to_dict(previous) if previous else {
            "model_version": "prod_v2026_05_12",
            "release_status": "archived",
            "approved_by": "system",
            "approved_at": "",
            "pairwise_ranking_accuracy": 0.82,
            "mean_band_error": 0.18,
        }

        return {
            "current_production": current_dict,
            "previous_production": previous_dict,
            "candidates": [self._release_record_to_dict(item) for item in candidates],
            "history": [self._release_event_to_dict(item) for item in history],
            "notes": [
                "Release actions now persist to DataVue DB.",
                "Release metadata is now aligned with the Meta Andromeda registry source of truth.",
                (
                    f"Latest calibration dataset: {latest_calibration.id} "
                    f"({latest_calibration.synced_count} items, policy {latest_calibration.label_policy_version})"
                    if latest_calibration
                    else "No calibration dataset has been materialized yet."
                ),
                *model_registry.list_registry_notes(
                    [current_dict["model_version"], previous_dict["model_version"], *[item.model_version for item in candidates]]
                ),
            ],
        }

    @staticmethod
    def _release_record_to_dict(record: MetaAndromedaReleaseRecord) -> dict:
        payload = {
            "model_version": record.model_version,
            "release_status": record.release_status,
            "approved_by": record.approved_by or "",
            "approved_at": record.approved_at or "",
            "pairwise_ranking_accuracy": record.pairwise_ranking_accuracy,
            "mean_band_error": record.mean_band_error,
        }
        if record.record_kind == "candidate":
            payload["created_at"] = record.created_at
            payload["promotion_gate_summary"] = deepcopy(record.promotion_gate_summary or {})
        return payload

    @staticmethod
    def _release_event_to_dict(event: MetaAndromedaReleaseEvent) -> dict:
        return {
            "action": event.action,
            "model_version": event.model_version,
            "actor": event.actor,
            "created_at": event.created_at,
            "note": event.note or "",
        }

    def get_asset_by_uri(self, db: Session, asset_uri: str) -> MetaAndromedaAsset | None:
        """根據 asset_uri 查詢已上傳的 MetaAndromedaAsset"""
        return db.query(MetaAndromedaAsset).filter(MetaAndromedaAsset.asset_uri == asset_uri).first()

    def create_uploaded_asset(self, db: Session, asset_record: dict):
        asset = MetaAndromedaAsset(**asset_record)
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return {
            "asset_uri": asset.asset_uri,
            "asset_id": asset.id,
            "storage_backend": asset.storage_backend,
            "storage_key": asset.storage_key,
            "asset_type": asset.asset_type,
            "checksum_sha256": asset.checksum_sha256,
            "upload_status": asset.upload_status,
            "source_filename": asset.source_filename,
            "file_size_bytes": asset.file_size_bytes,
            "public_url": asset.public_url,
            "uploaded_at": asset.uploaded_at.isoformat(),
        }

    def create_observed_creative(self, db: Session, observed_record: dict):
        existing = db.query(MetaAndromedaObservedCreative).filter(
            MetaAndromedaObservedCreative.id == observed_record["id"]
        ).first()

        if existing:
            for key, val in observed_record.items():
                if key != "id":
                    setattr(existing, key, val)
            db.commit()
            db.refresh(existing)
            observed = existing
        else:
            observed = MetaAndromedaObservedCreative(**observed_record)
            db.add(observed)
            db.commit()
            db.refresh(observed)
        return {
            "observed_creative_id": observed.id,
            "asset_id": observed.asset_id,
            "asset_uri": observed.asset_uri,
            "source_platform": observed.source_platform,
            "source_account_id": observed.source_account_id,
            "campaign_id": observed.campaign_id,
            "adset_id": observed.adset_id,
            "ad_id": observed.ad_id,
            "ad_name": observed.ad_name,
            "objective": observed.objective,
            "placement_family": observed.placement_family,
            "market": observed.market,
            "primary_text": observed.primary_text,
            "headline": observed.headline,
            "cta": observed.cta,
            "media_url": observed.media_url,
            "media_type": observed.media_type,
            "performance_snapshot": deepcopy(observed.performance_snapshot or {}),
            "observation_window_kind": observed.observation_window_kind,
            "observation_window_start": observed.observation_window_start,
            "observation_window_end": observed.observation_window_end,
            "source_fetched_at": observed.source_fetched_at,
            "lineage": deepcopy(observed.lineage or {}),
            "created_at": observed.created_at.isoformat() if observed.created_at else None,
        }

    def get_observed_creative(self, db: Session, observed_creative_id: str):
        observed = (
            db.query(MetaAndromedaObservedCreative)
            .filter(MetaAndromedaObservedCreative.id == observed_creative_id)
            .first()
        )
        if observed is None:
            return None
        return {
            "observed_creative_id": observed.id,
            "asset_id": observed.asset_id,
            "asset_uri": observed.asset_uri,
            "media_type": observed.media_type,
            "created_at": observed.created_at.isoformat() if observed.created_at else None,
        }

    def get_latest_score_event_for_observation(self, db: Session, observed_creative_id: str):
        score = (
            db.query(MetaAndromedaScoreEvent)
            .filter(
                MetaAndromedaScoreEvent.request_context["observed_creative_id"].as_string() == observed_creative_id
            )
            .order_by(MetaAndromedaScoreEvent.created_at.desc())
            .first()
        )
        if score is None:
            observed = self.get_observed_creative(db, observed_creative_id)
            if not observed or not observed.get("asset_uri"):
                return None
            score = (
                db.query(MetaAndromedaScoreEvent)
                .filter(MetaAndromedaScoreEvent.asset_uri == observed["asset_uri"])
                .order_by(MetaAndromedaScoreEvent.created_at.desc())
                .first()
            )
            if score is None:
                return None
        return self._score_to_detail(score)

    def create_score_event(self, db: Session, score_payload: dict):
        score = MetaAndromedaScoreEvent(
            id=score_payload["score_event_id"],
            status=score_payload["status"],
            runtime_job_id=score_payload.get("runtime_job_id"),
            created_at=score_payload["created_at"],
            queued_at=score_payload["queued_at"],
            started_at=score_payload.get("started_at"),
            completed_at=score_payload.get("completed_at"),
            failed_at=score_payload.get("failed_at"),
            updated_at=score_payload["updated_at"],
            asset_uri=score_payload["asset_uri"],
            asset_type=score_payload["asset_type"],
            asset_id=score_payload.get("asset_id"),
            preview_url=score_payload.get("preview_url"),
            request_mode=score_payload["request_mode"],
            objective=score_payload["objective"],
            placement_family=score_payload["placement_family"],
            market=score_payload["market"],
            prediction_mode=score_payload.get("prediction_mode"),
            overall_score=score_payload.get("overall_score"),
            roas_band=score_payload.get("roas_band"),
            model_version=score_payload.get("model_version"),
            reviewed=False,
            feedback_count=0,
            latest_feedback_decision=None,
            feature_manifest_id=score_payload.get("feature_manifest_id"),
            error_message=score_payload.get("error_message"),
            attempt_count=score_payload.get("attempt_count", 0),
            diagnostic_breakdown=score_payload.get("diagnostic_breakdown", {}),
            roas_prediction=score_payload.get("roas_prediction"),
            risk_tags=score_payload.get("risk_tags", []),
            top_positive_drivers=score_payload.get("top_positive_drivers", []),
            top_negative_drivers=score_payload.get("top_negative_drivers", []),
            explanations=score_payload.get("explanations"),
            lineage=score_payload.get("lineage", {}),
            request_context=score_payload.get("request_context", {}),
        )
        db.add(score)
        db.commit()
        db.refresh(score)
        return self._score_to_detail(score)

    def assign_runtime_job(self, db: Session, score_event_id: str, runtime_job_id: str):
        score = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.id == score_event_id).first()
        if score is None:
            raise KeyError(score_event_id)
        score.runtime_job_id = runtime_job_id
        score.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(score)
        return self._score_to_detail(score)

    def log_worker_event(
        self,
        db: Session,
        score_event_id: str,
        event_type: str,
        queue_host: str,
        status: str,
        runtime_job_id: str | None = None,
        attempt_count: int = 0,
        message: str | None = None,
        event_payload: dict | None = None,
    ) -> dict:
        event = MetaAndromedaWorkerEvent(
            score_event_id=score_event_id,
            event_type=event_type,
            queue_host=queue_host,
            runtime_job_id=runtime_job_id,
            status=status,
            attempt_count=attempt_count,
            message=message,
            event_payload=event_payload or {},
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return self._worker_event_to_dict(event)

    def find_worker_event(
        self,
        db: Session,
        *,
        score_event_id: str,
        event_type: str,
        runtime_job_id: str | None = None,
        receipt_id: str | None = None,
    ) -> dict | None:
        query = db.query(MetaAndromedaWorkerEvent).filter(
            MetaAndromedaWorkerEvent.score_event_id == score_event_id,
            MetaAndromedaWorkerEvent.event_type == event_type,
        )
        if runtime_job_id is not None:
            query = query.filter(MetaAndromedaWorkerEvent.runtime_job_id == runtime_job_id)
        events = query.order_by(MetaAndromedaWorkerEvent.created_at.desc()).all()
        for event in events:
            payload = event.event_payload or {}
            if receipt_id is None or payload.get("receipt_id") == receipt_id:
                return self._worker_event_to_dict(event)
        return None

    def create_dead_letter(
        self,
        db: Session,
        score_event_id: str,
        queue_host: str,
        runtime_job_id: str | None,
        failure_stage: str,
        attempt_count: int,
        final_error_message: str,
        dead_letter_payload: dict | None = None,
    ) -> dict:
        dead_letter = MetaAndromedaDeadLetter(
            score_event_id=score_event_id,
            queue_host=queue_host,
            runtime_job_id=runtime_job_id,
            failure_stage=failure_stage,
            attempt_count=attempt_count,
            final_error_message=final_error_message,
            dead_letter_payload=dead_letter_payload or {},
        )
        db.add(dead_letter)
        db.commit()
        db.refresh(dead_letter)
        return self._dead_letter_to_dict(dead_letter)

    def mark_score_processing(self, db: Session, score_event_id: str):
        now = datetime.now(timezone.utc)
        updated = (
            db.query(MetaAndromedaScoreEvent)
            .filter(
                MetaAndromedaScoreEvent.id == score_event_id,
                MetaAndromedaScoreEvent.status == "queued",
            )
            .update(
                {
                    MetaAndromedaScoreEvent.status: "processing",
                    MetaAndromedaScoreEvent.started_at: now,
                    MetaAndromedaScoreEvent.updated_at: now,
                    MetaAndromedaScoreEvent.attempt_count: MetaAndromedaScoreEvent.attempt_count + 1,
                },
                synchronize_session=False,
            )
        )
        if updated == 0:
            score = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.id == score_event_id).first()
            if score is None:
                raise KeyError(score_event_id)
            return None
        db.commit()
        score = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.id == score_event_id).first()
        db.refresh(score)
        return self._score_to_detail(score)

    def mark_score_completed(self, db: Session, score_event_id: str, result_payload: dict):
        score = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.id == score_event_id).first()
        if score is None:
            raise KeyError(score_event_id)
        if score.status in TERMINAL_SCORE_STATUSES:
            return self._score_to_detail(score)
        now = datetime.now(timezone.utc)
        score.status = result_payload["status"]
        score.prediction_mode = result_payload.get("prediction_mode")
        score.overall_score = result_payload.get("overall_score")
        score.roas_band = result_payload.get("roas_band")
        score.model_version = result_payload.get("model_version")
        score.feature_manifest_id = result_payload.get("feature_manifest_id")
        score.error_message = result_payload.get("error_message")
        score.diagnostic_breakdown = result_payload.get("diagnostic_breakdown", {})
        score.roas_prediction = result_payload.get("roas_prediction")
        score.risk_tags = result_payload.get("risk_tags", [])
        score.top_positive_drivers = result_payload.get("top_positive_drivers", [])
        score.top_negative_drivers = result_payload.get("top_negative_drivers", [])
        score.explanations = result_payload.get("explanations")
        score.lineage = result_payload.get("lineage", {})
        score.completed_at = now
        score.failed_at = None
        score.updated_at = now
        db.commit()
        db.refresh(score)
        return self._score_to_detail(score)

    def mark_score_failed(self, db: Session, score_event_id: str, error_message: str):
        score = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.id == score_event_id).first()
        if score is None:
            raise KeyError(score_event_id)
        if score.status in TERMINAL_SCORE_STATUSES:
            return self._score_to_detail(score)
        now = datetime.now(timezone.utc)
        score.status = "failed"
        score.error_message = error_message
        score.failed_at = now
        score.updated_at = now
        db.commit()
        db.refresh(score)
        return self._score_to_detail(score)

    def requeue_score_event(self, db: Session, score_event_id: str, error_message: str):
        score = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.id == score_event_id).first()
        if score is None:
            raise KeyError(score_event_id)
        now = datetime.now(timezone.utc)
        score.status = "queued"
        score.error_message = error_message
        score.updated_at = now
        db.commit()
        db.refresh(score)
        return self._score_to_detail(score)

    def list_feedback(self, db: Session, score_event_id: str):
        score = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.id == score_event_id).first()
        if score is None:
            raise KeyError(score_event_id)
        feedback = (
            db.query(MetaAndromedaFeedbackEvent)
            .filter(MetaAndromedaFeedbackEvent.score_event_id == score_event_id)
            .order_by(MetaAndromedaFeedbackEvent.created_at.asc())
            .all()
        )
        return {
            "score_event_id": score_event_id,
            "feedback": [
                {
                    "feedback_event_id": item.id,
                    "score_event_id": item.score_event_id,
                    "reviewer_id": item.reviewer_id,
                    "decision": item.decision,
                    "reason_codes": item.reason_codes or [],
                    "comment": item.comment,
                    "created_at": item.created_at.isoformat(),
                }
                for item in feedback
            ],
        }

    def submit_feedback(self, db: Session, score_event_id: str, reviewer_id: str, decision: str, reason_codes=None, comment=None):
        score = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.id == score_event_id).first()
        if score is None:
            raise KeyError(score_event_id)

        feedback = MetaAndromedaFeedbackEvent(
            score_event_id=score_event_id,
            reviewer_id=reviewer_id,
            decision=decision,
            reason_codes=reason_codes or [],
            comment=comment,
        )
        score.reviewed = True
        score.feedback_count += 1
        score.latest_feedback_decision = decision
        score.updated_at = datetime.now(timezone.utc)
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return {
            "feedback_event_id": feedback.id,
            "score_event_id": feedback.score_event_id,
            "reviewer_id": feedback.reviewer_id,
            "decision": feedback.decision,
            "reason_codes": feedback.reason_codes or [],
            "comment": feedback.comment,
            "created_at": feedback.created_at.isoformat(),
        }

    def perform_release_action(self, db: Session, action: str, model_version: str, actor: str, note: str | None):
        current = db.query(MetaAndromedaReleaseRecord).filter(MetaAndromedaReleaseRecord.record_kind == "current_production").first()
        previous = db.query(MetaAndromedaReleaseRecord).filter(MetaAndromedaReleaseRecord.record_kind == "previous_production").first()
        candidate = (
            db.query(MetaAndromedaReleaseRecord)
            .filter(
                MetaAndromedaReleaseRecord.record_kind == "candidate",
                MetaAndromedaReleaseRecord.model_version == model_version,
            )
            .first()
        )

        created_at = datetime.now(timezone.utc).isoformat()
        if action in {"approve", "reject"} and candidate is None:
            raise KeyError(model_version)

        if action == "approve":
            previous.model_version = current.model_version
            previous.release_status = "superseded"
            previous.approved_by = current.approved_by
            previous.approved_at = current.approved_at
            previous.created_at = current.created_at
            previous.pairwise_ranking_accuracy = current.pairwise_ranking_accuracy
            previous.mean_band_error = current.mean_band_error

            current.model_version = candidate.model_version
            current.release_status = "production"
            current.approved_by = actor
            current.approved_at = created_at
            current.created_at = created_at
            current.pairwise_ranking_accuracy = candidate.pairwise_ranking_accuracy
            current.mean_band_error = candidate.mean_band_error
            candidate.release_status = "approved"
        elif action == "reject":
            candidate.release_status = "rejected"
        elif action == "rollback":
            current_snapshot = {
                "model_version": current.model_version,
                "approved_by": current.approved_by,
                "approved_at": current.approved_at,
                "created_at": current.created_at,
                "pairwise_ranking_accuracy": current.pairwise_ranking_accuracy,
                "mean_band_error": current.mean_band_error,
            }
            current.model_version = previous.model_version
            current.release_status = "production"
            current.approved_by = actor
            current.approved_at = created_at
            current.created_at = created_at
            current.pairwise_ranking_accuracy = previous.pairwise_ranking_accuracy
            current.mean_band_error = previous.mean_band_error

            previous.model_version = current_snapshot["model_version"]
            previous.release_status = "superseded"
            previous.approved_by = current_snapshot["approved_by"]
            previous.approved_at = current_snapshot["approved_at"]
            previous.created_at = current_snapshot["created_at"]
            previous.pairwise_ranking_accuracy = current_snapshot["pairwise_ranking_accuracy"]
            previous.mean_band_error = current_snapshot["mean_band_error"]

        event = MetaAndromedaReleaseEvent(
            action=action,
            model_version=model_version,
            actor=actor,
            note=note,
            created_at=created_at,
        )
        db.add(event)
        db.commit()
        return {
            "status": "ok",
            "action": action,
            "model_version": model_version,
            "actor": actor,
            "created_at": created_at,
            "note": note,
        }

    def sync_calibration_dataset(
        self,
        db: Session,
        window_kind: str,
        excluded_observed_ids: list[str],
    ) -> dict:
        # 1. 撈取該窗口的所有 Observed Creative
        observed_list = (
            db.query(MetaAndromedaObservedCreative)
            .filter(MetaAndromedaObservedCreative.observation_window_kind == window_kind)
            .all()
        )
        
        import uuid
        dataset_id = f"cal_ds_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        synced_count = 0
        matched_count = 0
        band_score = {"low": 1, "mid": 2, "high": 3}
        dataset = MetaAndromedaCalibrationDataset(
            id=dataset_id,
            window_kind=window_kind,
            status="no_data_to_sync",
            label_policy_version=LABEL_POLICY_VERSION,
            excluded_observed_ids=excluded_observed_ids or [],
            synced_count=0,
            summary={},
        )
        db.add(dataset)
        
        # 2. 篩選有偏差且未被排除的進行標記
        for obs in observed_list:
            if obs.id in excluded_observed_ids:
                continue
            # 排除 spend=0 的記錄（廣告未實際投放，成效數據無意義）
            if float((obs.performance_snapshot or {}).get("spend", 0) or 0) <= 0:
                continue
            if not obs.asset_uri:
                continue
                
            # 尋找匹配的 Completed ScoreEvent
            pred = (
                db.query(MetaAndromedaScoreEvent)
                .filter(
                    MetaAndromedaScoreEvent.asset_uri == obs.asset_uri,
                    MetaAndromedaScoreEvent.status == "completed"
                )
                .order_by(MetaAndromedaScoreEvent.completed_at.desc())
                .first()
            )
            
            if not pred:
                continue
            matched_count += 1
                
            real_band, label_detail = _resolve_observed_band(obs.objective, obs.performance_snapshot)
                
            pred_band = pred.roas_band or "low"
            
            # 只有有偏差的才需要校準
            err = abs(band_score.get(pred_band, 1) - band_score.get(real_band, 1))
            if err > 0:
                item_id = f"cal_item_{uuid.uuid4().hex[:12]}"
                # 更新 lineage
                lineage = deepcopy(obs.lineage or {})
                lineage["calibration"] = {
                    "dataset_id": dataset_id,
                    "synced_at": datetime.now(timezone.utc).isoformat(),
                    "prediction_band": pred_band,
                    "observed_band": real_band,
                    "error": err,
                    "label_policy_version": LABEL_POLICY_VERSION,
                    "label_metric": label_detail["metric"],
                }
                obs.lineage = lineage
                db.add(
                    MetaAndromedaCalibrationItem(
                        id=item_id,
                        dataset_id=dataset_id,
                        observed_creative_id=obs.id,
                        score_event_id=pred.id,
                        asset_uri=obs.asset_uri,
                        objective=obs.objective,
                        market=obs.market,
                        placement_family=obs.placement_family,
                        prediction_band=pred_band,
                        observed_band=real_band,
                        error=float(err),
                        performance_snapshot=deepcopy(obs.performance_snapshot or {}),
                        label_policy_version=LABEL_POLICY_VERSION,
                    )
                )
                synced_count += 1
        dataset.synced_count = synced_count
        dataset.status = "queued_for_calibration" if synced_count > 0 else "no_data_to_sync"
        dataset.summary = {
            "matched_count": matched_count,
            "excluded_count": len(excluded_observed_ids or []),
            "label_policy_version": LABEL_POLICY_VERSION,
        }
        db.commit()
            
        return {
            "dataset_id": dataset_id,
            "synced_count": synced_count,
            "status": dataset.status,
            "item_count": synced_count,
            "label_policy_version": LABEL_POLICY_VERSION,
        }

    @staticmethod
    def list_observed_accounts(db: Session) -> list[dict]:
        from sqlalchemy import func
        rows = (
            db.query(
                MetaAndromedaObservedCreative.source_account_id,
                MetaAndromedaObservedCreative.source_platform,
                func.count(MetaAndromedaObservedCreative.id).label("total_creatives"),
                func.max(MetaAndromedaObservedCreative.created_at).label("last_imported_at"),
            )
            .group_by(
                MetaAndromedaObservedCreative.source_account_id,
                MetaAndromedaObservedCreative.source_platform,
            )
            .order_by(func.max(MetaAndromedaObservedCreative.created_at).desc())
            .all()
        )
        return [
            {
                "account_id": r.source_account_id,
                "platform": r.source_platform,
                "total_creatives": r.total_creatives,
                "last_imported_at": r.last_imported_at.isoformat() if r.last_imported_at else None,
            }
            for r in rows
        ]

    @staticmethod
    def get_drift_trend(db: Session, limit: int = 20, account_id: str | None = None) -> list[dict]:
        # 只取有足夠資料完成象限診斷的報告，排除：
        # 1. insufficient_data（配對數 < 5，無法計算 ρ）
        # 2. Phase 1 之前的舊報告（report_payload 無 period_diagnosis）
        query = db.query(MetaAndromedaDriftReport).filter(
            MetaAndromedaDriftReport.drift_status != "insufficient_data"
        )
        # account_id 隔離：在 DB 層過濾，確保無 account_id 的舊報告不會洩漏
        if account_id:
            query = query.filter(
                MetaAndromedaDriftReport.report_payload["account_id"].as_string() == account_id
            )
        rows = (
            query
            .order_by(MetaAndromedaDriftReport.created_at.desc())
            .limit(limit * 3)
            .all()
        )
        rows = list(reversed(rows))
        result = []
        for r in rows:
            p = r.report_payload or {}
            diagnosis = p.get("period_diagnosis") or {}
            period_state = diagnosis.get("state")
            # 跳過無象限診斷的舊報告（Phase 1 前建立）
            if not period_state:
                continue
            result.append({
                "drift_report_id": r.id,
                "window_kind": r.window_kind,
                "drift_status": r.drift_status,
                "note": r.note,
                "account_id": p.get("account_id"),
                "spearman_r": p.get("spearman_r"),
                "perf_median": p.get("perf_median"),
                "dominant_metric": p.get("dominant_metric"),
                "period_state": period_state,
                "period_label": diagnosis.get("label"),
                "creative_explained_variance": diagnosis.get("creative_explained_variance"),
                "total_matched": p.get("total_matched"),
                "since": p.get("since"),
                "until": p.get("until"),
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
        return result[:limit]

    @staticmethod
    def list_scoring_profiles(db: Session) -> list[dict]:
        rows = (
            db.query(MetaAndromedaScoringProfile)
            .order_by(MetaAndromedaScoringProfile.created_at.desc())
            .all()
        )
        return [
            {
                "profile_name": r.profile_name,
                "source": r.source,
                "base_profile_name": r.base_profile_name,
                "calibration_dataset_id": r.calibration_dataset_id,
                "is_promoted": r.is_promoted,
                "promoted_at": r.promoted_at.isoformat() if r.promoted_at else None,
                "bias_summary": r.bias_summary,
                "calibration_guidance": r.calibration_guidance,
                "few_shot_example_count": len(r.few_shot_examples or []),
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    @staticmethod
    def promote_scoring_profile(db: Session, profile_name: str) -> dict:
        from datetime import datetime, timezone
        target = db.query(MetaAndromedaScoringProfile).filter(
            MetaAndromedaScoringProfile.profile_name == profile_name
        ).first()
        if target is None:
            raise KeyError(f"Scoring profile not found: {profile_name}")

        db.query(MetaAndromedaScoringProfile).filter(
            MetaAndromedaScoringProfile.is_promoted == True  # noqa: E712
        ).update({"is_promoted": False, "promoted_at": None}, synchronize_session=False)

        now = datetime.now(timezone.utc)
        target.is_promoted = True
        target.promoted_at = now
        db.add(target)
        db.commit()

        from .runtime import invalidate_prompt_cache
        invalidate_prompt_cache()  # clear all so next scoring re-queries the promoted profile

        return {
            "profile_name": target.profile_name,
            "is_promoted": True,
            "promoted_at": now.isoformat(),
        }


repository = MetaAndromedaRepository()
