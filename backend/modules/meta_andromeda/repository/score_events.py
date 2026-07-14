"""ScoreEvent repository operations."""

from ._shared import *  # noqa: F401,F403
from ._stats import *  # noqa: F401,F403
from .release_metrics import *  # noqa: F401,F403

class ScoreEventMixin:
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
