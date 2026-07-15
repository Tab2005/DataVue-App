"""
GA4 洞察頁第 2 波驗證（docs/22 第 2 波：當日儀表板/Realtime/渠道/到達頁/商品/AI 白話解讀）

涵蓋：
- insights_service.py 純邏輯（百分位數、期間計算、渠道助攻/主攻分級、
  到達頁高流量低轉換標記、商品潛力標記、儀表板基線與異常判斷、Realtime 彙總）
- repository.py 新增的 snapshot 存取（get_snapshot_by_id / update_ai_summary）
- insights_router.py 新增端點的路由/序列化契約
- ai_service.py 新增的 report_type="ga4_insights" prompt 分支
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from modules.ga4.dependencies import (
    require_ga4_insights_manage_alerts,
    require_ga4_insights_view,
    require_ga4_module,
)
from modules.ga4.insights_router import get_current_user


def _override_dependencies(app, user, db):
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_ga4_module] = lambda: True
    app.dependency_overrides[require_ga4_insights_view] = lambda: True
    app.dependency_overrides[require_ga4_insights_manage_alerts] = lambda: True


class _FakeValue:
    def __init__(self, value):
        self.value = value


class _FakeRealtimeRow:
    def __init__(self, dimension_values, metric_values):
        self.dimension_values = [_FakeValue(v) for v in dimension_values]
        self.metric_values = [_FakeValue(v) for v in metric_values]


class _FakeRealtimeResponse:
    def __init__(self, rows):
        self.rows = rows


# ─── 純函數 ─────────────────────────────────────────────────────────
@pytest.mark.unit
def test_percentile_linear_interpolation():
    from modules.ga4.insights_service import _percentile

    values = [10, 20, 30, 40]
    assert _percentile(values, 0.0) == 10
    assert _percentile(values, 1.0) == 40
    assert _percentile(values, 0.5) == 25
    assert _percentile([], 0.5) == 0.0
    assert _percentile([7], 0.9) == 7


@pytest.mark.unit
def test_trailing_period_ends_yesterday():
    from modules.ga4.insights_service import GA4InsightsService

    now_local = datetime(2026, 7, 10, 15, 0)
    start, end = GA4InsightsService._trailing_period(7, now_local=now_local)
    assert end == "2026-07-09"
    assert start == "2026-07-03"


# ─── 當日儀表板：基線與異常判斷 ───────────────────────────────────────
@pytest.mark.unit
def test_fetch_intraday_dashboard_payload_flags_anomaly(mocker):
    from modules.ga4.insights_service import GA4InsightsService

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["hour", "sessionDefaultChannelGroup"]:
            return {
                "rows": [
                    {"hour": "09", "sessionDefaultChannelGroup": "Organic Search", "sessions": 10, "conversions": 1, "purchaseRevenue": 100.0},
                    {"hour": "10", "sessionDefaultChannelGroup": "Paid Search", "sessions": 20, "conversions": 2, "purchaseRevenue": 200.0},
                ]
            }, None
        if dimensions == ["hour"]:
            metric = metrics[0]
            return {"rows": [{"hour": "09", metric: 5}, {"hour": "10", metric: 5}]}, None
        return {"rows": []}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    payload = GA4InsightsService._fetch_intraday_dashboard_payload(
        user=MagicMock(), property_id="123456", db=None, now_local=datetime(2026, 7, 10, 10, 30)
    )

    assert payload["date"] == "2026-07-10"
    assert payload["current_hour"] == 10
    assert len(payload["hourly_totals"]) == 2
    # sessions 累計 = 10 + 20 = 30；8 週基線每期都是 5+5=10 → median 10 遠低於觀測值 → 異常
    assert payload["cumulative_totals"]["sessions"] == 30
    assert payload["baseline"]["sessions"]["sample_size"] == 8
    assert payload["is_anomaly"]["sessions"] is True


@pytest.mark.unit
def test_get_dashboard_uses_cache_without_refetching(mocker, db, sample_user):
    from modules.ga4.insights_service import DASHBOARD_KIND, GA4InsightsService
    from modules.ga4.repository import repository

    today = (datetime.utcnow() + timedelta(hours=8)).date().isoformat()
    repository.upsert_snapshot(
        db, property_id="123456", kind=DASHBOARD_KIND, date=today,
        payload={"date": today, "cached": True}, fetched_by=sample_user.id,
    )
    db.commit()

    mock_fetch = mocker.patch(
        "modules.ga4.insights_service.GA4InsightsService._fetch_intraday_dashboard_payload"
    )

    snapshot = GA4InsightsService.get_dashboard(db, user=sample_user, property_id="123456")

    assert snapshot.payload["cached"] is True
    mock_fetch.assert_not_called()


@pytest.mark.unit
def test_refresh_dashboard_respects_cooldown_then_refreshes(mocker, db, sample_user):
    from modules.ga4.insights_service import DASHBOARD_KIND, GA4InsightsService
    from modules.ga4.repository import repository

    today = (datetime.utcnow() + timedelta(hours=8)).date().isoformat()
    existing = repository.upsert_snapshot(
        db, property_id="123456", kind=DASHBOARD_KIND, date=today,
        payload={"date": today, "stage": "first"}, fetched_by=sample_user.id,
    )
    db.commit()
    db.refresh(existing)

    mock_fetch = mocker.patch(
        "modules.ga4.insights_service.GA4InsightsService._fetch_intraday_dashboard_payload",
        return_value={"date": today, "stage": "second"},
    )

    # 冷卻期內（剛寫入）：不重新抓取
    snapshot, refreshed = GA4InsightsService.refresh_dashboard(db, user=sample_user, property_id="123456")
    assert refreshed is False
    mock_fetch.assert_not_called()
    assert snapshot.payload["stage"] == "first"

    # 冷卻期外：允許重新抓取
    existing.fetched_at = datetime.utcnow() - timedelta(minutes=11)
    db.add(existing)
    db.commit()

    snapshot, refreshed = GA4InsightsService.refresh_dashboard(db, user=sample_user, property_id="123456")
    assert refreshed is True
    mock_fetch.assert_called_once()
    assert snapshot.payload["stage"] == "second"


# ─── Realtime 心跳 ──────────────────────────────────────────────────
@pytest.mark.unit
def test_get_realtime_aggregates_total_and_breakdown(mocker):
    from modules.ga4.insights_service import GA4InsightsService

    mocker.patch("modules.ga4.insights_service.GA4Client.get_credentials", return_value=MagicMock())

    def fake_run_realtime_report(creds, property_id, dimensions, metrics, limit=None):
        if dimensions == []:
            return _FakeRealtimeResponse([_FakeRealtimeRow([], ["42", "100"])])
        return _FakeRealtimeResponse([
            _FakeRealtimeRow(["/home"], ["30"]),
            _FakeRealtimeRow(["/product"], ["12"]),
        ])

    mocker.patch(
        "modules.ga4.insights_service.GA4Client.run_realtime_report", side_effect=fake_run_realtime_report
    )

    result = GA4InsightsService.get_realtime(user=MagicMock(), property_id="123456", db=None)

    assert result["window_minutes"] == 30
    assert result["active_users"] == 42
    assert result["event_count"] == 100
    assert result["by_screen"] == [
        {"screen_name": "/home", "active_users": 30},
        {"screen_name": "/product", "active_users": 12},
    ]


@pytest.mark.unit
def test_get_realtime_without_credentials_raises(mocker):
    from modules.ga4.insights_service import GA4InsightsService

    mocker.patch("modules.ga4.insights_service.GA4Client.get_credentials", return_value=None)

    with pytest.raises(RuntimeError):
        GA4InsightsService.get_realtime(user=MagicMock(), property_id="123456", db=None)


# ─── 渠道主攻/助攻對照 ──────────────────────────────────────────────
@pytest.mark.unit
def test_get_channels_tags_assist_close_balanced_and_insufficient(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["sessionDefaultChannelGroup"]:
            return {"rows": [
                {"sessionDefaultChannelGroup": "Organic Search", "conversions": 10},
                {"sessionDefaultChannelGroup": "Paid Search", "conversions": 10},
                {"sessionDefaultChannelGroup": "Direct", "conversions": 10},
                {"sessionDefaultChannelGroup": "Referral", "conversions": 0},
            ]}, None
        return {"rows": [
            {"firstUserDefaultChannelGroup": "Organic Search", "conversions": 20},  # ratio 2.0 -> assist
            {"firstUserDefaultChannelGroup": "Paid Search", "conversions": 5},      # ratio 0.5 -> close
            {"firstUserDefaultChannelGroup": "Direct", "conversions": 10},          # ratio 1.0 -> balanced
            {"firstUserDefaultChannelGroup": "Referral", "conversions": 3},         # closing 0 -> insufficient_data
        ]}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_channels(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    tags = {row["channel"]: row["tag"] for row in snapshot.payload["channels"]}
    assert tags["Organic Search"] == "assist"
    assert tags["Paid Search"] == "close"
    assert tags["Direct"] == "balanced"
    assert tags["Referral"] == "insufficient_data"


# ─── 到達頁：高流量低轉換 ───────────────────────────────────────────
@pytest.mark.unit
def test_get_landing_pages_flags_high_traffic_low_conversion(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    rows = [
        {"landingPage": "/a", "sessions": 1000, "engagementRate": 0.3, "conversions": 1, "bounceRate": 0.8},
        {"landingPage": "/b", "sessions": 50, "engagementRate": 0.6, "conversions": 10, "bounceRate": 0.2},
        {"landingPage": "/c", "sessions": 40, "engagementRate": 0.5, "conversions": 8, "bounceRate": 0.3},
        {"landingPage": "/d", "sessions": 30, "engagementRate": 0.5, "conversions": 6, "bounceRate": 0.3},
    ]
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics", return_value=({"rows": rows}, None)
    )

    snapshot = GA4InsightsService.get_landing_pages(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    flagged = {row["landingPage"]: row["is_high_traffic_low_conversion"] for row in snapshot.payload["landing_pages"]}
    assert flagged["/a"] is True
    assert flagged["/b"] is False
    assert flagged["/c"] is False
    assert flagged["/d"] is False


@pytest.mark.unit
def test_get_landing_pages_skips_tagging_with_small_sample(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    rows = [
        {"landingPage": "/a", "sessions": 1000, "engagementRate": 0.3, "conversions": 1, "bounceRate": 0.8},
        {"landingPage": "/b", "sessions": 10, "engagementRate": 0.6, "conversions": 5, "bounceRate": 0.2},
    ]
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics", return_value=({"rows": rows}, None)
    )

    snapshot = GA4InsightsService.get_landing_pages(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    assert all(row["is_high_traffic_low_conversion"] is False for row in snapshot.payload["landing_pages"])


# ─── 商品：潛力商品 ─────────────────────────────────────────────────
# 第 6 波後主查詢改用官方 cartToViewRate/purchaseToViewRate 且多一次
# itemName×itemCategory 分項查詢，同樣用 metrics=["itemsViewed"]，須靠
# dimensions 才能跟近/前 7 天查詢分開；完整覆蓋見 tests/test_ga4_item_analysis.py。
@pytest.mark.unit
def test_get_items_flags_potential_products(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    main_rows = [
        {"itemName": "P1", "itemsViewed": 40, "itemsAddedToCart": 20, "itemsPurchased": 5, "itemRevenue": 500.0, "cartToViewRate": 0.5, "purchaseToViewRate": 0.125},
        {"itemName": "P2", "itemsViewed": 500, "itemsAddedToCart": 50, "itemsPurchased": 40, "itemRevenue": 4000.0, "cartToViewRate": 0.1, "purchaseToViewRate": 0.08},
        {"itemName": "P3", "itemsViewed": 200, "itemsAddedToCart": 20, "itemsPurchased": 10, "itemRevenue": 1000.0, "cartToViewRate": 0.1, "purchaseToViewRate": 0.05},
        {"itemName": "P4", "itemsViewed": 300, "itemsAddedToCart": 15, "itemsPurchased": 5, "itemRevenue": 500.0, "cartToViewRate": 0.05, "purchaseToViewRate": 0.017},
    ]
    recent_rows = [
        {"itemName": "P1", "itemsViewed": 40},
        {"itemName": "P2", "itemsViewed": 500},
        {"itemName": "P3", "itemsViewed": 100},
        {"itemName": "P4", "itemsViewed": 100},
    ]
    prior_rows = [
        {"itemName": "P1", "itemsViewed": 10},   # growth = 3.0 -> high
        {"itemName": "P2", "itemsViewed": 500},  # growth = 0.0
        {"itemName": "P3", "itemsViewed": 100},  # growth = 0.0
        {"itemName": "P4", "itemsViewed": 200},  # growth = -0.5
    ]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            return {"rows": []}, None
        if metrics == ["itemsViewed"]:
            # 依日期區間分辨 recent vs prior（recent 較晚）
            if start_date >= "2026-07-03":
                return {"rows": recent_rows}, None
            return {"rows": prior_rows}, None
        return {"rows": main_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)
    mocker.patch(
        "modules.ga4.insights_service.GA4InsightsService._trailing_period",
        side_effect=lambda days, now_local=None: ("2026-07-03", "2026-07-09") if days == 7 else ("2026-06-26", "2026-07-09"),
    )

    snapshot = GA4InsightsService.get_items(db, user=sample_user, property_id="123456", days=14)
    db.commit()

    potential = {row["itemName"]: row["is_potential"] for row in snapshot.payload["items"]}
    # P1：瀏覽成長最高（3.0）、瀏覽後加購率最高（0.5）、瀏覽量最低（40）→ 三條件皆過中位數 → 潛力商品
    assert potential["P1"] is True
    assert potential["P2"] is False


# ─── repository：snapshot 存取 + AI 摘要持久化 ─────────────────────
@pytest.mark.unit
def test_repository_get_snapshot_and_update_ai_summary(db, sample_user):
    from modules.ga4.repository import repository

    row = repository.upsert_snapshot(
        db, property_id="123456", kind="daily_channel", date="2026-07-09",
        payload={"channels": []}, fetched_by=sample_user.id,
    )
    db.commit()

    fetched = repository.get_snapshot_by_id(db, row.id)
    assert fetched.id == row.id

    updated = repository.update_ai_summary(db, snapshot_id=row.id, ai_summary="測試白話解讀")
    db.commit()
    assert updated.ai_summary == "測試白話解讀"
    assert updated.ai_summary_generated_at is not None

    assert repository.update_ai_summary(db, snapshot_id="does-not-exist", ai_summary="x") is None


# ─── router：端點路由與序列化契約 ───────────────────────────────────
@pytest.mark.integration
def test_dashboard_and_refresh_endpoints(client, db, sample_user, mocker):
    _override_dependencies(client.app, sample_user, db)

    mock_get = mocker.patch(
        "modules.ga4.insights_router.GA4InsightsService.get_dashboard"
    )
    from database.models.ga4_insights import GA4InsightsSnapshot
    fake_row = GA4InsightsSnapshot(
        property_id="123456", kind="intraday_dashboard", date="2026-07-10", payload={"ok": True},
    )
    db.add(fake_row)
    db.commit()
    db.refresh(fake_row)
    mock_get.return_value = fake_row

    resp = client.get("/api/ga4/insights/dashboard", params={"property_id": "123456"})
    assert resp.status_code == 200
    assert resp.json()["payload"] == {"ok": True}
    assert resp.json()["snapshot_id"] == fake_row.id

    mock_refresh = mocker.patch(
        "modules.ga4.insights_router.GA4InsightsService.refresh_dashboard",
        return_value=(fake_row, True),
    )
    resp = client.post("/api/ga4/insights/dashboard/refresh", json={"property_id": "123456"})
    assert resp.status_code == 200
    assert resp.json()["refreshed"] is True
    mock_refresh.assert_called_once()


@pytest.mark.integration
def test_realtime_endpoint(client, db, sample_user, mocker):
    _override_dependencies(client.app, sample_user, db)
    mocker.patch(
        "modules.ga4.insights_router.GA4InsightsService.get_realtime",
        return_value={"window_minutes": 30, "active_users": 5, "event_count": 20, "by_screen": []},
    )
    resp = client.get("/api/ga4/insights/realtime", params={"property_id": "123456"})
    assert resp.status_code == 200
    assert resp.json()["active_users"] == 5


@pytest.mark.integration
def test_channels_landing_pages_items_endpoints(client, db, sample_user, mocker):
    _override_dependencies(client.app, sample_user, db)
    from modules.ga4.repository import repository

    for kind, path in [
        ("daily_channel", "channels"),
        ("landing_page", "landing-pages"),
        ("item", "items"),
    ]:
        row = repository.upsert_snapshot(
            db, property_id="123456", kind=kind, date="2026-07-09", payload={"kind": kind}, fetched_by=sample_user.id,
        )
        db.commit()
        method_name = {
            "daily_channel": "get_channels",
            "landing_page": "get_landing_pages",
            "item": "get_items",
        }[kind]
        mocker.patch(f"modules.ga4.insights_router.GA4InsightsService.{method_name}", return_value=row)

        resp = client.get(f"/api/ga4/insights/{path}", params={"property_id": "123456", "days": 7})
        assert resp.status_code == 200
        assert resp.json()["payload"] == {"kind": kind}


@pytest.mark.integration
def test_save_ai_summary_endpoint(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)
    from modules.ga4.repository import repository

    row = repository.upsert_snapshot(
        db, property_id="123456", kind="landing_page", date="2026-07-09", payload={}, fetched_by=sample_user.id,
    )
    db.commit()

    resp = client.put(
        f"/api/ga4/insights/snapshots/{row.id}/ai-summary",
        json={"ai_summary": "這是白話解讀"},
    )
    assert resp.status_code == 200
    assert resp.json()["ai_summary"] == "這是白話解讀"

    missing = client.put(
        "/api/ga4/insights/snapshots/does-not-exist/ai-summary",
        json={"ai_summary": "x"},
    )
    assert missing.status_code == 404


# ─── ai_service.py：ga4_insights prompt 分支 ───────────────────────
@pytest.mark.unit
def test_ai_service_ga4_insights_prompt_switches_focus_by_kind(mocker):
    from ai_service import AIService

    captured = {}

    def fake_zeabur(system_prompt, user_message, api_key, model):
        captured["system_prompt"] = system_prompt
        yield "ok"

    mocker.patch.object(AIService, "_analyze_with_zeabur", side_effect=fake_zeabur)

    list(AIService.analyze_data(
        data={"kind": "daily_channel", "channels": []},
        context="test",
        report_type="ga4_insights",
        provider="zeabur",
    ))

    assert "助攻" in captured["system_prompt"]
    assert "貢獻分析頁" in captured["system_prompt"]


# ─── docs/34 第二波：daily_channel prompt 依 attribution_model 調整用語 ──
@pytest.mark.unit
def test_ai_service_ga4_insights_prompt_avoids_last_click_metaphor_for_data_driven(mocker):
    """Data-driven 屬性不該被套用「結帳前臨門一腳」這類 last-click 專屬比喻。"""
    from ai_service import AIService

    captured = {}

    def fake_zeabur(system_prompt, user_message, api_key, model):
        captured["system_prompt"] = system_prompt
        yield "ok"

    mocker.patch.object(AIService, "_analyze_with_zeabur", side_effect=fake_zeabur)

    list(AIService.analyze_data(
        data={"kind": "daily_channel", "channels": [], "attribution_model": "data_driven"},
        context="test",
        report_type="ga4_insights",
        provider="zeabur",
    ))

    assert "結帳前推最後一把" not in captured["system_prompt"]
    assert "結帳前臨門一腳" not in captured["system_prompt"]
    assert "貢獻比較大" in captured["system_prompt"]


@pytest.mark.unit
def test_ai_service_ga4_insights_prompt_keeps_last_click_metaphor_for_last_click(mocker):
    """Last-click 屬性維持「最後一次點擊」語意，不能被 data_driven 用語覆蓋。"""
    from ai_service import AIService

    captured = {}

    def fake_zeabur(system_prompt, user_message, api_key, model):
        captured["system_prompt"] = system_prompt
        yield "ok"

    mocker.patch.object(AIService, "_analyze_with_zeabur", side_effect=fake_zeabur)

    list(AIService.analyze_data(
        data={"kind": "daily_channel", "channels": [], "attribution_model": "last_click"},
        context="test",
        report_type="ga4_insights",
        provider="zeabur",
    ))

    assert "最後一次點擊進來的" in captured["system_prompt"]
