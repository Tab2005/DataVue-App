"""
/health 和 /api/health 端點測試
屬於最基礎的 smoke test，確認服務可正常啟動與回應
"""
import pytest


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
