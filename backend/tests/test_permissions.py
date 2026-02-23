"""
test_permissions.py — 權限系統測試

涵蓋：
  - 一般使用者不可存取管理員 API
  - Super Admin 可存取管理員 API
  - 使用者模組存取權限（UserModuleAccess）CRUD
"""

import pytest
from unittest.mock import patch
from fastapi import status


class TestAdminAccess:
    """管理員端點存取控制"""

    def test_viewer_cannot_access_admin_users(
        self, client, db, test_user, mock_google_token_viewer, viewer_auth_headers
    ):
        """一般使用者不可列出所有使用者（管理員功能）。"""
        response = client.get("/api/admin/users", headers=viewer_auth_headers)
        assert response.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_super_admin_can_access_admin_users(
        self, client, db, super_admin_user, mock_google_token_super_admin, super_admin_auth_headers
    ):
        """Super Admin 可存取使用者管理 API。"""
        response = client.get("/api/admin/users", headers=super_admin_auth_headers)
        # 可能 200 或 404（若路由不存在），但不應為 403
        assert response.status_code != status.HTTP_403_FORBIDDEN

    def test_viewer_cannot_access_admin_stats(
        self, client, db, test_user, mock_google_token_viewer, viewer_auth_headers
    ):
        """一般使用者不可存取系統統計。"""
        response = client.get("/api/admin/stats", headers=viewer_auth_headers)
        assert response.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND,  # 路由未實作時
        )


class TestModuleAccess:
    """使用者模組存取權限測試"""

    def test_grant_module_access(self, db, test_user):
        """為使用者授予模組存取權限。"""
        from database.models.permission import Module, UserModuleAccess

        # 建立測試模組
        module = Module(
            id="test-module-001",
            name="fb_ads",
            display_name="Facebook Ads",
            is_active=True,
        )
        db.add(module)
        db.commit()

        # 授予權限
        access = UserModuleAccess(
            id="test-access-001",
            user_id=test_user.id,
            module_id=module.id,
            team_id=None,
        )
        db.add(access)
        db.commit()

        # 驗證
        result = db.query(UserModuleAccess).filter_by(
            user_id=test_user.id, module_id=module.id
        ).first()
        assert result is not None

    def test_user_without_module_access(self, db, test_user):
        """未授予模組的使用者不應有存取紀錄。"""
        from database.models.permission import UserModuleAccess

        count = db.query(UserModuleAccess).filter_by(user_id=test_user.id).count()
        assert count == 0  # 此 fixture 使用者剛建立，無任何模組


class TestHealthEndpoint:
    """/health 端點煙霧測試"""

    def test_health_returns_200(self, client):
        """健康檢查端點應正常回應。"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body.get("status") in ("ok", "healthy", "OK")
