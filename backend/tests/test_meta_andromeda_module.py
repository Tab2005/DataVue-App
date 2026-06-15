"""
Meta Andromeda module integration tests
"""

import asyncio
import hashlib
import hmac
import json
import os
from unittest.mock import Mock

import pytest

import modules.meta_andromeda.service as meta_andromeda_service_module
import modules.meta_andromeda.queue_host as meta_andromeda_queue_host_module
import modules.meta_andromeda.storage as meta_andromeda_storage_module
from modules.auth import dependencies as auth_dependencies
import redis_cache as redis_cache_module
from database import Module, Permission, Role, RolePermission, Team, TeamMember, UserModuleAccess, UserRole
from modules.meta_andromeda.repository import repository
from modules.meta_andromeda.runtime import runtime_adapter
from modules.meta_andromeda.service import MetaAndromedaService
from main import app
from modules.meta_andromeda.dependencies import (
    get_current_meta_andromeda_user,
    require_fb_ads_analytics_view,
    require_fb_ads_module,
    require_meta_andromeda_module,
)


@pytest.fixture
def meta_andromeda_access(client, sample_admin_user):
    app.dependency_overrides[get_current_meta_andromeda_user] = lambda: sample_admin_user
    app.dependency_overrides[require_meta_andromeda_module] = lambda: True
    app.dependency_overrides[require_fb_ads_module] = lambda: True
    app.dependency_overrides[require_fb_ads_analytics_view] = lambda: True
    yield client
    app.dependency_overrides.pop(get_current_meta_andromeda_user, None)
    app.dependency_overrides.pop(require_meta_andromeda_module, None)
    app.dependency_overrides.pop(require_fb_ads_module, None)
    app.dependency_overrides.pop(require_fb_ads_analytics_view, None)


@pytest.fixture
def meta_andromeda_permission_client(client, db, sample_user):
    app.dependency_overrides[get_current_meta_andromeda_user] = lambda: sample_user
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: sample_user
    app.dependency_overrides[auth_dependencies.get_db] = lambda: db
    yield client, sample_user
    app.dependency_overrides.pop(get_current_meta_andromeda_user, None)
    app.dependency_overrides.pop(auth_dependencies.get_current_user, None)
    app.dependency_overrides.pop(auth_dependencies.get_db, None)


def _setup_meta_andromeda_team_access(
    db,
    user,
    *,
    membership_role: UserRole,
    role_key: str,
    grant_module_access: bool = True,
):
    team = Team(name=f"Meta Team {role_key}", owner_id=user.id)
    db.add(team)
    db.flush()

    module = Module(key="meta_andromeda", name="Meta Andromeda", enabled=True)
    db.add(module)
    db.flush()

    db.add(TeamMember(team_id=team.id, user_id=user.id, role=membership_role))
    if grant_module_access:
        db.add(
            UserModuleAccess(
                user_id=user.id,
                team_id=team.id,
                module_id=module.id,
                enabled=True,
            )
        )

    db.commit()
    return team


def _ensure_module(db, *, module_key: str, module_name: str) -> Module:
    module = db.query(Module).filter(Module.key == module_key).first()
    if module is None:
        module = Module(key=module_key, name=module_name, enabled=True)
        db.add(module)
        db.flush()
    return module


def _grant_team_module_access(db, *, user_id: str, team_id: str, module_key: str, module_name: str) -> None:
    module = _ensure_module(db, module_key=module_key, module_name=module_name)
    access = db.query(UserModuleAccess).filter(
        UserModuleAccess.user_id == user_id,
        UserModuleAccess.team_id == team_id,
        UserModuleAccess.module_id == module.id,
    ).first()
    if access is None:
        db.add(
            UserModuleAccess(
                user_id=user_id,
                team_id=team_id,
                module_id=module.id,
                enabled=True,
            )
        )


def _grant_team_role_permission(
    db,
    *,
    role_key: str,
    permission_key: str,
    permission_name: str,
    module_key: str,
    module_name: str,
) -> None:
    role = db.query(Role).filter(Role.key == role_key).first()
    if role is None:
        role = Role(key=role_key, name=role_key, scope="team")
        db.add(role)
        db.flush()

    module = _ensure_module(db, module_key=module_key, module_name=module_name)
    permission = db.query(Permission).filter(Permission.key == permission_key).first()
    if permission is None:
        permission = Permission(
            module_id=module.id,
            key=permission_key,
            name=permission_name,
            category="feature",
        )
        db.add(permission)
        db.flush()

    role_permission = db.query(RolePermission).filter(
        RolePermission.role_id == role.id,
        RolePermission.permission_id == permission.id,
    ).first()
    if role_permission is None:
        db.add(RolePermission(role_id=role.id, permission_id=permission.id))


@pytest.mark.unit
def test_meta_andromeda_ping_returns_payload(meta_andromeda_access):
    response = meta_andromeda_access.get("/api/meta-andromeda/ping")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["module"] == "meta_andromeda"


@pytest.mark.unit
def test_meta_andromeda_upload_persists_file_to_storage_root(meta_andromeda_access, tmp_path):
    os.environ["META_ANDROMEDA_STORAGE_ROOT"] = str(tmp_path)
    try:
        response = meta_andromeda_access.post(
            "/api/meta-andromeda/assets:upload",
            data={
                "asset_type": "image",
                "source_filename": "creative-test.png",
            },
            files={"file": ("creative-test.png", b"fake-image-bytes", "image/png")},
        )
    finally:
        os.environ.pop("META_ANDROMEDA_STORAGE_ROOT", None)

    assert response.status_code == 201
    payload = response.json()
    assert payload["storage_backend"] == "filesystem"
    assert payload["storage_key"].endswith("creative-test.png")
    stored_path = tmp_path / payload["storage_key"]
    assert stored_path.exists()
    assert stored_path.read_bytes() == b"fake-image-bytes"


@pytest.mark.unit
def test_meta_andromeda_upload_supports_s3_compatible_storage(meta_andromeda_access, monkeypatch):
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_BACKEND", "s3_compatible")
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_S3_BUCKET", "meta-andromeda-assets")
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_S3_REGION", "ap-northeast-1")
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_S3_ENDPOINT_URL", "https://minio.example.com")
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_KEY_PREFIX", "shared/meta-andromeda")
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_PUBLIC_BASE_URL", "https://cdn.example.com/meta-andromeda")

    captured = {}

    class FakeS3Client:
        def upload_fileobj(self, Fileobj, Bucket, Key, ExtraArgs=None):
            captured["bytes"] = Fileobj.read()
            captured["bucket"] = Bucket
            captured["key"] = Key
            captured["extra_args"] = ExtraArgs or {}

    monkeypatch.setattr(
        meta_andromeda_storage_module.MetaAndromedaStorageAdapter,
        "_build_s3_client",
        lambda: FakeS3Client(),
    )

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/assets:upload",
        data={
            "asset_type": "image",
            "source_filename": "creative-object.png",
        },
        files={"file": ("creative-object.png", b"object-image-bytes", "image/png")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["storage_backend"] == "s3_compatible"
    assert payload["storage_key"].startswith("shared/meta-andromeda/uploads/")
    assert payload["public_url"].startswith("https://cdn.example.com/meta-andromeda/")
    assert captured["bucket"] == "meta-andromeda-assets"
    assert captured["bytes"] == b"object-image-bytes"
    assert captured["extra_args"]["ContentType"] == "image/png"


@pytest.mark.unit
def test_meta_andromeda_overview_returns_current_integration_state(meta_andromeda_access):
    response = meta_andromeda_access.get("/api/meta-andromeda/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["module"]["key"] == "meta_andromeda"
    assert payload["summary"]["integration_status"] == "in_progress"
    assert payload["summary"]["current_slice"] == "queue_host_observability_enabled"
    assert any(item["key"] == "review_queue" for item in payload["capabilities"])


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
def test_meta_andromeda_monitoring_timeline_returns_event_detail(meta_andromeda_access):
    response = meta_andromeda_access.get("/api/meta-andromeda/monitoring/score-events/ma_evt_20260605_002/timeline")

    assert response.status_code == 200
    payload = response.json()
    assert payload["score_event"]["score_event_id"] == "ma_evt_20260605_002"
    assert "worker_events" in payload
    assert "dead_letters" in payload
    assert payload["feedback"]


@pytest.mark.unit
def test_meta_andromeda_drift_trigger_creates_report_and_alert(meta_andromeda_access, db):
    repository.get_review_queue_detail(db, "ma_evt_20260605_003")
    repository.mark_score_failed(db, "ma_evt_20260605_003", "runtime_failure")
    repository.create_dead_letter(
        db,
        score_event_id="ma_evt_20260605_003",
        queue_host="redis_stream",
        runtime_job_id="job_failure_001",
        failure_stage="runtime",
        attempt_count=1,
        final_error_message="runtime_failure",
        dead_letter_payload={"source": "test"},
    )

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/drift:trigger",
        json={"window_kind": "last_7d", "note": "manual drift review"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["window_kind"] == "last_7d"
    assert payload["drift_status"] == "warning"

    monitoring = meta_andromeda_access.get("/api/meta-andromeda/monitoring/summary").json()
    assert monitoring["active_alerts"]
    assert any(report["window_kind"] == "last_7d" for report in monitoring["latest_drift_reports"])


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


@pytest.mark.unit
def test_meta_andromeda_review_queue_supports_filters(meta_andromeda_access):
    response = meta_andromeda_access.get(
        "/api/meta-andromeda/review-queue",
        params={"status": "completed", "reviewed": "false", "limit": 30},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["status_filter"] == "completed"
    assert payload["summary"]["reviewed_filter"] is False
    assert payload["items"]
    assert all(item["status"] == "completed" for item in payload["items"])
    assert all(item["reviewed"] is False for item in payload["items"])


@pytest.mark.unit
def test_meta_andromeda_review_queue_detail_returns_selected_item(meta_andromeda_access):
    response = meta_andromeda_access.get("/api/meta-andromeda/review-queue/ma_evt_20260605_001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["score_event_id"] == "ma_evt_20260605_001"
    assert payload["status"] == "completed"
    assert payload["top_positive_drivers"]


@pytest.mark.unit
def test_meta_andromeda_feedback_timeline_returns_read_only_entries(meta_andromeda_access):
    response = meta_andromeda_access.get("/api/meta-andromeda/scores/ma_evt_20260605_002/feedback")

    assert response.status_code == 200
    payload = response.json()
    assert payload["score_event_id"] == "ma_evt_20260605_002"
    assert payload["feedback"]
    assert payload["feedback"][0]["decision"] == "revise"


@pytest.mark.unit
def test_meta_andromeda_feedback_submit_updates_timeline(meta_andromeda_access):
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores/ma_evt_20260605_001/feedback",
        json={
            "decision": "approve",
            "reason_codes": ["ready_for_release"],
            "comment": "Looks good.",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["decision"] == "approve"
    assert payload["reason_codes"] == ["ready_for_release"]

    timeline = meta_andromeda_access.get("/api/meta-andromeda/scores/ma_evt_20260605_001/feedback")
    assert timeline.status_code == 200
    timeline_payload = timeline.json()
    assert timeline_payload["feedback"]
    assert timeline_payload["feedback"][-1]["decision"] == "approve"


@pytest.mark.asyncio
async def test_meta_andromeda_score_submit_queues_then_completes(meta_andromeda_access, db):
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


@pytest.mark.unit
def test_meta_andromeda_release_overview_returns_candidates_and_notes(meta_andromeda_access):
    response = meta_andromeda_access.get("/api/meta-andromeda/release/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_production"]["release_status"] == "production"
    assert payload["previous_production"]["release_status"] == "superseded"
    assert payload["candidates"]
    assert payload["history"]
    assert payload["notes"]


@pytest.mark.unit
def test_meta_andromeda_release_approve_updates_history(meta_andromeda_access):
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/release/approve",
        json={"model_version": "cand_v2026_06_05_a", "note": "Ship it"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "approve"
    assert payload["model_version"] == "cand_v2026_06_05_a"

    overview = meta_andromeda_access.get("/api/meta-andromeda/release/overview")
    assert overview.status_code == 200
    overview_payload = overview.json()
    assert overview_payload["history"][0]["action"] == "approve"


@pytest.mark.unit
def test_meta_andromeda_observation_import_accepts_supported_window_contract(meta_andromeda_access, monkeypatch):
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Contract Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text=payload.get("primary_text"),
            headline=payload.get("headline"),
            cta=payload.get("cta"),
            media_url="https://cdn.example.com/contract-ad.png",
            media_type="image",
            performance_snapshot={},
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": b"contract-image-bytes",
            "source_filename": f"{ad_id}.png",
            "content_type": "image/png",
            "asset_type": media_type,
        }

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_download_observed_asset_snapshot",
        staticmethod(fake_download_observed_asset_snapshot),
    )

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_30d",
            "market": "TW",
            "placement_family": "feed",
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "accepted"
    assert payload["source"]["platform"] == "facebook_ads"
    assert payload["source"]["account_id"] == "act_123456789"
    assert payload["source"]["ad_id"] == "120000000000012"
    assert payload["asset_uri"].startswith("storage://meta-andromeda/")
    assert payload["observation_window"]["kind"] == "last_30d"
    assert payload["observation_window"]["start"]
    assert payload["observation_window"]["end"]
    assert payload["observed_creative_id"].startswith("ma_obs_")


@pytest.mark.unit
def test_meta_andromeda_observation_import_rejects_unsupported_window_kind(meta_andromeda_access):
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_14d",
            "market": "TW",
            "placement_family": "feed",
        },
    )

    assert response.status_code == 422


@pytest.mark.unit
def test_meta_andromeda_facebook_importer_normalizes_ad_row():
    from modules.meta_andromeda.importers.facebook_ads_importer import normalize_facebook_ad_row

    candidate = normalize_facebook_ad_row(
        row={
            "campaign_id": "120000000000010",
            "adset_id": "120000000000011",
            "ad_id": "120000000000012",
            "name": "Summer Promo Ad 01",
            "objective": "OUTCOME_SALES",
            "image_url": "https://cdn.example.com/creative.png",
            "spend": 1200.5,
            "impressions": 18234,
            "clicks": 321,
            "purchases": 14,
            "purchase_value": 4800,
            "roas": 2.85,
            "ctr": 1.76,
            "cpc": 3.74,
        },
        account_id="act_123456789",
        market="TW",
        placement_family="feed",
        primary_text="Primary copy",
        headline="Headline copy",
        cta="SHOP_NOW",
        observation_window_kind="last_30d",
        observation_window_start="2026-05-17",
        observation_window_end="2026-06-15",
        source_fetched_at="2026-06-15T00:00:00Z",
    )

    assert candidate.source_platform == "facebook_ads"
    assert candidate.source_account_id == "act_123456789"
    assert candidate.campaign_id == "120000000000010"
    assert candidate.adset_id == "120000000000011"
    assert candidate.ad_id == "120000000000012"
    assert candidate.ad_name == "Summer Promo Ad 01"
    assert candidate.media_url == "https://cdn.example.com/creative.png"
    assert candidate.media_type == "image"
    assert candidate.performance_snapshot["purchases"] == 14
    assert candidate.performance_snapshot["roas"] == 2.85
    assert candidate.observation_window_kind == "last_30d"
    assert candidate.observation_window_start == "2026-05-17"
    assert candidate.observation_window_end == "2026-06-15"


@pytest.mark.unit
def test_meta_andromeda_observation_import_uses_facebook_importer(meta_andromeda_access, monkeypatch):
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Imported Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text=payload["primary_text"],
            headline=payload["headline"],
            cta=payload["cta"],
            media_url="https://cdn.example.com/imported-ad.png",
            media_type="image",
            performance_snapshot={
                "spend": 1200.5,
                "impressions": 18234,
                "clicks": 321,
                "purchases": 14,
                "purchase_value": 4800,
                "roas": 2.85,
                "ctr": 1.76,
                "cpc": 3.74,
            },
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": b"imported-image-bytes",
            "source_filename": f"{ad_id}.png",
            "content_type": "image/png",
            "asset_type": media_type,
        }

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_download_observed_asset_snapshot",
        staticmethod(fake_download_observed_asset_snapshot),
    )

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_30d",
            "market": "TW",
            "placement_family": "feed",
            "primary_text": "Primary copy",
            "headline": "Headline copy",
            "cta": "SHOP_NOW",
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["source"]["ad_id"] == "120000000000012"
    assert payload["asset_uri"].startswith("storage://meta-andromeda/")
    assert payload["performance_snapshot"]["purchases"] == 14
    assert payload["performance_snapshot"]["roas"] == 2.85
    assert payload["observation_window"]["kind"] == "last_30d"


@pytest.mark.unit
def test_meta_andromeda_observation_import_persists_asset_and_observed_record(
    meta_andromeda_access,
    db,
    monkeypatch,
):
    from database import MetaAndromedaAsset, MetaAndromedaObservedCreative
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Persisted Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text=payload["primary_text"],
            headline=payload["headline"],
            cta=payload["cta"],
            media_url="https://cdn.example.com/persisted-ad.png",
            media_type="image",
            performance_snapshot={
                "spend": 1200.5,
                "impressions": 18234,
                "clicks": 321,
                "purchases": 14,
                "purchase_value": 4800,
                "roas": 2.85,
                "ctr": 1.76,
                "cpc": 3.74,
            },
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": b"persisted-image-bytes",
            "source_filename": f"{ad_id}.png",
            "content_type": "image/png",
            "asset_type": media_type,
        }

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_download_observed_asset_snapshot",
        staticmethod(fake_download_observed_asset_snapshot),
    )

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_30d",
            "market": "TW",
            "placement_family": "feed",
            "primary_text": "Primary copy",
            "headline": "Headline copy",
            "cta": "SHOP_NOW",
        },
    )

    assert response.status_code == 202
    payload = response.json()

    stored_asset = db.query(MetaAndromedaAsset).filter(MetaAndromedaAsset.asset_uri == payload["asset_uri"]).one()
    observed = (
        db.query(MetaAndromedaObservedCreative)
        .filter(MetaAndromedaObservedCreative.id == payload["observed_creative_id"])
        .one()
    )

    assert stored_asset.asset_type == "image"
    assert stored_asset.source_filename == "120000000000012.png"
    assert observed.asset_id == stored_asset.id
    assert observed.ad_id == "120000000000012"
    assert observed.source_platform == "facebook_ads"
    assert observed.performance_snapshot["purchases"] == 14
    assert observed.observation_window_kind == "last_30d"


@pytest.mark.unit
def test_meta_andromeda_observation_import_denies_without_fb_ads_module_access(
    meta_andromeda_permission_client,
    db,
    monkeypatch,
):
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Denied Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text=None,
            headline=None,
            cta=None,
            media_url="https://cdn.example.com/denied-ad.png",
            media_type="image",
            performance_snapshot={},
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": b"denied-image-bytes",
            "source_filename": f"{ad_id}.png",
            "content_type": "image/png",
            "asset_type": media_type,
        }

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_download_observed_asset_snapshot",
        staticmethod(fake_download_observed_asset_snapshot),
    )

    client, user = meta_andromeda_permission_client
    team = _setup_meta_andromeda_team_access(
        db,
        user,
        membership_role=UserRole.MEMBER,
        role_key="team_member",
    )
    _grant_team_role_permission(
        db,
        role_key="team_member",
        permission_key="fb_ads:analytics:view",
        permission_name="數據查看",
        module_key="fb_ads",
        module_name="FB Ads",
    )
    db.commit()

    response = client.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        headers={"X-Team-ID": team.id},
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_30d",
            "market": "TW",
            "placement_family": "feed",
        },
    )

    assert response.status_code == 403
    assert "fb_ads" in response.text


@pytest.mark.unit
def test_meta_andromeda_observation_import_denies_without_fb_ads_analytics_permission(
    meta_andromeda_permission_client,
    db,
    monkeypatch,
):
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Denied Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text=None,
            headline=None,
            cta=None,
            media_url="https://cdn.example.com/denied-ad.png",
            media_type="image",
            performance_snapshot={},
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": b"denied-image-bytes",
            "source_filename": f"{ad_id}.png",
            "content_type": "image/png",
            "asset_type": media_type,
        }

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_download_observed_asset_snapshot",
        staticmethod(fake_download_observed_asset_snapshot),
    )

    client, user = meta_andromeda_permission_client
    team = _setup_meta_andromeda_team_access(
        db,
        user,
        membership_role=UserRole.MEMBER,
        role_key="team_member",
    )
    _grant_team_module_access(
        db,
        user_id=user.id,
        team_id=team.id,
        module_key="fb_ads",
        module_name="FB Ads",
    )
    db.commit()

    response = client.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        headers={"X-Team-ID": team.id},
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_30d",
            "market": "TW",
            "placement_family": "feed",
        },
    )

    assert response.status_code == 403
    assert "fb_ads:analytics:view" in response.text


@pytest.mark.unit
def test_meta_andromeda_observation_import_allows_with_fb_ads_module_and_permission(
    meta_andromeda_permission_client,
    db,
    monkeypatch,
):
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Allowed Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text=None,
            headline=None,
            cta=None,
            media_url="https://cdn.example.com/allowed-ad.png",
            media_type="image",
            performance_snapshot={"purchases": 14, "roas": 2.85},
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": b"allowed-image-bytes",
            "source_filename": f"{ad_id}.png",
            "content_type": "image/png",
            "asset_type": media_type,
        }

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_download_observed_asset_snapshot",
        staticmethod(fake_download_observed_asset_snapshot),
    )

    client, user = meta_andromeda_permission_client
    team = _setup_meta_andromeda_team_access(
        db,
        user,
        membership_role=UserRole.MEMBER,
        role_key="team_member",
    )
    _grant_team_module_access(
        db,
        user_id=user.id,
        team_id=team.id,
        module_key="fb_ads",
        module_name="FB Ads",
    )
    _grant_team_role_permission(
        db,
        role_key="team_member",
        permission_key="fb_ads:analytics:view",
        permission_name="數據查看",
        module_key="fb_ads",
        module_name="FB Ads",
    )
    db.commit()

    response = client.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        headers={"X-Team-ID": team.id},
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_30d",
            "market": "TW",
            "placement_family": "feed",
        },
    )

    assert response.status_code == 202
    assert response.json()["source"]["ad_id"] == "120000000000012"


@pytest.mark.unit
def test_meta_andromeda_team_user_without_module_access_is_denied_read_only_endpoint(
    meta_andromeda_permission_client,
    db,
):
    client, user = meta_andromeda_permission_client
    team = _setup_meta_andromeda_team_access(
        db,
        user,
        membership_role=UserRole.VIEWER,
        role_key="team_viewer",
        grant_module_access=False,
    )

    response = client.get("/api/meta-andromeda/overview", headers={"X-Team-ID": team.id})

    assert response.status_code == 403
    assert "meta_andromeda" in response.text


@pytest.mark.unit
def test_meta_andromeda_team_viewer_can_read_overview_with_team_module_access(
    meta_andromeda_permission_client,
    db,
):
    client, user = meta_andromeda_permission_client
    team = _setup_meta_andromeda_team_access(
        db,
        user,
        membership_role=UserRole.VIEWER,
        role_key="team_viewer",
    )

    response = client.get("/api/meta-andromeda/overview", headers={"X-Team-ID": team.id})

    assert response.status_code == 200
    assert response.json()["module"]["key"] == "meta_andromeda"


@pytest.mark.unit
def test_meta_andromeda_team_member_can_submit_feedback_in_team_workspace(
    meta_andromeda_permission_client,
    db,
):
    client, user = meta_andromeda_permission_client
    team = _setup_meta_andromeda_team_access(
        db,
        user,
        membership_role=UserRole.MEMBER,
        role_key="team_member",
    )

    response = client.post(
        "/api/meta-andromeda/scores/ma_evt_20260605_001/feedback",
        headers={"X-Team-ID": team.id},
        json={
            "decision": "approve",
            "reason_codes": ["team_member_feedback"],
            "comment": "Feedback is allowed for team members.",
        },
    )

    assert response.status_code == 201
    assert response.json()["decision"] == "approve"


@pytest.mark.unit
def test_meta_andromeda_team_member_can_trigger_drift_report_and_approve_release(
    meta_andromeda_permission_client,
    db,
):
    client, user = meta_andromeda_permission_client
    team = _setup_meta_andromeda_team_access(
        db,
        user,
        membership_role=UserRole.MEMBER,
        role_key="team_member",
    )

    drift_response = client.post(
        "/api/meta-andromeda/drift:trigger",
        headers={"X-Team-ID": team.id},
        json={"window_kind": "last_7d", "note": "member can operate with module access"},
    )
    release_response = client.post(
        "/api/meta-andromeda/release/approve",
        headers={"X-Team-ID": team.id},
        json={"model_version": "cand_v2026_06_05_a", "note": "member can release with module access"},
    )

    assert drift_response.status_code == 201
    assert drift_response.json()["window_kind"] == "last_7d"
    assert release_response.status_code == 200
    assert release_response.json()["action"] == "approve"
