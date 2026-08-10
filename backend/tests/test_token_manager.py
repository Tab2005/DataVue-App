"""
TokenManager 加密儲存/讀取單元測試（P2-3 補強測試覆蓋）

`modules/auth/service.py::TokenManager` 是 Facebook Token 與 AI API Key
的唯一加解密入口（`core.security.encrypt_value`/`decrypt_value` 的封裝），
過去只在其他測試裡被當成「已知會回傳某字串」直接 mock 掉，從未驗證過：
1. `_encrypt`/`_decrypt` 真的是可逆的（Fernet round-trip）。
2. `get_user_token`/`get_team_token` 從 DB 讀出加密欄位後真的有解密、
   以及各自的 fallback 規則（無 token 時降級用 Admin/Owner 的 token）。

`get_user_token`/`get_team_token` 內部用 `SessionLocal()` 自建 session，
不接受注入的 db session，所以用 monkeypatch 把 `modules.auth.service.
SessionLocal`（呼叫端已綁定的名稱，而非 `database.SessionLocal` 本身，
比照本次 session 稍早處理 shim 循環匯入時學到的「patch 呼叫端綁定名稱」
原則）換成綁定同一個 `db` fixture connection 的 sessionmaker，讓
TokenManager 內部另開的 session 與測試寫入的資料共用同一個交易，測試
結束時隨 `db` fixture 一併 rollback。
"""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import sessionmaker

import modules.auth.service as auth_service
from modules.auth.service import TokenManager


@pytest.fixture
def patched_session_local(db, monkeypatch):
    """讓 TokenManager 內部的 `SessionLocal()` 呼叫落在跟 `db` fixture
    相同的 connection/transaction 上，寫入的資料在同一測試內可見，且會
    隨 `db` fixture 的 rollback 一併清掉。"""
    connection = db.get_bind()
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    monkeypatch.setattr(auth_service, "SessionLocal", TestSessionLocal)
    return TestSessionLocal


# ─── _encrypt / _decrypt round-trip ─────────────────────────────────
@pytest.mark.unit
class TestTokenManagerEncryption:
    def test_encrypt_then_decrypt_round_trip(self):
        plaintext = "EAAG_fake_facebook_long_lived_token_1234567890"

        encrypted = TokenManager._encrypt(plaintext)

        assert encrypted is not None
        assert encrypted != plaintext
        assert TokenManager._decrypt(encrypted) == plaintext

    def test_encrypt_none_or_empty_returns_none(self):
        assert TokenManager._encrypt(None) is None
        assert TokenManager._encrypt("") is None

    def test_decrypt_none_or_empty_returns_none(self):
        assert TokenManager._decrypt(None) is None
        assert TokenManager._decrypt("") is None

    def test_decrypt_garbage_ciphertext_returns_none(self):
        """壞掉/被竄改的密文不該拋例外炸掉呼叫端，應回傳 None。"""
        assert TokenManager._decrypt("this-is-not-a-valid-fernet-token") is None

    def test_two_encryptions_of_same_value_differ(self):
        """Fernet 每次加密帶隨機 nonce，同一明文兩次加密結果不同，
        但都能各自解回原文——避免誤用成看起來像 hash 的固定輸出。"""
        plaintext = "same-secret"
        first = TokenManager._encrypt(plaintext)
        second = TokenManager._encrypt(plaintext)

        assert first != second
        assert TokenManager._decrypt(first) == plaintext
        assert TokenManager._decrypt(second) == plaintext


# ─── get_user_token ─────────────────────────────────────────────────
@pytest.mark.unit
class TestGetUserToken:
    def test_returns_decrypted_token_for_user_with_own_token(
        self, db, sample_user, patched_session_local
    ):
        sample_user.fb_access_token = TokenManager._encrypt("user-own-token")
        db.commit()

        result = TokenManager.get_user_token(sample_user.google_id)

        assert result == "user-own-token"

    def test_falls_back_to_admin_token_when_user_has_none(
        self, db, sample_user, sample_admin_user, patched_session_local
    ):
        sample_admin_user.fb_access_token = TokenManager._encrypt("admin-token")
        db.commit()

        result = TokenManager.get_user_token(sample_user.google_id, allow_fallback=True)

        assert result == "admin-token"

    def test_does_not_fall_back_when_allow_fallback_is_false(
        self, db, sample_user, sample_admin_user, patched_session_local
    ):
        sample_admin_user.fb_access_token = TokenManager._encrypt("admin-token")
        db.commit()

        result = TokenManager.get_user_token(sample_user.google_id, allow_fallback=False)

        assert result is None

    def test_returns_none_for_unknown_user_without_fallback(self, patched_session_local):
        result = TokenManager.get_user_token("no-such-google-id", allow_fallback=False)
        assert result is None


# ─── get_team_token ─────────────────────────────────────────────────
@pytest.mark.unit
class TestGetTeamToken:
    def test_returns_decrypted_team_token_when_present(self, db, patched_session_local):
        from database.models.team import Team

        team = Team(name="Team A", fb_access_token=TokenManager._encrypt("team-token"))
        db.add(team)
        db.commit()
        db.refresh(team)

        result = TokenManager.get_team_token(team.id)

        assert result == "team-token"

    def test_falls_back_to_owner_token_when_team_has_none(
        self, db, sample_user, patched_session_local
    ):
        from database.models.team import Team

        sample_user.fb_access_token = TokenManager._encrypt("owner-token")
        team = Team(name="Team B", owner_id=sample_user.id, fb_access_token=None)
        db.add(team)
        db.commit()
        db.refresh(team)

        result = TokenManager.get_team_token(team.id)

        assert result == "owner-token"

    def test_returns_none_when_team_not_found(self, patched_session_local):
        assert TokenManager.get_team_token("no-such-team-id") is None
