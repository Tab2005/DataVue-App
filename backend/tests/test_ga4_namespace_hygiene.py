"""釘住 docs/59 P2-4 / P2-5 的清理結果（docs/67）。

這兩項都是「清掉之後很容易被順手加回來」的東西：反射 helper 加回來會讓測試
好寫一點，通配 `__all__` 加回來會讓新增共用符號少改一行。這裡用測試把代價
講清楚，而不是靠人記得。
"""

import ast
import pathlib

import pytest


INSIGHTS_DIR = pathlib.Path(__file__).resolve().parents[1] / "modules" / "ga4" / "insights"


def _module_all(path: pathlib.Path):
    """回傳該檔 `__all__` 的 AST 節點（找不到就 None）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    return node.value
    return None


# ─── P2-4：反射 hack 不該回來 ────────────────────────────────────────


@pytest.mark.unit
def test_reflection_helpers_are_gone():
    """`_service_attr` / `_facade_attr` / `_get_channel_min_sample` 已移除。

    它們存在的唯一理由是讓測試 patch facade，代價是正式路徑每次呼叫都多一次
    `sys.modules` 查表，且無法從程式碼靜態判讀會執行哪個函式。測試要 patch
    請直接指使用處，例如 `modules.ga4.insights.items._trailing_period`。
    """
    from modules.ga4.insights import _shared

    for name in ("_service_attr", "_facade_attr", "_get_channel_min_sample"):
        assert not hasattr(_shared, name), f"{name} 又出現了（docs/59 P2-4 已移除）"


@pytest.mark.unit
def test_no_module_reflects_into_the_facade_at_runtime():
    """子模組不該再用 `sys.modules` 反查 facade。"""
    offenders = []
    for path in sorted(INSIGHTS_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        if 'sys.modules.get("modules.ga4.insights_service")' in source:
            offenders.append(path.name)
    assert offenders == []


@pytest.mark.unit
def test_patching_the_usage_site_actually_takes_effect(mocker):
    """確認「patch 使用處」這條路真的通——這是移除反射層後測試該走的寫法。

    子模組是 `from ._shared import *`，`_trailing_period` 在 `items` 命名空間是
    一份獨立繫結，所以要 patch `insights.items._trailing_period` 而不是 `_shared`
    的那份。這個測試同時是給後人的範例。
    """
    from modules.ga4.insights import items

    mocker.patch(
        "modules.ga4.insights.items._trailing_period",
        return_value=("2026-01-01", "2026-01-07"),
    )
    assert items._trailing_period(7) == ("2026-01-01", "2026-01-07")


# ─── P2-5：命名空間不該再被塞滿 ──────────────────────────────────────


@pytest.mark.unit
@pytest.mark.parametrize("filename", ["_shared.py", "__init__.py"])
def test_all_is_an_explicit_list_not_a_globals_comprehension(filename):
    node = _module_all(INSIGHTS_DIR / filename)
    assert node is not None, f"{filename} 應該要有 __all__"
    assert isinstance(node, ast.List), (
        f"{filename} 的 __all__ 又變成推導式了；請明列名稱（docs/59 P2-5）"
    )
    assert all(isinstance(e, ast.Constant) for e in node.elts)


@pytest.mark.unit
def test_stdlib_names_are_not_exported_from_the_facade():
    """`os` / `smtplib` / `median` 這些不該從 GA4 洞察的 facade 匯得到。

    它們原本是被 `from ._shared import *` 一路帶到每個子模組與 facade 上的。
    需要的子模組現在各自 import。
    """
    import modules.ga4.insights_service as facade

    leaked = [
        name for name in ("os", "sys", "re", "logging", "smtplib", "asyncio", "median", "EmailMessage")
        if name in getattr(facade, "__all__", [])
    ]
    assert leaked == [], f"stdlib 又漏進 facade 的 __all__：{leaked}"


@pytest.mark.unit
def test_public_api_used_by_router_and_scheduler_is_still_exported():
    """外部真的會 import 的名字要留在 __all__ 裡。

    漏掉的代價是 import 時直接 ImportError（實作時就踩過一次
    `LANDING_PAGE_KEY_EVENT_PATTERN`），這個測試讓它在單元層就被抓到。
    """
    import modules.ga4.insights_service as facade

    required = [
        "GA4InsightsService", "GA4Service", "GA4Client", "repository",
        "LANDING_PAGE_KEY_EVENT_PATTERN", "DASHBOARD_KIND", "MAX_CONVERSION_EVENTS",
        "ATTRIBUTION_SETTINGS_KIND", "ATTRIBUTION_SETTINGS_DATE",
        "classify_landing_page", "classify_item_category", "_percentile",
    ]
    missing = [name for name in required if not hasattr(facade, name)]
    assert missing == [], f"facade 少了外部會用到的名字：{missing}"


@pytest.mark.unit
def test_submodules_import_their_own_stdlib():
    """用到 stdlib 的子模組要自己 import，不靠 `_shared` 的星號帶進來。"""
    expectations = {
        "anomaly_rules.py": ["import asyncio", "import smtplib", "from email.message import EmailMessage"],
        "items.py": ["from statistics import median"],
        "dashboard.py": ["from datetime import date, datetime, timedelta"],
    }
    for filename, needles in expectations.items():
        source = (INSIGHTS_DIR / filename).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in source, f"{filename} 少了 `{needle}`（docs/59 P2-5）"
