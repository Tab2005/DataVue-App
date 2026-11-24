"""Meta Graph / Marketing API 版本設定測試。"""

import importlib
import re
from pathlib import Path

import pytest

import core.meta_api as meta_api

BACKEND_ROOT = Path(__file__).resolve().parents[1]

# 舊的維護腳本不在執行路徑上，不納入檢查
EXCLUDED_DIRS = {"venv", ".venv", "tests", "__pycache__", "alembic"}
EXCLUDED_FILES = {Path("scripts/maintenance/main_legacy.py")}

HARDCODED_VERSION = re.compile(r"graph\.facebook\.com/v\d+\.\d+")


def _reload(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("META_GRAPH_API_VERSION", raising=False)
    else:
        monkeypatch.setenv("META_GRAPH_API_VERSION", value)
    return importlib.reload(meta_api)


@pytest.fixture(autouse=True)
def _restore_module(monkeypatch):
    yield
    monkeypatch.delenv("META_GRAPH_API_VERSION", raising=False)
    importlib.reload(meta_api)


def test_default_version_is_v27(monkeypatch):
    mod = _reload(monkeypatch, None)
    assert mod.META_API_VERSION == "v27.0"
    assert mod.GRAPH_API_BASE_URL == "https://graph.facebook.com/v27.0"


def test_env_override_for_rollback(monkeypatch):
    mod = _reload(monkeypatch, " v25.0 ")
    assert mod.GRAPH_API_BASE_URL == "https://graph.facebook.com/v25.0"


def test_blank_env_falls_back_to_default(monkeypatch):
    mod = _reload(monkeypatch, "")
    assert mod.META_API_VERSION == mod.DEFAULT_META_API_VERSION


@pytest.mark.parametrize("bad", ["27.0", "v27", "latest", "v27.0/"])
def test_invalid_env_value_raises(monkeypatch, bad):
    with pytest.raises(ValueError):
        _reload(monkeypatch, bad)


def test_no_hardcoded_graph_versions_outside_meta_api():
    offenders = []
    for path in BACKEND_ROOT.rglob("*.py"):
        rel = path.relative_to(BACKEND_ROOT)
        if rel.parts[0] in EXCLUDED_DIRS or rel in EXCLUDED_FILES:
            continue
        if rel == Path("core/meta_api.py"):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), 1):
            if HARDCODED_VERSION.search(line):
                offenders.append(f"{rel}:{lineno}")
    assert not offenders, "請改用 core.meta_api.GRAPH_API_BASE_URL：" + ", ".join(offenders)


def test_runtime_clients_use_shared_base_url():
    from batch_api import FacebookBatchService
    from modules.fb_ads import _base
    from service_modules.facebook_api import FacebookAPIClient
    from services.facebook_service import FacebookService

    expected = meta_api.GRAPH_API_BASE_URL
    assert _base.BASE_URL == expected
    assert FacebookService.BASE_URL == expected
    assert FacebookAPIClient.BASE_URL == expected
    assert FacebookBatchService.BASE_URL == expected
