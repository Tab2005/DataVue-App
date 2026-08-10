"""
GA4Client OAuth / 憑證 / 屬性列舉單元測試（P2-3 補強測試覆蓋）

既有 `test_ga4_module_refactor.py` 只驗證 `ga4_service.GA4Service` 轉發層有
「真的呼叫」`GA4Client`／`GA4AnalyticsService`，但呼叫目標本身整個被 mock
掉，從未驗證 `modules/ga4/client.py` 的真正實作邏輯：
- `exchange_code`：多組 redirect_uri／有無 client_secret 的重試序列、各種
  失敗路徑的錯誤訊息組裝。
- `get_credentials`：token 過期判斷（expiry 時間差 / `creds.expired`）、
  refresh 成功後回寫資料庫、refresh 失敗時的降級行為。
- `list_properties`：無憑證、無帳號、正常彙整、API 例外等路徑。
"""
from unittest.mock import MagicMock

import pytest

from modules.ga4.client import GA4Client


def _make_response(status_code, json_data):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


class _FakeUser:
    """避免用 MagicMock 當 user：MagicMock 存取任何屬性都會自動生出新的
    Mock（hasattr 恆真、值也不是預期的字串/None），會讓 exchange_code /
    get_credentials 內部的條件判斷失真。"""

    def __init__(self, **attrs):
        for key, value in attrs.items():
            setattr(self, key, value)


# ─── exchange_code ──────────────────────────────────────────────────
@pytest.mark.unit
class TestGA4ClientExchangeCode:
    def test_returns_error_when_client_credentials_missing(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)

        success, message = GA4Client.exchange_code(_FakeUser(), "auth-code", MagicMock())

        assert success is False
        assert "not configured" in message

    def test_success_on_first_attempt_with_secret(self, monkeypatch, mocker):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")
        mock_post = mocker.patch(
            "requests.post",
            return_value=_make_response(
                200, {"access_token": "AT", "refresh_token": "RT", "expires_in": 3600}
            ),
        )
        user = _FakeUser()
        db = MagicMock()

        success, message = GA4Client.exchange_code(user, "auth-code", db)

        assert success is True
        assert user.ga4_access_token == "AT"
        assert user.ga4_refresh_token == "RT"
        db.commit.assert_called_once()
        assert mock_post.call_count == 1

    def test_falls_back_across_redirect_uris_before_dropping_secret(self, monkeypatch, mocker):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")
        fail = _make_response(400, {"error": "redirect_uri_mismatch"})
        success_resp = _make_response(200, {"access_token": "AT", "expires_in": 3600})
        mock_post = mocker.patch("requests.post", side_effect=[fail, fail, success_resp])

        success, message = GA4Client.exchange_code(_FakeUser(), "auth-code", MagicMock())

        assert success is True
        # 3 個 redirect_uri 中第 3 個（仍帶 secret）才成功，不需要進到「無 secret」階段
        assert mock_post.call_count == 3

    def test_retries_without_secret_when_all_with_secret_fail(self, monkeypatch, mocker):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")
        fail = _make_response(400, {"error": "invalid_client"})
        success_resp = _make_response(200, {"access_token": "AT", "expires_in": 3600})
        mock_post = mocker.patch("requests.post", side_effect=[fail, fail, fail, success_resp])

        success, message = GA4Client.exchange_code(_FakeUser(), "auth-code", MagicMock())

        assert success is True
        # 3 次帶 secret 全失敗後，第 4 次（無 secret 的第一次嘗試）才成功
        assert mock_post.call_count == 4
        assert "client_secret" not in mock_post.call_args_list[3].kwargs["data"]

    def test_returns_descriptive_error_when_all_attempts_fail(self, monkeypatch, mocker):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")
        fail = _make_response(
            400, {"error": "invalid_grant", "error_description": "Bad code"}
        )
        mocker.patch("requests.post", return_value=fail)

        success, message = GA4Client.exchange_code(_FakeUser(), "bad-code", MagicMock())

        assert success is False
        assert "invalid_grant" in message
        assert "Bad code" in message

    def test_does_not_overwrite_refresh_token_when_absent_from_response(self, monkeypatch, mocker):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")
        mocker.patch(
            "requests.post",
            return_value=_make_response(200, {"access_token": "AT", "expires_in": 3600}),
        )
        user = _FakeUser(ga4_refresh_token="EXISTING_RT")

        GA4Client.exchange_code(user, "auth-code", MagicMock())

        assert user.ga4_refresh_token == "EXISTING_RT"

    def test_returns_exception_message_on_network_error(self, monkeypatch, mocker):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")
        mocker.patch("requests.post", side_effect=ConnectionError("boom"))

        success, message = GA4Client.exchange_code(_FakeUser(), "auth-code", MagicMock())

        assert success is False
        assert "boom" in message


# ─── get_credentials ────────────────────────────────────────────────
def _patch_credentials_class(mocker, expired):
    """`Credentials` 建構子換成 MagicMock，讓測試直接控制 `.expired`／`.token`，
    不依賴 google-auth 內部 `expired` property 跨版本的實際計算方式。"""
    fake_creds = MagicMock()
    fake_creds.expired = expired
    fake_creds.token = "refreshed-token"
    mocker.patch("modules.ga4.client.Credentials", return_value=fake_creds)
    return fake_creds


@pytest.mark.unit
class TestGA4ClientGetCredentials:
    def test_returns_none_when_tokens_missing(self):
        user = _FakeUser(ga4_access_token=None, ga4_refresh_token=None)
        assert GA4Client.get_credentials(user) is None

    def test_returns_credentials_without_refresh_when_not_expiring_soon(self, mocker):
        from datetime import datetime, timedelta

        fake_creds = _patch_credentials_class(mocker, expired=False)
        user = _FakeUser(
            ga4_access_token="AT",
            ga4_refresh_token="RT",
            ga4_expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db = MagicMock()

        result = GA4Client.get_credentials(user, db)

        assert result is fake_creds
        fake_creds.refresh.assert_not_called()
        db.commit.assert_not_called()

    def test_refreshes_and_persists_when_expiring_within_five_minutes(self, mocker):
        from datetime import datetime, timedelta

        fake_creds = _patch_credentials_class(mocker, expired=False)
        user = _FakeUser(
            ga4_access_token="AT",
            ga4_refresh_token="RT",
            ga4_expires_at=datetime.utcnow() + timedelta(seconds=60),
        )
        db = MagicMock()

        result = GA4Client.get_credentials(user, db)

        assert result is fake_creds
        fake_creds.refresh.assert_called_once()
        assert user.ga4_access_token == "refreshed-token"
        db.commit.assert_called_once()

    def test_refreshes_when_already_expired(self, mocker):
        from datetime import datetime, timedelta

        fake_creds = _patch_credentials_class(mocker, expired=True)
        user = _FakeUser(
            ga4_access_token="AT",
            ga4_refresh_token="RT",
            ga4_expires_at=datetime.utcnow() - timedelta(hours=1),
        )

        result = GA4Client.get_credentials(user, MagicMock())

        assert result is fake_creds
        fake_creds.refresh.assert_called_once()

    def test_refreshes_when_no_expiry_information_available(self, mocker):
        fake_creds = _patch_credentials_class(mocker, expired=False)
        user = _FakeUser(ga4_access_token="AT", ga4_refresh_token="RT", ga4_expires_at=None)

        GA4Client.get_credentials(user, MagicMock())

        fake_creds.refresh.assert_called_once()

    def test_returns_none_when_refresh_fails(self, mocker):
        from datetime import datetime, timedelta

        fake_creds = _patch_credentials_class(mocker, expired=True)
        fake_creds.refresh.side_effect = Exception("refresh failed")
        user = _FakeUser(
            ga4_access_token="AT",
            ga4_refresh_token="RT",
            ga4_expires_at=datetime.utcnow() - timedelta(hours=1),
        )

        result = GA4Client.get_credentials(user, MagicMock())

        assert result is None


# ─── list_properties ────────────────────────────────────────────────
class _FakeAccount:
    def __init__(self, name):
        self.name = name


class _FakeProperty:
    def __init__(self, name, display_name):
        self.name = name
        self.display_name = display_name
        self.create_time = None
        self.update_time = None
        self.currency_code = "TWD"
        self.time_zone = "Asia/Taipei"
        self.parent = None


@pytest.mark.unit
class TestGA4ClientListProperties:
    def test_returns_error_when_no_credentials(self, mocker):
        mocker.patch("modules.ga4.client.GA4Client.get_credentials", return_value=None)

        properties, error = GA4Client.list_properties(_FakeUser())

        assert properties == []
        assert error == "No GA4 credentials found"

    def test_returns_error_when_no_accounts(self, mocker):
        mocker.patch("modules.ga4.client.GA4Client.get_credentials", return_value=MagicMock())
        fake_admin_client = MagicMock()
        fake_admin_client.list_accounts.return_value = []
        mocker.patch(
            "modules.ga4.client.AnalyticsAdminServiceClient", return_value=fake_admin_client
        )

        properties, error = GA4Client.list_properties(_FakeUser())

        assert properties == []
        assert error == "No GA4 accounts found"

    def test_aggregates_properties_across_accounts(self, mocker):
        mocker.patch("modules.ga4.client.GA4Client.get_credentials", return_value=MagicMock())
        fake_admin_client = MagicMock()
        fake_admin_client.list_accounts.return_value = [_FakeAccount("accounts/1")]
        fake_admin_client.list_properties.return_value = [
            _FakeProperty("properties/111", "Site A"),
            _FakeProperty("properties/222", "Site B"),
        ]
        mocker.patch(
            "modules.ga4.client.AnalyticsAdminServiceClient", return_value=fake_admin_client
        )

        properties, error = GA4Client.list_properties(_FakeUser())

        assert error is None
        assert {p["property_id"] for p in properties} == {"111", "222"}
        assert {p["display_name"] for p in properties} == {"Site A", "Site B"}
        fake_admin_client.list_properties.assert_called_once_with(
            request={"filter": "parent:accounts/1"}
        )

    def test_returns_error_message_on_api_exception(self, mocker):
        mocker.patch("modules.ga4.client.GA4Client.get_credentials", return_value=MagicMock())
        fake_admin_client = MagicMock()
        fake_admin_client.list_accounts.side_effect = Exception("quota exceeded")
        mocker.patch(
            "modules.ga4.client.AnalyticsAdminServiceClient", return_value=fake_admin_client
        )

        properties, error = GA4Client.list_properties(_FakeUser())

        assert properties == []
        assert error == "quota exceeded"
