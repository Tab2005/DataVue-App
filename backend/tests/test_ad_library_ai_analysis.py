"""
Ad Library AI 分析測試（docs/75）

1. ai_analysis：脈絡字數上限、錯誤輸出判斷
2. AIService：ad_library_campaign prompt 分支
3. router：POST /ai-analysis（串流＋保存）、GET /ai-analysis（最近結果與是否過期）、授權
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from database.models.ad_library import AdLibraryAiAnalysis
from modules.ad_library import ai_analysis, repository
from modules.ad_library import router as ad_library_router
from modules.ai_hub.service import AIService
from modules.fb_ads import accounts_service

from tests.test_ad_library_ai_context import _row, _seed, ad_library_client  # noqa: F401  (fixture)


# ── 1. ai_analysis ─────────────────────────────────────────────────────
def _context(n_ads=20):
    ads = [
        {"ad_id": f"a{i}", "copy": {"primary_text": [f"P{i}"]}, "media": [], "metrics": {"spend": float(i)}}
        for i in range(n_ads)
    ]
    return {
        "adsets": [{"adset_id": "s1", "ads": ads}],
        "contents": {f"P{i}": {"kind": "primary_text", "text": "文案" * 50} for i in range(n_ads)},
        "comparisons": [{"fixed_refs": ["P0"], "variants": [{"refs": [], "ad_ids": ["a0"]}]}],
        "notes": [],
    }


def test_fit_context_keeps_small_context_untouched():
    ctx = _context(2)
    assert ai_analysis.fit_context(ctx, max_chars=10_000) is ctx


def test_fit_context_drops_lowest_spend_ads_and_prunes_contents():
    ctx = _context(20)
    full = len(ai_analysis.serialize(ctx))
    fitted = ai_analysis.fit_context(ctx, max_chars=full // 2)
    assert len(ai_analysis.serialize(fitted)) <= full // 2
    kept = [a["ad_id"] for a in fitted["adsets"][0]["ads"]]
    assert "a19" in kept and "a1" not in kept
    assert "P1" not in fitted["contents"]
    assert "P0" in fitted["contents"]  # 仍被比對組引用
    assert "已省略花費最低" in fitted["notes"][-1]
    assert len(ctx["adsets"][0]["ads"]) == 20  # 不改動原物件


def test_context_hash_is_stable_and_sensitive():
    a, b = _context(3), _context(3)
    assert ai_analysis.context_hash(a) == ai_analysis.context_hash(b)
    b["adsets"][0]["ads"][0]["metrics"]["spend"] = 99.0
    assert ai_analysis.context_hash(a) != ai_analysis.context_hash(b)


def test_is_error_output():
    assert ai_analysis.is_error_output("Error: No valid API Key or AI Service configured.")
    assert ai_analysis.is_error_output("## 摘要\n部分內容\n[System Error during Analysis: timeout]")
    assert ai_analysis.is_error_output("   ")
    assert not ai_analysis.is_error_output("## 📌 重點摘要\n- 內容")


# ── 2. prompt ──────────────────────────────────────────────────────────
def test_ad_library_prompt_branch_contains_key_rules():
    captured = {}

    def fake_openrouter(system_prompt, user_message, api_key, model):
        captured.update(system_prompt=system_prompt, user_message=user_message, model=model)
        yield "ok"

    with patch.object(AIService, "_analyze_with_openrouter", side_effect=fake_openrouter):
        out = list(AIService.analyze_data(
            data={"campaign": {"name": "春季活動"}}, context="ctx", api_key="k",
            model="m", report_type="ad_library_campaign",
        ))
    assert out == ["ok"]
    prompt = captured["system_prompt"]
    assert "asset_results" in prompt
    assert "1,000" in prompt  # 樣本量規則
    assert "其他條件相同" in prompt  # 成效歸屬規則
    assert "settings_available" in prompt
    assert "勝負結論只能來自" in prompt  # 2026-10-15 試跑後：不得比較文案與素材都不同的廣告
    assert "極高機率" in prompt  # 禁止斷定用語
    assert "春季活動" in captured["user_message"]


# ── 3. router ──────────────────────────────────────────────────────────
class _NoCloseSession:
    """讓串流結束後的保存寫進測試用 session，且不被 close。"""

    def __init__(self, db):
        self._db = db

    def __getattr__(self, name):
        return getattr(self._db, name)

    def close(self):
        pass


def _mine(ids=("act_mine",)):
    return patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": i, "name": i} for i in ids], None)),
    )


def _ai_patches(db, *, api_key="sk-test", chunks=("## 📌 重點摘要\n", "- 內容"), model_setting="openai/gpt-x"):
    analyze = MagicMock(side_effect=lambda **kwargs: iter(chunks))
    return analyze, [
        patch.object(ad_library_router.TokenManager, "get_ai_api_key", return_value=api_key),
        patch.object(ad_library_router.TokenManager, "get_ai_settings", return_value={"ai_model": model_setting}),
        patch.object(ad_library_router.AIService, "analyze_data", analyze),
        patch.object(ad_library_router, "_open_session", lambda: _NoCloseSession(db)),
    ]


def _start(patches):
    for p in patches:
        p.start()


def _stop(patches):
    for p in patches:
        p.stop()


@pytest.mark.integration
def test_post_ai_analysis_streams_and_saves(ad_library_client, db):  # noqa: F811
    _seed(db)
    analyze, patches = _ai_patches(db)
    _start(patches)
    try:
        with _mine():
            resp = ad_library_client.post(
                "/api/ad-library/ai-analysis", json={"account_id": "act_mine", "campaign_id": "c1"}
            )
    finally:
        _stop(patches)
    assert resp.status_code == 200
    assert resp.text == "## 📌 重點摘要\n- 內容"
    kwargs = analyze.call_args.kwargs
    assert kwargs["report_type"] == "ad_library_campaign"
    assert kwargs["model"] == "openai/gpt-x"
    assert kwargs["data"]["campaign"]["campaign_id"] == "c1"

    row = db.query(AdLibraryAiAnalysis).filter_by(account_id="act_mine", campaign_id="c1").one()
    assert row.status == "succeeded"
    assert row.content == "## 📌 重點摘要\n- 內容"
    assert row.model == "openai/gpt-x"
    assert row.context_hash == resp.headers["X-Context-Hash"]
    assert row.context_chars > 0


@pytest.mark.integration
def test_post_ai_analysis_marks_model_errors_failed(ad_library_client, db):  # noqa: F811
    _seed(db)
    _analyze, patches = _ai_patches(db, chunks=("\n[System Error during Analysis: 401]",))
    _start(patches)
    try:
        with _mine():
            ad_library_client.post(
                "/api/ad-library/ai-analysis",
                json={"account_id": "act_mine", "campaign_id": "c1", "model": "anthropic/claude-x"},
            )
    finally:
        _stop(patches)
    row = db.query(AdLibraryAiAnalysis).filter_by(account_id="act_mine").one()
    assert row.status == "failed"
    assert row.model == "anthropic/claude-x"


@pytest.mark.integration
def test_post_ai_analysis_requires_api_key_and_access(ad_library_client, db):  # noqa: F811
    _seed(db)
    analyze, patches = _ai_patches(db, api_key=None)
    _start(patches)
    try:
        with _mine():
            no_key = ad_library_client.post(
                "/api/ad-library/ai-analysis", json={"account_id": "act_mine", "campaign_id": "c1"}
            )
            outside = ad_library_client.post(
                "/api/ad-library/ai-analysis", json={"account_id": "act_other", "campaign_id": "c1"}
            )
    finally:
        _stop(patches)
    assert no_key.status_code == 400
    assert "API Key" in no_key.json()["detail"]
    assert outside.status_code == 403
    analyze.assert_not_called()

    _analyze, patches = _ai_patches(db)
    _start(patches)
    try:
        with _mine():
            missing = ad_library_client.post(
                "/api/ad-library/ai-analysis", json={"account_id": "act_mine", "campaign_id": "nope"}
            )
    finally:
        _stop(patches)
    assert missing.status_code == 404


@pytest.mark.integration
def test_get_ai_analysis_reports_latest_and_staleness(ad_library_client, db):  # noqa: F811
    _seed(db)
    _analyze, patches = _ai_patches(db)
    _start(patches)
    try:
        with _mine():
            before = ad_library_client.get(
                "/api/ad-library/ai-analysis", params={"account_id": "act_mine", "campaign_id": "c1"}
            ).json()
            ad_library_client.post("/api/ad-library/ai-analysis", json={"account_id": "act_mine", "campaign_id": "c1"})
            after = ad_library_client.get(
                "/api/ad-library/ai-analysis", params={"account_id": "act_mine", "campaign_id": "c1"}
            ).json()
            repository.upsert_items(db, [_row("a9", ["新廣告"], ["m9"], spend=5)])
            stale = ad_library_client.get(
                "/api/ad-library/ai-analysis", params={"account_id": "act_mine", "campaign_id": "c1"}
            ).json()
            outside = ad_library_client.get(
                "/api/ad-library/ai-analysis", params={"account_id": "act_other", "campaign_id": "c1"}
            )
    finally:
        _stop(patches)

    assert before["analysis"] is None and before["is_stale"] is False
    assert before["has_api_key"] is True and before["model"] == "openai/gpt-x"
    assert before["context_chars"] > 0
    assert after["analysis"]["content"] == "## 📌 重點摘要\n- 內容"
    assert after["is_stale"] is False
    assert stale["is_stale"] is True
    assert outside.status_code == 403
