"""Item x landing page cross-reference helpers for GA4 insights (docs/47)."""

from __future__ import annotations

from datetime import datetime, timedelta

from ._shared import *
from ._parallel import resolve_ga4_credentials, run_parallel


def get_item_landing_cross(db, *, user: User, property_id: str, days: int = 7, compare: bool = False):
    start_date, end_date = _trailing_period(days)

    # docs/56：比較期間的日期先算好，下面的並行扇出才能一併發出去。
    compare_start_date = compare_end_date = None
    if compare:
        compare_end_obj = datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=1)
        compare_start_obj = compare_end_obj - timedelta(days=days - 1)
        compare_start_date = compare_start_obj.strftime("%Y-%m-%d")
        compare_end_date = compare_end_obj.strftime("%Y-%m-%d")

    credentials = resolve_ga4_credentials(user, db)

    # 查詢 1：商品指標，直接複製 items.py 現有的官方/fallback 容錯邏輯
    # （刻意不重構共用，換取不動到 items.py 既有已測試路徑的風險）。
    # 鍰內兩步有相依（第二步要看第一步的錯誤），整段當成一個 task。
    def _fetch_items():
        data, error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=ITEM_METRICS_WITH_OFFICIAL_RATES, dimensions=["itemName"], credentials=credentials,
        )
        if not error:
            return data, False
        logger.warning(
            "[GA4Insights] item-landing-cross official rate metrics failed %s: %s; falling back to local ratios",
            property_id, error,
        )
        data, error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=ITEM_METRICS_FALLBACK, dimensions=["itemName"], credentials=credentials,
        )
        if error:
            raise RuntimeError(error)
        return data, True

    # docs/65：商品指標鍰、商品×到達頁對照、到達頁指標、到達頁比較彼此無資料
    # 相依，一次並行送出。商品比較要等上面 fallback 的結果才能決定指標，放第二階段。
    tasks = {
        "items": _fetch_items,
        "mapping": lambda: GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=["itemsViewed"], dimensions=["itemName", "landingPage"], credentials=credentials,
        ),
        "landing": lambda: GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=["sessions", "sessionKeyEventRate", "bounceRate"], dimensions=["landingPage"], credentials=credentials,
        ),
    }
    if compare:
        tasks["landing_compare"] = lambda: GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=compare_start_date, end_date=compare_end_date,
            metrics=["sessions", "sessionKeyEventRate", "bounceRate"], dimensions=["landingPage"], credentials=credentials,
        )
    phase1 = run_parallel(tasks)

    data, used_fallback_conversion_metrics = phase1["items"]
    item_rows = (data or {}).get("rows", [])

    # 查詢 2：商品 × 到達頁對照。刻意只用純計數指標 itemsViewed，不夾帶比率
    # 指標——跟既有 itemName × itemCategory（items.py）已驗證可行的組合同
    # 一種形狀，避開比率指標在雙維度查詢下的相容性風險（docs/47 的核心設計
    # 決策）。同商品對應多個到達頁時取瀏覽量最高者當「主要到達頁」。
    best_views_by_item: dict[str, int] = {}
    primary_landing_page_by_item: dict[str, str] = {}
    mapping_data, mapping_error = phase1["mapping"]
    if not mapping_error:
        for row in (mapping_data or {}).get("rows", []):
            item_name = row.get("itemName", "")
            landing_page = row.get("landingPage", "")
            views = row.get("itemsViewed", 0)
            if not item_name or not landing_page:
                continue
            if item_name not in best_views_by_item or views > best_views_by_item[item_name]:
                best_views_by_item[item_name] = views
                primary_landing_page_by_item[item_name] = landing_page
    else:
        logger.warning("[GA4Insights] item-landing-cross mapping query failed %s: %s", property_id, mapping_error)

    # 查詢 3：到達頁指標，沿用 landing_pages.py 的查詢形狀。
    landing_metrics_by_page: dict[str, dict] = {}
    landing_data, landing_error = phase1["landing"]
    if not landing_error:
        for row in (landing_data or {}).get("rows", []):
            page = row.get("landingPage", "")
            if not page:
                continue
            landing_metrics_by_page[page] = {
                "sessions": row.get("sessions", 0),
                "session_key_event_rate": row.get("sessionKeyEventRate", 0.0),
                "bounce_rate": row.get("bounceRate", 0.0),
            }
    else:
        logger.warning("[GA4Insights] item-landing-cross landing page query failed %s: %s", property_id, landing_error)

    # docs/56：跟上一期比較（開關預設關閉）。關鍵決策：固定用「本期」算出來
    # 的 primary_landing_page_by_item 配對，不對上一期重新判定哪個頁面瀏覽量
    # 最高——否則配對到的頁面可能跟本期不同，比較就會變成拿兩個不同頁面比。
    prior_purchase_to_view_rate_by_item: dict[str, float] = {}
    prior_landing_metrics_by_page: dict[str, dict] = {}
    item_compare_error = None
    landing_compare_error = None
    if compare:
        item_compare_metrics = ITEM_METRICS_FALLBACK if used_fallback_conversion_metrics else ITEM_METRICS_WITH_OFFICIAL_RATES
        item_compare_data, item_compare_error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=compare_start_date, end_date=compare_end_date,
            metrics=item_compare_metrics, dimensions=["itemName"], credentials=credentials,
        )
        if item_compare_error:
            logger.warning("[GA4Insights] item-landing-cross item compare query failed %s: %s", property_id, item_compare_error)
        else:
            for row in (item_compare_data or {}).get("rows", []):
                item_name = row.get("itemName", "")
                if not item_name:
                    continue
                prior_views = row.get("itemsViewed", 0)
                if used_fallback_conversion_metrics:
                    prior_rate = (row.get("itemsPurchased", 0) / prior_views) if prior_views else 0.0
                else:
                    prior_rate = row.get("purchaseToViewRate", 0.0)
                prior_purchase_to_view_rate_by_item[item_name] = prior_rate

        landing_compare_data, landing_compare_error = phase1["landing_compare"]
        if landing_compare_error:
            logger.warning("[GA4Insights] item-landing-cross landing compare query failed %s: %s", property_id, landing_compare_error)
        else:
            for row in (landing_compare_data or {}).get("rows", []):
                page = row.get("landingPage", "")
                if not page:
                    continue
                prior_landing_metrics_by_page[page] = {
                    "sessions": row.get("sessions", 0),
                    "session_key_event_rate": row.get("sessionKeyEventRate", 0.0),
                }

    def _growth_rate(current: float, prior: float) -> float:
        return ((current - prior) / prior) if prior else (1.0 if current > 0 else 0.0)

    # 應用層合併：查不到對照到達頁（瀏覽量 0 或查詢失敗）該商品的頁面欄位
    # 留 None，不擋主表格（同 items.py 既有 category_breakdown_error 容錯慣例）。
    enriched = []
    for row in item_rows:
        item_name = row.get("itemName")
        views = row.get("itemsViewed", 0)
        purchased = row.get("itemsPurchased", 0)
        if used_fallback_conversion_metrics:
            purchase_to_view_rate = (purchased / views) if views else 0.0
        else:
            purchase_to_view_rate = row.get("purchaseToViewRate", 0.0)

        primary_landing_page = primary_landing_page_by_item.get(item_name)
        page_metrics = landing_metrics_by_page.get(primary_landing_page) if primary_landing_page else None

        # docs/56：比較欄位——item_is_new 只看商品本身上一期有沒有資料；頁面
        # 那兩欄各自看「本期配對到的那個頁面」在上一期有沒有資料，找不到就
        # 留 None（不特別標記新頁面，跟商品的 is_new 語意不同，見文件說明）。
        item_is_new = False
        purchase_to_view_rate_prior = purchase_to_view_rate_delta_pp = None
        page_sessions_prior = page_sessions_growth_rate = None
        page_session_key_event_rate_prior = page_session_key_event_rate_delta_pp = None
        if compare and not item_compare_error:
            if item_name not in prior_purchase_to_view_rate_by_item:
                item_is_new = True
            else:
                purchase_to_view_rate_prior = prior_purchase_to_view_rate_by_item[item_name]
                purchase_to_view_rate_delta_pp = (purchase_to_view_rate - purchase_to_view_rate_prior) * 100
        if compare and not landing_compare_error and primary_landing_page:
            prior_page_metrics = prior_landing_metrics_by_page.get(primary_landing_page)
            if prior_page_metrics is not None and page_metrics is not None:
                page_sessions_prior = prior_page_metrics["sessions"]
                page_sessions_growth_rate = _growth_rate(page_metrics["sessions"], page_sessions_prior)
                page_session_key_event_rate_prior = prior_page_metrics["session_key_event_rate"]
                page_session_key_event_rate_delta_pp = (
                    page_metrics["session_key_event_rate"] - page_session_key_event_rate_prior
                ) * 100

        enriched.append({
            "itemName": item_name,
            "itemsViewed": views,
            "purchase_to_view_rate": purchase_to_view_rate,
            "primary_landing_page": primary_landing_page,
            "page_sessions": page_metrics["sessions"] if page_metrics else None,
            "page_session_key_event_rate": page_metrics["session_key_event_rate"] if page_metrics else None,
            "page_bounce_rate": page_metrics["bounce_rate"] if page_metrics else None,
            "page_underperforms_item": False,
            "item_is_new": item_is_new,
            "purchase_to_view_rate_prior": purchase_to_view_rate_prior,
            "purchase_to_view_rate_delta_pp": purchase_to_view_rate_delta_pp,
            "page_sessions_prior": page_sessions_prior,
            "page_sessions_growth_rate": page_sessions_growth_rate,
            "page_session_key_event_rate_prior": page_session_key_event_rate_prior,
            "page_session_key_event_rate_delta_pp": page_session_key_event_rate_delta_pp,
        })

    # 差異標記：到達頁轉換率落在後 25 百分位、但商品瀏覽後購買率不在後 25
    # 百分位——代表頁面可能有設計/載入速度問題，而非商品本身不吸引人
    # （docs/40 的原始動機範例）。只在有配對到到達頁的商品裡計算分位數，
    # 樣本數 <4 不標記（沿用到達頁分頁既有的四分位判定慣例）。
    matched = [r for r in enriched if r["page_session_key_event_rate"] is not None]
    if len(matched) >= 4:
        page_rate_p25 = _percentile(sorted(r["page_session_key_event_rate"] for r in matched), 0.25)
        item_rate_p25 = _percentile(sorted(r["purchase_to_view_rate"] for r in matched), 0.25)
        for row in matched:
            row["page_underperforms_item"] = (
                row["page_session_key_event_rate"] <= page_rate_p25
                and row["purchase_to_view_rate"] > item_rate_p25
            )

    payload = {
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "items": enriched,
        "used_fallback_conversion_metrics": used_fallback_conversion_metrics,
        "mapping_query_error": mapping_error,
        "landing_query_error": landing_error,
        "compare_enabled": compare,
        "compare_start_date": compare_start_date,
        "compare_end_date": compare_end_date,
        "item_compare_query_error": item_compare_error,
        "landing_compare_query_error": landing_compare_error,
    }
    # docs/56：跟上一期比較是完全獨立的一份 payload，用 ":cmp" 後綴分開存
    # 快照，AI 解讀不會跟「沒開比較」的那份互相覆寫。
    kind = "item_landing_cross"
    if compare:
        kind += ":cmp"
    return repository.upsert_snapshot(
        db, property_id=property_id, kind=kind, date=end_date, payload=payload, fetched_by=user.id,
    )
