"""
GA4 到達頁分類篩選驗證（docs/22 第 5 波，追加）

涵蓋：
- `classify_landing_page` 純函數：自訂規則 priority 首匹配、大小寫不敏感、
  prefix/contains 兩種比對、有規則但無匹配歸 other（不退回內建預設）、
  完全無規則時退回內建關鍵詞啟發式
- `get_landing_pages`：分類改為同分類內四分位（不同分類量級不互相污染）、
  `category_counts`/`conversion_rate_definition` 回應欄位
- repository CRUD（依 priority 排序）
- `upsert_landing_page_rule` 的 create-or-update-by-id 語意
- 端點路由與 `Literal` 驗證 422
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


# ─── classify_landing_page ──────────────────────────────────────────
@pytest.mark.unit
def test_classify_landing_page_custom_rules_first_match_by_priority():
    from modules.ga4.insights_service import classify_landing_page

    rules = [
        {"category": "functional", "match_type": "prefix", "pattern": "/shop/cart", "priority": 1},
        {"category": "product", "match_type": "prefix", "pattern": "/shop", "priority": 2},
    ]
    # /shop/cart/123 同時符合兩條規則，priority 較小（1）的優先
    assert classify_landing_page("/shop/cart/123", rules) == "functional"
    # /shop/tshirt 只符合第二條
    assert classify_landing_page("/shop/tshirt", rules) == "product"


@pytest.mark.unit
def test_classify_landing_page_case_insensitive():
    from modules.ga4.insights_service import classify_landing_page

    rules = [{"category": "product", "match_type": "prefix", "pattern": "/Shop", "priority": 1}]
    assert classify_landing_page("/SHOP/tshirt", rules) == "product"


@pytest.mark.unit
def test_classify_landing_page_contains_match_type():
    from modules.ga4.insights_service import classify_landing_page

    rules = [{"category": "article", "match_type": "contains", "pattern": "blog", "priority": 1}]
    assert classify_landing_page("/zh-tw/blog/2026/07", rules) == "article"
    assert classify_landing_page("/zh-tw/shop", rules) == "other"


@pytest.mark.unit
def test_classify_landing_page_no_match_falls_to_other_not_default_keywords():
    from modules.ga4.insights_service import classify_landing_page

    # 有自訂規則但完全不匹配 → other，不應退回內建關鍵詞（即使 /blog 本來會被關鍵詞猜成 article）
    rules = [{"category": "product", "match_type": "prefix", "pattern": "/shop", "priority": 1}]
    assert classify_landing_page("/blog/post-1", rules) == "other"


@pytest.mark.unit
@pytest.mark.parametrize(
    "path,expected_category",
    [
        ("/products/123", "product"),
        ("/blog/hello-world", "article"),
        ("/cart", "functional"),
        ("/checkout/step-2", "functional"),
        ("/some-random-page", "other"),
    ],
)
def test_classify_landing_page_default_keyword_heuristic_when_no_rules(path, expected_category):
    from modules.ga4.insights_service import classify_landing_page

    assert classify_landing_page(path, []) == expected_category


# ─── get_landing_pages：同分類內四分位（依 session_key_event_rate） ────
# 主查詢與關鍵事件分項查詢用不同 dimensions 區分（["landingPage"] vs
# ["landingPage","eventName"]），mock 需分別回應正確的指標鍵名
# （keyEvents / sessionKeyEventRate，而非舊的 conversions）。
def _fake_landing_pages_get_analytics(main_rows, breakdown_rows):
    def _fake(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["landingPage", "eventName"]:
            return {"rows": breakdown_rows}, None
        return {"rows": main_rows}, None
    return _fake


@pytest.mark.unit
def test_get_landing_pages_tags_within_category_only(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    # 4 個商品頁（其中 1 個高流量低轉換率）+ 2 個文章頁（樣本不足 <4，維持不標記）
    main_rows = [
        {"landingPage": "/products/a", "sessions": 1000, "engagementRate": 0.3, "keyEvents": 5, "bounceRate": 0.8, "sessionKeyEventRate": 0.01},
        {"landingPage": "/products/b", "sessions": 50, "engagementRate": 0.6, "keyEvents": 10, "bounceRate": 0.2, "sessionKeyEventRate": 0.5},
        {"landingPage": "/products/c", "sessions": 40, "engagementRate": 0.5, "keyEvents": 8, "bounceRate": 0.3, "sessionKeyEventRate": 0.4},
        {"landingPage": "/products/d", "sessions": 30, "engagementRate": 0.5, "keyEvents": 6, "bounceRate": 0.3, "sessionKeyEventRate": 0.3},
        {"landingPage": "/blog/1", "sessions": 2000, "engagementRate": 0.2, "keyEvents": 1, "bounceRate": 0.9, "sessionKeyEventRate": 0.005},
        {"landingPage": "/blog/2", "sessions": 1800, "engagementRate": 0.2, "keyEvents": 1, "bounceRate": 0.9, "sessionKeyEventRate": 0.005},
    ]
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        side_effect=_fake_landing_pages_get_analytics(main_rows, []),
    )

    snapshot = GA4InsightsService.get_landing_pages(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    by_page = {row["landingPage"]: row for row in snapshot.payload["landing_pages"]}
    assert by_page["/products/a"]["category"] == "product"
    assert by_page["/products/a"]["conversions"] == 5
    assert by_page["/products/a"]["is_high_traffic_low_conversion"] is True
    # /blog 頁面雖然流量極高、關鍵事件發生率極低（跟商品頁比也是全站最糟），
    # 但文章分類只有 2 個樣本（<4），依規則不應被標記
    assert by_page["/blog/1"]["category"] == "article"
    assert by_page["/blog/1"]["is_high_traffic_low_conversion"] is False
    assert by_page["/blog/2"]["is_high_traffic_low_conversion"] is False

    assert snapshot.payload["category_counts"] == {"product": 4, "article": 2}
    assert "session_key_event_rate_definition" in snapshot.payload
    assert "key_events_count_definition" in snapshot.payload
    assert snapshot.kind == "landing_page"
    assert snapshot.payload["key_event"] is None


@pytest.mark.unit
def test_get_landing_pages_uses_custom_rules_when_present(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService
    from modules.ga4.repository import repository

    repository.create_landing_page_rule(
        db, property_id="123456", category="functional", match_type="prefix",
        pattern="/checkout", priority=1, created_by=sample_user.id,
    )
    db.commit()

    main_rows = [{"landingPage": "/checkout/step-1", "sessions": 10, "engagementRate": 0.5, "keyEvents": 1, "bounceRate": 0.2, "sessionKeyEventRate": 0.1}]
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        side_effect=_fake_landing_pages_get_analytics(main_rows, []),
    )

    snapshot = GA4InsightsService.get_landing_pages(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    assert snapshot.payload["landing_pages"][0]["category"] == "functional"


# ─── 第 5 波追加：關鍵事件分項統計 + 事件口徑篩選 ───────────────────
@pytest.mark.unit
def test_get_landing_pages_builds_key_events_breakdown_and_available_events(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    main_rows = [
        {"landingPage": "/products/a", "sessions": 100, "engagementRate": 0.5, "keyEvents": 5, "bounceRate": 0.3, "sessionKeyEventRate": 0.04},
    ]
    breakdown_rows = [
        {"landingPage": "/products/a", "eventName": "purchase", "keyEvents": 3},
        {"landingPage": "/products/a", "eventName": "sign_up", "keyEvents": 2},
    ]
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        side_effect=_fake_landing_pages_get_analytics(main_rows, breakdown_rows),
    )

    snapshot = GA4InsightsService.get_landing_pages(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    row = snapshot.payload["landing_pages"][0]
    assert row["key_events_breakdown"] == {"purchase": 3, "sign_up": 2}
    assert snapshot.payload["available_key_events"] == ["purchase", "sign_up"]


@pytest.mark.unit
def test_get_landing_pages_with_key_event_switches_metrics_and_kind(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    captured_metrics = []

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["landingPage", "eventName"]:
            return {"rows": []}, None
        captured_metrics.append(metrics)
        return {
            "rows": [{
                "landingPage": "/products/a", "sessions": 100, "engagementRate": 0.5,
                "keyEvents:purchase": 3, "bounceRate": 0.3, "sessionKeyEventRate:purchase": 0.03,
            }]
        }, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_landing_pages(
        db, user=sample_user, property_id="123456", days=7, key_event="purchase"
    )
    db.commit()

    assert "keyEvents:purchase" in captured_metrics[0]
    assert "sessionKeyEventRate:purchase" in captured_metrics[0]
    assert snapshot.payload["landing_pages"][0]["conversions"] == 3
    assert snapshot.payload["landing_pages"][0]["session_key_event_rate"] == 0.03
    # 指定事件的 snapshot 獨立存放，不覆寫全事件口徑的 "landing_page"
    assert snapshot.kind == "landing_page:purchase"
    assert snapshot.payload["key_event"] == "purchase"


@pytest.mark.unit
def test_get_landing_pages_key_event_snapshot_does_not_overwrite_all_events_snapshot(mocker, db, sample_user):
    """全事件口徑（無 key_event）與指定事件口徑的 snapshot 各佔一個
    (property_id, kind, date) 唯一鍵，互不覆寫（同第 4 波渠道維度前例）。"""
    from modules.ga4.insights_service import GA4InsightsService

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["landingPage", "eventName"]:
            return {"rows": []}, None
        return {
            "rows": [{
                "landingPage": "/products/a", "sessions": 100, "engagementRate": 0.5,
                "keyEvents": 5, "bounceRate": 0.3, "sessionKeyEventRate": 0.05,
                "keyEvents:purchase": 3, "sessionKeyEventRate:purchase": 0.03,
            }]
        }, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    all_events_snapshot = GA4InsightsService.get_landing_pages(db, user=sample_user, property_id="123456", days=7)
    db.commit()
    purchase_snapshot = GA4InsightsService.get_landing_pages(
        db, user=sample_user, property_id="123456", days=7, key_event="purchase"
    )
    db.commit()

    assert all_events_snapshot.id != purchase_snapshot.id
    assert all_events_snapshot.kind == "landing_page"
    assert purchase_snapshot.kind == "landing_page:purchase"
    # 重新讀取全事件口徑的 snapshot，確認沒有被指定事件口徑的查詢覆寫掉
    from modules.ga4.repository import repository
    reloaded = repository.get_latest_snapshot(db, property_id="123456", kind="landing_page")
    assert reloaded.id == all_events_snapshot.id


@pytest.mark.unit
def test_get_landing_pages_rejects_invalid_key_event_format():
    from modules.ga4.insights_service import GA4InsightsService

    with pytest.raises(ValueError):
        GA4InsightsService.get_landing_pages(
            db=None, user=MagicMock(), property_id="123456", days=7, key_event="not valid!"
        )


# ─── repository + service：upsert 語意 ──────────────────────────────
@pytest.mark.unit
def test_repository_list_landing_page_rules_ordered_by_priority(db, sample_user):
    from modules.ga4.repository import repository

    repository.create_landing_page_rule(
        db, property_id="123456", category="product", match_type="prefix",
        pattern="/shop", priority=5, created_by=sample_user.id,
    )
    repository.create_landing_page_rule(
        db, property_id="123456", category="article", match_type="prefix",
        pattern="/blog", priority=1, created_by=sample_user.id,
    )
    db.commit()

    rules = repository.list_landing_page_rules(db, property_id="123456")
    assert [r.pattern for r in rules] == ["/blog", "/shop"]


@pytest.mark.unit
def test_service_upsert_landing_page_rule_create_then_update(db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    created = GA4InsightsService.upsert_landing_page_rule(
        db, rule_id=None, user_id=sample_user.id, property_id="123456",
        category="product", match_type="prefix", pattern="/shop", priority=1,
    )
    db.commit()

    updated = GA4InsightsService.upsert_landing_page_rule(
        db, rule_id=created.id, user_id=sample_user.id, property_id="123456",
        category="functional", match_type="contains", pattern="/shop-cart", priority=2,
    )
    db.commit()

    assert updated.id == created.id
    assert updated.category == "functional"
    assert updated.match_type == "contains"
    assert updated.priority == 2

    missing = GA4InsightsService.upsert_landing_page_rule(
        db, rule_id="does-not-exist", user_id=sample_user.id, property_id="123456",
        category="product", match_type="prefix", pattern="/x", priority=0,
    )
    assert missing is None

    assert GA4InsightsService.delete_landing_page_rule(db, rule_id=created.id) is True
    db.commit()
    assert GA4InsightsService.list_landing_page_rules(db, property_id="123456") == []


# ─── router ───────────────────────────────────────────────────────────
@pytest.mark.integration
def test_landing_page_rules_crud_endpoints(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)

    created = client.put(
        "/api/ga4/insights/landing-page-rules",
        json={"property_id": "123456", "category": "product", "match_type": "prefix", "pattern": "/shop", "priority": 1},
    )
    assert created.status_code == 200
    rule_id = created.json()["id"]

    listed = client.get("/api/ga4/insights/landing-page-rules", params={"property_id": "123456"})
    assert listed.status_code == 200
    assert listed.json()["rules"][0]["id"] == rule_id

    updated = client.put(
        "/api/ga4/insights/landing-page-rules",
        json={"id": rule_id, "property_id": "123456", "category": "article", "match_type": "contains", "pattern": "/blog", "priority": 2},
    )
    assert updated.status_code == 200
    assert updated.json()["category"] == "article"

    deleted = client.delete(f"/api/ga4/insights/landing-page-rules/{rule_id}")
    assert deleted.status_code == 200

    missing = client.delete(f"/api/ga4/insights/landing-page-rules/{rule_id}")
    assert missing.status_code == 404


@pytest.mark.integration
def test_landing_page_rule_payload_rejects_invalid_category_and_match_type(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)

    bad_category = client.put(
        "/api/ga4/insights/landing-page-rules",
        json={"property_id": "123456", "category": "not_a_category", "match_type": "prefix", "pattern": "/x", "priority": 0},
    )
    assert bad_category.status_code == 422

    bad_match_type = client.put(
        "/api/ga4/insights/landing-page-rules",
        json={"property_id": "123456", "category": "product", "match_type": "regex", "pattern": "/x", "priority": 0},
    )
    assert bad_match_type.status_code == 422


@pytest.mark.integration
def test_landing_pages_endpoint_response_includes_category_fields(client, db, sample_user, mocker):
    _override_dependencies(client.app, sample_user, db)
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        return_value=({"rows": [{"landingPage": "/products/x", "sessions": 5, "engagementRate": 0.5, "keyEvents": 1, "bounceRate": 0.2, "sessionKeyEventRate": 0.2}]}, None),
    )

    resp = client.get("/api/ga4/insights/landing-pages", params={"property_id": "123456", "days": 7})
    assert resp.status_code == 200
    payload = resp.json()["payload"]
    assert payload["landing_pages"][0]["category"] == "product"
    assert payload["category_counts"] == {"product": 1}
    assert "session_key_event_rate_definition" in payload
    assert "key_events_count_definition" in payload
    assert "available_key_events" in payload


@pytest.mark.integration
def test_landing_pages_endpoint_rejects_invalid_key_event_with_422(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)

    resp = client.get(
        "/api/ga4/insights/landing-pages",
        params={"property_id": "123456", "days": 7, "key_event": "not valid!"},
    )
    assert resp.status_code == 422
