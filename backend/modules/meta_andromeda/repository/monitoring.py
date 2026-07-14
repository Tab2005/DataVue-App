"""Monitoring repository operations."""

from ._shared import *  # noqa: F401,F403
from ._stats import *  # noqa: F401,F403
from .release_metrics import *  # noqa: F401,F403

class MonitoringMixin:
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

    def get_monitoring_summary(self, db: Session):
        score_rows = [
            row for row in db.query(MetaAndromedaScoreEvent).all()
            if (row.lineage or {}).get("scoring_purpose") != "backtest"
        ]
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
        # 2. insufficient_sample（配對數 >= 5 但 Spearman 樣本 < 15，ρ 不具統計意義）
        # 3. Phase 1 之前的舊報告（report_payload 無 period_diagnosis）
        query = db.query(MetaAndromedaDriftReport).filter(
            MetaAndromedaDriftReport.drift_status.notin_(["insufficient_data", "insufficient_sample"])
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
