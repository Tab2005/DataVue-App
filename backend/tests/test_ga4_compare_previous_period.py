"""
GA4「跟上一期比較」後端測試（docs/54 步驟 6 + docs/56 步驟 6）

docs/59 P1-1 指出：docs/54 / docs/56 引入的比較邏輯**完全沒有自動化測試**
（`grep "def test_.*compare"` 在 tests/ 下沒有任何結果），當時是用臨時腳本
驗證後刪除的。本檔補上原訂範圍：

  1. 次數型指標用相對成長率 vs 比率型指標用百分點差異的分流（docs/54 的
     核心口徑決策，避免「轉換率 5%→6%」被講成「成長 20%」）
  2. `is_new` / `item_is_new` 的判定，以及「查詢失敗時不可標記為新」這個
     刻意設計——不能把「查不到」誤講成「這是新項目」
  3. 各支比較查詢**各自獨立容錯**（`compare_query_error` /
     `item_compare_query_error` / `landing_compare_query_error`）
  4. **docs/56 最關鍵的「固定用本期配對」邏輯**：上一期不重新判定主要到達
     頁。這是整個 docs/56 的核心決策，日後若有人「順手優化」成重新計算配
     對，必須要有測試擋下來
  5. `compare=False` 的既有行為不受影響（回歸）、`:cmp` kind 後綴

比較期間的推導：主期間是 `_trailing_period(days)`（截至昨天往前 days 天），
上一期則是再往前接著的同樣長度一段。測試用 `_expected_periods()` 算出兩段
日期，mock 再依 `start_date` 分派本期/上一期的假資料。
"""

import pytest

from modules.ga4.insights._shared import _trailing_period
from modules.ga4.insights_service import GA4InsightsService

PROPERTY_ID = "123456"
DAYS = 7


def _expected_periods(days=DAYS):
    """回傳 ((本期起, 本期迄), (上一期起, 上一期迄))，與實作同一套推導。"""
    from datetime import datetime, timedelta

    start_date, end_date = _trailing_period(days)
    prior_end = datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=1)
    prior_start = prior_end - timedelta(days=days - 1)
    return (start_date, end_date), (prior_start.strftime("%Y-%m-%d"), prior_end.strftime("%Y-%m-%d"))


(CURRENT_START, CURRENT_END), (PRIOR_START, PRIOR_END) = _expected_periods()


def _is_prior(start_date):
    return start_date == PRIOR_START


# ─────────────────────────────────────────────────────────────────────
# 1. 到達頁（docs/54）
# ─────────────────────────────────────────────────────────────────────
def _landing_dispatcher(*, current_rows, prior_rows, prior_error=None, breakdown_rows=None):
    """依 dimensions + 期間分派：主查詢/分項查詢/比較查詢。"""
    def fake(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["landingPage", "eventName"]:
            return {"rows": breakdown_rows or []}, None
        if _is_prior(start_date):
            if prior_error:
                return None, prior_error
            return {"rows": prior_rows}, None
        return {"rows": current_rows}, None
    return fake


def _landing_row(page, *, sessions, key_events, rate, bounce):
    return {
        "landingPage": page, "sessions": sessions, "engagementRate": 0.5,
        "bounceRate": bounce, "keyEvents": key_events, "sessionKeyEventRate": rate,
    }


@pytest.mark.unit
def test_landing_compare_disabled_leaves_comparison_fields_empty(mocker, db, sample_user):
    """回歸：compare=False 時 payload 不帶比較狀態、kind 沒有 :cmp 後綴。"""
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        side_effect=_landing_dispatcher(
            current_rows=[_landing_row("/a", sessions=100, key_events=10, rate=0.10, bounce=0.5)],
            prior_rows=[],
        ),
    )

    snapshot = GA4InsightsService.get_landing_pages(db, user=sample_user, property_id=PROPERTY_ID, days=DAYS)
    db.commit()

    payload = snapshot.payload
    assert payload["compare_enabled"] is False
    assert payload["compare_start_date"] is None
    assert payload["compare_end_date"] is None
    assert snapshot.kind == "landing_page"
    row = payload["landing_pages"][0]
    assert row["is_new"] is False
    assert row["sessions_prior"] is None
    assert row["sessions_growth_rate"] is None


@pytest.mark.unit
def test_landing_compare_uses_growth_rate_for_counts_and_pp_for_ratios(mocker, db, sample_user):
    """docs/54 核心口徑：次數型用相對成長率、比率型用百分點差異。

    工作階段 80→100 是 +25% 成長率；轉換率 5%→6% 必須是 +1.0pp，
    **不是** +20%（這正是當初刻意分流的理由）。
    """
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        side_effect=_landing_dispatcher(
            current_rows=[_landing_row("/a", sessions=100, key_events=12, rate=0.06, bounce=0.40)],
            prior_rows=[_landing_row("/a", sessions=80, key_events=10, rate=0.05, bounce=0.50)],
        ),
    )

    snapshot = GA4InsightsService.get_landing_pages(
        db, user=sample_user, property_id=PROPERTY_ID, days=DAYS, compare=True
    )
    db.commit()

    payload = snapshot.payload
    assert payload["compare_enabled"] is True
    assert payload["compare_start_date"] == PRIOR_START
    assert payload["compare_end_date"] == PRIOR_END
    assert snapshot.kind == "landing_page:cmp"

    row = payload["landing_pages"][0]
    assert row["is_new"] is False
    # 次數型 → 相對成長率
    assert row["sessions_prior"] == 80
    assert row["sessions_growth_rate"] == pytest.approx(0.25)
    assert row["conversions_prior"] == 10
    assert row["conversions_growth_rate"] == pytest.approx(0.2)
    # 比率型 → 百分點差異（不是 (0.06-0.05)/0.05 = 20%）
    assert row["session_key_event_rate_prior"] == pytest.approx(0.05)
    assert row["session_key_event_rate_delta_pp"] == pytest.approx(1.0)
    assert row["bounce_rate_delta_pp"] == pytest.approx(-10.0)


@pytest.mark.unit
def test_landing_compare_marks_pages_missing_from_prior_period_as_new(mocker, db, sample_user):
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        side_effect=_landing_dispatcher(
            current_rows=[
                _landing_row("/old", sessions=100, key_events=10, rate=0.10, bounce=0.5),
                _landing_row("/brand-new", sessions=30, key_events=3, rate=0.10, bounce=0.5),
            ],
            prior_rows=[_landing_row("/old", sessions=80, key_events=8, rate=0.10, bounce=0.5)],
        ),
    )

    snapshot = GA4InsightsService.get_landing_pages(
        db, user=sample_user, property_id=PROPERTY_ID, days=DAYS, compare=True
    )
    db.commit()

    by_page = {r["landingPage"]: r for r in snapshot.payload["landing_pages"]}
    assert by_page["/old"]["is_new"] is False
    assert by_page["/brand-new"]["is_new"] is True
    # 新頁面沒有上一期數字可比，比較欄位一律留空
    assert by_page["/brand-new"]["sessions_prior"] is None
    assert by_page["/brand-new"]["sessions_growth_rate"] is None


@pytest.mark.unit
def test_landing_compare_query_failure_never_marks_rows_as_new(mocker, db, sample_user):
    """刻意設計：比較查詢失敗時所有列都不標記新頁面，避免把「查詢失敗」
    誤講成「這是新頁面」。錯誤另外記在 payload 供前端提示。"""
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        side_effect=_landing_dispatcher(
            current_rows=[_landing_row("/a", sessions=100, key_events=10, rate=0.10, bounce=0.5)],
            prior_rows=[],
            prior_error="compare boom",
        ),
    )

    snapshot = GA4InsightsService.get_landing_pages(
        db, user=sample_user, property_id=PROPERTY_ID, days=DAYS, compare=True
    )
    db.commit()

    payload = snapshot.payload
    assert payload["compare_query_error"] == "compare boom"
    row = payload["landing_pages"][0]
    assert row["is_new"] is False          # ← 關鍵：不可誤標
    assert row["sessions_growth_rate"] is None
    assert row["session_key_event_rate_delta_pp"] is None
    # 主表格本身不受影響
    assert row["sessions"] == 100


# ─────────────────────────────────────────────────────────────────────
# 2. 商品（docs/54）
# ─────────────────────────────────────────────────────────────────────
def _item_row(name, *, views, cart, purchased, revenue, cart_rate, purchase_rate):
    return {
        "itemName": name, "itemsViewed": views, "itemsAddedToCart": cart,
        "itemsPurchased": purchased, "itemRevenue": revenue,
        "cartToViewRate": cart_rate, "purchaseToViewRate": purchase_rate,
    }


def _items_dispatcher(*, current_rows, prior_rows, prior_error=None):
    def fake(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["itemName", "itemCategory"]:
            return {"rows": []}, None
        if _is_prior(start_date):
            if prior_error:
                return None, prior_error
            return {"rows": prior_rows}, None
        # items.py 另有「近 7 天 / 前 7 天」趨勢查詢，也走 itemName 維度；
        # 給同一份本期資料即可，不影響比較欄位的斷言。
        return {"rows": current_rows}, None
    return fake


@pytest.mark.unit
def test_items_compare_splits_growth_rate_and_pp_and_flags_new_items(mocker, db, sample_user):
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        side_effect=_items_dispatcher(
            current_rows=[
                _item_row("P1", views=100, cart=20, purchased=6, revenue=600.0, cart_rate=0.20, purchase_rate=0.06),
                _item_row("P-NEW", views=10, cart=1, purchased=0, revenue=0.0, cart_rate=0.10, purchase_rate=0.0),
            ],
            prior_rows=[
                _item_row("P1", views=80, cart=12, purchased=4, revenue=400.0, cart_rate=0.15, purchase_rate=0.05),
            ],
        ),
    )

    snapshot = GA4InsightsService.get_items(
        db, user=sample_user, property_id=PROPERTY_ID, days=DAYS, compare=True
    )
    db.commit()

    payload = snapshot.payload
    assert payload["compare_enabled"] is True
    assert snapshot.kind == "item:cmp"

    by_item = {r["itemName"]: r for r in payload["items"]}
    p1 = by_item["P1"]
    assert p1["is_new"] is False
    # 次數/金額型 → 相對成長率
    assert p1["views_prior"] == 80
    assert p1["views_compare_growth_rate"] == pytest.approx(0.25)
    assert p1["revenue_prior"] == pytest.approx(400.0)
    assert p1["revenue_growth_rate"] == pytest.approx(0.5)
    # 比率型 → 百分點差異
    assert p1["cart_to_view_rate_delta_pp"] == pytest.approx(5.0)
    assert p1["purchase_to_view_rate_delta_pp"] == pytest.approx(1.0)

    assert by_item["P-NEW"]["is_new"] is True
    assert by_item["P-NEW"]["views_prior"] is None


@pytest.mark.unit
def test_items_compare_query_failure_never_marks_items_as_new(mocker, db, sample_user):
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        side_effect=_items_dispatcher(
            current_rows=[_item_row("P1", views=100, cart=20, purchased=6, revenue=600.0, cart_rate=0.2, purchase_rate=0.06)],
            prior_rows=[],
            prior_error="item compare boom",
        ),
    )

    snapshot = GA4InsightsService.get_items(
        db, user=sample_user, property_id=PROPERTY_ID, days=DAYS, compare=True
    )
    db.commit()

    payload = snapshot.payload
    assert payload["compare_query_error"] == "item compare boom"
    row = payload["items"][0]
    assert row["is_new"] is False
    assert row["views_compare_growth_rate"] is None
    assert row["purchase_to_view_rate_delta_pp"] is None


# ─────────────────────────────────────────────────────────────────────
# 3. 商品頁面比對（docs/56）—— 固定配對是本組的重點
# ─────────────────────────────────────────────────────────────────────
def _cross_dispatcher(
    *, item_rows, mapping_rows, landing_rows,
    prior_item_rows=None, prior_landing_rows=None,
    prior_item_error=None, prior_landing_error=None,
):
    def fake(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        prior = _is_prior(start_date)
        if dimensions == ["itemName", "landingPage"]:
            return {"rows": mapping_rows}, None
        if dimensions == ["landingPage"]:
            if prior:
                if prior_landing_error:
                    return None, prior_landing_error
                return {"rows": prior_landing_rows or []}, None
            return {"rows": landing_rows}, None
        # dimensions == ["itemName"]
        if prior:
            if prior_item_error:
                return None, prior_item_error
            return {"rows": prior_item_rows or []}, None
        return {"rows": item_rows}, None
    return fake


@pytest.mark.unit
def test_cross_compare_keeps_current_pairing_instead_of_recomputing(mocker, db, sample_user):
    """**docs/56 的核心決策**：上一期沿用本期算出的「商品→主要到達頁」配對，
    不重新判定。

    佈局刻意做成陷阱：本期 P1 的主要到達頁是 /a（瀏覽 70 > /b 的 30），但上
    一期 /b 的流量遠高於 /a。若實作改成「對上一期重新判定主要頁面」，就會拿
    /b 的數據來比，比較的對象在兩期之間被悄悄換掉。正確行為是**固定用 /a**。
    """
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        side_effect=_cross_dispatcher(
            item_rows=[_item_row("P1", views=100, cart=20, purchased=6, revenue=600.0, cart_rate=0.2, purchase_rate=0.06)],
            mapping_rows=[
                {"itemName": "P1", "landingPage": "/a", "itemsViewed": 70},
                {"itemName": "P1", "landingPage": "/b", "itemsViewed": 30},
            ],
            landing_rows=[
                {"landingPage": "/a", "sessions": 120, "sessionKeyEventRate": 0.10, "bounceRate": 0.4},
                {"landingPage": "/b", "sessions": 900, "sessionKeyEventRate": 0.50, "bounceRate": 0.2},
            ],
            prior_item_rows=[_item_row("P1", views=80, cart=12, purchased=4, revenue=400.0, cart_rate=0.15, purchase_rate=0.05)],
            prior_landing_rows=[
                {"landingPage": "/a", "sessions": 100, "sessionKeyEventRate": 0.08, "bounceRate": 0.4},
                {"landingPage": "/b", "sessions": 5000, "sessionKeyEventRate": 0.90, "bounceRate": 0.1},
            ],
        ),
    )

    snapshot = GA4InsightsService.get_item_landing_cross(
        db, user=sample_user, property_id=PROPERTY_ID, days=DAYS, compare=True
    )
    db.commit()

    row = snapshot.payload["items"][0]
    assert row["primary_landing_page"] == "/a"
    # 比的是 /a 的上一期（100 sessions / 8%），不是流量更高的 /b（5000 / 90%）
    assert row["page_sessions_prior"] == 100
    assert row["page_sessions_growth_rate"] == pytest.approx(0.2)
    assert row["page_session_key_event_rate_prior"] == pytest.approx(0.08)
    assert row["page_session_key_event_rate_delta_pp"] == pytest.approx(2.0)


@pytest.mark.unit
def test_cross_compare_flags_new_items_and_leaves_unmatched_pages_unflagged(mocker, db, sample_user):
    """`item_is_new` 只看商品本身；配對頁面在上一期沒資料時，頁面欄位留 None
    但**不**標記為新（docs/56 拍板決策 3：頁面沒資料不一定代表是新頁面）。"""
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        side_effect=_cross_dispatcher(
            item_rows=[
                _item_row("P-NEW", views=50, cart=5, purchased=2, revenue=200.0, cart_rate=0.1, purchase_rate=0.04),
                _item_row("P-OLD", views=100, cart=20, purchased=6, revenue=600.0, cart_rate=0.2, purchase_rate=0.06),
            ],
            mapping_rows=[
                {"itemName": "P-NEW", "landingPage": "/new-page", "itemsViewed": 40},
                {"itemName": "P-OLD", "landingPage": "/old-page", "itemsViewed": 90},
            ],
            landing_rows=[
                {"landingPage": "/new-page", "sessions": 60, "sessionKeyEventRate": 0.05, "bounceRate": 0.6},
                {"landingPage": "/old-page", "sessions": 120, "sessionKeyEventRate": 0.10, "bounceRate": 0.4},
            ],
            # 上一期只有 P-OLD / /old-page
            prior_item_rows=[_item_row("P-OLD", views=80, cart=12, purchased=4, revenue=400.0, cart_rate=0.15, purchase_rate=0.05)],
            prior_landing_rows=[{"landingPage": "/old-page", "sessions": 100, "sessionKeyEventRate": 0.08, "bounceRate": 0.4}],
        ),
    )

    snapshot = GA4InsightsService.get_item_landing_cross(
        db, user=sample_user, property_id=PROPERTY_ID, days=DAYS, compare=True
    )
    db.commit()

    by_item = {r["itemName"]: r for r in snapshot.payload["items"]}

    new_item = by_item["P-NEW"]
    assert new_item["item_is_new"] is True
    assert new_item["purchase_to_view_rate_prior"] is None
    # 配對頁面 /new-page 上一期沒資料 → 頁面比較欄位留 None，但本期數字仍在
    assert new_item["page_sessions_prior"] is None
    assert new_item["page_sessions_growth_rate"] is None
    assert new_item["page_sessions"] == 60

    old_item = by_item["P-OLD"]
    assert old_item["item_is_new"] is False
    assert old_item["purchase_to_view_rate_delta_pp"] == pytest.approx(1.0)
    assert old_item["page_sessions_prior"] == 100


@pytest.mark.unit
def test_cross_item_compare_failure_does_not_affect_page_comparison(mocker, db, sample_user):
    """兩支比較查詢各自獨立容錯：商品那支失敗，頁面那支仍要正常產出。"""
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        side_effect=_cross_dispatcher(
            item_rows=[_item_row("P1", views=100, cart=20, purchased=6, revenue=600.0, cart_rate=0.2, purchase_rate=0.06)],
            mapping_rows=[{"itemName": "P1", "landingPage": "/a", "itemsViewed": 70}],
            landing_rows=[{"landingPage": "/a", "sessions": 120, "sessionKeyEventRate": 0.10, "bounceRate": 0.4}],
            prior_landing_rows=[{"landingPage": "/a", "sessions": 100, "sessionKeyEventRate": 0.08, "bounceRate": 0.4}],
            prior_item_error="item compare boom",
        ),
    )

    snapshot = GA4InsightsService.get_item_landing_cross(
        db, user=sample_user, property_id=PROPERTY_ID, days=DAYS, compare=True
    )
    db.commit()

    payload = snapshot.payload
    assert payload["item_compare_query_error"] == "item compare boom"
    assert payload["landing_compare_query_error"] is None

    row = payload["items"][0]
    assert row["item_is_new"] is False                 # 查詢失敗不可誤標為新
    assert row["purchase_to_view_rate_delta_pp"] is None
    # 頁面那半邊不受影響
    assert row["page_sessions_prior"] == 100
    assert row["page_sessions_growth_rate"] == pytest.approx(0.2)


@pytest.mark.unit
def test_cross_landing_compare_failure_does_not_affect_item_comparison(mocker, db, sample_user):
    """反向：頁面那支失敗，商品比較仍要正常產出。"""
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        side_effect=_cross_dispatcher(
            item_rows=[_item_row("P1", views=100, cart=20, purchased=6, revenue=600.0, cart_rate=0.2, purchase_rate=0.06)],
            mapping_rows=[{"itemName": "P1", "landingPage": "/a", "itemsViewed": 70}],
            landing_rows=[{"landingPage": "/a", "sessions": 120, "sessionKeyEventRate": 0.10, "bounceRate": 0.4}],
            prior_item_rows=[_item_row("P1", views=80, cart=12, purchased=4, revenue=400.0, cart_rate=0.15, purchase_rate=0.05)],
            prior_landing_error="landing compare boom",
        ),
    )

    snapshot = GA4InsightsService.get_item_landing_cross(
        db, user=sample_user, property_id=PROPERTY_ID, days=DAYS, compare=True
    )
    db.commit()

    payload = snapshot.payload
    assert payload["item_compare_query_error"] is None
    assert payload["landing_compare_query_error"] == "landing compare boom"

    row = payload["items"][0]
    assert row["purchase_to_view_rate_delta_pp"] == pytest.approx(1.0)
    assert row["page_sessions_prior"] is None
    assert row["page_session_key_event_rate_delta_pp"] is None


@pytest.mark.unit
def test_cross_compare_disabled_leaves_comparison_fields_empty(mocker, db, sample_user):
    """回歸：compare=False 時既有行為完全不變。"""
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        side_effect=_cross_dispatcher(
            item_rows=[_item_row("P1", views=100, cart=20, purchased=6, revenue=600.0, cart_rate=0.2, purchase_rate=0.06)],
            mapping_rows=[{"itemName": "P1", "landingPage": "/a", "itemsViewed": 70}],
            landing_rows=[{"landingPage": "/a", "sessions": 120, "sessionKeyEventRate": 0.10, "bounceRate": 0.4}],
        ),
    )

    snapshot = GA4InsightsService.get_item_landing_cross(
        db, user=sample_user, property_id=PROPERTY_ID, days=DAYS
    )
    db.commit()

    payload = snapshot.payload
    assert payload["compare_enabled"] is False
    assert payload["item_compare_query_error"] is None
    assert payload["landing_compare_query_error"] is None
    assert snapshot.kind == "item_landing_cross"
    row = payload["items"][0]
    assert row["item_is_new"] is False
    assert row["page_sessions_prior"] is None


@pytest.mark.unit
def test_cross_compare_uses_fallback_metrics_consistently_across_periods(mocker, db, sample_user):
    """官方比率指標不可用時，本期與上一期都要退回本地件數比計算，
    否則兩期用不同口徑相減，百分點差異會是錯的。"""
    def fake(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        # 只要求到官方比率指標就失敗，逼實作走 fallback
        if "purchaseToViewRate" in metrics:
            return None, "official rate metrics incompatible"
        if dimensions == ["itemName", "landingPage"]:
            return {"rows": [{"itemName": "P1", "landingPage": "/a", "itemsViewed": 70}]}, None
        if dimensions == ["landingPage"]:
            return {"rows": [{"landingPage": "/a", "sessions": 120, "sessionKeyEventRate": 0.1, "bounceRate": 0.4}]}, None
        if _is_prior(start_date):
            # 上一期：80 瀏覽 / 4 購買 → 5%
            return {"rows": [{"itemName": "P1", "itemsViewed": 80, "itemsAddedToCart": 12,
                              "itemsPurchased": 4, "itemRevenue": 400.0}]}, None
        # 本期：100 瀏覽 / 6 購買 → 6%
        return {"rows": [{"itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20,
                          "itemsPurchased": 6, "itemRevenue": 600.0}]}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake)

    snapshot = GA4InsightsService.get_item_landing_cross(
        db, user=sample_user, property_id=PROPERTY_ID, days=DAYS, compare=True
    )
    db.commit()

    payload = snapshot.payload
    assert payload["used_fallback_conversion_metrics"] is True
    row = payload["items"][0]
    assert row["purchase_to_view_rate"] == pytest.approx(0.06)
    assert row["purchase_to_view_rate_prior"] == pytest.approx(0.05)
    assert row["purchase_to_view_rate_delta_pp"] == pytest.approx(1.0)
