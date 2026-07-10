"""
GA4 商品分類補充規則驗證（docs/22 第 7 波，追加）

背景：商品分類（`item_category`）預設抓 GA4 原生 `itemCategory` 維度；若網站
電商追蹤沒有回傳，GA4 端本身就是 "(not set)"。本波加一張自訂規則表，只在
GA4 沒有值時補分類，兩套資料來源用明確優先順序區隔，避免互相覆蓋。

涵蓋：
- `classify_item_category` 純函數：GA4 有值時永遠優先（即使同時有自訂規則
  比對成功）；GA4 無值時才退回自訂規則（priority 首匹配、大小寫不敏感）；
  兩者皆無則 `(not set)`；回傳的 `source` 標記正確（ga4/custom_rule/unset）
- repository CRUD（依 priority 排序）
- service 的 create-or-update-by-id upsert 語意
- `get_items` 整合：GA4 有值的商品不受自訂規則影響；GA4 "(not set)" 的商品
  套用自訂規則；`item_category_source` 進每列 payload
- 端點路由與 `Literal`（match_type）驗證 422；`category` 為自由文字不受枚舉限制
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


# ─── classify_item_category：優先順序 ───────────────────────────────
@pytest.mark.unit
def test_classify_item_category_ga4_value_wins_even_with_matching_custom_rule():
    from modules.ga4.insights_service import classify_item_category

    rules = [{"category": "居家清潔", "match_type": "contains", "pattern": "凝膠", "priority": 1}]
    # GA4 已經回報分類，即使商品名稱也符合自訂規則，GA4 的值仍優先
    category, source = classify_item_category("除霉凝膠 120g", "殺蟲劑", rules)
    assert category == "殺蟲劑"
    assert source == "ga4"


@pytest.mark.unit
def test_classify_item_category_falls_back_to_custom_rule_when_ga4_unset():
    from modules.ga4.insights_service import classify_item_category

    rules = [
        {"category": "居家清潔", "match_type": "contains", "pattern": "凝膠", "priority": 2},
        {"category": "驅蟲用品", "match_type": "contains", "pattern": "蟑螂", "priority": 1},
    ]
    category, source = classify_item_category("強效小蟑螂專用凝膠 15g", "(not set)", rules)
    # 兩條規則都比對得到，priority 較小（1）的優先
    assert category == "驅蟲用品"
    assert source == "custom_rule"


@pytest.mark.unit
def test_classify_item_category_falls_back_to_custom_rule_when_ga4_missing():
    from modules.ga4.insights_service import classify_item_category

    rules = [{"category": "居家清潔", "match_type": "prefix", "pattern": "和淨", "priority": 1}]
    category, source = classify_item_category("和淨除霉凝膠", None, rules)
    assert category == "居家清潔"
    assert source == "custom_rule"


@pytest.mark.unit
def test_classify_item_category_unset_when_no_ga4_and_no_matching_rule():
    from modules.ga4.insights_service import classify_item_category

    rules = [{"category": "居家清潔", "match_type": "prefix", "pattern": "和淨", "priority": 1}]
    category, source = classify_item_category("完全不相關的商品", "(not set)", rules)
    assert category == "(not set)"
    assert source == "unset"


@pytest.mark.unit
def test_classify_item_category_unset_when_no_rules_at_all():
    from modules.ga4.insights_service import classify_item_category

    category, source = classify_item_category("任何商品", None, [])
    assert category == "(not set)"
    assert source == "unset"


# ─── get_items 整合：GA4 優先、規則補缺 ─────────────────────────────
@pytest.mark.unit
def test_get_items_ga4_category_not_overridden_by_custom_rule(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService
    from modules.ga4.repository import repository

    repository.create_item_category_rule(
        db, property_id="123456", category="錯誤分類", match_type="contains",
        pattern="P1", priority=1, created_by=sample_user.id,
    )
    db.commit()

    main_rows = [{
        "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20, "itemsPurchased": 5,
        "itemRevenue": 500.0, "cartToViewRate": 0.2, "purchaseToViewRate": 0.05,
    }]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            return {"rows": [{"itemName": "P1", "itemCategory": "電子產品", "itemsViewed": 100}]}, None
        if metrics == ["itemsViewed"] and dimensions == ["itemName"]:
            return {"rows": []}, None
        return {"rows": main_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_items(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    row = snapshot.payload["items"][0]
    assert row["item_category"] == "電子產品"
    assert row["item_category_source"] == "ga4"


@pytest.mark.unit
def test_get_items_custom_rule_fills_gap_when_ga4_unset(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService
    from modules.ga4.repository import repository

    repository.create_item_category_rule(
        db, property_id="123456", category="驅蟲用品", match_type="contains",
        pattern="蟑螂", priority=1, created_by=sample_user.id,
    )
    db.commit()

    main_rows = [{
        "itemName": "強效小蟑螂專用凝膠", "itemsViewed": 20, "itemsAddedToCart": 5, "itemsPurchased": 1,
        "itemRevenue": 300.0, "cartToViewRate": 0.25, "purchaseToViewRate": 0.05,
    }]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            # GA4 對這個商品沒有分類資料
            return {"rows": [{"itemName": "強效小蟑螂專用凝膠", "itemCategory": "(not set)", "itemsViewed": 20}]}, None
        if metrics == ["itemsViewed"] and dimensions == ["itemName"]:
            return {"rows": []}, None
        return {"rows": main_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_items(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    row = snapshot.payload["items"][0]
    assert row["item_category"] == "驅蟲用品"
    assert row["item_category_source"] == "custom_rule"
    assert snapshot.payload["category_counts"] == {"驅蟲用品": 1}


# ─── repository + service：upsert 語意 ──────────────────────────────
@pytest.mark.unit
def test_repository_list_item_category_rules_ordered_by_priority(db, sample_user):
    from modules.ga4.repository import repository

    repository.create_item_category_rule(
        db, property_id="123456", category="A", match_type="prefix",
        pattern="a", priority=5, created_by=sample_user.id,
    )
    repository.create_item_category_rule(
        db, property_id="123456", category="B", match_type="prefix",
        pattern="b", priority=1, created_by=sample_user.id,
    )
    db.commit()

    rules = repository.list_item_category_rules(db, property_id="123456")
    assert [r.category for r in rules] == ["B", "A"]


@pytest.mark.unit
def test_service_upsert_item_category_rule_create_then_update(db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    created = GA4InsightsService.upsert_item_category_rule(
        db, rule_id=None, user_id=sample_user.id, property_id="123456",
        category="居家清潔", match_type="prefix", pattern="和淨", priority=1,
    )
    db.commit()

    updated = GA4InsightsService.upsert_item_category_rule(
        db, rule_id=created.id, user_id=sample_user.id, property_id="123456",
        category="驅蟲用品", match_type="contains", pattern="蟑螂", priority=2,
    )
    db.commit()

    assert updated.id == created.id
    assert updated.category == "驅蟲用品"
    assert updated.match_type == "contains"

    missing = GA4InsightsService.upsert_item_category_rule(
        db, rule_id="does-not-exist", user_id=sample_user.id, property_id="123456",
        category="X", match_type="prefix", pattern="x", priority=0,
    )
    assert missing is None

    assert GA4InsightsService.delete_item_category_rule(db, rule_id=created.id) is True
    db.commit()
    assert GA4InsightsService.list_item_category_rules(db, property_id="123456") == []


# ─── router ───────────────────────────────────────────────────────────
@pytest.mark.integration
def test_item_category_rules_crud_endpoints(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)

    created = client.put(
        "/api/ga4/insights/item-category-rules",
        json={"property_id": "123456", "category": "居家清潔", "match_type": "prefix", "pattern": "和淨", "priority": 1},
    )
    assert created.status_code == 200
    rule_id = created.json()["id"]

    listed = client.get("/api/ga4/insights/item-category-rules", params={"property_id": "123456"})
    assert listed.status_code == 200
    assert listed.json()["rules"][0]["id"] == rule_id

    updated = client.put(
        "/api/ga4/insights/item-category-rules",
        json={"id": rule_id, "property_id": "123456", "category": "驅蟲用品", "match_type": "contains", "pattern": "蟑螂", "priority": 2},
    )
    assert updated.status_code == 200
    assert updated.json()["category"] == "驅蟲用品"

    deleted = client.delete(f"/api/ga4/insights/item-category-rules/{rule_id}")
    assert deleted.status_code == 200

    missing = client.delete(f"/api/ga4/insights/item-category-rules/{rule_id}")
    assert missing.status_code == 404


@pytest.mark.integration
def test_item_category_rule_payload_rejects_invalid_match_type(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)

    resp = client.put(
        "/api/ga4/insights/item-category-rules",
        json={"property_id": "123456", "category": "任意分類名稱", "match_type": "regex", "pattern": "/x", "priority": 0},
    )
    assert resp.status_code == 422


@pytest.mark.integration
def test_item_category_rule_payload_accepts_free_text_category(client, db, sample_user):
    """商品分類是自由文字，不像到達頁受 4 類枚舉限制。"""
    _override_dependencies(client.app, sample_user, db)

    resp = client.put(
        "/api/ga4/insights/item-category-rules",
        json={"property_id": "123456", "category": "任意商店自訂分類名稱", "match_type": "prefix", "pattern": "x", "priority": 0},
    )
    assert resp.status_code == 200
    assert resp.json()["category"] == "任意商店自訂分類名稱"
