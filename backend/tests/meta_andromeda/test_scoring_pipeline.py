from .conftest import *  # noqa: F401,F403


@pytest.mark.unit
def test_meta_andromeda_runtime_health_reports_missing_internal_asset_worker_config_on_web_filesystem(meta_andromeda_access, monkeypatch):
    monkeypatch.setenv("SERVICE_ROLE", "web")
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_BACKEND", "filesystem")
    monkeypatch.delenv("META_ANDROMEDA_INTERNAL_WORKER_BASE_URL", raising=False)
    monkeypatch.delenv("META_ANDROMEDA_INTERNAL_WORKER_SHARED_SECRET", raising=False)
    monkeypatch.delenv("META_ANDROMEDA_INTERNAL_WORKER_TOKEN", raising=False)

    response = meta_andromeda_access.get("/api/meta-andromeda/runtime-health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"degraded", "unhealthy"}
    assert payload["checks"]["storage"]["mode"] == "worker_remote"
    assert payload["checks"]["internal_asset_worker"]["required"] is True
    assert payload["checks"]["internal_asset_worker"]["auth_configured"] is False


@pytest.mark.unit
def test_meta_andromeda_monitoring_exposes_worker_host_observability(meta_andromeda_access):
    response = meta_andromeda_access.get("/api/meta-andromeda/monitoring/summary")

    assert response.status_code == 200
    payload = response.json()
    assert "worker_host" in payload
    assert payload["worker_host"]["host_strategy"] == "shared_queue_host_adapter"
    assert "recent_events" in payload["worker_host"]
    assert "dead_letters" in payload["worker_host"]
    assert "latest_drift_reports" in payload


@pytest.mark.unit
def test_meta_andromeda_runtime_health_returns_shared_runtime_summary(meta_andromeda_access):
    response = meta_andromeda_access.get("/api/meta-andromeda/runtime/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"healthy", "degraded", "unhealthy"}
    assert "checks" in payload
    assert "storage" in payload["checks"]
    assert "model_registry" in payload["checks"]


@pytest.mark.unit
def test_meta_andromeda_score_submit_supports_database_queue_host(meta_andromeda_access, monkeypatch):
    monkeypatch.setenv("META_ANDROMEDA_QUEUE_HOST", "database_queue")
    monkeypatch.setenv("META_ANDROMEDA_SCORE_LOCAL_ASYNC_FALLBACK", "false")

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores",
        json={
            "asset_uri": "storage://meta-andromeda/uploads/test/db-queue.png",
            "asset_type": "image",
            "asset_id": "asset_db_queue_score",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "queued"

    monitoring = meta_andromeda_access.get("/api/meta-andromeda/monitoring/summary").json()
    assert monitoring["worker_host"]["active_host"] == "database_queue"
    assert any(
        event["queue_host"] == "database_queue" for event in monitoring["worker_host"]["recent_events"]
    )


@pytest.mark.unit
def test_meta_andromeda_score_submit_supports_external_webhook_queue_host(meta_andromeda_access, monkeypatch):
    monkeypatch.setenv("META_ANDROMEDA_QUEUE_HOST", "external_webhook")
    monkeypatch.setenv("META_ANDROMEDA_EXTERNAL_QUEUE_ENDPOINT", "https://queue.example.com/enqueue")
    monkeypatch.setenv("META_ANDROMEDA_EXTERNAL_QUEUE_SIGNING_SECRET", "secret-123")

    response_mock = Mock()
    response_mock.status_code = 202
    response_mock.json = Mock(return_value={
        "receipt_id": "receipt_123",
        "accepted_at": "2026-06-09T10:00:00Z",
        "worker_hint": "queue-worker-a",
    })
    captured = {}

    def fake_post(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return response_mock

    monkeypatch.setattr(meta_andromeda_queue_host_module.requests, "post", fake_post)

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores",
        json={
            "asset_uri": "storage://meta-andromeda/uploads/test/ext-queue.png",
            "asset_type": "image",
            "asset_id": "asset_ext_queue_score",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "queued"

    monitoring = meta_andromeda_access.get("/api/meta-andromeda/monitoring/summary").json()
    assert monitoring["worker_host"]["active_host"] == "external_webhook"
    matching_events = [
        event for event in monitoring["worker_host"]["recent_events"] if event["queue_host"] == "external_webhook"
    ]
    assert matching_events
    assert matching_events[0]["event_payload"]["receipt_id"] == "receipt_123"
    assert matching_events[0]["event_payload"]["worker_hint"] == "queue-worker-a"
    assert captured["kwargs"]["headers"]["X-Meta-Andromeda-Request-Id"]
    assert captured["kwargs"]["headers"]["X-Meta-Andromeda-Signature"]


@pytest.mark.unit
def test_meta_andromeda_external_worker_callback_completes_score(meta_andromeda_access, db, monkeypatch):
    monkeypatch.setenv("META_ANDROMEDA_EXTERNAL_WORKER_SHARED_SECRET", "worker-secret")

    queued_response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores",
        json={
            "asset_uri": "storage://meta-andromeda/uploads/test/external-worker-complete.png",
            "asset_type": "image",
            "asset_id": "asset_external_worker_complete",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
        },
    )
    assert queued_response.status_code == 201
    queued_payload = queued_response.json()
    score_event_id = queued_payload["score_event_id"]
    runtime_job_id = queued_payload["runtime_job_id"]

    callback_payload = {
        "event_type": "completed",
        "queue_host": "external_webhook",
        "runtime_job_id": runtime_job_id,
        "worker_id": "worker-a",
        "receipt_id": "receipt_cb_001",
        "result_payload": {
            "prediction_mode": "diagnostic_plus_roas",
            "overall_score": 88,
            "roas_band": "high",
            "model_version": "cand_v2026_06_05_a",
            "diagnostic_breakdown": {"cta_presence": "clear"},
            "risk_tags": ["external_worker"],
            "top_positive_drivers": ["clear CTA"],
            "top_negative_drivers": ["needs more variants"],
            "explanations": {"summary": "Completed by external worker."},
        },
    }
    raw_body = json.dumps(callback_payload).encode("utf-8")
    signature = hmac.new(b"worker-secret", raw_body, hashlib.sha256).hexdigest()

    response = meta_andromeda_access.post(
        f"/api/meta-andromeda/worker/score-events/{score_event_id}/callbacks",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Meta-Andromeda-Worker-Signature": signature,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] is True
    assert payload["current_status"] == "completed"

    detail = MetaAndromedaService.get_score_detail(db, score_event_id)
    assert detail["status"] == "completed"
    assert detail["overall_score"] == 88
    assert detail["lineage"]["scoring_mode"] == "external_worker"


@pytest.mark.unit
def test_meta_andromeda_external_worker_callback_retryable_failure_requeues(meta_andromeda_access, db, monkeypatch):
    monkeypatch.setenv("META_ANDROMEDA_EXTERNAL_WORKER_SHARED_SECRET", "worker-secret")
    monkeypatch.setenv("META_ANDROMEDA_SCORE_MAX_ATTEMPTS", "3")

    queued_response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores",
        json={
            "asset_uri": "storage://meta-andromeda/uploads/test/external-worker-retry.png",
            "asset_type": "image",
            "asset_id": "asset_external_worker_retry",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
        },
    )
    assert queued_response.status_code == 201
    queued_payload = queued_response.json()
    score_event_id = queued_payload["score_event_id"]
    runtime_job_id = queued_payload["runtime_job_id"]

    monkeypatch.setattr(
        meta_andromeda_service_module.queue_host_adapter,
        "enqueue_score_event",
        lambda score_event_id, delay_seconds=1.0: {
            "accepted": True,
            "queue_host": "external_webhook",
            "dispatch_mode": "webhook_post",
            "delay_seconds": delay_seconds,
            "request_id": "retry_dispatch_001",
            "receipt_id": "retry_receipt_001",
        },
    )

    callback_payload = {
        "event_type": "failed",
        "queue_host": "external_webhook",
        "runtime_job_id": runtime_job_id,
        "worker_id": "worker-b",
        "receipt_id": "receipt_cb_retry",
        "error_message": "worker_timeout",
        "retryable": True,
        "retry_delay_seconds": 0,
    }
    raw_body = json.dumps(callback_payload).encode("utf-8")
    signature = hmac.new(b"worker-secret", raw_body, hashlib.sha256).hexdigest()

    response = meta_andromeda_access.post(
        f"/api/meta-andromeda/worker/score-events/{score_event_id}/callbacks",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Meta-Andromeda-Worker-Signature": signature,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_status"] == "queued"

    monitoring = MetaAndromedaService.get_monitoring_summary(db)
    assert any(
        event["event_type"] == "external_worker_retry_scheduled"
        for event in monitoring["worker_host"]["recent_events"]
    )


@pytest.mark.unit
def test_meta_andromeda_score_submit_supports_redis_stream_queue_host(meta_andromeda_access, monkeypatch):
    monkeypatch.setenv("META_ANDROMEDA_QUEUE_HOST", "redis_stream")
    monkeypatch.setenv("META_ANDROMEDA_REDIS_STREAM_KEY", "meta_andromeda:test_queue")

    redis_mock = Mock()
    redis_mock.xadd = Mock(return_value="1749388800000-0")
    monkeypatch.setattr(redis_cache_module, "get_redis_client", lambda: redis_mock)
    monkeypatch.setattr(meta_andromeda_queue_host_module, "get_redis_client", lambda: redis_mock)

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores",
        json={
            "asset_uri": "storage://meta-andromeda/uploads/test/redis-queue.png",
            "asset_type": "image",
            "asset_id": "asset_redis_queue_score",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "queued"

    monitoring = meta_andromeda_access.get("/api/meta-andromeda/monitoring/summary").json()
    matching_events = [
        event for event in monitoring["worker_host"]["recent_events"] if event["queue_host"] == "redis_stream"
    ]
    assert matching_events
    assert matching_events[0]["event_payload"]["stream_key"] == "meta_andromeda:test_queue"
    assert matching_events[0]["event_payload"]["receipt_id"] == "1749388800000-0"


@pytest.mark.unit
def test_meta_andromeda_redis_stream_consumer_acks_messages(meta_andromeda_access, db, monkeypatch):
    monkeypatch.setenv("META_ANDROMEDA_QUEUE_HOST", "redis_stream")
    monkeypatch.setenv("META_ANDROMEDA_REDIS_STREAM_KEY", "meta_andromeda:test_queue")
    monkeypatch.setenv("META_ANDROMEDA_REDIS_STREAM_GROUP", "meta_andromeda:test_group")
    monkeypatch.setenv("META_ANDROMEDA_REDIS_STREAM_CONSUMER", "meta_andromeda:test_consumer")

    class SessionProxy:
        def __init__(self, session):
            self._session = session

        def __getattr__(self, name):
            return getattr(self._session, name)

        def close(self):
            return None

    monkeypatch.setattr(meta_andromeda_queue_host_module, "SessionLocal", lambda: SessionProxy(db))

    queued_response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores",
        json={
            "asset_uri": "storage://meta-andromeda/uploads/test/redis-consumer.png",
            "asset_type": "image",
            "asset_id": "asset_redis_consumer_score",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
        },
    )
    assert queued_response.status_code == 201
    score_event_id = queued_response.json()["score_event_id"]

    redis_mock = Mock()
    redis_mock.xgroup_create = Mock()
    redis_mock.xreadgroup = Mock(return_value=[
        ("meta_andromeda:test_queue", [("1749388800001-0", {
            "score_event_id": score_event_id,
            "delay_seconds": "0",
        })])
    ])
    redis_mock.xack = Mock()
    redis_mock.xdel = Mock()

    scheduled = []

    monkeypatch.setattr(meta_andromeda_queue_host_module, "get_redis_client", lambda: redis_mock)
    monkeypatch.setattr(
        meta_andromeda_queue_host_module,
        "add_meta_andromeda_score_job",
        lambda score_event_id, delay_seconds=0, queue_host="redis_stream": scheduled.append(
            {"score_event_id": score_event_id, "delay_seconds": delay_seconds, "queue_host": queue_host}
        ),
    )

    summary = meta_andromeda_queue_host_module.queue_host_adapter.consume_redis_stream_batch()
    assert summary["accepted"] is True
    assert summary["consumed_count"] == 1
    assert scheduled and scheduled[0]["score_event_id"] == score_event_id
    assert scheduled[0]["queue_host"] == "redis_stream"
    redis_mock.xack.assert_called_once()
    redis_mock.xdel.assert_called_once()

    monitoring = MetaAndromedaService.get_monitoring_summary(db)
    assert any(
        event["event_type"] == "redis_stream_consumed" for event in monitoring["worker_host"]["recent_events"]
    )


@pytest.mark.unit
def test_meta_andromeda_redis_stream_reclaim_reschedules_stale_pending_messages(
    meta_andromeda_access,
    db,
    monkeypatch,
):
    monkeypatch.setenv("META_ANDROMEDA_QUEUE_HOST", "redis_stream")
    monkeypatch.setenv("META_ANDROMEDA_REDIS_STREAM_KEY", "meta_andromeda:test_queue")
    monkeypatch.setenv("META_ANDROMEDA_REDIS_STREAM_GROUP", "meta_andromeda:test_group")
    monkeypatch.setenv("META_ANDROMEDA_REDIS_STREAM_CONSUMER", "meta_andromeda:test_consumer")
    monkeypatch.setenv("META_ANDROMEDA_REDIS_STREAM_RECLAIM_IDLE_MS", "15000")

    class SessionProxy:
        def __init__(self, session):
            self._session = session

        def __getattr__(self, name):
            return getattr(self._session, name)

        def close(self):
            return None

    monkeypatch.setattr(meta_andromeda_queue_host_module, "SessionLocal", lambda: SessionProxy(db))

    queued_response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores",
        json={
            "asset_uri": "storage://meta-andromeda/uploads/test/redis-reclaim.png",
            "asset_type": "image",
            "asset_id": "asset_redis_reclaim_score",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
        },
    )
    assert queued_response.status_code == 201
    score_event_id = queued_response.json()["score_event_id"]

    redis_mock = Mock()
    redis_mock.xgroup_create = Mock()
    redis_mock.xautoclaim = Mock(return_value=(
        "0-0",
        [("1749388800002-0", {"score_event_id": score_event_id, "delay_seconds": "0"})],
        [],
    ))
    redis_mock.xack = Mock()
    redis_mock.xdel = Mock()

    scheduled = []

    monkeypatch.setattr(meta_andromeda_queue_host_module, "get_redis_client", lambda: redis_mock)
    monkeypatch.setattr(
        meta_andromeda_queue_host_module,
        "add_meta_andromeda_score_job",
        lambda score_event_id, delay_seconds=0, queue_host="redis_stream": scheduled.append(
            {"score_event_id": score_event_id, "delay_seconds": delay_seconds, "queue_host": queue_host}
        ),
    )

    summary = meta_andromeda_queue_host_module.queue_host_adapter.reclaim_redis_stream_pending()
    assert summary["accepted"] is True
    assert summary["claimed_count"] == 1
    assert summary["dispatch_mode"] == "redis_reclaim"
    assert scheduled and scheduled[0]["score_event_id"] == score_event_id
    assert scheduled[0]["queue_host"] == "redis_stream"
    redis_mock.xack.assert_called_once()
    redis_mock.xdel.assert_called_once()

    monitoring = MetaAndromedaService.get_monitoring_summary(db)
    matching_events = [
        event for event in monitoring["worker_host"]["recent_events"] if event["event_type"] == "redis_stream_reclaimed"
    ]
    assert matching_events
    assert matching_events[0]["event_payload"]["claim_mode"] == "stale_pending"


@pytest.mark.asyncio
async def test_meta_andromeda_score_submit_queues_then_completes(meta_andromeda_access, db, monkeypatch):
    monkeypatch.setenv("META_ANDROMEDA_SCORING_PROVIDER", "auto")
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores",
        json={
            "asset_uri": "storage://meta-andromeda/uploads/test/creative.png",
            "asset_type": "image",
            "asset_id": "asset_test_score",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
        },
    )

    assert response.status_code == 201
    queued_payload = response.json()
    assert queued_payload["status"] == "queued"
    score_event_id = queued_payload["score_event_id"]
    repository.mark_score_processing(db, score_event_id)
    current = repository.get_review_queue_detail(db, score_event_id)
    result = await runtime_adapter.generate_score_result(current)
    repository.mark_score_completed(db, score_event_id, result)

    detail = meta_andromeda_access.get(f"/api/meta-andromeda/scores/{score_event_id}")
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload["status"] == "completed"
    assert detail_payload["overall_score"] is not None
    assert detail_payload["model_version"] == "cand_v2026_06_05_a"
    assert detail_payload["lineage"]["registry_model_version"] == "cand_v2026_06_05_a"
    assert detail_payload["lineage"]["registry_source"] == "datavue.meta_andromeda.registry"
    assert detail_payload["attempt_count"] >= 1


@pytest.mark.asyncio
async def test_meta_andromeda_score_retries_then_completes(meta_andromeda_access, db, monkeypatch):
    monkeypatch.setenv("META_ANDROMEDA_SCORE_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("META_ANDROMEDA_SCORE_RETRY_DELAY_SECONDS", "0")
    monkeypatch.setenv("META_ANDROMEDA_SCORE_LOCAL_ASYNC_FALLBACK", "false")

    class SessionProxy:
        def __init__(self, session):
            self._session = session

        def __getattr__(self, name):
            return getattr(self._session, name)

        def close(self):
            return None

    monkeypatch.setattr(meta_andromeda_service_module, "SessionLocal", lambda: SessionProxy(db))

    state = {"calls": 0}
    original_generate = runtime_adapter.generate_score_result

    async def flaky_generate(score_payload):
        state["calls"] += 1
        if state["calls"] == 1:
            raise RuntimeError("transient_runtime_error")
        return await original_generate(score_payload)

    monkeypatch.setattr(runtime_adapter, "generate_score_result", flaky_generate)

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores",
        json={
            "asset_uri": "storage://meta-andromeda/uploads/test/retry.png",
            "asset_type": "image",
            "asset_id": "asset_retry_score",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
        },
    )

    assert response.status_code == 201
    score_event_id = response.json()["score_event_id"]

    first_attempt = await MetaAndromedaService.process_score_event(score_event_id)
    assert first_attempt["status"] == "queued"
    assert first_attempt["attempt_count"] == 1
    assert first_attempt["error_message"] == "transient_runtime_error"

    second_attempt = await MetaAndromedaService.process_score_event(score_event_id)
    assert second_attempt["status"] == "completed"
    assert second_attempt["attempt_count"] == 2

    monitoring = MetaAndromedaService.get_monitoring_summary(db)
    assert monitoring["worker_host"]["recent_events"]
    assert any(
        event["event_type"] == "retry_scheduled" for event in monitoring["worker_host"]["recent_events"]
    )


@pytest.mark.asyncio
async def test_meta_andromeda_score_timeout_marks_failed(meta_andromeda_access, db, monkeypatch):
    monkeypatch.setenv("META_ANDROMEDA_SCORE_TIMEOUT_SECONDS", "0.01")
    monkeypatch.setenv("META_ANDROMEDA_SCORE_MAX_ATTEMPTS", "1")

    class SessionProxy:
        def __init__(self, session):
            self._session = session

        def __getattr__(self, name):
            return getattr(self._session, name)

        def close(self):
            return None

    monkeypatch.setattr(meta_andromeda_service_module, "SessionLocal", lambda: SessionProxy(db))

    original_generate = runtime_adapter.generate_score_result

    async def slow_generate(score_payload):
        await asyncio.sleep(0.05)
        return await original_generate(score_payload)

    monkeypatch.setattr(runtime_adapter, "generate_score_result", slow_generate)

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores",
        json={
            "asset_uri": "storage://meta-andromeda/uploads/test/timeout.png",
            "asset_type": "image",
            "asset_id": "asset_timeout_score",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
        },
    )

    assert response.status_code == 201
    score_event_id = response.json()["score_event_id"]

    result = await MetaAndromedaService.process_score_event(score_event_id)
    assert result["status"] == "failed"
    assert "timed out" in result["error_message"]

    monitoring = MetaAndromedaService.get_monitoring_summary(db)
    assert monitoring["worker_host"]["dead_letter_count"] >= 1
    assert monitoring["worker_host"]["dead_letters"]
    assert monitoring["worker_host"]["dead_letters"][0]["failure_stage"] == "runtime"


@pytest.mark.asyncio
async def test_meta_andromeda_asset_prep_does_not_block_event_loop(meta_andromeda_access, db, monkeypatch):
    """docs/24 Wave 1 迴歸測試：素材準備（DB 查詢/讀檔/ffmpeg 抽幀）必須整段丟到
    asyncio.to_thread 執行，不能直接卡在 event loop 上。這裡用同步 time.sleep 模擬
    阻塞 I/O，並在同一段時間內跑一個心跳 coroutine；若素材準備仍卡在 loop 上，
    心跳會完全停擺，heartbeat 次數會遠低於預期次數。
    """
    monkeypatch.setenv("META_ANDROMEDA_SCORING_PROVIDER", "heuristic")

    def blocking_prepare(score_payload):
        time.sleep(0.3)
        return None

    monkeypatch.setattr(
        MetaAndromedaRuntimeAdapter, "_prepare_asset_context", staticmethod(blocking_prepare)
    )

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores",
        json={
            "asset_uri": "storage://meta-andromeda/uploads/test/loop-heartbeat.png",
            "asset_type": "image",
            "asset_id": "asset_loop_heartbeat_score",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
        },
    )
    assert response.status_code == 201
    score_event_id = response.json()["score_event_id"]
    repository.mark_score_processing(db, score_event_id)
    current = repository.get_review_queue_detail(db, score_event_id)

    heartbeat_count = 0

    async def heartbeat():
        nonlocal heartbeat_count
        for _ in range(15):
            await asyncio.sleep(0.02)
            heartbeat_count += 1

    await asyncio.gather(
        runtime_adapter.generate_score_result(current),
        heartbeat(),
    )

    # 0.3 秒的阻塞 I/O 若真的卡住 event loop，15 次、每次 0.02s 的心跳幾乎跑不完；
    # 丟進 to_thread 後心跳應該能照常跑滿。
    assert heartbeat_count >= 10


@pytest.mark.unit
def test_meta_andromeda_monitoring_summary_uses_real_latency_metrics(meta_andromeda_access, db):
    from database.models.meta_andromeda import MetaAndromedaScoreEvent
    from datetime import datetime, timedelta, timezone

    _clear_meta_andromeda_operational_data(db)

    base = datetime(2026, 6, 18, 12, 0, tzinfo=timezone.utc)
    db.add_all(
        [
            MetaAndromedaScoreEvent(
                id="lat_evt_1",
                status="completed",
                asset_uri="storage://latency/1.png",
                asset_type="image",
                request_mode="auto",
                objective="purchase",
                placement_family="feed",
                market="TW",
                queued_at=base,
                completed_at=base + timedelta(seconds=2),
                created_at=base,
                updated_at=base + timedelta(seconds=2),
            ),
            MetaAndromedaScoreEvent(
                id="lat_evt_2",
                status="failed",
                asset_uri="storage://latency/2.png",
                asset_type="image",
                request_mode="auto",
                objective="purchase",
                placement_family="feed",
                market="TW",
                queued_at=base + timedelta(seconds=1),
                failed_at=base + timedelta(seconds=5),
                created_at=base + timedelta(seconds=1),
                updated_at=base + timedelta(seconds=5),
            ),
            MetaAndromedaScoreEvent(
                id="lat_evt_3",
                status="queued",
                asset_uri="storage://latency/3.png",
                asset_type="image",
                request_mode="auto",
                objective="purchase",
                placement_family="feed",
                market="TW",
                queued_at=base + timedelta(seconds=2),
                created_at=base + timedelta(seconds=2),
                updated_at=base + timedelta(seconds=2),
            ),
        ]
    )
    db.commit()

    response = meta_andromeda_access.get("/api/meta-andromeda/monitoring/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["jobs"]["score-request"]["latency_ms"]["avg"] == 3000
    assert payload["jobs"]["score-request"]["latency_ms"]["p95"] == 4000
    assert payload["jobs"]["score-request"]["latency_ms"]["max"] == 4000
    assert payload["jobs"]["score-request"]["queue_depth"]["current"] == 1
    assert payload["jobs"]["score-request"]["queue_depth"]["peak"] >= 2


@pytest.mark.unit
def test_meta_andromeda_heuristic_runtime_uses_lower_score_and_dynamic_confidence():
    from modules.meta_andromeda.runtime import build_heuristic_score_result
    from modules.meta_andromeda.model_registry import model_registry

    registry_entry = model_registry.get_entry("candidate_v0")
    result = build_heuristic_score_result(
        {
            "asset_type": "image",
            "objective": "purchase",
            "request_mode": "auto",
            "placement_family": "all",
            "request_context": {
                "headline": "",
                "primary_text": "",
                "cta": "",
                "objective": "purchase",
                "placement_family": "all",
                "market": "TW",
            },
        },
        registry_entry,
    )

    assert result["overall_score"] < 60
    assert result["roas_prediction"]["confidence"] != 0.61
    assert result["lineage"]["label_policy_version"] == "ma_label_policy_v2"


@pytest.mark.unit
def test_meta_andromeda_scheduler_disabled_skips_score_job_registration(monkeypatch):
    scheduled = []

    monkeypatch.setattr(scheduler_module, "is_scheduler_enabled", lambda: False)
    monkeypatch.setattr(
        scheduler_module.scheduler,
        "add_job",
        lambda *args, **kwargs: scheduled.append({"args": args, "kwargs": kwargs}),
    )

    job = scheduler_module.add_meta_andromeda_score_job("ma_evt_scheduler_disabled", delay_seconds=0)

    assert job is None
    assert scheduled == []


@pytest.mark.unit
def test_meta_andromeda_mark_score_processing_claim_is_single_shot(meta_andromeda_access, db):
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores",
        json={
            "asset_uri": "storage://meta-andromeda/uploads/test/claim-once.png",
            "asset_type": "image",
            "asset_id": "asset_claim_once",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
        },
    )

    assert response.status_code == 201
    score_event_id = response.json()["score_event_id"]

    first_claim = repository.mark_score_processing(db, score_event_id)
    second_claim = repository.mark_score_processing(db, score_event_id)
    latest = repository.get_review_queue_detail(db, score_event_id)

    assert first_claim is not None
    assert second_claim is None
    assert latest["status"] == "processing"
    assert latest["attempt_count"] == 1


@pytest.mark.unit
def test_meta_andromeda_external_worker_completed_callback_is_idempotent(meta_andromeda_access, db, monkeypatch):
    from database.models.meta_andromeda import MetaAndromedaWorkerEvent

    monkeypatch.setenv("META_ANDROMEDA_EXTERNAL_WORKER_SHARED_SECRET", "worker-secret")

    queued_response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores",
        json={
            "asset_uri": "storage://meta-andromeda/uploads/test/external-worker-idempotent.png",
            "asset_type": "image",
            "asset_id": "asset_external_worker_idempotent",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
        },
    )
    score_event_id = queued_response.json()["score_event_id"]
    runtime_job_id = queued_response.json()["runtime_job_id"]

    callback_payload = {
        "event_type": "completed",
        "queue_host": "external_webhook",
        "runtime_job_id": runtime_job_id,
        "worker_id": "worker-a",
        "receipt_id": "receipt_cb_idempotent",
        "result_payload": {
            "prediction_mode": "diagnostic_plus_roas",
            "overall_score": 86,
            "roas_band": "high",
            "model_version": "cand_v2026_06_05_a",
            "diagnostic_breakdown": {"cta_presence": "clear"},
            "risk_tags": ["external_worker"],
            "top_positive_drivers": ["clear CTA"],
            "top_negative_drivers": ["needs more variants"],
            "explanations": {"summary": "Completed by external worker."},
        },
    }
    raw_body = json.dumps(callback_payload).encode("utf-8")
    signature = hmac.new(b"worker-secret", raw_body, hashlib.sha256).hexdigest()

    response1 = meta_andromeda_access.post(
        f"/api/meta-andromeda/worker/score-events/{score_event_id}/callbacks",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Meta-Andromeda-Worker-Signature": signature,
        },
    )
    response2 = meta_andromeda_access.post(
        f"/api/meta-andromeda/worker/score-events/{score_event_id}/callbacks",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Meta-Andromeda-Worker-Signature": signature,
        },
    )

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response2.json()["current_status"] == "completed"
    assert (
        db.query(MetaAndromedaWorkerEvent)
        .filter(
            MetaAndromedaWorkerEvent.score_event_id == score_event_id,
            MetaAndromedaWorkerEvent.event_type == "external_worker_completed",
        )
        .count()
        == 1
    )


@pytest.mark.unit
def test_meta_andromeda_external_worker_stale_failed_callback_does_not_override_completed(
    meta_andromeda_access,
    db,
    monkeypatch,
):
    monkeypatch.setenv("META_ANDROMEDA_EXTERNAL_WORKER_SHARED_SECRET", "worker-secret")

    queued_response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores",
        json={
            "asset_uri": "storage://meta-andromeda/uploads/test/external-worker-stale.png",
            "asset_type": "image",
            "asset_id": "asset_external_worker_stale",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
        },
    )
    score_event_id = queued_response.json()["score_event_id"]
    runtime_job_id = queued_response.json()["runtime_job_id"]

    completed_payload = {
        "event_type": "completed",
        "queue_host": "external_webhook",
        "runtime_job_id": runtime_job_id,
        "worker_id": "worker-a",
        "receipt_id": "receipt_cb_stale_completed",
        "result_payload": {
            "prediction_mode": "diagnostic_plus_roas",
            "overall_score": 81,
            "roas_band": "mid",
            "model_version": "cand_v2026_06_05_a",
            "diagnostic_breakdown": {"cta_presence": "clear"},
            "risk_tags": ["external_worker"],
            "top_positive_drivers": ["clear CTA"],
            "top_negative_drivers": ["needs more variants"],
            "explanations": {"summary": "Completed first."},
        },
    }
    failed_payload = {
        "event_type": "failed",
        "queue_host": "external_webhook",
        "runtime_job_id": runtime_job_id,
        "worker_id": "worker-a",
        "receipt_id": "receipt_cb_stale_failed",
        "error_message": "late_failure",
        "retryable": False,
    }

    for payload in (completed_payload, failed_payload):
        raw_body = json.dumps(payload).encode("utf-8")
        signature = hmac.new(b"worker-secret", raw_body, hashlib.sha256).hexdigest()
        response = meta_andromeda_access.post(
            f"/api/meta-andromeda/worker/score-events/{score_event_id}/callbacks",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Meta-Andromeda-Worker-Signature": signature,
            },
        )
        assert response.status_code == 200

    detail = MetaAndromedaService.get_score_detail(db, score_event_id)
    assert detail["status"] == "completed"
    assert detail["error_message"] is None


@pytest.mark.asyncio
async def test_meta_andromeda_openrouter_invalid_schema_falls_back_to_heuristic(meta_andromeda_access, db, monkeypatch):
    from services.ai.openrouter_client import OpenRouterClient

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores",
        json={
            "asset_uri": "https://cdn.example.com/meta-andromeda/test-schema.png",
            "asset_type": "image",
            "asset_id": "asset_invalid_schema",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
        },
    )
    score_event_id = response.json()["score_event_id"]
    repository.mark_score_processing(db, score_event_id)
    current = repository.get_review_queue_detail(db, score_event_id)

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("META_ANDROMEDA_SCORING_PROVIDER", "openrouter")

    def fake_init(self, api_key=None):
        self.api_key = api_key or "test-openrouter-key"
        self.client = object()
        self.model_name = "deepseek/deepseek-v4-flash"

    def fake_generate_content(self, *args, **kwargs):
        return json.dumps(
            {
                "overall_score": "not-a-number",
                "roas_band": "extreme",
                "top_positive_drivers": "invalid",
                "top_negative_drivers": [],
                "risk_tags": [],
                "diagnostic_breakdown": {},
                "summary": "bad schema",
            }
        )

    monkeypatch.setattr(OpenRouterClient, "__init__", fake_init)
    monkeypatch.setattr(OpenRouterClient, "generate_content", fake_generate_content)

    result = await runtime_adapter.generate_score_result(current)

    assert result["lineage"]["scoring_mode"] == "heuristic"
    assert "provider_fallback" in result["risk_tags"]
