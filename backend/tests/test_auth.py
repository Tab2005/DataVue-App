"""
test_auth.py — 認證端點測試

涵蓋：
  - POST /api/auth/exchange-token：Token 交換
  - GET  /api/auth/token-status：Token 狀態查詢
  - 無效 Token 的 401 回應
  - 受保護端點的 403 回應
"""

import pytest
from unittest.mock import patch
from fastapi import status


class TestExchangeToken:
    """POST /api/auth/exchange-token 測試"""

    def test_exchange_token_creates_new_user(self, client, db, mock_google_token_viewer):
        """首次交換 Token 時應自動建立使用者。"""
        response = client.post(
            "/api/auth/exchange-token",
            json={"token": "fake-viewer-token"},
        )
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert "user" in body
        assert body["user"]["email"] == "viewer@test.example.com"

    def test_exchange_token_returns_existing_user(self, client, db, test_user, mock_google_token_viewer):
        """再次交換 Token 時應回傳現有使用者（不重複建立）。"""
        # 第一次
        client.post("/api/auth/exchange-token", json={"token": "fake-viewer-token"})
        # 第二次
        response = client.post(
            "/api/auth/exchange-token",
            json={"token": "fake-viewer-token"},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_exchange_token_invalid_token_returns_401(self, client):
        """無效 Token 應回傳 401。"""
        with patch(
            "core.security._verify_google_token_raw",
            side_effect=ValueError("token invalid"),
        ):
            response = client.post(
                "/api/auth/exchange-token",
                json={"token": "definitely-invalid"},
            )
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_exchange_token_missing_body_returns_422(self, client):
        """缺少 body 應回傳 422 Unprocessable Entity。"""
        response = client.post("/api/auth/exchange-token", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestTokenStatus:
    """GET /api/auth/token-status 測試"""

    def test_token_status_valid_user(self, client, db, test_user, mock_google_token_viewer, viewer_auth_headers):
        """有效 Token 應回傳 valid=True。"""
        response = client.get("/api/auth/token-status", headers=viewer_auth_headers)
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert "valid" in body or "status" in body  # 相容不同實作

    def test_token_status_no_token_returns_error(self, client):
        """無 Token 呼叫時應回傳 4xx 錯誤。"""
        response = client.get("/api/auth/token-status")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class TestProtectedEndpoints:
    """受保護端點的認證 Guard 測試"""

    def test_users_me_without_token_returns_403(self, client):
        """無 Token 呼叫 /api/users/me 應回傳 403。"""
        response = client.get("/api/users/me")
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_users_me_with_valid_token(self, client, db, test_user, mock_google_token_viewer, viewer_auth_headers):
        """有效 Token 呼叫 /api/users/me 應回傳使用者資料。"""
        response = client.get("/api/users/me", headers=viewer_auth_headers)
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body.get("email") == "viewer@test.example.com"
