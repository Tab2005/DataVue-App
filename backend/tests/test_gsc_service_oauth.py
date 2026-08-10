"""
GSCService OAuth / 憑證 / 網站列表單元測試（P2-3 補強測試覆蓋）

同 `test_ga4_client_oauth.py`：`modules/gsc/service.py` 的
`exchange_code`/`get_credentials`/`list_sites` 在既有測試中從未被直接
測過（只在 forwarding shim 的測試裡整包 mock 掉），這裡補上直接測試，
涵蓋多組 redirect_uri 重試、token 過期刷新回寫、以及網站列表的成功/
失敗路徑。
"""
from unittest.mock import MagicMock

import pytest

from modules.gsc.service import GSCService


def _make_response(status_code, json_data):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


class _FakeUser:
    def __init__(self, **attrs):
        for key, value in attrs.items():
            setattr(self, key, value)


# ─── exchange_code ──────────────────────────────────────────────────
@pytest.mark.unit
class TestGSCServiceExchangeCode:
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

        success, message = GSCService.exchange_code(user, "auth-code", db)

        assert success is True
        assert user.gsc_access_token == "AT"
        assert user.gsc_refresh_token == "RT"
        db.commit.assert_called_once()
        assert mock_post.call_count == 1

    def test_retries_without_secret_when_all_with_secret_fail(self, monkeypatch, mocker):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")
        fail = _make_response(400, {"error": "invalid_client"})
        success_resp = _make_response(200, {"access_token": "AT", "expires_in": 3600})
        mock_post = mocker.patch("requests.post", side_effect=[fail, fail, fail, success_resp])

        success, message = GSCService.exchange_code(_FakeUser(), "auth-code", MagicMock())

        assert success is True
        assert mock_post.call_count == 4
        assert "client_secret" not in mock_post.call_args_list[3].kwargs["data"]

    def test_returns_descriptive_error_when_all_attempts_fail(self, monkeypatch, mocker):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")
        fail = _make_response(
            400, {"error": "invalid_grant", "error_description": "Bad code"}
        )
        mocker.patch("requests.post", return_value=fail)

        success, message = GSCService.exchange_code(_FakeUser(), "bad-code", MagicMock())

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
        user = _FakeUser(gsc_refresh_token="EXISTING_RT")

        GSCService.exchange_code(user, "auth-code", MagicMock())

        assert user.gsc_refresh_token == "EXISTING_RT"

    def test_returns_exception_message_on_network_error(self, monkeypatch, mocker):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")
        mocker.patch("requests.post", side_effect=ConnectionError("boom"))

        success, message = GSCService.exchange_code(_FakeUser(), "auth-code", MagicMock())

        assert success is False
        assert "boom" in message


# ─── get_credentials ────────────────────────────────────────────────
def _patch_credentials_class(mocker, expired):
    fake_creds = MagicMock()
    fake_creds.expired = expired
    fake_creds.token = "refreshed-token"
    mocker.patch("modules.gsc.service.Credentials", return_value=fake_creds)
    return fake_creds


@pytest.mark.unit
class TestGSCServiceGetCredentials:
    def test_returns_none_when_tokens_missing(self):
        user = _FakeUser(gsc_access_token=None, gsc_refresh_token=None)
        assert GSCService.get_credentials(user) is None

    def test_returns_credentials_without_refresh_when_not_expiring_soon(self, mocker):
        from datetime import datetime, timedelta

        fake_creds = _patch_credentials_class(mocker, expired=False)
        user = _FakeUser(
            gsc_access_token="AT",
            gsc_refresh_token="RT",
            gsc_expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db = MagicMock()

        result = GSCService.get_credentials(user, db)

        assert result is fake_creds
        fake_creds.refresh.assert_not_called()
        db.commit.assert_not_called()

    def test_refreshes_and_persists_when_expiring_within_five_minutes(self, mocker):
        from datetime import datetime, timedelta

        fake_creds = _patch_credentials_class(mocker, expired=False)
        user = _FakeUser(
            gsc_access_token="AT",
            gsc_refresh_token="RT",
            gsc_expires_at=datetime.utcnow() + timedelta(seconds=60),
        )
        db = MagicMock()

        result = GSCService.get_credentials(user, db)

        assert result is fake_creds
        fake_creds.refresh.assert_called_once()
        assert user.gsc_access_token == "refreshed-token"
        db.commit.assert_called_once()

    def test_refreshes_when_already_expired(self, mocker):
        from datetime import datetime, timedelta

        fake_creds = _patch_credentials_class(mocker, expired=True)
        user = _FakeUser(
            gsc_access_token="AT",
            gsc_refresh_token="RT",
            gsc_expires_at=datetime.utcnow() - timedelta(hours=1),
        )

        result = GSCService.get_credentials(user, MagicMock())

        assert result is fake_creds
        fake_creds.refresh.assert_called_once()

    def test_does_not_return_none_when_refresh_fails(self, mocker):
        """GSC 的 get_credentials 與 GA4 行為不同：refresh 失敗只記警告，
        仍回傳（未刷新的）creds，讓 googleapiclient 自行嘗試刷新，而不是
        直接回 None（見 modules/gsc/service.py 註解）。"""
        from datetime import datetime, timedelta

        fake_creds = _patch_credentials_class(mocker, expired=True)
        fake_creds.refresh.side_effect = Exception("refresh failed")
        user = _FakeUser(
            gsc_access_token="AT",
            gsc_refresh_token="RT",
            gsc_expires_at=datetime.utcnow() - timedelta(hours=1),
        )

        result = GSCService.get_credentials(user, MagicMock())

        assert result is fake_creds


# ─── list_sites ─────────────────────────────────────────────────────
@pytest.mark.unit
class TestGSCServiceListSites:
    def test_returns_error_when_no_credentials(self, mocker):
        mocker.patch("modules.gsc.service.GSCService.get_credentials", return_value=None)

        sites, error = GSCService.list_sites(_FakeUser())

        assert sites is None
        assert error == "No GSC credentials found"

    def test_returns_site_entries_on_success(self, mocker):
        mocker.patch("modules.gsc.service.GSCService.get_credentials", return_value=MagicMock())
        fake_search_console = MagicMock()
        fake_search_console.sites.return_value.list.return_value.execute.return_value = {
            "siteEntry": [{"siteUrl": "https://example.com/"}]
        }
        mocker.patch("modules.gsc.service.build", return_value=fake_search_console)

        sites, error = GSCService.list_sites(_FakeUser())

        assert error is None
        assert sites == [{"siteUrl": "https://example.com/"}]

    def test_returns_error_message_on_api_exception(self, mocker):
        mocker.patch("modules.gsc.service.GSCService.get_credentials", return_value=MagicMock())
        mocker.patch("modules.gsc.service.build", side_effect=Exception("quota exceeded"))

        sites, error = GSCService.list_sites(_FakeUser())

        assert sites is None
        assert error == "quota exceeded"
