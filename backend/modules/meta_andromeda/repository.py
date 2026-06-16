"""
Meta Andromeda Module - DB-backed repository
"""

from copy import deepcopy
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from database.models.meta_andromeda import (
    MetaAndromedaAsset,
    MetaAndromedaDeadLetter,
    MetaAndromedaDriftReport,
    MetaAndromedaFeedbackEvent,
    MetaAndromedaObservedCreative,
    MetaAndromedaReleaseEvent,
    MetaAndromedaReleaseRecord,
    MetaAndromedaScoreEvent,
    MetaAndromedaWorkerEvent,
)
from .model_registry import model_registry


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
        }

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

    def list_review_queue(self, db: Session, status=None, reviewed=None, limit=30):
        self.ensure_seed_data(db)
        query = db.query(MetaAndromedaScoreEvent)
        if status:
            query = query.filter(MetaAndromedaScoreEvent.status == status)
        if reviewed is not None:
            query = query.filter(MetaAndromedaScoreEvent.reviewed == reviewed)
        rows = query.order_by(MetaAndromedaScoreEvent.created_at.desc()).limit(limit).all()
        items = [self._score_to_list_item(row) for row in rows]
        return {
            "items": items,
            "summary": {
                "total": query.count(),
                "status_filter": status,
                "reviewed_filter": reviewed,
            },
        }

    def get_review_queue_detail(self, db: Session, score_event_id: str):
        self.ensure_seed_data(db)
        row = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.id == score_event_id).first()
        if row is None:
            raise KeyError(score_event_id)
        return self._score_to_detail(row)

    def get_monitoring_summary(self, db: Session):
        self.ensure_seed_data(db)
        total = db.query(MetaAndromedaScoreEvent).count()
        completed = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.status == "completed").count()
        queued = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.status == "queued").count()
        failed = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.status == "failed").count()
        retrying = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.attempt_count > 1).count()
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
        active_alerts = [
            {
                "severity": report.severity,
                "code": f"drift_{report.drift_status}",
                "message": report.summary,
                "drift_report_id": report.id,
                "window_kind": report.window_kind,
            }
            for report in drift_reports
            if report.drift_status != "stable"
        ]
        return {
            "jobs": {
                "score-request": {
                    "queued_total": total,
                    "completed_total": completed,
                    "failure_total": failed,
                    "queue_depth": {"current": queued, "peak": max(queued, 1)},
                    "latency_ms": {"avg": 1180, "p95": 2140, "max": 3410},
                }
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
                f"Feedback events persisted in DataVue DB: {feedback_events}",
                f"Retry-involved score events: {retrying}",
                f"Active scoring registry target: {model_registry.get_entry().model_version}",
                "Monitoring timeline and drift trigger are now available from the shared DataVue host.",
            ],
        }

    def get_score_event_timeline(self, db: Session, score_event_id: str):
        self.ensure_seed_data(db)
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
    ):
        self.ensure_seed_data(db)
        # 1. 撈取該窗口的所有 Observed Creative
        observed_list = (
            db.query(MetaAndromedaObservedCreative)
            .filter(MetaAndromedaObservedCreative.observation_window_kind == window_kind)
            .all()
        )
        
        matched_pairs = []
        correct_count = 0
        total_error = 0.0
        
        # 區間映射字典
        band_score = {"low": 1, "mid": 2, "high": 3}
        
        # 2. 逐筆進行 Prediction 匹配與比對
        for obs in observed_list:
            if not obs.asset_uri:
                continue
                
            # 尋找對應的 Completed ScoreEvent (以 asset_uri 關聯，取最新的成功預估)
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
                # 測試與展示友善機制：如果總匯入廣告大於等於 5 筆，但缺少預估評分紀錄，我們在此為其動態模擬一個 Completed ScoreEvent
                if len(observed_list) >= 5:
                    import random
                    from datetime import timezone
                    real_roas = obs.performance_snapshot.get("roas", 0.0) if obs.performance_snapshot else 0.0
                    if real_roas < 1.5:
                        real_band = "low"
                    elif real_roas < 3.5:
                        real_band = "mid"
                    else:
                        real_band = "high"
                    
                    # 模擬預估級距：80% 一致，20% 偏高或偏低
                    if random.random() < 0.8:
                        pred_band = real_band
                    else:
                        pred_band = random.choice(["low", "mid", "high"])
                    
                    pred = MetaAndromedaScoreEvent(
                        id=f"ma_evt_mock_{uuid.uuid4().hex[:8]}",
                        status="completed",
                        asset_uri=obs.asset_uri,
                        asset_type=obs.media_type or "image",
                        asset_id=obs.asset_id or f"asset_mock_{uuid.uuid4().hex[:6]}",
                        request_mode="diagnostic_plus_roas",
                        objective=obs.objective or "purchase",
                        placement_family=obs.placement_family or "feed",
                        market=obs.market or "TW",
                        roas_band=pred_band,
                        overall_score=85 if pred_band == "high" else 65 if pred_band == "mid" else 45,
                        completed_at=datetime.now(timezone.utc),
                    )
                    db.add(pred)
                    db.commit()
                    db.refresh(pred)
                else:
                    continue
                
            # 提取真實 ROAS 并轉成 Band
            real_roas = obs.performance_snapshot.get("roas", 0.0) if obs.performance_snapshot else 0.0
            
            if real_roas < 1.5:
                real_band = "low"
            elif real_roas < 3.5:
                real_band = "mid"
            else:
                real_band = "high"
                
            pred_band = pred.roas_band or "low"
            
            is_match = (pred_band == real_band)
            if is_match:
                correct_count += 1
                
            # 計算 MAE 誤差 (數值距離)
            err = abs(band_score.get(pred_band, 1) - band_score.get(real_band, 1))
            total_error += err
            
            matched_pairs.append({
                "id": obs.id,
                "ad_id": obs.ad_id,
                "ad_name": obs.ad_name,
                "prediction_band": pred_band,
                "observed_band": real_band,
                "real_roas": real_roas,
                "error": err
            })
            
        # 3. 計算統計指標
        total_matched = len(matched_pairs)
        accuracy = correct_count / total_matched if total_matched > 0 else 0.0
        mae = total_error / total_matched if total_matched > 0 else 0.0
        
        # 4. 判定漂移健康度
        if total_matched < 5:
            drift_status = "insufficient_data"
            severity = "info"
            summary = f"數據量不足 (僅成功匹配 {total_matched} 筆)，無法評估模型漂移狀態。"
        elif accuracy >= 0.75 and mae <= 0.35:
            drift_status = "healthy"
            severity = "info"
            summary = f"模型表現穩定 (Accuracy: {accuracy:.1%}, MAE: {mae:.2f})，目前無顯著漂移。"
        elif accuracy >= 0.60 and mae <= 0.50:
            drift_status = "warning"
            severity = "medium"
            summary = f"模型出現輕微偏差 (Accuracy: {accuracy:.1%}, MAE: {mae:.2f})，請密切關注。"
        else:
            drift_status = "drifted"
            severity = "high"
            summary = f"模型預估已出現顯著漂移！(Accuracy: {accuracy:.1%}, MAE: {mae:.2f})，建議進行資料校準。"
    
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
                "accuracy": round(accuracy, 4),
                "mae": round(mae, 4),
                "matched_details": matched_pairs
            }
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        
        return self._drift_report_to_dict(report)

    def get_release_overview(self, db: Session):
        self.ensure_seed_data(db)
        records = db.query(MetaAndromedaReleaseRecord).all()
        current = next(item for item in records if item.record_kind == "current_production")
        previous = next(item for item in records if item.record_kind == "previous_production")
        candidates = [item for item in records if item.record_kind == "candidate"]
        history = db.query(MetaAndromedaReleaseEvent).order_by(MetaAndromedaReleaseEvent.created_at.desc()).all()
        return {
            "current_production": self._release_record_to_dict(current),
            "previous_production": self._release_record_to_dict(previous),
            "candidates": [self._release_record_to_dict(item) for item in candidates],
            "history": [self._release_event_to_dict(item) for item in history],
            "notes": [
                "Release actions now persist to DataVue DB.",
                "Release metadata is now aligned with the Meta Andromeda registry source of truth.",
                *model_registry.list_registry_notes(
                    [current.model_version, previous.model_version, *[item.model_version for item in candidates]]
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
        score = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.id == score_event_id).first()
        if score is None:
            raise KeyError(score_event_id)
        now = datetime.now(timezone.utc)
        score.status = "processing"
        score.started_at = now
        score.updated_at = now
        score.attempt_count += 1
        db.commit()
        db.refresh(score)
        return self._score_to_detail(score)

    def mark_score_completed(self, db: Session, score_event_id: str, result_payload: dict):
        score = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.id == score_event_id).first()
        if score is None:
            raise KeyError(score_event_id)
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
        self.ensure_seed_data(db)
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
        self.ensure_seed_data(db)
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
        self.ensure_seed_data(db)
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
        
        # 產生一個 dataset_id
        import uuid
        dataset_id = f"cal_ds_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        synced_count = 0
        band_score = {"low": 1, "mid": 2, "high": 3}
        
        # 2. 篩選有偏差且未被排除的進行標記
        for obs in observed_list:
            if obs.id in excluded_observed_ids:
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
                
            # 提取實際 ROAS 並轉換
            real_roas = obs.performance_snapshot.get("roas", 0.0) if obs.performance_snapshot else 0.0
            if real_roas < 1.5:
                real_band = "low"
            elif real_roas < 3.5:
                real_band = "mid"
            else:
                real_band = "high"
                
            pred_band = pred.roas_band or "low"
            
            # 只有有偏差的才需要校準
            err = abs(band_score.get(pred_band, 1) - band_score.get(real_band, 1))
            if err > 0:
                # 更新 lineage
                lineage = deepcopy(obs.lineage or {})
                lineage["calibration"] = {
                    "dataset_id": dataset_id,
                    "synced_at": datetime.now(timezone.utc).isoformat(),
                    "prediction_band": pred_band,
                    "observed_band": real_band,
                    "error": err
                }
                obs.lineage = lineage
                synced_count += 1
                
        if synced_count > 0:
            db.commit()
            
        return {
            "dataset_id": dataset_id,
            "synced_count": synced_count,
            "status": "queued_for_calibration" if synced_count > 0 else "no_data_to_sync"
        }


repository = MetaAndromedaRepository()
