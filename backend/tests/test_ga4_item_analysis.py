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
    # category_breakdown_error 讓前端能分辨「查詢真的失敗」跟「GA4 本來就
    # 沒有 item_category 資料」，兩者在畫面上都會顯示「未分類」但成因不同。
    assert snapshot.payload["category_breakdown_error"] == "quota exceeded"


@pytest.mark.unit
def test_get_items_category_breakdown_error_is_none_on_success(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    main_rows = [{
        "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 5,
        "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.05,
    }]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            return {"rows": [{"itemName": "P1", "itemCategory": "(not set)", "itemsViewed": 100}]}, None
        if metrics == ["itemsViewed"] and dimensions == ["itemName"]:
            return {"rows": []}, None
        return {"rows": main_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_items(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    # 查詢成功但 GA4 本身回報 "(not set)"（網站沒送 item_category）：
    # 這是合法結果，category_breakdown_error 應為 None，跟查詢失敗區分開來。
    assert snapshot.payload["category_breakdown_error"] is None
    assert snapshot.payload["items"][0]["item_category"] == "(not set)"


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
        "modules.ga4.insights.items._trailing_period",
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
        "modules.ga4.insights.items._trailing_period",
        side_effect=lambda days, now_local=None: ("2026-07-03", "2026-07-09") if days == 7 else ("2026-06-26", "2026-07-09"),
    )

    snapshot = GA4InsightsService.get_items(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    row = snapshot.payload["items"][0]
    assert row["views_recent_7d"] == 40
    assert row["views_prior_7d"] == 10
    assert row["views_growth_rate"] == pytest.approx((40 - 10) / 10)


# ─── docs/45：商品渠道篩選（比照到達頁 42+44，僅套用在主查詢） ────────
@pytest.mark.unit
def test_get_items_with_channel_filter_applies_dimension_filter_to_main_query_only(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    captured_calls = []
    main_rows = [{
        "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 5,
        "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.05,
    }]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, dimension_filter=None, **_):
        captured_calls.append({"metrics": metrics, "dimensions": dimensions, "dimension_filter": dimension_filter})
        if dimensions == ["itemName", "itemCategory"]:
            return {"rows": []}, None
        if metrics == ["itemsViewed"] and dimensions == ["itemName"]:
            return {"rows": []}, None
        return {"rows": main_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_items(
        db, user=sample_user, property_id="123456", days=7,
        channel_dimension="source_medium", channel_value="google / organic",
    )
    db.commit()

    main_calls = [c for c in captured_calls if c["dimensions"] == ["itemName"] and c["metrics"] != ["itemsViewed"]]
    growth_calls = [c for c in captured_calls if c["metrics"] == ["itemsViewed"] and c["dimensions"] == ["itemName"]]
    breakdown_calls = [c for c in captured_calls if c["dimensions"] == ["itemName", "itemCategory"]]

    # 主查詢有套渠道篩選；瀏覽成長比較（近7天/前7天）與分類拆解維持全渠道
    # 不受篩選影響（跟使用者確認過的範圍，避免全渠道成長被誤讀成該渠道表現）。
    assert main_calls and all(c["dimension_filter"] == ("sessionSourceMedium", "google / organic") for c in main_calls)
    assert growth_calls and all(c["dimension_filter"] is None for c in growth_calls)
    assert breakdown_calls and all(c["dimension_filter"] is None for c in breakdown_calls)
    assert snapshot.payload["channel_dimension"] == "source_medium"
    assert snapshot.payload["channel_value"] == "google / organic"
    assert snapshot.kind.startswith("item:ch_")


@pytest.mark.unit
def test_get_items_channel_filter_requires_both_params():
    from modules.ga4.insights_service import GA4InsightsService

    with pytest.raises(ValueError):
        GA4InsightsService.get_items(
            db=None, user=MagicMock(), property_id="123456", days=7,
            channel_dimension="source_medium", channel_value=None,
        )
    with pytest.raises(ValueError):
        GA4InsightsService.get_items(
            db=None, user=MagicMock(), property_id="123456", days=7,
            channel_dimension=None, channel_value="google / organic",
        )


@pytest.mark.unit
def test_get_items_rejects_unsupported_channel_dimension():
    from modules.ga4.insights_service import GA4InsightsService

    with pytest.raises(ValueError):
        GA4InsightsService.get_items(
            db=None, user=MagicMock(), property_id="123456", days=7,
            channel_dimension="not_a_real_dimension", channel_value="x",
        )


@pytest.mark.unit
def test_get_items_with_channel_group_applies_or_filter(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    GA4InsightsService.upsert_channel_group_rule(
        db, rule_id=None, user_id=sample_user.id, property_id="123456",
        channel_dimension="source_medium", group_label="Facebook Ads",
        match_type="contains", pattern="facebook / cpc", priority=0,
    )
    GA4InsightsService.upsert_channel_group_rule(
        db, rule_id=None, user_id=sample_user.id, property_id="123456",
        channel_dimension="source_medium", group_label="Facebook Ads",
        match_type="prefix", pattern="facebook / post", priority=1,
    )
    db.commit()

    captured_main_filters = []
    main_rows = [{
        "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 5,
        "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.05,
    }]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, dimension_filter=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            return {"rows": []}, None
        if metrics == ["itemsViewed"] and dimensions == ["itemName"]:
            return {"rows": []}, None
        captured_main_filters.append(dimension_filter)
        return {"rows": main_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_items(
        db, user=sample_user, property_id="123456", days=7,
        channel_dimension="source_medium", channel_group="Facebook Ads",
    )
    db.commit()

    expected_filter = [
        ("sessionSourceMedium", "contains", "facebook / cpc"),
        ("sessionSourceMedium", "prefix", "facebook / post"),
    ]
    assert captured_main_filters and all(f == expected_filter for f in captured_main_filters)
    assert snapshot.payload["channel_group"] == "Facebook Ads"
    assert snapshot.payload["channel_value"] is None
    assert snapshot.kind.startswith("item:chg_")


@pytest.mark.unit
def test_get_items_channel_group_and_value_are_mutually_exclusive():
    from modules.ga4.insights_service import GA4InsightsService

    with pytest.raises(ValueError):
        GA4InsightsService.get_items(
            db=None, user=MagicMock(), property_id="123456", days=7,
            channel_dimension="source_medium", channel_value="google / organic", channel_group="Facebook Ads",
        )


@pytest.mark.unit
def test_get_items_rejects_unknown_channel_group(db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    with pytest.raises(ValueError):
        GA4InsightsService.get_items(
            db=db, user=sample_user, property_id="123456", days=7,
            channel_dimension="source_medium", channel_group="Does Not Exist",
        )


@pytest.mark.unit
def test_get_items_channel_group_and_value_snapshots_are_independent(mocker, db, sample_user):
    """精確值篩選（ch_ 前綴）跟自訂分組篩選（chg_ 前綴）各自存成獨立快照。"""
    from modules.ga4.insights_service import GA4InsightsService

    GA4InsightsService.upsert_channel_group_rule(
        db, rule_id=None, user_id=sample_user.id, property_id="123456",
        channel_dimension="source_medium", group_label="Facebook Ads",
        match_type="contains", pattern="facebook", priority=0,
    )
    db.commit()

    main_rows = [{
        "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 5,
        "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.05,
    }]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            return {"rows": []}, None
        if metrics == ["itemsViewed"] and dimensions == ["itemName"]:
            return {"rows": []}, None
        return {"rows": main_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    value_snapshot = GA4InsightsService.get_items(
        db, user=sample_user, property_id="123456", days=7,
        channel_dimension="source_medium", channel_value="facebook / cpc",
    )
    db.commit()
    group_snapshot = GA4InsightsService.get_items(
        db, user=sample_user, property_id="123456", days=7,
        channel_dimension="source_medium", channel_group="Facebook Ads",
    )
    db.commit()

    assert value_snapshot.id != group_snapshot.id
    assert value_snapshot.kind.startswith("item:ch_")
    assert group_snapshot.kind.startswith("item:chg_")


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


@pytest.mark.integration
def test_items_endpoint_accepts_channel_value_and_channel_group(client, db, sample_user, mocker):
    _override_dependencies(client.app, sample_user, db)
    from modules.ga4.insights_service import GA4InsightsService

    GA4InsightsService.upsert_channel_group_rule(
        db, rule_id=None, user_id=sample_user.id, property_id="123456",
        channel_dimension="source_medium", group_label="Facebook Ads",
        match_type="contains", pattern="facebook", priority=0,
    )
    db.commit()

    main_rows = [{
        "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 5,
        "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.05,
    }]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            return {"rows": []}, None
        if metrics == ["itemsViewed"] and dimensions == ["itemName"]:
            return {"rows": []}, None
        return {"rows": main_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    resp = client.get("/api/ga4/insights/items", params={
        "property_id": "123456", "days": 7,
        "channel_dimension": "source_medium", "channel_value": "facebook / cpc",
    })
    assert resp.status_code == 200
    assert resp.json()["payload"]["channel_value"] == "facebook / cpc"

    resp = client.get("/api/ga4/insights/items", params={
        "property_id": "123456", "days": 7,
        "channel_dimension": "source_medium", "channel_group": "Facebook Ads",
    })
    assert resp.status_code == 200
    assert resp.json()["payload"]["channel_group"] == "Facebook Ads"


@pytest.mark.integration
def test_items_endpoint_rejects_value_and_group_together_with_400(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)

    resp = client.get("/api/ga4/insights/items", params={
        "property_id": "123456", "days": 7, "channel_dimension": "source_medium",
        "channel_value": "google / organic", "channel_group": "Facebook Ads",
    })
    assert resp.status_code == 400


@pytest.mark.integration
def test_items_endpoint_rejects_unknown_channel_dimension_with_422(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)

    resp = client.get("/api/ga4/insights/items", params={
        "property_id": "123456", "days": 7,
        "channel_dimension": "not_a_real_dimension", "channel_value": "x",
    })
    assert resp.status_code == 422
