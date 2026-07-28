"""
GA4 商品頁面與商品轉換率交叉對照驗證（docs/47 步驟 1+3）

涵蓋：
- 三支查詢（商品指標／商品×到達頁對照／到達頁指標）在應用層正確合併
- 同商品對應多個到達頁時，取瀏覽量最高者當「主要到達頁」
- 差異標記（page_underperforms_item）的四分位判定，含樣本數 <4 不標記
- 查無對照到達頁時該商品頁面欄位留 None、不中斷主表格
- 官方比率指標查詢失敗時退回本地件數比（沿用 items.py 既有容錯慣例）
- mapping/landing 查詢失敗時記錄在 payload 的錯誤欄位，不中斷主表格
- 端點路由與序列化契約
"""
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


@pytest.mark.unit
def test_get_item_landing_cross_merges_item_and_landing_page_metrics(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    item_rows = [{
        "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 5,
        "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.05,
    }]
    mapping_rows = [{"itemName": "P1", "landingPage": "/products/p1", "itemsViewed": 80}]
    landing_rows = [{"landingPage": "/products/p1", "sessions": 200, "sessionKeyEventRate": 0.12, "bounceRate": 0.4}]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "landingPage"]:
            return {"rows": mapping_rows}, None
        if dimensions == ["landingPage"]:
            return {"rows": landing_rows}, None
        return {"rows": item_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_item_landing_cross(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    row = snapshot.payload["items"][0]
    assert row["itemName"] == "P1"
    assert row["purchase_to_view_rate"] == 0.05
    assert row["primary_landing_page"] == "/products/p1"
    assert row["page_sessions"] == 200
    assert row["page_session_key_event_rate"] == 0.12
    assert row["page_bounce_rate"] == 0.4
    assert snapshot.kind == "item_landing_cross"


@pytest.mark.unit
def test_get_item_landing_cross_picks_highest_view_landing_page_when_multiple(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    item_rows = [{
        "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 5,
        "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.05,
    }]
    # P1 同時出現在兩個到達頁，/products/p1 瀏覽量較高應勝出
    mapping_rows = [
        {"itemName": "P1", "landingPage": "/products/p1", "itemsViewed": 70},
        {"itemName": "P1", "landingPage": "/campaign/landing", "itemsViewed": 30},
    ]
    landing_rows = [
        {"landingPage": "/products/p1", "sessions": 200, "sessionKeyEventRate": 0.12, "bounceRate": 0.4},
        {"landingPage": "/campaign/landing", "sessions": 50, "sessionKeyEventRate": 0.02, "bounceRate": 0.8},
    ]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "landingPage"]:
            return {"rows": mapping_rows}, None
        if dimensions == ["landingPage"]:
            return {"rows": landing_rows}, None
        return {"rows": item_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_item_landing_cross(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    assert snapshot.payload["items"][0]["primary_landing_page"] == "/products/p1"


@pytest.mark.unit
def test_get_item_landing_cross_flags_page_underperforms_item(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    # 4 個商品：P1 到達頁轉換率最低（後 25 百分位）但商品購買率不低 → 應標記。
    # P2~P4 陪襯，維持足夠樣本數（>=4）讓分位數判定生效。
    item_rows = [
        {"itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 8, "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.08},
        {"itemName": "P2", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 2, "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.02},
        {"itemName": "P3", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 5, "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.05},
        {"itemName": "P4", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 6, "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.06},
    ]
    mapping_rows = [
        {"itemName": "P1", "landingPage": "/products/p1", "itemsViewed": 100},
        {"itemName": "P2", "landingPage": "/products/p2", "itemsViewed": 100},
        {"itemName": "P3", "landingPage": "/products/p3", "itemsViewed": 100},
        {"itemName": "P4", "landingPage": "/products/p4", "itemsViewed": 100},
    ]
    landing_rows = [
        {"landingPage": "/products/p1", "sessions": 200, "sessionKeyEventRate": 0.01, "bounceRate": 0.9},
        {"landingPage": "/products/p2", "sessions": 200, "sessionKeyEventRate": 0.30, "bounceRate": 0.2},
        {"landingPage": "/products/p3", "sessions": 200, "sessionKeyEventRate": 0.20, "bounceRate": 0.3},
        {"landingPage": "/products/p4", "sessions": 200, "sessionKeyEventRate": 0.25, "bounceRate": 0.25},
    ]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "landingPage"]:
            return {"rows": mapping_rows}, None
        if dimensions == ["landingPage"]:
            return {"rows": landing_rows}, None
        return {"rows": item_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_item_landing_cross(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    by_item = {row["itemName"]: row for row in snapshot.payload["items"]}
    assert by_item["P1"]["page_underperforms_item"] is True
    assert by_item["P2"]["page_underperforms_item"] is False
    assert by_item["P3"]["page_underperforms_item"] is False


@pytest.mark.unit
def test_get_item_landing_cross_does_not_flag_when_sample_below_four(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    item_rows = [
        {"itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 8, "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.08},
        {"itemName": "P2", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 2, "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.02},
    ]
    mapping_rows = [
        {"itemName": "P1", "landingPage": "/products/p1", "itemsViewed": 100},
        {"itemName": "P2", "landingPage": "/products/p2", "itemsViewed": 100},
    ]
    landing_rows = [
        {"landingPage": "/products/p1", "sessions": 200, "sessionKeyEventRate": 0.01, "bounceRate": 0.9},
        {"landingPage": "/products/p2", "sessions": 200, "sessionKeyEventRate": 0.30, "bounceRate": 0.2},
    ]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "landingPage"]:
            return {"rows": mapping_rows}, None
        if dimensions == ["landingPage"]:
            return {"rows": landing_rows}, None
        return {"rows": item_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_item_landing_cross(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    assert all(row["page_underperforms_item"] is False for row in snapshot.payload["items"])


@pytest.mark.unit
def test_get_item_landing_cross_handles_missing_mapping_gracefully(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    item_rows = [{
        "itemName": "P1", "itemsViewed": 0, "itemsAddedToCart": 0, "itemsPurchased": 0,
        "itemRevenue": 0.0, "cartToViewRate": 0.0, "purchaseToViewRate": 0.0,
    }]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "landingPage"]:
            return {"rows": []}, None
        if dimensions == ["landingPage"]:
            return {"rows": []}, None
        return {"rows": item_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_item_landing_cross(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    row = snapshot.payload["items"][0]
    assert row["primary_landing_page"] is None
    assert row["page_sessions"] is None
    assert row["page_session_key_event_rate"] is None
    assert row["page_bounce_rate"] is None
    assert row["page_underperforms_item"] is False


@pytest.mark.unit
def test_get_item_landing_cross_falls_back_to_local_ratio_when_official_metrics_fail(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    call_count = {"main": 0}

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "landingPage"]:
            return {"rows": []}, None
        if dimensions == ["landingPage"]:
            return {"rows": []}, None
        call_count["main"] += 1
        if "cartToViewRate" in metrics:
            return None, "Field cartToViewRate is incompatible with itemName"
        return {"rows": [{"itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 10, "itemRevenue": 500.0}]}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_item_landing_cross(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    assert call_count["main"] == 2
    assert snapshot.payload["used_fallback_conversion_metrics"] is True
    assert snapshot.payload["items"][0]["purchase_to_view_rate"] == pytest.approx(10 / 100)


@pytest.mark.unit
def test_get_item_landing_cross_records_query_errors_without_raising(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    item_rows = [{
        "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 5,
        "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.05,
    }]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "landingPage"]:
            return None, "quota exceeded"
        if dimensions == ["landingPage"]:
            return None, "quota exceeded"
        return {"rows": item_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_item_landing_cross(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    assert snapshot.payload["mapping_query_error"] == "quota exceeded"
    assert snapshot.payload["landing_query_error"] == "quota exceeded"
    assert snapshot.payload["items"][0]["primary_landing_page"] is None


@pytest.mark.unit
def test_get_item_landing_cross_raises_when_item_query_fails_completely(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "landingPage"]:
            return {"rows": []}, None
        if dimensions == ["landingPage"]:
            return {"rows": []}, None
        return None, "No GA4 credentials found"

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    with pytest.raises(RuntimeError):
        GA4InsightsService.get_item_landing_cross(db, user=sample_user, property_id="123456", days=7)


# ─── 端點：路由與序列化契約 ──────────────────────────────────────────
@pytest.mark.integration
def test_item_landing_cross_endpoint_response_includes_expected_fields(client, db, sample_user, mocker):
    _override_dependencies(client.app, sample_user, db)

    item_rows = [{
        "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 5,
        "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.05,
    }]
    mapping_rows = [{"itemName": "P1", "landingPage": "/products/p1", "itemsViewed": 80}]
    landing_rows = [{"landingPage": "/products/p1", "sessions": 200, "sessionKeyEventRate": 0.12, "bounceRate": 0.4}]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "landingPage"]:
            return {"rows": mapping_rows}, None
        if dimensions == ["landingPage"]:
            return {"rows": landing_rows}, None
        return {"rows": item_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    resp = client.get("/api/ga4/insights/item-landing-cross", params={"property_id": "123456", "days": 7})
    assert resp.status_code == 200
    payload = resp.json()["payload"]
    row = payload["items"][0]
    assert row["itemName"] == "P1"
    assert row["primary_landing_page"] == "/products/p1"
    assert row["page_session_key_event_rate"] == 0.12


@pytest.mark.integration
def test_item_landing_cross_endpoint_returns_400_when_item_query_fails(client, db, sample_user, mocker):
    _override_dependencies(client.app, sample_user, db)

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "landingPage"]:
            return {"rows": []}, None
        if dimensions == ["landingPage"]:
            return {"rows": []}, None
        return None, "No GA4 credentials found"

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    resp = client.get("/api/ga4/insights/item-landing-cross", params={"property_id": "123456", "days": 7})
    assert resp.status_code == 400
