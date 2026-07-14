"""WorkerCallbackServiceMixin for Meta Andromeda service."""

from . import _shared
from ._shared import *  # noqa: F403


class WorkerCallbackServiceMixin:

    @staticmethod
    def _build_external_worker_signature(raw_body: bytes) -> str | None:
        secret = settings.META_ANDROMEDA_EXTERNAL_WORKER_SHARED_SECRET
        if not secret:
            return None
        return hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()


    @staticmethod
    def _build_internal_worker_signature(raw_body: bytes) -> str | None:
        secret = settings.META_ANDROMEDA_INTERNAL_WORKER_SHARED_SECRET
        if not secret:
            return None
        return hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()


    @staticmethod
    def build_internal_worker_upload_auth_payload(
        *,
        asset_type: str,
        source_filename: str,
        uploaded_by: str | None,
        content_type: str | None,
        file_bytes: bytes,
    ) -> bytes:
        payload = {
            "asset_type": asset_type,
            "source_filename": source_filename,
            "uploaded_by": uploaded_by or "",
            "content_type": content_type or "",
            "file_sha256": hashlib.sha256(file_bytes).hexdigest(),
        }
        return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


    @staticmethod
    def verify_internal_worker_request(
        raw_body: bytes,
        signature: str | None = None,
        worker_token: str | None = None,
    ) -> None:
        expected_signature = MetaAndromedaService._build_internal_worker_signature(raw_body)
        expected_token = settings.META_ANDROMEDA_INTERNAL_WORKER_TOKEN

        if expected_signature:
            if not signature or not hmac.compare_digest(signature, expected_signature):
                raise PermissionError("invalid_internal_worker_signature")
            return

        if expected_token:
            if not worker_token or not hmac.compare_digest(worker_token, expected_token):
                raise PermissionError("invalid_internal_worker_token")
            return

        raise PermissionError("internal_worker_auth_not_configured")


    @staticmethod
    def verify_external_worker_callback(
        raw_body: bytes,
        signature: str | None = None,
        worker_token: str | None = None,
    ) -> None:
        expected_signature = MetaAndromedaService._build_external_worker_signature(raw_body)
        expected_token = settings.META_ANDROMEDA_EXTERNAL_WORKER_TOKEN

        if expected_signature:
            if not signature or not hmac.compare_digest(signature, expected_signature):
                raise PermissionError("invalid_worker_signature")
            return

        if expected_token:
            if not worker_token or not hmac.compare_digest(worker_token, expected_token):
                raise PermissionError("invalid_worker_token")
            return

        raise PermissionError("external_worker_callback_auth_not_configured")


    @staticmethod
    def _ensure_external_processing_state(db, score_event_id: str) -> dict:
        current = repository.get_review_queue_detail(db, score_event_id)
        if current["status"] == "queued":
            claimed = repository.mark_score_processing(db, score_event_id)
            return claimed or repository.get_review_queue_detail(db, score_event_id)
        return current


    @staticmethod
    def _external_worker_event_name(event_type: str) -> str:
        return f"external_worker_{event_type}"


    @staticmethod
    def _is_duplicate_external_callback(
        db,
        score_event_id: str,
        *,
        event_type: str,
        runtime_job_id: str | None,
        receipt_id: str | None,
    ) -> bool:
        return (
            repository.find_worker_event(
                db,
                score_event_id=score_event_id,
                event_type=MetaAndromedaService._external_worker_event_name(event_type),
                runtime_job_id=runtime_job_id,
                receipt_id=receipt_id,
            )
            is not None
        )


    @staticmethod
    def _normalize_external_result_payload(result_payload: dict) -> dict:
        normalized = dict(result_payload)
        model_version = normalized.get("model_version")
        registry_entry = model_registry.get_entry(model_version=model_version)
        normalized.setdefault("status", "completed")
        normalized.setdefault("prediction_mode", "diagnostic_plus_roas")
        normalized.setdefault("feature_manifest_id", registry_entry.feature_manifest_id)
        normalized.setdefault("error_message", None)
        normalized.setdefault("diagnostic_breakdown", {})
        normalized.setdefault("roas_prediction", {})
        normalized.setdefault("risk_tags", [])
        normalized.setdefault("top_positive_drivers", [])
        normalized.setdefault("top_negative_drivers", [])
        normalized.setdefault("explanations", {})
        lineage = dict(normalized.get("lineage") or {})
        lineage.setdefault("feature_manifest_id", registry_entry.feature_manifest_id)
        lineage.setdefault("registry_model_version", registry_entry.model_version)
        lineage.setdefault("registry_provider", registry_entry.provider)
        lineage.setdefault("provider_model", registry_entry.provider_model)
        lineage.setdefault("registry_profile", registry_entry.scoring_profile)
        lineage.setdefault("registry_source", registry_entry.source_of_truth)
        lineage.setdefault("scoring_mode", "external_worker")
        normalized["lineage"] = lineage
        normalized["model_version"] = registry_entry.model_version
        return normalized


    @staticmethod
    def handle_external_worker_callback(db, score_event_id: str, payload: dict) -> dict:
        current = repository.get_review_queue_detail(db, score_event_id)
        queue_host = payload.get("queue_host") or "external_webhook"
        runtime_job_id = payload.get("runtime_job_id") or current.get("runtime_job_id")
        if runtime_job_id and current.get("runtime_job_id") != runtime_job_id:
            if current.get("status") in {"completed", "failed"}:
                return current
            current = repository.assign_runtime_job(db, score_event_id, runtime_job_id)

        event_type = payload["event_type"]
        attempt_count = payload.get("attempt_count") or current.get("attempt_count", 0)
        worker_payload = {
            "worker_id": payload.get("worker_id"),
            "receipt_id": payload.get("receipt_id"),
            "retryable": payload.get("retryable", False),
            "retry_delay_seconds": payload.get("retry_delay_seconds"),
            "callback_metadata": payload.get("callback_metadata") or {},
        }
        if MetaAndromedaService._is_duplicate_external_callback(
            db,
            score_event_id,
            event_type=event_type,
            runtime_job_id=runtime_job_id,
            receipt_id=payload.get("receipt_id"),
        ):
            return repository.get_review_queue_detail(db, score_event_id)

        if event_type == "accepted":
            repository.log_worker_event(
                db,
                score_event_id=score_event_id,
                event_type="external_worker_accepted",
                queue_host=queue_host,
                runtime_job_id=runtime_job_id,
                status=current["status"],
                attempt_count=attempt_count,
                message="external worker accepted dispatch",
                event_payload=worker_payload,
            )
            return repository.get_review_queue_detail(db, score_event_id)

        if event_type == "processing":
            if current["status"] in {"completed", "failed"}:
                return current
            processing = MetaAndromedaService._ensure_external_processing_state(db, score_event_id)
            repository.log_worker_event(
                db,
                score_event_id=score_event_id,
                event_type="external_worker_processing",
                queue_host=queue_host,
                runtime_job_id=runtime_job_id,
                status="processing",
                attempt_count=processing["attempt_count"],
                message="external worker started processing",
                event_payload=worker_payload,
            )
            return processing

        if event_type == "completed":
            if not payload.get("result_payload"):
                raise ValueError("completed callback requires result_payload")
            if current["status"] in {"completed", "failed"}:
                return current
            MetaAndromedaService._ensure_external_processing_state(db, score_event_id)
            normalized_result = MetaAndromedaService._normalize_external_result_payload(payload["result_payload"])
            completed = repository.mark_score_completed(db, score_event_id, normalized_result)
            repository.log_worker_event(
                db,
                score_event_id=score_event_id,
                event_type="external_worker_completed",
                queue_host=queue_host,
                runtime_job_id=runtime_job_id,
                status="completed",
                attempt_count=completed["attempt_count"],
                message="external worker completed scoring",
                event_payload={**worker_payload, "model_version": completed["model_version"]},
            )
            return completed

        if event_type == "failed":
            if current["status"] in {"completed", "failed"}:
                return current
            processing = MetaAndromedaService._ensure_external_processing_state(db, score_event_id)
            error_message = payload.get("error_message") or "external_worker_failed"
            if payload.get("retryable") and processing["attempt_count"] < settings.META_ANDROMEDA_SCORE_MAX_ATTEMPTS:
                queued = repository.requeue_score_event(db, score_event_id, error_message)
                repository.log_worker_event(
                    db,
                    score_event_id=score_event_id,
                    event_type="external_worker_retry_scheduled",
                    queue_host=queue_host,
                    runtime_job_id=runtime_job_id,
                    status="queued",
                    attempt_count=queued["attempt_count"],
                    message=error_message,
                    event_payload=worker_payload,
                )
                return MetaAndromedaService.enqueue_score_event(
                    db,
                    score_event_id=score_event_id,
                    runtime_job_id=queued["runtime_job_id"],
                    delay_seconds=payload.get("retry_delay_seconds")
                    or settings.META_ANDROMEDA_SCORE_RETRY_DELAY_SECONDS,
                    event_type="external_worker_retry_dispatch_requested",
                )

            failed = repository.mark_score_failed(db, score_event_id, error_message)
            repository.log_worker_event(
                db,
                score_event_id=score_event_id,
                event_type="external_worker_failed",
                queue_host=queue_host,
                runtime_job_id=runtime_job_id,
                status="failed",
                attempt_count=failed["attempt_count"],
                message=error_message,
                event_payload=worker_payload,
            )
            repository.create_dead_letter(
                db,
                score_event_id=score_event_id,
                queue_host=queue_host,
                runtime_job_id=runtime_job_id,
                failure_stage="external_worker",
                attempt_count=failed["attempt_count"],
                final_error_message=error_message,
                dead_letter_payload=worker_payload,
            )
            repository.log_worker_event(
                db,
                score_event_id=score_event_id,
                event_type="external_worker_dead_lettered",
                queue_host=queue_host,
                runtime_job_id=runtime_job_id,
                status="failed",
                attempt_count=failed["attempt_count"],
                message=error_message,
                event_payload={"failure_stage": "external_worker", **worker_payload},
            )
            return failed

        raise ValueError(f"Unsupported external worker event_type: {event_type}")


    @staticmethod
    def _mark_score_processing_sync(score_event_id: str, queue_host: str) -> tuple[dict | None, dict | None]:
        """同步版本：DB 標記評分開始處理 + 寫入 worker event。純 DB I/O，
        透過 asyncio.to_thread 呼叫避免卡住 event loop（docs/24 Wave 1）。

        回傳 (current, not_found_detail)：current 非 None 時代表已標記為
        processing，可以繼續往下跑評分；not_found_detail 非 None 時代表 score
        event 已不在可處理狀態，呼叫端應直接回傳它並結束（維持原本提前 return 的行為）。
        """
        db = _shared.SessionLocal()
        try:
            current = repository.mark_score_processing(db, score_event_id)
            if current is None:
                return None, repository.get_review_queue_detail(db, score_event_id)
            repository.log_worker_event(
                db,
                score_event_id=score_event_id,
                event_type="processing_started",
                queue_host=queue_host,
                runtime_job_id=current["runtime_job_id"],
                status="processing",
                attempt_count=current["attempt_count"],
                message="worker started",
                event_payload={
                    "queue_host": queue_host,
                    "max_concurrency": settings.META_ANDROMEDA_SCORE_MAX_CONCURRENCY,
                },
            )
            return current, None
        finally:
            db.close()


    @staticmethod
    def _prepare_score_retry_or_failure(score_event_id: str, queue_host: str, error_message: str):
        """同步版本：判斷是否還有重試次數並寫入對應 DB 狀態（純 DB I/O，見 docs/24 Wave 1）。

        回傳 ("retry", queued) 時，呼叫端需留在 event loop thread 上呼叫
        MetaAndromedaService.enqueue_score_event() 完成實際派工——該呼叫在
        local_async fallback 時會呼叫 asyncio.create_task()，必須跑在有運作中
        event loop 的執行緒，不能丟進 to_thread。回傳 ("failed", failed) 時已是
        終態，直接回傳給呼叫端即可。
        """
        db = _shared.SessionLocal()
        try:
            latest = repository.get_review_queue_detail(db, score_event_id)
            if latest["attempt_count"] < settings.META_ANDROMEDA_SCORE_MAX_ATTEMPTS:
                queued = repository.requeue_score_event(db, score_event_id, error_message)
                repository.log_worker_event(
                    db,
                    score_event_id=score_event_id,
                    event_type="retry_scheduled",
                    queue_host=queue_host,
                    runtime_job_id=queued["runtime_job_id"],
                    status="queued",
                    attempt_count=queued["attempt_count"],
                    message=error_message,
                    event_payload={"retry_delay_seconds": settings.META_ANDROMEDA_SCORE_RETRY_DELAY_SECONDS},
                )
                return "retry", queued

            failed = repository.mark_score_failed(db, score_event_id, error_message)
            repository.log_worker_event(
                db,
                score_event_id=score_event_id,
                event_type="failed",
                queue_host=queue_host,
                runtime_job_id=failed["runtime_job_id"],
                status="failed",
                attempt_count=failed["attempt_count"],
                message=error_message,
                event_payload={"queue_host": queue_host},
            )
            repository.create_dead_letter(
                db,
                score_event_id=score_event_id,
                queue_host=queue_host,
                runtime_job_id=failed["runtime_job_id"],
                failure_stage="runtime",
                attempt_count=failed["attempt_count"],
                final_error_message=error_message,
                dead_letter_payload={
                    "queue_host": queue_host,
                    "attempt_count": failed["attempt_count"],
                    "runtime_job_id": failed["runtime_job_id"],
                },
            )
            repository.log_worker_event(
                db,
                score_event_id=score_event_id,
                event_type="dead_lettered",
                queue_host=queue_host,
                runtime_job_id=failed["runtime_job_id"],
                status="failed",
                attempt_count=failed["attempt_count"],
                message=error_message,
                event_payload={"failure_stage": "runtime"},
            )
            return "failed", failed
        finally:
            db.close()


    @staticmethod
    def _complete_score_event_sync(score_event_id: str, queue_host: str, result: dict) -> dict:
        """同步版本：DB 標記評分完成 + 寫入 worker event（純 DB I/O，見 docs/24 Wave 1）。"""
        db = _shared.SessionLocal()
        try:
            completed = repository.mark_score_completed(db, score_event_id, result)
            repository.log_worker_event(
                db,
                score_event_id=score_event_id,
                event_type="completed",
                queue_host=queue_host,
                runtime_job_id=completed["runtime_job_id"],
                status="completed",
                attempt_count=completed["attempt_count"],
                message="worker completed",
                event_payload={"queue_host": queue_host, "model_version": completed["model_version"]},
            )
            return completed
        finally:
            db.close()


    @staticmethod
    async def process_score_event(score_event_id: str, queue_host: str = "unknown") -> dict:
        async with _score_event_semaphore.acquire():
            current, not_found_detail = await asyncio.to_thread(
                MetaAndromedaService._mark_score_processing_sync, score_event_id, queue_host
            )
            if current is None:
                return not_found_detail

            try:
                result = await asyncio.wait_for(
                    runtime_adapter.generate_score_result(current),
                    timeout=settings.META_ANDROMEDA_SCORE_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                error_message = f"score runtime timed out after {settings.META_ANDROMEDA_SCORE_TIMEOUT_SECONDS:.2f}s"
            except Exception as exc:
                error_message = str(exc)
            else:
                return await asyncio.to_thread(
                    MetaAndromedaService._complete_score_event_sync, score_event_id, queue_host, result
                )

            kind, payload = await asyncio.to_thread(
                MetaAndromedaService._prepare_score_retry_or_failure,
                score_event_id,
                queue_host,
                error_message,
            )
            if kind == "failed":
                return payload

            queued = payload
            db = _shared.SessionLocal()
            try:
                return MetaAndromedaService.enqueue_score_event(
                    db,
                    score_event_id=score_event_id,
                    runtime_job_id=queued["runtime_job_id"],
                    delay_seconds=settings.META_ANDROMEDA_SCORE_RETRY_DELAY_SECONDS,
                    event_type="retry_dispatch_requested",
                )
            finally:
                db.close()

