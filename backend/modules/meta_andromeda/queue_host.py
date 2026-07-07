"""
Meta Andromeda queue host adapter
"""

import asyncio
import hashlib
import hmac
import json
from uuid import uuid4

import requests

from core.config import settings
from core.scheduler import (
    add_meta_andromeda_score_job,
    is_scheduler_enabled,
    process_meta_andromeda_score_event,
    scheduler,
)
from database import SessionLocal
from modules.meta_andromeda.repository import repository
from redis_cache import get_redis_client


class MetaAndromedaQueueHostAdapter:
    @staticmethod
    def _build_external_signature(payload: dict) -> str | None:
        signing_secret = settings.META_ANDROMEDA_EXTERNAL_QUEUE_SIGNING_SECRET
        if not signing_secret:
            return None
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signature = hmac.new(signing_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return signature

    @staticmethod
    def get_active_host() -> str:
        configured = settings.META_ANDROMEDA_QUEUE_HOST

        if settings.SERVICE_ROLE == "web":
            # docs/24 Wave 2：web process 絕不能在本地執行評分/匯入，即使本地
            # AsyncIOScheduler 因為週報排程而處於 running 狀態也一樣——否則
            # Meta Andromeda 負載又會跑回同一個 event loop，等於沒拆分。
            if configured in {"redis_stream", "database_queue", "external_webhook"}:
                return configured
            # auto / apscheduler / local_async 或其他未知值一律收斂成
            # redis_stream；Redis 不可用時退回 database_queue，交給 worker
            # process 的 sweeper 補派工。
            return "redis_stream" if get_redis_client() else "database_queue"

        if configured == "apscheduler" and not (is_scheduler_enabled() and scheduler.running):
            if settings.META_ANDROMEDA_SCORE_LOCAL_ASYNC_FALLBACK:
                return "local_async"
            return "unavailable"
        if configured != "auto":
            return configured
        if is_scheduler_enabled() and scheduler.running:
            return "apscheduler"
        if settings.META_ANDROMEDA_SCORE_LOCAL_ASYNC_FALLBACK:
            return "local_async"
        return "unavailable"

    @staticmethod
    def _ensure_stream_group(client) -> None:
        try:
            client.xgroup_create(
                settings.META_ANDROMEDA_REDIS_STREAM_KEY,
                settings.META_ANDROMEDA_REDIS_STREAM_GROUP,
                id="0",
                mkstream=True,
            )
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    @staticmethod
    def _ack_and_delete(client, message_id: str) -> None:
        client.xack(
            settings.META_ANDROMEDA_REDIS_STREAM_KEY,
            settings.META_ANDROMEDA_REDIS_STREAM_GROUP,
            message_id,
        )
        client.xdel(settings.META_ANDROMEDA_REDIS_STREAM_KEY, message_id)

    @staticmethod
    def _schedule_observation_import_message(client, message_id: str, payload: dict) -> bool:
        """docs/24 Wave 2：分流處理 `kind=observation_import` 的 stream 訊息。

        觀測匯入在 dispatch 當下還沒有對應的 DB row 可寫 worker event（那是
        評分事件才有的表），所以這裡只負責把 job 交給 scheduler，不記錄
        worker_event——匯入進度改用既有的 import_status_store 追蹤。
        """
        from core.scheduler import add_meta_andromeda_observation_import_job

        raw_payload = payload.get("payload")
        if not raw_payload:
            MetaAndromedaQueueHostAdapter._ack_and_delete(client, message_id)
            return False

        import_payload = json.loads(raw_payload)
        user_id = payload.get("user_id") or None
        team_id = payload.get("team_id") or None
        delay_seconds = float(payload.get("delay_seconds", "0") or 0)

        add_meta_andromeda_observation_import_job(
            import_payload,
            user_id=user_id,
            team_id=team_id,
            delay_seconds=delay_seconds,
        )
        MetaAndromedaQueueHostAdapter._ack_and_delete(client, message_id)
        return True

    @staticmethod
    def _schedule_redis_stream_message(
        client,
        db,
        message_id: str,
        payload: dict,
        event_type: str,
        consumer: str,
        claim_mode: str = "fresh",
    ) -> bool:
        # docs/24 Wave 2：同一個 stream 現在混合評分事件與觀測匯入兩種訊息，
        # 靠 `kind` 欄位分流；缺 `kind` 的舊訊息預設當評分事件處理（向後相容）。
        if payload.get("kind") == "observation_import":
            return MetaAndromedaQueueHostAdapter._schedule_observation_import_message(
                client, message_id, payload
            )

        score_event_id = payload.get("score_event_id")
        delay_seconds = float(payload.get("delay_seconds", "0") or 0)
        if not score_event_id:
            MetaAndromedaQueueHostAdapter._ack_and_delete(client, message_id)
            return False

        current = repository.get_review_queue_detail(db, score_event_id)
        add_meta_andromeda_score_job(
            score_event_id,
            delay_seconds=delay_seconds,
            queue_host="redis_stream",
        )
        repository.log_worker_event(
            db,
            score_event_id=score_event_id,
            event_type=event_type,
            queue_host="redis_stream",
            runtime_job_id=current.get("runtime_job_id"),
            status="queued",
            attempt_count=current.get("attempt_count", 0),
            message=f"stream ack {message_id}",
            event_payload={
                "message_id": message_id,
                "stream_key": settings.META_ANDROMEDA_REDIS_STREAM_KEY,
                "consumer": consumer,
                "claim_mode": claim_mode,
            },
        )
        MetaAndromedaQueueHostAdapter._ack_and_delete(client, message_id)
        return True

    def consume_redis_stream_batch(self) -> dict:
        client = get_redis_client()
        if not client:
            return {
                "accepted": False,
                "queue_host": "redis_stream",
                "dispatch_mode": "redis_unavailable",
                "consumed_count": 0,
            }

        self._ensure_stream_group(client)
        entries = client.xreadgroup(
            groupname=settings.META_ANDROMEDA_REDIS_STREAM_GROUP,
            consumername=settings.META_ANDROMEDA_REDIS_STREAM_CONSUMER,
            streams={settings.META_ANDROMEDA_REDIS_STREAM_KEY: ">"},
            count=settings.META_ANDROMEDA_REDIS_STREAM_BATCH_SIZE,
            block=1,
        )

        consumed_count = 0
        db = SessionLocal()
        try:
            for _, messages in entries:
                for message_id, payload in messages:
                    if self._schedule_redis_stream_message(
                        client,
                        db,
                        message_id,
                        payload,
                        event_type="redis_stream_consumed",
                        consumer=settings.META_ANDROMEDA_REDIS_STREAM_CONSUMER,
                        claim_mode="fresh",
                    ):
                        consumed_count += 1
        finally:
            db.close()

        return {
            "accepted": True,
            "queue_host": "redis_stream",
            "dispatch_mode": "redis_consumer",
            "consumed_count": consumed_count,
        }

    def reclaim_redis_stream_pending(self) -> dict:
        client = get_redis_client()
        if not client:
            return {
                "accepted": False,
                "queue_host": "redis_stream",
                "dispatch_mode": "redis_unavailable",
                "claimed_count": 0,
            }

        self._ensure_stream_group(client)
        try:
            reclaim_result = client.xautoclaim(
                settings.META_ANDROMEDA_REDIS_STREAM_KEY,
                settings.META_ANDROMEDA_REDIS_STREAM_GROUP,
                settings.META_ANDROMEDA_REDIS_STREAM_CONSUMER,
                min_idle_time=settings.META_ANDROMEDA_REDIS_STREAM_RECLAIM_IDLE_MS,
                start_id="0-0",
                count=settings.META_ANDROMEDA_REDIS_STREAM_RECLAIM_BATCH_SIZE,
            )
        except Exception as exc:
            if "unknown command" in str(exc).lower():
                return {
                    "accepted": False,
                    "queue_host": "redis_stream",
                    "dispatch_mode": "redis_xautoclaim_unsupported",
                    "claimed_count": 0,
                }
            raise

        claimed_entries = []
        next_start_id = "0-0"
        if isinstance(reclaim_result, (list, tuple)):
            if len(reclaim_result) >= 2:
                next_start_id = reclaim_result[0]
                claimed_entries = reclaim_result[1] or []
            elif len(reclaim_result) == 1:
                claimed_entries = reclaim_result[0] or []

        claimed_count = 0
        db = SessionLocal()
        try:
            for message_id, payload in claimed_entries:
                if self._schedule_redis_stream_message(
                    client,
                    db,
                    message_id,
                    payload,
                    event_type="redis_stream_reclaimed",
                    consumer=settings.META_ANDROMEDA_REDIS_STREAM_CONSUMER,
                    claim_mode="stale_pending",
                ):
                    claimed_count += 1
        finally:
            db.close()

        return {
            "accepted": True,
            "queue_host": "redis_stream",
            "dispatch_mode": "redis_reclaim",
            "claimed_count": claimed_count,
            "next_start_id": next_start_id,
            "min_idle_ms": settings.META_ANDROMEDA_REDIS_STREAM_RECLAIM_IDLE_MS,
        }

    def enqueue_observation_import_event(
        self,
        payload: dict,
        *,
        user_id: str | None,
        team_id: str | None = None,
        delay_seconds: float = 0.0,
    ) -> dict:
        """docs/24 Wave 2：把觀測匯入 job 經 Redis stream 派給獨立 worker
        process。只有 Redis 可用時才會 accepted=True；呼叫端（web 角色的
        router）在 accepted=False 時應退回本 process 內執行（Wave 1 的
        to_thread 化已確保這麼做不會卡住 event loop，只是失去負載隔離）。
        """
        client = get_redis_client()
        if not client:
            return {
                "accepted": False,
                "queue_host": "redis_stream",
                "dispatch_mode": "redis_unavailable",
            }

        request_id = f"ma_obs_stream_{uuid4().hex[:12]}"
        stream_payload = {
            "kind": "observation_import",
            "request_id": request_id,
            "payload": json.dumps(payload),
            "user_id": user_id or "",
            "team_id": team_id or "",
            "delay_seconds": str(delay_seconds),
        }
        receipt_id = client.xadd(
            settings.META_ANDROMEDA_REDIS_STREAM_KEY,
            stream_payload,
        )
        return {
            "accepted": True,
            "queue_host": "redis_stream",
            "dispatch_mode": "redis_xadd",
            "request_id": request_id,
            "receipt_id": receipt_id,
            "stream_key": settings.META_ANDROMEDA_REDIS_STREAM_KEY,
        }

    def enqueue_score_event(self, score_event_id: str, delay_seconds: float = 1.0) -> dict:
        queue_host = self.get_active_host()

        if queue_host == "database_queue":
            return {
                "accepted": True,
                "queue_host": "database_queue",
                "dispatch_mode": "db_backlog",
                "delay_seconds": delay_seconds,
            }

        if queue_host == "redis_stream":
            client = get_redis_client()
            if not client:
                return {
                    "accepted": False,
                    "queue_host": "redis_stream",
                    "dispatch_mode": "redis_unavailable",
                    "delay_seconds": delay_seconds,
                }
            request_id = f"ma_stream_{uuid4().hex[:12]}"
            stream_payload = {
                "request_id": request_id,
                "score_event_id": score_event_id,
                "delay_seconds": str(delay_seconds),
                "queue_host": "redis_stream",
            }
            receipt_id = client.xadd(
                settings.META_ANDROMEDA_REDIS_STREAM_KEY,
                stream_payload,
            )
            return {
                "accepted": True,
                "queue_host": "redis_stream",
                "dispatch_mode": "redis_xadd",
                "delay_seconds": delay_seconds,
                "request_id": request_id,
                "receipt_id": receipt_id,
                "stream_key": settings.META_ANDROMEDA_REDIS_STREAM_KEY,
            }

        if queue_host == "external_webhook":
            endpoint = settings.META_ANDROMEDA_EXTERNAL_QUEUE_ENDPOINT
            if not endpoint:
                return {
                    "accepted": False,
                    "queue_host": "external_webhook",
                    "dispatch_mode": "missing_endpoint",
                    "delay_seconds": delay_seconds,
                }

            request_id = f"ma_dispatch_{uuid4().hex[:12]}"
            payload = {
                "request_id": request_id,
                "score_event_id": score_event_id,
                "delay_seconds": delay_seconds,
                "queue_host": "external_webhook",
            }
            headers = {"Content-Type": "application/json"}
            if settings.META_ANDROMEDA_EXTERNAL_QUEUE_TOKEN:
                headers["Authorization"] = f"Bearer {settings.META_ANDROMEDA_EXTERNAL_QUEUE_TOKEN}"
            signature = self._build_external_signature(payload)
            if signature:
                headers["X-Meta-Andromeda-Signature"] = signature
            headers["X-Meta-Andromeda-Request-Id"] = request_id
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=settings.META_ANDROMEDA_EXTERNAL_QUEUE_TIMEOUT_SECONDS,
            )
            response_payload = {}
            try:
                response_payload = response.json() if hasattr(response, "json") else {}
            except Exception:
                response_payload = {}
            return {
                "accepted": 200 <= response.status_code < 300,
                "queue_host": "external_webhook",
                "dispatch_mode": "webhook_post",
                "delay_seconds": delay_seconds,
                "http_status": response.status_code,
                "request_id": request_id,
                "receipt_id": response_payload.get("receipt_id"),
                "accepted_at": response_payload.get("accepted_at"),
                "worker_hint": response_payload.get("worker_hint"),
            }

        if queue_host == "apscheduler" and is_scheduler_enabled() and scheduler.running:
            add_meta_andromeda_score_job(
                score_event_id,
                delay_seconds=delay_seconds,
                queue_host="apscheduler",
            )
            return {
                "accepted": True,
                "queue_host": "apscheduler",
                "dispatch_mode": "scheduler_job",
                "delay_seconds": delay_seconds,
            }

        if queue_host == "local_async" and settings.META_ANDROMEDA_SCORE_LOCAL_ASYNC_FALLBACK:
            async def _run() -> None:
                if delay_seconds > 0:
                    await asyncio.sleep(delay_seconds)
                await process_meta_andromeda_score_event(score_event_id, "local_async")

            asyncio.create_task(_run())
            return {
                "accepted": True,
                "queue_host": "local_async",
                "dispatch_mode": "in_process_task",
                "delay_seconds": delay_seconds,
            }

        return {
            "accepted": False,
            "queue_host": "unavailable",
            "dispatch_mode": "none",
            "delay_seconds": delay_seconds,
        }


queue_host_adapter = MetaAndromedaQueueHostAdapter()
