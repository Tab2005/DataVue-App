"""
GA4 洞察模組屬性層級授權測試（docs/60；補 docs/59 P0-2 / P0-3 的 IDOR）

背景：`require_ga4_insights_view` / `require_ga4_insights_manage_alerts` 只確認
「這個人能不能用洞察功能」，不確認「這筆資料是不是他的」。查詢類端點有隱性
門檻——一律用呼叫者自己的 GA4 OAuth 憑證打 Data API；但快照類（ai-summary /
share）與規則/KPI 類端點是純本地資料表讀寫，原本任何有洞察權限的登入者只要
拿到別人的 snapshot_id / rule_id 就能改寫、甚至替別人的資料開公開分享連結。

本檔驗證新增的授權層：

  1. `has_ga4_property_access` 兩段式判斷：本地快照快路徑、Admin API 慢路徑、
     以及 Admin API 失敗時保守拒絕。
  2. 資源 id 為路徑參數的端點（snapshot / 各類規則 / KPI 目標）未授權一律回
     404，訊息與「不存在」相同，且確認資料未被改動。
  3. property_id 為顯式參數的端點（各類規則清單、KPI 清單）未授權回 403。
  4. 規則 upsert 不得把既有規則搬到另一個 property（原本會直接覆寫
     `row.property_id`）。

`ga4_property_access` fixture（conftest）把 Admin API 慢路徑換成固定清單，
只授予 "123456"；因此 "999999" 一律代表「別人的屬性」。
"""

from unittest.mock import patch

import pytest

from database.models.ga4_insights import (
    GA4ChannelGroupRule,
    GA4InsightsSnapshot,
    GA4ItemCategoryRule,
    GA4KpiTarget,
    GA4LandingPageRule,
)
from modules.ga4.dependencies import (
    has_ga4_property_access,
    require_ga4_insights_manage_alerts,
    require_ga4_insights_view,
    require_ga4_module,
)
from modules.ga4.insights_router import get_current_user

MINE = "123456"
THEIRS = "999999"


def _override_dependencies(app, user, db):
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_ga4_module] = lambda: True
    app.dependency_overrides[require_ga4_insights_view] = lambda: True
    app.dependency_overrides[require_ga4_insights_manage_alerts] = lambda: True


def _make_snapshot(db, *, property_id=THEIRS, fetched_by=None, **overrides):
    row = GA4InsightsSnapshot(
        property_id=property_id,
        kind="landing_page",
        date="2026-07-20",
        payload={"landing_pages": []},
        fetched_by=fetched_by,
        **overrides,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _add(db, row):
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ─── 1. has_ga4_property_access 本身 ────────────────────────────────
@pytest.mark.unit
def test_property_access_fast_path_uses_own_snapshot_without_admin_api(db, sample_user):
    """使用者自己抓過的 property：直接放行，且完全不呼叫 Admin API。

    快照列只會在 Data API 查詢成功後才寫入，而 GA4 憑證是 per-user OAuth，
    所以「有一筆 fetched_by == 我的快照」本身就是存取權的證據。
    """
    _make_snapshot(db, property_id=MINE, fetched_by=sample_user.id)

    with patch("modules.ga4.dependencies.GA4Client.list_properties") as list_properties:
        assert has_ga4_property_access(db, user=sample_user, property_id=MINE) is True
    list_properties.assert_not_called()


@pytest.mark.unit
def test_property_access_ignores_snapshots_fetched_by_other_users(db, sample_user, sample_admin_user):
    """別人抓的快照不算數——快路徑比對的是 fetched_by，不是「這個 property 有沒有快照」。"""
    _make_snapshot(db, property_id=THEIRS, fetched_by=sample_admin_user.id)

    with patch(
        "modules.ga4.dependencies.GA4Client.list_properties",
        return_value=([{"property_id": MINE}], None),
    ):
        assert has_ga4_property_access(db, user=sample_user, property_id=THEIRS) is False


@pytest.mark.unit
def test_property_access_slow_path_consults_admin_api(db, sample_user):
    """還沒抓過任何資料（冷啟動）時回退問 Admin API 的屬性清單。"""
    with patch(
        "modules.ga4.dependencies.GA4Client.list_properties",
        return_value=([{"property_id": MINE}], None),
    ):
        assert has_ga4_property_access(db, user=sample_user, property_id=MINE) is True
        assert has_ga4_property_access(db, user=sample_user, property_id=THEIRS) is False


@pytest.mark.unit
def test_property_access_slow_path_caches_the_property_list(db, sample_user):
    """Admin API 是 list_accounts + 每個 account 一次 list_properties，冷啟動時
    多支清單請求幾乎同時發出，結果必須快取，不能每次都重打。"""
    with patch(
        "modules.ga4.dependencies.GA4Client.list_properties",
        return_value=([{"property_id": MINE}], None),
    ) as list_properties:
        for _ in range(3):
            assert has_ga4_property_access(db, user=sample_user, property_id=MINE) is True

    assert list_properties.call_count == 1


@pytest.mark.unit
def test_property_access_does_not_cache_admin_api_failures(db, sample_user):
    """查詢失敗不進快取——否則一次暫時性錯誤會把使用者鎖在門外整個 TTL。"""
    with patch(
        "modules.ga4.dependencies.GA4Client.list_properties",
        return_value=([], "temporary failure"),
    ) as failing:
        assert has_ga4_property_access(db, user=sample_user, property_id=MINE) is False
        assert has_ga4_property_access(db, user=sample_user, property_id=MINE) is False
    assert failing.call_count == 2

    with patch(
        "modules.ga4.dependencies.GA4Client.list_properties",
        return_value=([{"property_id": MINE}], None),
    ):
        assert has_ga4_property_access(db, user=sample_user, property_id=MINE) is True


@pytest.mark.unit
def test_property_access_denies_when_admin_api_errors(db, sample_user):
    """Admin API 失敗一律保守拒絕（同 contribution `resolve_accessible_account_ids` 慣例）。"""
    with patch(
        "modules.ga4.dependencies.GA4Client.list_properties",
        return_value=([], "No GA4 credentials found"),
    ):
        assert has_ga4_property_access(db, user=sample_user, property_id=MINE) is False


# ─── 2. 快照類端點（docs/59 P0-2） ──────────────────────────────────
@pytest.mark.integration
def test_save_ai_summary_on_other_property_snapshot_returns_404(
    client, db, sample_user, ga4_property_access
):
    _override_dependencies(client.app, sample_user, db)
    snapshot = _make_snapshot(db, property_id=THEIRS, ai_summary="別人的解讀")

    resp = client.put(
        f"/api/ga4/insights/snapshots/{snapshot.id}/ai-summary",
        json={"ai_summary": "攻擊者寫入的內容"},
    )

    assert resp.status_code == 404
    # 與「快照不存在」同訊息，無法從回應區分該 id 是否存在
    assert resp.json()["error"] == "Snapshot not found"
    db.refresh(snapshot)
    assert snapshot.ai_summary == "別人的解讀"


@pytest.mark.integration
def test_create_share_link_on_other_property_snapshot_returns_404(
    client, db, sample_user, ga4_property_access
):
    """最嚴重的一條：分享連結端點 `GET /share/{token}` 無需登入，
    替別人的快照開連結等同把別的屬性的 GA4 數據對外發佈。"""
    _override_dependencies(client.app, sample_user, db)
    snapshot = _make_snapshot(db, property_id=THEIRS)

    resp = client.post(f"/api/ga4/insights/snapshots/{snapshot.id}/share")

    assert resp.status_code == 404
    assert resp.json()["error"] == "Snapshot not found"
    db.refresh(snapshot)
    assert snapshot.share_token is None


@pytest.mark.integration
def test_snapshot_endpoints_allow_owner_via_fetched_by(client, db, sample_user):
    """反向確認：自己抓的快照仍然能存 AI 解讀與開分享連結（不掛
    ga4_property_access fixture，證明走的是本地快照快路徑）。"""
    _override_dependencies(client.app, sample_user, db)
    snapshot = _make_snapshot(db, property_id=MINE, fetched_by=sample_user.id)

    saved = client.put(
        f"/api/ga4/insights/snapshots/{snapshot.id}/ai-summary",
        json={"ai_summary": "我的解讀"},
    )
    assert saved.status_code == 200

    shared = client.post(f"/api/ga4/insights/snapshots/{snapshot.id}/share")
    assert shared.status_code == 200
    assert shared.json()["share_token"]


# ─── 3. 規則類端點（docs/59 P0-3） ──────────────────────────────────
@pytest.mark.integration
def test_landing_page_rule_update_and_delete_on_other_property_returns_404(
    client, db, sample_user, ga4_property_access
):
    _override_dependencies(client.app, sample_user, db)
    rule = _add(db, GA4LandingPageRule(
        property_id=THEIRS, category="product", match_type="prefix",
        pattern="/shop", priority=1, created_by=sample_user.id,
    ))

    updated = client.put(
        "/api/ga4/insights/landing-page-rules",
        json={"id": rule.id, "property_id": THEIRS, "category": "article",
              "match_type": "contains", "pattern": "/blog", "priority": 2},
    )
    assert updated.status_code == 403  # property_id 是顯式參數 → 403

    deleted = client.delete(f"/api/ga4/insights/landing-page-rules/{rule.id}")
    assert deleted.status_code == 404
    assert deleted.json()["error"] == "Landing page rule not found"

    db.refresh(rule)
    assert rule.category == "product"


@pytest.mark.integration
def test_landing_page_rule_cannot_be_moved_to_another_property(client, db, sample_user):
    """原本 upsert 直接覆寫 `row.property_id`，等於可以把一條規則搬到另一個
    屬性底下。這裡刻意讓使用者「兩個屬性都有權限」——授權檢查會全數通過，
    專門驗證換綁本身被擋下（無權限的情境已由上一個測試涵蓋，回 404）。"""
    _override_dependencies(client.app, sample_user, db)
    rule = _add(db, GA4LandingPageRule(
        property_id=THEIRS, category="product", match_type="prefix",
        pattern="/shop", priority=1, created_by=sample_user.id,
    ))

    with patch(
        "modules.ga4.dependencies.GA4Client.list_properties",
        return_value=([{"property_id": MINE}, {"property_id": THEIRS}], None),
    ):
        resp = client.put(
            "/api/ga4/insights/landing-page-rules",
            json={"id": rule.id, "property_id": MINE, "category": "product",
                  "match_type": "prefix", "pattern": "/shop", "priority": 1},
        )

    assert resp.status_code == 400
    db.refresh(rule)
    assert rule.property_id == THEIRS


@pytest.mark.integration
def test_item_category_rule_delete_on_other_property_returns_404(
    client, db, sample_user, ga4_property_access
):
    _override_dependencies(client.app, sample_user, db)
    rule = _add(db, GA4ItemCategoryRule(
        property_id=THEIRS, category="鞋類", match_type="contains",
        pattern="鞋", priority=1, created_by=sample_user.id,
    ))

    resp = client.delete(f"/api/ga4/insights/item-category-rules/{rule.id}")

    assert resp.status_code == 404
    assert resp.json()["error"] == "Item category rule not found"
    assert db.query(GA4ItemCategoryRule).filter_by(id=rule.id).first() is not None


@pytest.mark.integration
def test_channel_group_rule_delete_on_other_property_returns_404(
    client, db, sample_user, ga4_property_access
):
    _override_dependencies(client.app, sample_user, db)
    rule = _add(db, GA4ChannelGroupRule(
        property_id=THEIRS, channel_dimension="source_medium", group_label="FB",
        match_type="prefix", pattern="facebook", priority=1, created_by=sample_user.id,
    ))

    resp = client.delete(f"/api/ga4/insights/channel-group-rules/{rule.id}")

    assert resp.status_code == 404
    assert resp.json()["error"] == "Channel group rule not found"
    assert db.query(GA4ChannelGroupRule).filter_by(id=rule.id).first() is not None


@pytest.mark.integration
def test_kpi_target_delete_on_other_property_returns_404(
    client, db, sample_user, ga4_property_access
):
    _override_dependencies(client.app, sample_user, db)
    target = _add(db, GA4KpiTarget(
        property_id=THEIRS, metric_key="conversions", period_type="month",
        period_key="2026-07", target_value=100.0, created_by=sample_user.id,
    ))

    resp = client.delete(f"/api/ga4/insights/kpi-targets/{target.id}")

    assert resp.status_code == 404
    assert resp.json()["error"] == "KPI target not found"
    assert db.query(GA4KpiTarget).filter_by(id=target.id).first() is not None


# ─── 4. 清單類端點：property_id 為顯式參數 → 403 ────────────────────
@pytest.mark.integration
@pytest.mark.parametrize("path", [
    "landing-page-rules",
    "item-category-rules",
    "channel-group-rules",
    "kpi-targets",
])
def test_rule_list_endpoints_reject_other_property_with_403(
    client, db, sample_user, ga4_property_access, path
):
    _override_dependencies(client.app, sample_user, db)

    resp = client.get(f"/api/ga4/insights/{path}", params={"property_id": THEIRS})

    assert resp.status_code == 403
    assert THEIRS in resp.json()["error"]


@pytest.mark.integration
def test_list_channel_groups_rejects_other_property_with_403(
    client, db, sample_user, ga4_property_access
):
    _override_dependencies(client.app, sample_user, db)

    resp = client.get(
        "/api/ga4/insights/channel-groups",
        params={"property_id": THEIRS, "channel_dimension": "source_medium"},
    )

    assert resp.status_code == 403


@pytest.mark.integration
def test_rule_create_on_other_property_returns_403(
    client, db, sample_user, ga4_property_access
):
    _override_dependencies(client.app, sample_user, db)

    resp = client.put(
        "/api/ga4/insights/landing-page-rules",
        json={"property_id": THEIRS, "category": "product",
              "match_type": "prefix", "pattern": "/shop", "priority": 0},
    )

    assert resp.status_code == 403
    assert db.query(GA4LandingPageRule).filter_by(property_id=THEIRS).first() is None
