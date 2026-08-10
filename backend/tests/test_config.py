"""
core/config.py Pydantic BaseSettings 遷移驗證
（docs/07_audits_and_reviews/CODE_REVIEW_ACTION_PLAN_2026-07-01.md P1-3）
"""

import pytest
from pydantic import ValidationError

from core.config import Settings, settings


def test_settings_default_values(monkeypatch):
    """本機/CI 的 .env 常會覆寫 META_ANDROMEDA_SCORING_PROVIDER=heuristic（避免測試
    打真實 API），這裡先清掉該 env var 才能驗證 schema 本身宣告的預設值。"""
    monkeypatch.delenv("META_ANDROMEDA_SCORING_PROVIDER", raising=False)
    fresh = Settings(_env_file=None)
    assert fresh.SERVICE_ROLE == "all"
    assert fresh.META_ANDROMEDA_SCORE_MAX_ATTEMPTS == 3
    assert fresh.META_ANDROMEDA_SCORING_PROVIDER == "auto"
    assert fresh.ENV == "development"


def test_type_coercion_rejects_invalid_int_at_construction():
    """型別驗證是這次遷移的主要動機——非數字字串應該直接報錯，而不是像舊版
    property + int(os.getenv(...)) 那樣未捕捉例外，錯誤訊息模糊。"""
    with pytest.raises(ValidationError):
        Settings(_env_file=None, META_ANDROMEDA_SCORE_MAX_ATTEMPTS="not-a-number")


def test_assignment_revalidates_and_applies_floor_clamp():
    """validate_assignment=True 讓 monkeypatch.setattr(settings, "FIELD", value)
    在測試中途覆寫時，仍會套用跟建構時一樣的 clamp 邏輯（延續舊版 property
    內 max(1, ...) 的下限保護語意）。"""
    fresh = Settings(_env_file=None)
    fresh.META_ANDROMEDA_SCORE_MAX_ATTEMPTS = 0
    assert fresh.META_ANDROMEDA_SCORE_MAX_ATTEMPTS == 1

    fresh.META_ANDROMEDA_WEEKLY_LOOP_HOUR = 99
    assert fresh.META_ANDROMEDA_WEEKLY_LOOP_HOUR == 23


def test_service_role_normalized_on_assignment():
    fresh = Settings(_env_file=None)
    fresh.SERVICE_ROLE = "  WEB  "
    assert fresh.SERVICE_ROLE == "web"
    assert fresh.is_web_role is True


def test_google_ai_api_key_fallback_chain():
    fresh = Settings(_env_file=None)
    fresh.ZEABUR_AI_HUB_API_KEY = "zeabur-key"
    assert fresh.GOOGLE_AI_API_KEY == "zeabur-key"

    fresh.GOOGLE_API_KEY_ENV = "google-api-key"
    assert fresh.GOOGLE_AI_API_KEY == "google-api-key"

    fresh.GOOGLE_AI_API_KEY_ENV = "google-ai-api-key"
    assert fresh.GOOGLE_AI_API_KEY == "google-ai-api-key"


def test_openrouter_api_key_fallback_chain():
    fresh = Settings(_env_file=None)
    fresh.ZEABUR_AI_HUB_API_KEY = "zeabur-key"
    assert fresh.OPENROUTER_API_KEY == "zeabur-key"

    fresh.OPENROUTER_API_KEY_ENV = "openrouter-key"
    assert fresh.OPENROUTER_API_KEY == "openrouter-key"


def test_super_admin_emails_parsing():
    fresh = Settings(_env_file=None, SUPER_ADMIN_EMAIL="A@Example.com, b@example.com ,,")
    assert fresh.super_admin_emails == ["a@example.com", "b@example.com"]


def test_allowed_media_hosts_parsing():
    fresh = Settings(_env_file=None, META_ANDROMEDA_ALLOWED_MEDIA_HOSTS="Foo.com, Bar.com")
    assert fresh.META_ANDROMEDA_ALLOWED_MEDIA_HOSTS == ["foo.com", "bar.com"]


def test_storage_root_defaults_when_unset():
    fresh = Settings(_env_file=None)
    assert fresh.META_ANDROMEDA_STORAGE_ROOT
    assert fresh.META_ANDROMEDA_STORAGE_ROOT.endswith("meta_andromeda")


def test_validate_required_reports_missing_fields():
    fresh = Settings(_env_file=None, GOOGLE_CLIENT_ID="", ENCRYPTION_KEY="")
    assert fresh.validate_required() == ["GOOGLE_CLIENT_ID", "ENCRYPTION_KEY"]

    fresh.GOOGLE_CLIENT_ID = "client-id"
    fresh.ENCRYPTION_KEY = "key"
    assert fresh.validate_required() == []


def test_module_singleton_is_settings_instance():
    assert isinstance(settings, Settings)
