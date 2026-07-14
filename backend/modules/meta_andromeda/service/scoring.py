"""ScoringServiceMixin for Meta Andromeda service."""

from ._shared import *  # noqa: F403


class ScoringServiceMixin:

    @staticmethod
    def create_score_event(db, payload: dict) -> dict:
        score_payload = runtime_adapter.build_score_submission(payload)
        if payload.get("request_context"):
            score_payload.setdefault("request_context", {}).update(payload["request_context"])
        return repository.create_score_event(db, score_payload)


    @staticmethod
    def assign_score_runtime_job(db, score_event_id: str, runtime_job_id: str) -> dict:
        return repository.assign_runtime_job(db, score_event_id, runtime_job_id)


    @staticmethod
    def enqueue_score_event(
        db,
        score_event_id: str,
        runtime_job_id: str,
        delay_seconds: float = 1.0,
        event_type: str = "dispatch_requested",
    ) -> dict:
        current = repository.get_review_queue_detail(db, score_event_id)
        dispatch = queue_host_adapter.enqueue_score_event(score_event_id, delay_seconds=delay_seconds)
        repository.log_worker_event(
            db,
            score_event_id=score_event_id,
            event_type=event_type,
            queue_host=dispatch["queue_host"],
            runtime_job_id=runtime_job_id,
            status="queued" if dispatch["accepted"] else "dispatch_failed",
            attempt_count=current["attempt_count"],
            message=dispatch["dispatch_mode"],
            event_payload=dispatch,
        )
        if dispatch["accepted"]:
            return repository.get_review_queue_detail(db, score_event_id)
        return repository.get_review_queue_detail(db, score_event_id)


    @staticmethod
    def get_score_detail(db, score_event_id: str) -> dict:
        return repository.get_review_queue_detail(db, score_event_id)
