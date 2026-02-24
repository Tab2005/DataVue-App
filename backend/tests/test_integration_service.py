"""
integration_service.py 單元測試
測試 CRUD 操作與 Token 加解密（使用 mock 避免 Fernet 金鑰依賴）
"""
import pytest
from unittest.mock import patch


@pytest.mark.integration
def test_get_user_integration_returns_none_when_not_exists(db, sample_user):
    """查詢不存在的整合應回傳 None"""
    from services.integration_service import get_user_integration

    result = get_user_integration(db, sample_user.id, "facebook")
    assert result is None


@pytest.mark.integration
def test_upsert_and_get_user_integration(db, sample_user):
    """建立整合後應可正確查詢"""
    from services.integration_service import upsert_user_integration, get_user_integration

    # mock _safe_encrypt 避免 Fernet 金鑰環境依賴
    with patch("services.integration_service._safe_encrypt", return_value="encrypted_token"):
        upsert_user_integration(
            db,
            user_id=sample_user.id,
            provider="facebook",
            access_token="raw_test_token",
        )

    result = get_user_integration(db, sample_user.id, "facebook")
    assert result is not None
    assert result.provider == "facebook"


@pytest.mark.integration
def test_delete_user_integration(db, sample_user):
    """刪除整合後查詢應回傳 None"""
    from services.integration_service import (
        upsert_user_integration,
        delete_user_integration,
        get_user_integration,
    )

    with patch("services.integration_service._safe_encrypt", return_value="encrypted_token"):
        upsert_user_integration(
            db,
            user_id=sample_user.id,
            provider="gsc",
            access_token="some_token",
        )

    delete_user_integration(db, sample_user.id, "gsc")
    result = get_user_integration(db, sample_user.id, "gsc")
    assert result is None


@pytest.mark.integration
def test_upsert_updates_existing_integration(db, sample_user):
    """重複 upsert 應更新現有記錄而非新增"""
    from services.integration_service import (
        upsert_user_integration,
        get_user_integration,
        get_all_user_integrations,
    )

    with patch("services.integration_service._safe_encrypt", side_effect=lambda v: f"enc_{v}" if v else None):
        upsert_user_integration(db, user_id=sample_user.id, provider="ga4", access_token="token_v1")
        upsert_user_integration(db, user_id=sample_user.id, provider="ga4", access_token="token_v2")

    all_integrations = get_all_user_integrations(db, sample_user.id)
    ga4_integrations = [i for i in all_integrations if i.provider == "ga4"]

    # 應只有一筆 ga4 整合
    assert len(ga4_integrations) == 1


@pytest.mark.integration
def test_delete_nonexistent_returns_false(db, sample_user):
    """刪除不存在的整合應回傳 False"""
    from services.integration_service import delete_user_integration

    result = delete_user_integration(db, sample_user.id, "facebook")
    assert result is False
