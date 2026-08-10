"""成效分析頁「AI 廣告分析」快照/分享連結測試（docs/58）。"""
import pytest

from routers.analytics_ai import get_current_user, require_analytics_view, require_fb_ads_module


def _override_dependencies(app, user):
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_fb_ads_module] = lambda: True
    app.dependency_overrides[require_analytics_view] = lambda: True


SAMPLE_PAYLOAD = {
    "account_id": "act_123",
    "team_id": None,
    "level": "campaign",
    "date_since": "2026-07-01",
    "date_until": "2026-07-07",
    "payload": {
        "selected_metrics": [{"key": "ctr", "label": "CTR", "format": "percent"}],
        "summary": {"ctr": 2.34},
        "rows": [{"name": "Campaign A", "ctr": 3.1}],
        "level": "campaign",
        "date_since": "2026-07-01",
        "date_until": "2026-07-07",
    },
}


# ─── ai_service.py：analytics_table prompt 分支 ─────────────────────
@pytest.mark.unit
def test_ai_service_analytics_table_prompt_includes_selected_metric_labels(mocker):
    from modules.ai_hub.service import AIService

    captured = {}

    def fake_zeabur(system_prompt, user_message, api_key, model):
        captured["system_prompt"] = system_prompt
        yield "ok"

    mocker.patch.object(AIService, "_analyze_with_zeabur", side_effect=fake_zeabur)

    list(AIService.analyze_data(
        data={
            "selected_metrics": [{"key": "ctr", "label": "CTR", "format": "percent"}],
            "summary": {"ctr": 2.34},
            "rows": [{"name": "Campaign A", "ctr": 3.1}],
        },
        context="test",
        report_type="analytics_table",
        provider="zeabur",
    ))

    assert "CTR" in captured["system_prompt"]
    assert "只分析" in captured["system_prompt"]


@pytest.mark.unit
def test_ai_service_analytics_table_prompt_handles_empty_selected_metrics(mocker):
    """使用者還沒勾選任何指標時，prompt 要明確要求 AI 說明而不是亂分析其他欄位。"""
    from modules.ai_hub.service import AIService

    captured = {}

    def fake_zeabur(system_prompt, user_message, api_key, model):
        captured["system_prompt"] = system_prompt
        yield "ok"

    mocker.patch.object(AIService, "_analyze_with_zeabur", side_effect=fake_zeabur)

    list(AIService.analyze_data(
        data={"selected_metrics": [], "summary": {}, "rows": []},
        context="test",
        report_type="analytics_table",
        provider="zeabur",
    ))

    assert "尚未勾選任何指標" in captured["system_prompt"]


@pytest.mark.unit
def test_ai_service_analytics_table_prompt_does_not_force_spend_roas(mocker):
    """跟 weekly_summary 的差別：不能沿用寫死「花費/ROAS/成交數」的範例，
    否則使用者只勾 CTR 時，AI 還是會被範例帶著講花費/ROAS。"""
    from modules.ai_hub.service import AIService

    captured = {}

    def fake_zeabur(system_prompt, user_message, api_key, model):
        captured["system_prompt"] = system_prompt
        yield "ok"

    mocker.patch.object(AIService, "_analyze_with_zeabur", side_effect=fake_zeabur)

    list(AIService.analyze_data(
        data={
            "selected_metrics": [{"key": "ctr", "label": "CTR", "format": "percent"}],
            "summary": {"ctr": 2.34},
            "rows": [],
        },
        context="test",
        report_type="analytics_table",
        provider="zeabur",
    ))

    assert "花費、ROAS、成交數" not in captured["system_prompt"]


# ─── 快照 CRUD + 分享連結端點 ────────────────────────────────────────
def test_analytics_ai_snapshot_create_ai_summary_and_share_flow(client, db, sample_user):
    _override_dependencies(client.app, sample_user)

    created = client.post("/api/analytics-ai/snapshots", json=SAMPLE_PAYLOAD)
    assert created.status_code == 200
    body = created.json()
    snapshot_id = body["snapshot_id"]
    assert body["account_id"] == "act_123"
    assert body["level"] == "campaign"
    assert body["payload"]["selected_metrics"][0]["key"] == "ctr"
    assert body["ai_summary"] is None

    saved = client.put(
        f"/api/analytics-ai/snapshots/{snapshot_id}/ai-summary",
        json={"ai_summary": "這是 AI 白話解讀"},
    )
    assert saved.status_code == 200
    assert saved.json()["ai_summary"] == "這是 AI 白話解讀"

    missing = client.put(
        "/api/analytics-ai/snapshots/does-not-exist/ai-summary",
        json={"ai_summary": "x"},
    )
    assert missing.status_code == 404

    shared_first = client.post(f"/api/analytics-ai/snapshots/{snapshot_id}/share")
    assert shared_first.status_code == 200
    token = shared_first.json()["share_token"]
    assert token

    # 重複點擊「產生分享連結」要回傳同一組 token（get_or_create），不是每次都換新的。
    shared_second = client.post(f"/api/analytics-ai/snapshots/{snapshot_id}/share")
    assert shared_second.json()["share_token"] == token

    # 公開端點：拿掉認證/權限依賴的覆寫（但保留 get_db，測試仍要連同一個
    # transaction-bound session），驗證它真的不需要登入即可存取。
    app_overrides_backup = dict(client.app.dependency_overrides)
    for dep in (get_current_user, require_fb_ads_module, require_analytics_view):
        client.app.dependency_overrides.pop(dep, None)
    try:
        public = client.get(f"/api/analytics-ai/share/{token}")
        assert public.status_code == 200
        public_body = public.json()
        assert public_body["account_id"] == "act_123"
        assert public_body["ai_summary"] == "這是 AI 白話解讀"
        assert public_body["payload"]["rows"][0]["name"] == "Campaign A"
        # 分享頁不該洩漏內部欄位。
        assert "created_by" not in public_body
        assert "team_id" not in public_body

        not_found = client.get("/api/analytics-ai/share/does-not-exist-token")
        assert not_found.status_code == 404
    finally:
        client.app.dependency_overrides.update(app_overrides_backup)


def test_analytics_ai_snapshot_share_returns_404_for_missing_snapshot(client, db, sample_user):
    _override_dependencies(client.app, sample_user)

    resp = client.post("/api/analytics-ai/snapshots/does-not-exist/share")
    assert resp.status_code == 404


def test_analytics_ai_create_snapshot_rejects_non_member_team_id(client, db, sample_user):
    """team_id 帶了非本人所屬的團隊時要擋下來，不能任意把快照掛到別的團隊底下。"""
    from database import Team

    _override_dependencies(client.app, sample_user)

    other_team = Team(id="team-not-mine", name="Someone Else's Team")
    db.add(other_team)
    db.commit()

    payload = dict(SAMPLE_PAYLOAD)
    payload["team_id"] = "team-not-mine"

    resp = client.post("/api/analytics-ai/snapshots", json=payload)
    assert resp.status_code == 403


def test_analytics_ai_create_snapshot_allows_member_team_id(client, db, sample_user):
    from database import Team, TeamMember

    _override_dependencies(client.app, sample_user)

    team = Team(id="team-mine", name="My Team")
    db.add(team)
    db.add(TeamMember(team_id="team-mine", user_id=sample_user.id))
    db.commit()

    payload = dict(SAMPLE_PAYLOAD)
    payload["team_id"] = "team-mine"

    resp = client.post("/api/analytics-ai/snapshots", json=payload)
    assert resp.status_code == 200
    assert resp.json()["snapshot_id"]
