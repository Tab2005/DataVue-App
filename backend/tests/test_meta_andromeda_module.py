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
import core.scheduler as scheduler_module
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
def meta_andromeda_access(client, db, sample_admin_user):
    repository.ensure_seed_data(db)
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
    repository.ensure_seed_data(db)
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


def _clear_meta_andromeda_operational_data(db) -> None:
    from database.models.meta_andromeda import (
        MetaAndromedaDeadLetter,
        MetaAndromedaDriftReport,
        MetaAndromedaFeedbackEvent,
        MetaAndromedaObservedCreative,
        MetaAndromedaScoreEvent,
        MetaAndromedaWorkerEvent,
    )

    db.query(MetaAndromedaDeadLetter).delete()
    db.query(MetaAndromedaWorkerEvent).delete()
    db.query(MetaAndromedaFeedbackEvent).delete()
    db.query(MetaAndromedaDriftReport).delete()
    db.query(MetaAndromedaObservedCreative).delete()
    db.query(MetaAndromedaScoreEvent).delete()
    db.commit()


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
def test_meta_andromeda_upload_rejects_empty_file(meta_andromeda_access):
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/assets:upload",
        data={
            "asset_type": "image",
            "source_filename": "empty.png",
        },
        files={"file": ("empty.png", b"", "image/png")},
    )

    assert response.status_code == 400
    assert (response.json().get("detail") or response.json().get("error")) == "upload_empty_file"


@pytest.mark.unit
def test_meta_andromeda_upload_rejects_mime_extension_mismatch(meta_andromeda_access):
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/assets:upload",
        data={
            "asset_type": "image",
            "source_filename": "creative.png",
        },
        files={"file": ("creative.png", b"fake-bytes", "video/mp4")},
    )

    assert response.status_code == 415
    assert (response.json().get("detail") or response.json().get("error")) == "upload_mime_not_allowed"


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
    assert payload["drift_status"] == "insufficient_data"

    monitoring = meta_andromeda_access.get("/api/meta-andromeda/monitoring/summary").json()
    assert any(report["window_kind"] == "last_7d" for report in monitoring["latest_drift_reports"])


@pytest.mark.unit
def test_meta_andromeda_drift_accuracy_and_mae_calculation(meta_andromeda_access, db):
    from database.models.meta_andromeda import MetaAndromedaObservedCreative, MetaAndromedaScoreEvent
    
    # 清除現有的相關資料，確保測試環境純淨
    db.query(MetaAndromedaObservedCreative).delete()
    db.query(MetaAndromedaScoreEvent).delete()
    db.commit()

    # 1. 建立 5 筆預測與真實績效完全吻合的 healthy 數據
    # 區間切分: low < 1.5, 1.5 <= mid < 3.5, high >= 3.5
    test_cases = [
        {"uri": "uri_1", "pred_band": "high", "real_roas": 5.0},  # high == high
        {"uri": "uri_2", "pred_band": "mid", "real_roas": 2.0},   # mid == mid
        {"uri": "uri_3", "pred_band": "low", "real_roas": 0.5},   # low == low
        {"uri": "uri_4", "pred_band": "high", "real_roas": 4.0},  # high == high
        {"uri": "uri_5", "pred_band": "mid", "real_roas": 3.0},   # mid == mid
    ]

    for idx, tc in enumerate(test_cases):
        # 建立 Observed Creative
        obs = MetaAndromedaObservedCreative(
            id=f"test_obs_{idx}",
            asset_uri=tc["uri"],
            source_platform="facebook_ads",
            source_account_id="act_12345",
            ad_id=f"ad_{idx}",
            placement_family="feed",
            market="TW",
            media_type="image",
            observation_window_kind="last_7d",
            observation_window_start="2026-06-09",
            observation_window_end="2026-06-16",
            source_fetched_at="2026-06-16T12:00:00Z",
            performance_snapshot={"roas": tc["real_roas"]}
        )
        db.add(obs)

        # 建立對應的 completed ScoreEvent
        score_evt = MetaAndromedaScoreEvent(
            id=f"test_score_{idx}",
            status="completed",
            asset_uri=tc["uri"],
            asset_type="image",
            request_mode="manual",
            objective="CONVERSIONS",
            placement_family="feed",
            market="TW",
            roas_band=tc["pred_band"]
        )
        db.add(score_evt)

    db.commit()

    # 觸發 Drift 診斷
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/drift:trigger",
        json={"window_kind": "last_7d", "note": "healthy check"},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["drift_status"] == "healthy"
    assert payload["report_payload"]["accuracy"] == 1.0
    assert payload["report_payload"]["mae"] == 0.0

    # 2. 修改為預估與實際嚴重偏離的 drifted 數據
    # 5 筆預估都是 high (3)，實際均為 low (1, ROAS=0.5)
    db.query(MetaAndromedaScoreEvent).update({"roas_band": "high"})
    db.commit()
    
    # 重新觸發
    response2 = meta_andromeda_access.post(
        "/api/meta-andromeda/drift:trigger",
        json={"window_kind": "last_7d", "note": "drifted check"},
    )
    assert response2.status_code == 201
    payload2 = response2.json()
    assert payload2["drift_status"] == "drifted"
    assert payload2["report_payload"]["accuracy"] == 0.4
    assert payload2["report_payload"]["mae"] == 0.8


@pytest.mark.unit
def test_meta_andromeda_drift_matching_by_checksum(meta_andromeda_access, db):
    from database.models.meta_andromeda import (
        MetaAndromedaAsset,
        MetaAndromedaObservedCreative,
        MetaAndromedaScoreEvent
    )
    
    db.query(MetaAndromedaObservedCreative).delete()
    db.query(MetaAndromedaScoreEvent).delete()
    db.query(MetaAndromedaAsset).delete()
    db.commit()

    checksums = ["sum_1", "sum_2", "sum_3", "sum_4", "sum_5"]
    
    for idx, cs in enumerate(checksums):
        asset_obs = MetaAndromedaAsset(
            id=f"ast_obs_{idx}",
            asset_uri=f"storage://meta-andromeda/obs_{idx}.png",
            storage_backend="filesystem",
            storage_key=f"obs_{idx}.png",
            asset_type="image",
            source_filename=f"obs_{idx}.png",
            checksum_sha256=cs,
        )
        asset_pred = MetaAndromedaAsset(
            id=f"ast_pred_{idx}",
            asset_uri=f"storage://meta-andromeda/pred_{idx}.png",
            storage_backend="filesystem",
            storage_key=f"pred_{idx}.png",
            asset_type="image",
            source_filename=f"pred_{idx}.png",
            checksum_sha256=cs,
        )
        db.add(asset_obs)
        db.add(asset_pred)
        db.flush()

        obs = MetaAndromedaObservedCreative(
            id=f"test_obs_cs_{idx}",
            asset_id=asset_obs.id,
            asset_uri=asset_obs.asset_uri,
            source_platform="facebook_ads",
            source_account_id="act_12345",
            ad_id=f"ad_cs_{idx}",
            placement_family="feed",
            market="TW",
            media_type="image",
            observation_window_kind="last_7d",
            observation_window_start="2026-06-09",
            observation_window_end="2026-06-16",
            source_fetched_at="2026-06-16T12:00:00Z",
            performance_snapshot={"roas": 2.0}
        )
        db.add(obs)

        score_evt = MetaAndromedaScoreEvent(
            id=f"test_score_cs_{idx}",
            status="completed",
            asset_id=asset_pred.id,
            asset_uri=asset_pred.asset_uri,
            asset_type="image",
            request_mode="manual",
            objective="CONVERSIONS",
            placement_family="feed",
            market="TW",
            roas_band="mid"
        )
        db.add(score_evt)

    db.commit()

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/drift:trigger",
        json={"window_kind": "last_7d", "note": "checksum match check"},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["drift_status"] == "healthy"
    assert payload["report_payload"]["total_matched"] == 5
    assert payload["report_payload"]["accuracy"] == 1.0


@pytest.mark.unit
def test_meta_andromeda_monitoring_summary_does_not_reseed_read_path(meta_andromeda_access, db):
    from database.models.meta_andromeda import (
        MetaAndromedaDriftReport,
        MetaAndromedaScoreEvent,
        MetaAndromedaWorkerEvent,
    )

    _clear_meta_andromeda_operational_data(db)

    response = meta_andromeda_access.get("/api/meta-andromeda/monitoring/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["latest_drift_reports"] == []
    assert payload["worker_host"]["recent_events"] == []
    assert db.query(MetaAndromedaScoreEvent).count() == 0
    assert db.query(MetaAndromedaWorkerEvent).count() == 0
    assert db.query(MetaAndromedaDriftReport).count() == 0


@pytest.mark.unit
def test_meta_andromeda_drift_trigger_does_not_persist_mock_scores(meta_andromeda_access, db):
    from database.models.meta_andromeda import MetaAndromedaObservedCreative, MetaAndromedaScoreEvent

    _clear_meta_andromeda_operational_data(db)

    for idx in range(5):
        db.add(
            MetaAndromedaObservedCreative(
                id=f"no_pred_obs_{idx}",
                asset_uri=f"storage://meta-andromeda/uploads/no-pred-{idx}.png",
                source_platform="facebook_ads",
                source_account_id="act_999",
                ad_id=f"ad_no_pred_{idx}",
                placement_family="feed",
                market="TW",
                media_type="image",
                observation_window_kind="last_7d",
                observation_window_start="2026-06-09",
                observation_window_end="2026-06-16",
                source_fetched_at="2026-06-16T12:00:00Z",
                performance_snapshot={"roas": 1.2 + idx * 0.1},
                lineage={"source": "unit_test"},
            )
        )
    db.commit()

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/drift:trigger",
        json={"window_kind": "last_7d", "note": "missing predictions should not backfill"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["drift_status"] == "insufficient_data"
    assert db.query(MetaAndromedaScoreEvent).count() == 0


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
def test_meta_andromeda_observation_import_auto_creates_score_event(
    meta_andromeda_access,
    db,
    monkeypatch,
):
    from database import MetaAndromedaScoreEvent
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Auto Score Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text="Primary copy",
            headline="Headline copy",
            cta="SHOP_NOW",
            media_url="https://cdn.example.com/auto-score-ad.png",
            media_type="image",
            performance_snapshot={"roas": 2.85},
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": b"auto-score-image-bytes",
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
    monkeypatch.setattr(
        meta_andromeda_service_module.queue_host_adapter,
        "enqueue_score_event",
        lambda score_event_id, delay_seconds=1.0: {
            "accepted": True,
            "queue_host": "database_queue",
            "dispatch_mode": "db_backlog",
            "delay_seconds": delay_seconds,
        },
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
    assert payload["score_event_id"] is None
    assert payload["score_status"] == "queued_background"
    assert payload["runtime_job_id"] is None

    score_event = (
        db.query(MetaAndromedaScoreEvent)
        .filter(MetaAndromedaScoreEvent.asset_uri == payload["asset_uri"])
        .one()
    )
    assert score_event.status == "queued"
    assert score_event.asset_uri == payload["asset_uri"]
    assert score_event.runtime_job_id.startswith("ma_score_")


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
def test_meta_andromeda_observation_import_rejects_disallowed_media_host(meta_andromeda_access, monkeypatch):
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Blocked Host Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text=None,
            headline=None,
            cta=None,
            media_url="https://evil.example.net/blocked.png",
            media_type="image",
            performance_snapshot={"roas": 2.0},
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
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

    assert response.status_code == 400
    assert (response.json().get("detail") or response.json().get("error")) == "observed_media_url_host_not_allowed"


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


@pytest.mark.unit
def test_sync_calibration_dataset_endpoint(meta_andromeda_access, db):
    from database.models.meta_andromeda import (
        MetaAndromedaCalibrationDataset,
        MetaAndromedaCalibrationItem,
        MetaAndromedaObservedCreative,
        MetaAndromedaScoreEvent,
    )
    
    # 確保資料庫純淨
    db.query(MetaAndromedaObservedCreative).delete()
    db.query(MetaAndromedaScoreEvent).delete()
    db.commit()

    # 建立一個有偏差的配對 (pred: high vs real: low)
    obs = MetaAndromedaObservedCreative(
        id="obs_to_calibrate",
        asset_uri="cal_uri_1",
        source_platform="facebook_ads",
        source_account_id="act_12345",
        ad_id="ad_cal_1",
        placement_family="feed",
        market="TW",
        media_type="image",
        observation_window_kind="last_7d",
        observation_window_start="2026-06-09",
        observation_window_end="2026-06-16",
        source_fetched_at="2026-06-16T12:00:00Z",
        performance_snapshot={"roas": 0.5}  # low (1)
    )
    db.add(obs)

    score_evt = MetaAndromedaScoreEvent(
        id="score_to_calibrate",
        status="completed",
        asset_uri="cal_uri_1",
        asset_type="image",
        request_mode="manual",
        objective="CONVERSIONS",
        placement_family="feed",
        market="TW",
        roas_band="high"  # high (3), err = abs(3 - 1) = 2 > 0
    )
    db.add(score_evt)
    db.commit()

    # 呼叫 API 同步
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/calibration/sync",
        json={"window_kind": "last_7d", "excluded_observed_ids": []}
    )
    assert response.status_code == 201
    payload = response.json()
    assert "dataset_id" in payload
    assert payload["synced_count"] == 1
    assert payload["item_count"] == 1
    assert payload["status"] == "queued_for_calibration"
    assert payload["label_policy_version"] == "ma_label_policy_v2"

    # 檢查資料庫中 Observed Creative 的 lineage["calibration"] 是否被寫入
    obs_db = db.query(MetaAndromedaObservedCreative).filter(MetaAndromedaObservedCreative.id == "obs_to_calibrate").first()
    assert obs_db.lineage["calibration"]["dataset_id"] == payload["dataset_id"]
    assert obs_db.lineage["calibration"]["error"] == 2
    assert obs_db.lineage["calibration"]["label_policy_version"] == "ma_label_policy_v2"

    dataset = db.query(MetaAndromedaCalibrationDataset).filter(MetaAndromedaCalibrationDataset.id == payload["dataset_id"]).one()
    item = db.query(MetaAndromedaCalibrationItem).filter(MetaAndromedaCalibrationItem.dataset_id == payload["dataset_id"]).one()
    assert dataset.synced_count == 1
    assert dataset.label_policy_version == "ma_label_policy_v2"
    assert item.prediction_band == "high"
    assert item.observed_band == "low"


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


@pytest.mark.asyncio
async def test_meta_andromeda_storage_image_is_encoded_and_sent_as_data_uri(
    db,
    sample_admin_user,
    tmp_path,
    monkeypatch,
):
    from database.models.meta_andromeda import MetaAndromedaAsset
    from modules.meta_andromeda.runtime import runtime_adapter
    from services.ai.openrouter_client import OpenRouterClient

    monkeypatch.setenv("META_ANDROMEDA_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("META_ANDROMEDA_SCORING_PROVIDER", "openrouter")

    storage_key = "uploads/test/base64-vision.png"
    stored_path = tmp_path / storage_key
    stored_path.parent.mkdir(parents=True, exist_ok=True)
    stored_path.write_bytes(b"fake-image-bytes-for-base64")

    asset = MetaAndromedaAsset(
        id="asset_base64_multimodal",
        asset_uri="storage://meta-andromeda/uploads/test/base64-vision.png",
        storage_backend="filesystem",
        storage_key=storage_key,
        asset_type="image",
        source_filename="base64-vision.png",
        checksum_sha256="checksum-base64-vision",
        file_size_bytes=len(b"fake-image-bytes-for-base64"),
        uploaded_by=sample_admin_user.id,
    )
    db.add(asset)
    db.commit()

    class SessionProxy:
        def __init__(self, session):
            self._session = session

        def __getattr__(self, name):
            return getattr(self._session, name)

        def close(self):
            return None

    monkeypatch.setattr("database.SessionLocal", lambda: SessionProxy(db))

    captured = {}

    def fake_init(self, api_key=None):
        self.api_key = api_key or "test-openrouter-key"
        self.client = object()
        self.model_name = "google/gemini-3.5-flash"

    def fake_generate_content(
        self,
        prompt,
        model,
        system_prompt,
        temperature,
        max_tokens,
        timeout_seconds,
        user_content,
    ):
        captured["model"] = model
        captured["user_content"] = user_content
        return json.dumps(
            {
                "overall_score": 83,
                "roas_band": "high",
                "top_positive_drivers": ["CTA 清楚"],
                "top_negative_drivers": ["文案略多"],
                "risk_tags": [],
                "diagnostic_breakdown": {"cta_presence": "清楚"},
                "summary": "模型已收到圖片資料。",
            }
        )

    monkeypatch.setattr(OpenRouterClient, "__init__", fake_init)
    monkeypatch.setattr(OpenRouterClient, "generate_content", fake_generate_content)

    result = await runtime_adapter.generate_score_result(
        {
            "asset_id": asset.id,
            "asset_uri": asset.asset_uri,
            "asset_type": "image",
            "request_mode": "auto",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
            "request_context": {
                "headline": "限時優惠",
                "primary_text": "立即點擊",
                "cta": "Shop Now",
            },
        }
    )

    assert result["status"] == "completed"
    assert captured["model"]
    image_parts = [part for part in captured["user_content"] if part.get("type") == "image_url"]
    assert len(image_parts) == 1
    assert image_parts[0]["image_url"]["url"].startswith("data:image/png;base64,")


def test_meta_andromeda_image_auto_compression():
    import io
    from PIL import Image, ImageDraw
    from modules.meta_andromeda.service import MetaAndromedaService

    # 1. 生成一個大於 400KB 的大圖片以觸發壓縮
    img = Image.new("RGB", (1500, 1500), color="blue")
    draw = ImageDraw.Draw(img)
    # 加入高頻噪點線條使檔案增大
    for i in range(0, 1500, 4):
        draw.line((0, i, 1500, i), fill="red", width=2)
        draw.line((i, 0, i, 1500), fill="green", width=2)
        
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    large_bytes = buf.getvalue()
    
    # 確保產生的測試圖大於 400KB
    assert len(large_bytes) > 400 * 1024

    # 2. 調用壓縮功能
    compressed_bytes = MetaAndromedaService._compress_image(
        large_bytes, "test_large.jpg", "image/jpeg"
    )

    # 3. 驗證壓縮結果
    assert len(compressed_bytes) < len(large_bytes)

    # 讀取壓縮後的圖片，確認尺寸最長邊被限制在 1200 像素以內
    compressed_img = Image.open(io.BytesIO(compressed_bytes))
    width, height = compressed_img.size
    assert max(width, height) <= 1200


# =============================================================================
# docs/23: Non-ROAS objective groups (traffic/awareness/video/engagement) 預測對照補完
# 驗證目標：
#   1. is_predicted_band_eligible() 對所有已知 group 回傳 True；is_roas_band_eligible()
#      仍守住原本 NON_ROAS 路由（heuristic 與 observed_label 繼續走 CTR/CPC 邏輯）
#   2. _DEFAULT_OBJECTIVE_PROFILES 把這四組的 roas_band_eligible 改成 True，並要求
#      prompt 輸出該群組對應的潛力 band（CTR / 品牌記憶度 / VTR / 互動率）
#   3. _validate_provider_result 對四組的非空 band 都會保留下來（不再強制 null）
#   4. _score_to_list_item / _score_to_detail 會在 detail 頁 payload 加 objective_group
#   5. 端對端：mock provider 為四組各回一個 band → 寫入 DB → 從 detail 讀回來仍是 band；
#      sync_calibration_dataset 與 create_drift_report 不再把這四組當 skipped_not_band_eligible
# =============================================================================


@pytest.mark.unit
def test_objective_routing_is_predicted_band_eligible_covers_all_known_groups():
    """docs/23 step 1: is_predicted_band_eligible() 對所有已知 group（含 lead /
    conversion / app）回傳 True，僅 unknown 為 False。"""
    from modules.meta_andromeda.objective_routing import (
        CONVERSION,
        LEAD,
        TRAFFIC,
        AWARENESS,
        ENGAGEMENT,
        VIDEO,
        APP,
        UNKNOWN,
        is_predicted_band_eligible,
        is_roas_band_eligible,
        KNOWN_OBJECTIVE_GROUPS,
    )

    for group in KNOWN_OBJECTIVE_GROUPS:
        assert is_predicted_band_eligible(group) is True, f"{group} 應該是 True"
    assert is_predicted_band_eligible(UNKNOWN) is False

    # 守住原本的 NON_ROAS 路由——heuristic fallback 與 observed_label 邏輯不動
    assert is_roas_band_eligible(TRAFFIC) is False
    assert is_roas_band_eligible(AWARENESS) is False
    assert is_roas_band_eligible(ENGAGEMENT) is False
    assert is_roas_band_eligible(VIDEO) is False
    # conversion / lead / app 走 ROAS/CPA 邏輯
    assert is_roas_band_eligible(CONVERSION) is True
    assert is_roas_band_eligible(LEAD) is True
    assert is_roas_band_eligible(APP) is True


@pytest.mark.unit
def test_default_objective_profiles_make_non_roas_groups_band_eligible():
    """docs/23 step 2: _DEFAULT_OBJECTIVE_PROFILES 把 traffic/awareness/video/
    engagement 的 roas_band_eligible 改為 True，prompt 也不再寫「Set roas_band to
    null」。"""
    from modules.meta_andromeda.runtime import _DEFAULT_OBJECTIVE_PROFILES

    for group in ("traffic", "awareness", "video", "engagement"):
        profile = _DEFAULT_OBJECTIVE_PROFILES[group]
        assert profile["roas_band_eligible"] is True, (
            f"{group} 應該 roas_band_eligible=True（doc/23 step 2）"
        )
        prompt = profile["user_prompt_template"]
        assert "Set roas_band to null" not in prompt, (
            f"{group} prompt 仍含有『Set roas_band to null』，需要改成可比對 band 要求"
        )
        assert "high/mid/low" in prompt, (
            f"{group} prompt 沒要求輸出 high/mid/null band"
        )

    # lead 原本就走這套設計，避免本次改動影響到 lead
    lead_profile = _DEFAULT_OBJECTIVE_PROFILES["lead"]
    assert lead_profile["roas_band_eligible"] is True
    assert "LEAD QUALITY BAND" in lead_profile["user_prompt_template"]


@pytest.mark.unit
def test_validate_provider_result_preserves_band_for_non_roas_groups():
    """docs/23 step 3: AI provider 對 traffic/awareness/video/engagement 真的回
    band 時，_validate_provider_result 不會把它強制 null 掉。"""
    from modules.meta_andromeda.runtime import _validate_provider_result
    from modules.meta_andromeda.model_registry import model_registry

    registry_entry = model_registry.get_entry("candidate_v0")

    for group, band in (
        ("traffic", "high"),
        ("awareness", "mid"),
        ("video", "low"),
        ("engagement", "high"),
    ):
        parsed = {
            "overall_score": 72,
            "roas_band": band,
            "top_positive_drivers": ["測試"],
            "top_negative_drivers": [],
            "risk_tags": [],
            "diagnostic_breakdown": {
                "thumb_stop": {"score": 70, "reasoning": "test"},
            },
            "summary": f"{group} 評分測試",
        }
        result = _validate_provider_result(
            parsed,
            {
                "asset_type": "image",
                "objective": group,
                "request_mode": "auto",
                "placement_family": "feed",
                "market": "TW",
                "request_context": {
                    "headline": "h",
                    "primary_text": "p",
                    "cta": "c",
                    "objective": group,
                    "placement_family": "feed",
                    "market": "TW",
                },
            },
            registry_entry,
            roas_band_eligible=True,
            objective_group=group,
        )
        assert result["roas_band"] == band, f"{group} 的 band 應該被保留為 {band}"
        assert result["roas_prediction"]["band"] == band
        assert result["roas_prediction"]["eligible"] is True
        assert result["prediction_mode"] == "diagnostic_plus_roas"
        assert result["lineage"]["objective_group"] == group


@pytest.mark.unit
def test_score_to_list_item_includes_objective_group():
    """docs/23 step 3: _score_to_list_item 把 objective_group 加進 payload，detail
    頁前端才能動態決定該顯示哪個 band 標籤。"""
    from modules.meta_andromeda.repository import MetaAndromedaRepository
    from database.models.meta_andromeda import MetaAndromedaScoreEvent

    class _Stub:
        id = "evt_x"
        status = "completed"
        runtime_job_id = None
        created_at = None
        queued_at = None
        started_at = None
        completed_at = None
        failed_at = None
        updated_at = None
        asset_uri = "storage://x.png"
        asset_type = "image"
        asset_id = "asset_x"
        preview_url = None
        request_mode = "auto"
        objective = "traffic"
        placement_family = "feed"
        market = "TW"
        prediction_mode = "diagnostic_plus_roas"
        overall_score = 70
        roas_band = "high"
        model_version = "v1"
        reviewed = False
        feedback_count = 0
        latest_feedback_decision = None
        feature_manifest_id = None
        error_message = None
        attempt_count = 0
        request_context = {}
        # _score_to_detail 也會讀這些欄位，stub 必須具備
        diagnostic_breakdown = {}
        roas_prediction = None
        risk_tags = []
        top_positive_drivers = []
        top_negative_drivers = []
        explanations = None
        lineage = {}

    item = MetaAndromedaRepository._score_to_list_item(_Stub())
    assert item["objective"] == "traffic"
    assert item["objective_group"] == "traffic"

    # _score_to_detail 透過 _score_to_list_item 組裝，detail 頁 payload 也會有
    detail = MetaAndromedaRepository._score_to_detail(_Stub())
    assert detail["objective_group"] == "traffic"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "objective,expected_group,expected_metric_focus",
    [
        ("traffic", "traffic", "ctr"),
        ("link_clicks", "traffic", "ctr"),
        ("outcome_traffic", "traffic", "ctr"),
        ("brand_awareness", "awareness", "cpm_reach"),
        ("reach", "awareness", "cpm_reach"),
        ("video_views", "video", "vtr"),
        ("outcome_engagement", "engagement", "engagement_rate"),
        ("post_engagement", "engagement", "engagement_rate"),
    ],
)
async def test_non_roas_objectives_resolve_to_correct_group_and_metric_focus(
    objective, expected_group, expected_metric_focus
):
    """docs/23 step 5: 4 個 group（含其常見 objective alias）都解析到正確的
    objective_group，且 prompt profile 的 metric_focus 也正確——這是「觀測端
    labeling.py 走 CTR/CPC 邏輯」與「預測端 prompt 走潛力 band 邏輯」兩條路由
    共用的路由表，必須一致。"""
    from modules.meta_andromeda.objective_routing import resolve_objective_group
    from modules.meta_andromeda.runtime import _DEFAULT_OBJECTIVE_PROFILES

    assert resolve_objective_group(objective) == expected_group
    assert _DEFAULT_OBJECTIVE_PROFILES[expected_group]["metric_focus"] == expected_metric_focus


@pytest.mark.asyncio
async def test_non_roas_group_end_to_end_ai_band_flows_through_to_detail(
    meta_andromeda_access, db, monkeypatch
):
    """docs/23 step 5: traffic 素材的 AI band 應該一路從 mock provider →
    _validate_provider_result → DB score_event → get_review_queue_detail 都被保
    留下來，不會被任何 gate 強制 null。"""
    from database.models.meta_andromeda import MetaAndromedaScoreEvent
    from modules.meta_andromeda.runtime import runtime_adapter, invalidate_prompt_cache
    from services.ai.openrouter_client import OpenRouterClient

    # 確保 prompt profile 是 migration 後的最新版（process 內 _prompt_profile_cache
    # 可能在更早的測試中 cache 過舊的 prompt）
    invalidate_prompt_cache()

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("META_ANDROMEDA_SCORING_PROVIDER", "openrouter")

    def fake_init(self, api_key=None):
        self.api_key = api_key or "test-openrouter-key"
        self.client = object()
        self.model_name = "google/gemini-3.5-flash"

    def fake_generate_content(
        self, prompt, model, system_prompt, temperature, max_tokens, timeout_seconds, user_content
    ):
        # 確認 prompt 真的在向模型要求可比對 band（doc/23 step 2）
        assert "CTR POTENTIAL BAND" in prompt or "roas_band" in prompt
        return json.dumps(
            {
                "overall_score": 78,
                "roas_band": "high",
                "top_positive_drivers": ["thumb-stop 強"],
                "top_negative_drivers": [],
                "risk_tags": [],
                "diagnostic_breakdown": {
                    "thumb_stop": {"score": 80, "reasoning": "test"},
                },
                "summary": "traffic 評分測試",
            }
        )

    monkeypatch.setattr(OpenRouterClient, "__init__", fake_init)
    monkeypatch.setattr(OpenRouterClient, "generate_content", fake_generate_content)

    # 模擬一筆 traffic 素材的 score_event 已經 queued
    score_event = MetaAndromedaScoreEvent(
        id="ma_evt_docs23_traffic_e2e",
        status="queued",
        asset_uri="storage://docs23-traffic.png",
        asset_type="image",
        request_mode="auto",
        objective="traffic",
        placement_family="feed",
        market="TW",
    )
    db.add(score_event)
    db.commit()
    repository.mark_score_processing(db, score_event.id)

    current = repository.get_review_queue_detail(db, score_event.id)
    result = await runtime_adapter.generate_score_result(current)
    repository.mark_score_completed(db, score_event.id, result)

    detail = repository.get_review_queue_detail(db, score_event.id)
    assert detail["status"] == "completed"
    assert detail["objective_group"] == "traffic"
    assert detail["roas_band"] == "high"
    assert detail["roas_prediction"]["band"] == "high"
    assert detail["roas_prediction"]["eligible"] is True
    # 觀測端 labeling 走 NON_ROAS 路由用 CTR/CPC，這層是另一條邏輯，不影響
    assert detail["prediction_mode"] == "diagnostic_plus_roas"


@pytest.mark.unit
def test_non_roas_group_enters_calibration_dataset_when_band_predicted(meta_andromeda_access, db):
    """docs/23 step 5: sync_calibration_dataset 對 traffic 等非 ROAS 群組，只要
    pred.roas_band 非 null 就要納入校準集（之前會被 skipped_not_band_eligible 排除）。"""
    from database.models.meta_andromeda import (
        MetaAndromedaCalibrationDataset,
        MetaAndromedaCalibrationItem,
        MetaAndromedaObservedCreative,
        MetaAndromedaScoreEvent,
    )

    # 確保資料庫乾淨
    db.query(MetaAndromedaObservedCreative).delete()
    db.query(MetaAndromedaScoreEvent).delete()
    db.commit()

    obs = MetaAndromedaObservedCreative(
        id="obs_docs23_traffic",
        asset_uri="docs23_traffic_uri",
        source_platform="facebook_ads",
        source_account_id="act_traffic",
        ad_id="ad_docs23_traffic",
        objective="traffic",  # sync_calibration_dataset 會把這個寫進 CalibrationItem.objective
        placement_family="feed",
        market="TW",
        media_type="image",
        observation_window_kind="last_7d",
        observation_window_start="2026-06-09",
        observation_window_end="2026-06-16",
        source_fetched_at="2026-06-16T12:00:00Z",
        # traffic 走 CTR：CTR 高=好（label_detail.metric=ctr）
        performance_snapshot={"spend": 100.0, "impressions": 5000, "clicks": 250, "ctr": 5.0},
    )
    db.add(obs)

    score_evt = MetaAndromedaScoreEvent(
        id="score_docs23_traffic",
        status="completed",
        asset_uri="docs23_traffic_uri",
        asset_type="image",
        request_mode="auto",
        objective="traffic",  # 非 ROAS 群組
        placement_family="feed",
        market="TW",
        roas_band="high",  # AI 真的回 band（doc/23 step 2 之後這才會發生）
        roas_prediction={"eligible": True, "band": "high", "confidence": 0.7, "reason_if_unavailable": None},
        lineage={"scoring_mode": "ai", "diagnostic_scores": {}},
    )
    db.add(score_evt)
    db.commit()

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/calibration/sync",
        json={"window_kind": "last_7d", "excluded_observed_ids": []},
    )
    assert response.status_code == 201
    payload = response.json()

    dataset = (
        db.query(MetaAndromedaCalibrationDataset)
        .filter(MetaAndromedaCalibrationDataset.id == payload["dataset_id"])
        .one()
    )
    # 之前這個值會是 skipped_not_band_eligible=1, synced_count=0；現在應該 synced_count=1
    assert dataset.summary["skipped_not_band_eligible"] == 0
    assert payload["synced_count"] == 1

    item = (
        db.query(MetaAndromedaCalibrationItem)
        .filter(MetaAndromedaCalibrationItem.dataset_id == payload["dataset_id"])
        .one()
    )
    assert item.objective == "traffic"
    assert item.prediction_band == "high"
    assert item.observed_band in ("high", "mid", "low")  # 動態門檻算出來的 band


@pytest.mark.unit
def test_non_roas_group_enters_drift_report_accuracy_when_band_predicted(meta_andromeda_access, db):
    """docs/23 step 5: create_drift_report 對 traffic 等非 ROAS 群組，只要
    pred.roas_band 非 null 就要納入 accuracy/MAE 計算（之前會被
    `if not pred_roas_eligible: continue` 排除）。"""
    from database.models.meta_andromeda import (
        MetaAndromedaObservedCreative,
        MetaAndromedaScoreEvent,
    )
    from datetime import datetime, timezone

    db.query(MetaAndromedaObservedCreative).delete()
    db.query(MetaAndromedaScoreEvent).delete()
    db.commit()

    obs = MetaAndromedaObservedCreative(
        id="obs_docs23_awareness_drift",
        asset_uri="docs23_awareness_uri",
        source_platform="facebook_ads",
        source_account_id="act_aware",
        ad_id="ad_docs23_awareness",
        objective="brand_awareness",  # labeling.label_observed_band 用這個路由觀測端 metric
        placement_family="feed",
        market="TW",
        media_type="image",
        observation_window_kind="last_7d",
        observation_window_start="2026-06-09",
        observation_window_end="2026-06-16",
        source_fetched_at="2026-06-16T12:00:00Z",
        # awareness 走 CPM/Reach 觀測
        performance_snapshot={"spend": 100.0, "impressions": 5000, "reach": 4000, "cpm": 20.0},
    )
    db.add(obs)

    base = datetime(2026, 6, 16, 12, 0, tzinfo=timezone.utc)
    score_evt = MetaAndromedaScoreEvent(
        id="score_docs23_awareness_drift",
        status="completed",
        asset_uri="docs23_awareness_uri",
        asset_type="image",
        request_mode="auto",
        objective="brand_awareness",
        placement_family="feed",
        market="TW",
        completed_at=base,
        roas_band="mid",
        roas_prediction={"eligible": True, "band": "mid", "confidence": 0.7, "reason_if_unavailable": None},
        lineage={"scoring_mode": "ai", "diagnostic_scores": {}},
    )
    db.add(score_evt)
    db.commit()

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/drift:trigger",
        json={"window_kind": "last_7d"},
    )
    assert response.status_code in (200, 201)
    payload = response.json()
    # docs/23 真正要驗的：traffic/awareness/video/engagement 的素材在 drift
    # report 不再被 skipped_not_band_eligible 排除，會進入 accuracy/MAE 計算。
    # 回傳欄位不是 `matched_count`，而是 `report_payload.total_band_matched` +
    # `matched_details[].band_eligible=true` 兩條線索（小樣本時 drift_status
    # 仍會是 `insufficient_data`，那是另一條獨立邏輯，不影響本次目標）。
    report_payload = payload.get("report_payload", {})
    assert report_payload.get("total_band_matched", 0) >= 1
    matched = report_payload.get("matched_details", [])
    assert matched, "expected at least one matched_details entry for awareness"
    assert matched[0].get("band_eligible") is True
    # 之前被排除時，band_eligible 會是 false 且不會出現在 matched_details 裡


@pytest.mark.unit
def test_heuristic_fallback_still_skips_band_for_non_roas_groups():
    """docs/23 step 4.3.1: heuristic 規則引擎在 traffic/awareness/video/
    engagement 仍不應該湊 band 出來，維持降級模式的明確標示。"""
    from modules.meta_andromeda.runtime import build_heuristic_score_result
    from modules.meta_andromeda.model_registry import model_registry

    registry_entry = model_registry.get_entry("candidate_v0")
    for objective in ("traffic", "brand_awareness", "video_views", "post_engagement"):
        result = build_heuristic_score_result(
            {
                "asset_type": "image",
                "objective": objective,
                "request_mode": "auto",
                "placement_family": "feed",
                "request_context": {
                    "headline": "標題",
                    "primary_text": "內文",
                    "cta": "立即了解",
                    "objective": objective,
                    "placement_family": "feed",
                    "market": "TW",
                },
            },
            registry_entry,
        )
        assert result["roas_band"] is None, (
            f"{objective} 的 heuristic fallback 不該湊 band，會誤導下游"
        )
        assert result["roas_prediction"]["eligible"] is False
        assert result["prediction_mode"] == "diagnostic_only"

