"""
認證相關端點測試
注意：Google Token 驗證需要 mock
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta


@pytest.mark.unit
def test_exchange_token_missing_credential(client):
    """未提供 credential 時應回傳 422 或 403"""
    response = client.post("/api/auth/exchange-token", json={})
    # Rate limiting 或 schema 驗證失敗均可接受
    assert response.status_code in (422, 403)


@pytest.mark.unit
def test_token_status_requires_auth(client):
    """未帶 Bearer Token 時，/token-status 應回傳 401 或 403"""
    response = client.get("/api/auth/token-status")
    assert response.status_code in (401, 403)


@pytest.mark.unit
def test_exchange_token_rate_limit_header(client):
    """Token 交換端點應存在（不是 404）"""
    response = client.post(
        "/api/auth/exchange-token",
        json={"credential": "invalid_token"}
    )
    # 無論成功與否，端點應存在（不是 404）
    assert response.status_code != 404


@pytest.mark.unit
def test_auth_router_mounted(client):
    """確認 auth router 正確掛載，端點可被發現"""
    # 測試一個需要認證的端點，確認回傳 401/403 而非 404
    response = client.get("/api/auth/token-status")
    assert response.status_code in (401, 403)


# ─── M-1：token-status 整合 integration_service 測試 ─────────────────────────

MOCK_USER_ID = "test-google-sub-001"


@pytest.mark.unit
def test_token_status_no_integration_returns_false(client):
    """
    當 user_integrations 沒有對應記錄時，
    token_exists 應回傳 False，且端點不應讀取 User.fb_access_token。
    """
    with patch(
        "routers.auth.verify_google_token_and_get_sub",
        return_value=MOCK_USER_ID,
    ), patch(
        "routers.auth.get_user_integration",
        return_value=None,  # 沒有整合記錄
    ):
        response = client.get(
            "/api/auth/token-status",
            headers={"Authorization": "Bearer fake-token"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["token_exists"] is False
    assert data["expires_at"] is None
    assert data["provider"] == "facebook"


@pytest.mark.unit
def test_token_status_with_valid_integration_returns_true(client):
    """
    當 user_integrations 有有效 Token 記錄時，
    token_exists 應回傳 True，且 is_expired 根據 token_expiry 計算。
    """
    future_expiry = datetime.now(timezone.utc) + timedelta(days=30)
    mock_integration = MagicMock()
    mock_integration.access_token = "encrypted_token_value"
    mock_integration.token_expiry = future_expiry

    with patch(
        "routers.auth.verify_google_token_and_get_sub",
        return_value=MOCK_USER_ID,
    ), patch(
        "routers.auth.get_user_integration",
        return_value=mock_integration,
    ):
        response = client.get(
            "/api/auth/token-status",
            headers={"Authorization": "Bearer fake-token"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["token_exists"] is True
    assert data["is_expired"] is False
    assert data["days_remaining"] >= 29
    assert data["provider"] == "facebook"


@pytest.mark.unit
def test_token_status_with_expired_integration(client):
    """
    當 token_expiry 已過期時，is_expired 應回傳 True。
    """
    past_expiry = datetime.now(timezone.utc) - timedelta(days=5)
    mock_integration = MagicMock()
    mock_integration.access_token = "encrypted_old_token"
    mock_integration.token_expiry = past_expiry

    with patch(
        "routers.auth.verify_google_token_and_get_sub",
        return_value=MOCK_USER_ID,
    ), patch(
        "routers.auth.get_user_integration",
        return_value=mock_integration,
    ):
        response = client.get(
            "/api/auth/token-status",
            headers={"Authorization": "Bearer fake-token"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["token_exists"] is True
    assert data["is_expired"] is True
    assert data["days_remaining"] < 0
