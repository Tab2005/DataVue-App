"""Item x landing page cross-reference helpers for GA4 insights (docs/47)."""

from __future__ import annotations

from ._shared import *


def get_item_landing_cross(db, *, user: User, property_id: str, days: int = 7):
    start_date, end_date = _service_attr("_trailing_period", _trailing_period)(days)

    # 查詢 1：商品指標，直接複製 items.py 現有的官方/fallback 容錯邏輯
    # （刻意不重構共用，換取不動到 items.py 既有已測試路徑的風險）。
    data, error = GA4Service.get_analytics(
        user=user, property_id=property_id, start_date=start_date, end_date=end_date,
        metrics=ITEM_METRICS_WITH_OFFICIAL_RATES, dimensions=["itemName"], db=db,
    )
    used_fallback_conversion_metrics = False
    if error:
        logger.warning(
            "[GA4Insights] item-landing-cross official rate metrics failed %s: %s; falling back to local ratios",
            property_id, error,
        )
        data, error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=ITEM_METRICS_FALLBACK, dimensions=["itemName"], db=db,
        )
        if error:
            raise RuntimeError(error)
        used_fallback_conversion_metrics = True
    item_rows = (data or {}).get("rows", [])

    # 查詢 2：商品 × 到達頁對照。刻意只用純計數指標 itemsViewed，不夾帶比率
    # 指標——跟既有 itemName × itemCategory（items.py）已驗證可行的組合同
    # 一種形狀，避開比率指標在雙維度查詢下的相容性風險（docs/47 的核心設計
    # 決策）。同商品對應多個到達頁時取瀏覽量最高者當「主要到達頁」。
    best_views_by_item: dict[str, int] = {}
    primary_landing_page_by_item: dict[str, str] = {}
    mapping_data, mapping_error = GA4Service.get_analytics(
        user=user, property_id=property_id, start_date=start_date, end_date=end_date,
        metrics=["itemsViewed"], dimensions=["itemName", "landingPage"], db=db,
    )
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
    landing_data, landing_error = GA4Service.get_analytics(
        user=user, property_id=property_id, start_date=start_date, end_date=end_date,
        metrics=["sessions", "sessionKeyEventRate", "bounceRate"], dimensions=["landingPage"], db=db,
    )
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

        enriched.append({
            "itemName": item_name,
            "itemsViewed": views,
            "purchase_to_view_rate": purchase_to_view_rate,
            "primary_landing_page": primary_landing_page,
            "page_sessions": page_metrics["sessions"] if page_metrics else None,
            "page_session_key_event_rate": page_metrics["session_key_event_rate"] if page_metrics else None,
            "page_bounce_rate": page_metrics["bounce_rate"] if page_metrics else None,
            "page_underperforms_item": False,
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
    }
    return repository.upsert_snapshot(
        db, property_id=property_id, kind="item_landing_cross", date=end_date, payload=payload, fetched_by=user.id,
    )
