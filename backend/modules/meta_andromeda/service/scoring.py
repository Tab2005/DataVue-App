"""ScoringServiceMixin for Meta Andromeda service."""

from . import _shared


class ScoringServiceMixin:

    @staticmethod
    def create_score_event(db, payload: dict) -> dict:
        score_payload = _shared.runtime_adapter.build_score_submission(payload)
        if payload.get("request_context"):
            score_payload.setdefault("request_context", {}).update(payload["request_context"])
        return _shared.repository.create_score_event(db, score_payload)


    @staticmethod
    def assign_score_runtime_job(db, score_event_id: str, runtime_job_id: str) -> dict:
        return _shared.repository.assign_runtime_job(db, score_event_id, runtime_job_id)


    @staticmethod
    def enqueue_score_event(
        db,
        score_event_id: str,
        runtime_job_id: str,
        delay_seconds: float = 1.0,
        event_type: str = "dispatch_requested",
    ) -> dict:
        current = _shared.repository.get_review_queue_detail(db, score_event_id)
        dispatch = _shared.queue_host_adapter.enqueue_score_event(score_event_id, delay_seconds=delay_seconds)
        _shared.repository.log_worker_event(
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
        # docs/68 A3：兩個分支過去回傳完全相同（都是重新查一次 review queue
        # detail），合併成單一路徑。派工失敗時 score event 本身仍停留在
        # queued（交由 sweeper 之後補派）——額外帶出 dispatch_accepted，讓
        # 呼叫端（如觀測匯入的自動評分流程）能感知這次派工是否真的成功，
        # 而不是誤以為「有回傳值就代表已經排進佇列」。
        detail = _shared.repository.get_review_queue_detail(db, score_event_id)
        detail["dispatch_accepted"] = dispatch["accepted"]
        return detail


    @staticmethod
    def get_score_detail(db, score_event_id: str) -> dict:
        return _shared.repository.get_review_queue_detail(db, score_event_id)
