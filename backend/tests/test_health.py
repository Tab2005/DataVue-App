"""
/health、/api/health、/health/detail 端點測試
屬於最基礎的 smoke test，確認服務可正常啟動與回應
"""
import pytest

from main import app
from modules.auth import dependencies as auth_dependencies


@pytest.mark.unit
def test_health_endpoint_returns_200(client):
    """健康端點應回傳 200 狀態碼"""
    response = client.get("/health")
    assert response.status_code == 200


@pytest.mark.unit
def test_health_endpoint_has_required_fields(client):
    """健康端點回應應包含 status、checks 欄位（checks 內含 database）"""
    response = client.get("/health")
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "meta_andromeda" in data["checks"]


@pytest.mark.unit
def test_api_health_backward_compat(client):
    """/api/health 向後相容路由應正常回應"""
    response = client.get("/api/health")
    assert response.status_code == 200


@pytest.mark.unit
def test_health_database_connected(client):
    """健康端點的 checks.database 狀態應為 ok（SQLite in-memory 可用）"""
    response = client.get("/health")
    data = response.json()
    assert data["checks"]["database"] == "ok"


@pytest.mark.unit
def test_health_meta_andromeda_runtime_check_is_structured(client):
    response = client.get("/health")
    data = response.json()
    runtime_check = data["checks"]["meta_andromeda"]
    assert isinstance(runtime_check, dict)
    assert "status" in runtime_check
    assert "queue_host" in runtime_check
    assert "checks" in runtime_check


@pytest.mark.unit
def test_health_does_not_leak_internal_config(client):
    """P0-2：公開 /health 不應含任何 API 金鑰長度或用戶統計等內部組態"""
    response = client.get("/health")
    data = response.json()
    assert "ai_config_debug" not in data
    assert "git_info" not in data


@pytest.mark.unit
def test_health_detail_requires_auth(client):
    """未帶 token 存取 /health/detail 應被拒絕"""
    response = client.get("/health/detail")
    assert response.status_code in (401, 403)


@pytest.mark.unit
def test_health_detail_requires_super_admin(client, db, sample_user):
    """一般（非 super admin）使用者存取 /health/detail 應回傳 403"""
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: sample_user
    try:
        response = client.get("/health/detail")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(auth_dependencies.get_current_user, None)


@pytest.mark.unit
def test_health_detail_returns_debug_info_for_super_admin(client, db, sample_admin_user):
    """Super admin 存取 /health/detail 應能看到 ai_config_debug 除錯資訊"""
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: sample_admin_user
    try:
        response = client.get("/health/detail")
        assert response.status_code == 200
        data = response.json()
        assert "ai_config_debug" in data
        assert "META_ANDROMEDA_SCORING_PROVIDER" in data["ai_config_debug"]
        # /health/detail 應同時包含基礎健康檢查欄位
        assert "checks" in data
        assert "database" in data["checks"]
    finally:
        app.dependency_overrides.pop(auth_dependencies.get_current_user, None)
