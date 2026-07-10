"""
GA4 商品分析篩選＋購買轉換率＋口徑對齊驗證（docs/22 第 6 波，追加）

涵蓋：
- 主查詢改用官方 `cartToViewRate`/`purchaseToViewRate`（使用者去重口徑）
- 相容性保險：官方指標查詢失敗時退回本地件數比，並標記 `used_fallback_conversion_metrics`
- 商品主要分類（itemName × itemCategory，取瀏覽最高者；查詢失敗不中斷主表格）
- 潛力標記改用 `cart_to_view_rate`，且維持「全店」中位數（不隨分類切分）
- `views_recent_7d`/`views_prior_7d` 進 payload 且與成長率一致
- 向後相容欄位檢查
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


# ─── 官方口徑：主查詢使用 cartToViewRate/purchaseToViewRate ───────────
@pytest.mark.unit
def test_get_items_uses_official_rate_metrics(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    captured_metrics = []
    main_rows = [{
        "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 5,
        "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.05,
    }]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            return {"rows": []}, None
        if metrics == ["itemsViewed"] and dimensions == ["itemName"]:
            return {"rows": []}, None
        captured_metrics.append(metrics)
        return {"rows": main_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_items(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    assert "cartToViewRate" in captured_metrics[0]
    assert "purchaseToViewRate" in captured_metrics[0]
    row = snapshot.payload["items"][0]
    assert row["cart_to_view_rate"] == 0.2
    assert row["purchase_to_view_rate"] == 0.05
    assert snapshot.payload["used_fallback_conversion_metrics"] is False
    assert "cart_to_view_rate_definition" in snapshot.payload
    assert "purchase_to_view_rate_definition" in snapshot.payload
    # 舊件數比仍保留供回溯
    assert row["add_to_cart_rate"] == pytest.approx(20 / 100)


# ─── 相容性保險：官方指標失敗時退回本地件數比 ─────────────────────
@pytest.mark.unit
def test_get_items_falls_back_to_local_ratios_when_official_metrics_fail(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    call_count = {"main": 0}

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            return {"rows": []}, None
        if metrics == ["itemsViewed"] and dimensions == ["itemName"]:
            return {"rows": []}, None
        call_count["main"] += 1
        if "cartToViewRate" in metrics:
            return None, "Field cartToViewRate is incompatible with itemName"
        return {
            "rows": [{"itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 10, "itemRevenue": 500.0}]
        }, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_items(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    assert call_count["main"] == 2  # 先試官方指標、失敗後退回基礎指標
    assert snapshot.payload["used_fallback_conversion_metrics"] is True
    row = snapshot.payload["items"][0]
    assert row["cart_to_view_rate"] == pytest.approx(20 / 100)
    assert row["purchase_to_view_rate"] == pytest.approx(10 / 100)


@pytest.mark.unit
def test_get_items_raises_when_fallback_also_fails(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            return {"rows": []}, None
        if metrics == ["itemsViewed"] and dimensions == ["itemName"]:
            return {"rows": []}, None
        return None, "No GA4 credentials found"

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    with pytest.raises(RuntimeError):
        GA4InsightsService.get_items(db, user=sample_user, property_id="123456", days=7)


# ─── 商品主要分類 ────────────────────────────────────────────────────
@pytest.mark.unit
def test_get_items_assigns_main_category_by_highest_views(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    main_rows = [{
        "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 5,
        "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.05,
    }]
    # P1 同時出現在兩個分類，Apparel 瀏覽量較高應勝出
    breakdown_rows = [
        {"itemName": "P1", "itemCategory": "Apparel", "itemsViewed": 70},
        {"itemName": "P1", "itemCategory": "Accessories", "itemsViewed": 30},
    ]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            return {"rows": breakdown_rows}, None
        if metrics == ["itemsViewed"] and dimensions == ["itemName"]:
            return {"rows": []}, None
        return {"rows": main_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_items(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    assert snapshot.payload["items"][0]["item_category"] == "Apparel"
    assert snapshot.payload["category_counts"] == {"Apparel": 1}


@pytest.mark.unit
def test_get_items_defaults_to_not_set_when_category_breakdown_fails(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    main_rows = [{
        "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 5,
        "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.05,
    }]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            return None, "quota exceeded"
        if metrics == ["itemsViewed"] and dimensions == ["itemName"]:
            return {"rows": []}, None
        return {"rows": main_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_items(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    assert snapshot.payload["items"][0]["item_category"] == "(not set)"
    assert snapshot.payload["category_counts"] == {"(not set)": 1}


# ─── 潛力標記：全店中位數，不隨分類切分 ─────────────────────────────
@pytest.mark.unit
def test_get_items_potential_flag_uses_store_wide_median_not_per_category(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    # 4 個商品橫跨 2 個分類；P1 條件最好但分類內只有它自己（若比照第 5 波
    # 同分類邏輯樣本會 <4 而不標記）——驗證這裡仍用全店中位數會標記成功。
    main_rows = [
        {"itemName": "P1", "itemsViewed": 40, "itemsAddedToCart": 20, "itemsPurchased": 5, "itemRevenue": 500.0, "cartToViewRate": 0.5, "purchaseToViewRate": 0.125},
        {"itemName": "P2", "itemsViewed": 500, "itemsAddedToCart": 50, "itemsPurchased": 40, "itemRevenue": 4000.0, "cartToViewRate": 0.1, "purchaseToViewRate": 0.08},
        {"itemName": "P3", "itemsViewed": 200, "itemsAddedToCart": 20, "itemsPurchased": 10, "itemRevenue": 1000.0, "cartToViewRate": 0.1, "purchaseToViewRate": 0.05},
        {"itemName": "P4", "itemsViewed": 300, "itemsAddedToCart": 15, "itemsPurchased": 5, "itemRevenue": 500.0, "cartToViewRate": 0.05, "purchaseToViewRate": 0.017},
    ]
    breakdown_rows = [
        {"itemName": "P1", "itemCategory": "Apparel", "itemsViewed": 40},
        {"itemName": "P2", "itemCategory": "Electronics", "itemsViewed": 500},
        {"itemName": "P3", "itemCategory": "Electronics", "itemsViewed": 200},
        {"itemName": "P4", "itemCategory": "Electronics", "itemsViewed": 300},
    ]
    recent_rows = [
        {"itemName": "P1", "itemsViewed": 40}, {"itemName": "P2", "itemsViewed": 500},
        {"itemName": "P3", "itemsViewed": 100}, {"itemName": "P4", "itemsViewed": 100},
    ]
    prior_rows = [
        {"itemName": "P1", "itemsViewed": 10}, {"itemName": "P2", "itemsViewed": 500},
        {"itemName": "P3", "itemsViewed": 100}, {"itemName": "P4", "itemsViewed": 200},
    ]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            return {"rows": breakdown_rows}, None
        if metrics == ["itemsViewed"] and dimensions == ["itemName"]:
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

    by_item = {row["itemName"]: row for row in snapshot.payload["items"]}
    # P1 是 Apparel 分類裡唯一的商品（樣本數 1，若同分類判定會被跳過）；
    # 全店中位數判定下應正常被標記為潛力商品。
    assert by_item["P1"]["item_category"] == "Apparel"
    assert by_item["P1"]["is_potential"] is True
    assert by_item["P2"]["is_potential"] is False


# ─── views_recent_7d / views_prior_7d 進 payload ────────────────────
@pytest.mark.unit
def test_get_items_includes_raw_view_counts_for_growth_rate(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    main_rows = [{
        "itemName": "P1", "itemsViewed": 40, "itemsAddedToCart": 20, "itemsPurchased": 5,
        "itemRevenue": 500.0, "cartToViewRate": 0.5, "purchaseToViewRate": 0.125,
    }]
    recent_rows = [{"itemName": "P1", "itemsViewed": 40}]
    prior_rows = [{"itemName": "P1", "itemsViewed": 10}]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            return {"rows": []}, None
        if metrics == ["itemsViewed"] and dimensions == ["itemName"]:
            if start_date >= "2026-07-03":
                return {"rows": recent_rows}, None
            return {"rows": prior_rows}, None
        return {"rows": main_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)
    mocker.patch(
        "modules.ga4.insights_service.GA4InsightsService._trailing_period",
        side_effect=lambda days, now_local=None: ("2026-07-03", "2026-07-09") if days == 7 else ("2026-06-26", "2026-07-09"),
    )

    snapshot = GA4InsightsService.get_items(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    row = snapshot.payload["items"][0]
    assert row["views_recent_7d"] == 40
    assert row["views_prior_7d"] == 10
    assert row["views_growth_rate"] == pytest.approx((40 - 10) / 10)


# ─── router：端點行為與序列化契約 ───────────────────────────────────
@pytest.mark.integration
def test_items_endpoint_response_includes_new_fields(client, db, sample_user, mocker):
    _override_dependencies(client.app, sample_user, db)

    main_rows = [{
        "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 5,
        "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.05,
    }]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            return {"rows": [{"itemName": "P1", "itemCategory": "Apparel", "itemsViewed": 100}]}, None
        if metrics == ["itemsViewed"] and dimensions == ["itemName"]:
            return {"rows": []}, None
        return {"rows": main_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    resp = client.get("/api/ga4/insights/items", params={"property_id": "123456", "days": 7})
    assert resp.status_code == 200
    payload = resp.json()["payload"]
    assert payload["items"][0]["item_category"] == "Apparel"
    assert payload["items"][0]["cart_to_view_rate"] == 0.2
    assert payload["category_counts"] == {"Apparel": 1}
    assert payload["used_fallback_conversion_metrics"] is False
