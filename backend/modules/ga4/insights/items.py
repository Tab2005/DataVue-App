"""Items helpers for GA4 insights."""

from __future__ import annotations

from ._shared import *


def get_items(db, *, user: User, property_id: str, days: int = 7):
    start_date, end_date = _service_attr("_trailing_period", _trailing_period)(days)

    data, error = GA4Service.get_analytics(
        user=user, property_id=property_id, start_date=start_date, end_date=end_date,
        metrics=ITEM_METRICS_WITH_OFFICIAL_RATES, dimensions=["itemName"], db=db,
    )
    used_fallback_conversion_metrics = False
    if error:
        logger.warning(
            "[GA4Insights] items official rate metrics failed %s: %s; falling back to local ratios",
            property_id, error,
        )
        data, error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=ITEM_METRICS_FALLBACK, dimensions=["itemName"], db=db,
        )
        if error:
            raise RuntimeError(error)
        used_fallback_conversion_metrics = True
    rows = (data or {}).get("rows", [])

    # 瀏覽成長比較固定用「近 7 天 vs 前 7 天」（3.4 節），與 days 參數（表格期間）無關
    recent_start, recent_end = _service_attr("_trailing_period", _trailing_period)(7)
    prior_end = (datetime.strptime(recent_start, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    prior_start = (datetime.strptime(recent_start, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")

    recent_data, _ = GA4Service.get_analytics(
        user=user, property_id=property_id, start_date=recent_start, end_date=recent_end,
        metrics=["itemsViewed"], dimensions=["itemName"], db=db,
    )
    prior_data, _ = GA4Service.get_analytics(
        user=user, property_id=property_id, start_date=prior_start, end_date=prior_end,
        metrics=["itemsViewed"], dimensions=["itemName"], db=db,
    )
    recent_views = {row["itemName"]: row.get("itemsViewed", 0) for row in (recent_data or {}).get("rows", [])}
    prior_views = {row["itemName"]: row.get("itemsViewed", 0) for row in (prior_data or {}).get("rows", [])}

    # 商品主要分類：itemName × itemCategory，同商品多分類時取瀏覽量最高者
    # （查詢失敗只記警告、不中斷主表格，同第 5 波分項查詢容錯慣例）。
    # `category_breakdown_error` 進 payload：讓前端能分辨「查詢真的失敗」
    # 跟「GA4 本來就沒有 item_category 資料（網站未回傳）」，否則兩種情況
    # 在畫面上都是一片「未分類」，使用者無從判斷是系統問題還是自家網站
    # 的 GA4/GTM 電子商務事件沒有設定商品分類。
    category_by_item: dict[str, str] = {}
    best_views_by_item: dict[str, int] = {}
    breakdown_data, breakdown_error = GA4Service.get_analytics(
        user=user, property_id=property_id, start_date=start_date, end_date=end_date,
        metrics=["itemsViewed"], dimensions=["itemName", "itemCategory"], db=db,
    )
    if not breakdown_error:
        for row in (breakdown_data or {}).get("rows", []):
            item_name = row.get("itemName", "")
            item_category = row.get("itemCategory") or "(not set)"
            views = row.get("itemsViewed", 0)
            if item_name not in best_views_by_item or views > best_views_by_item[item_name]:
                best_views_by_item[item_name] = views
                category_by_item[item_name] = item_category
    else:
        logger.warning("[GA4Insights] items category breakdown failed %s: %s", property_id, breakdown_error)

    # 第 7 波：GA4 的 itemCategory 是權威來源，只在 GA4 回報 "(not set)"
    # 時才用自訂規則補分類（見 classify_item_category 的優先順序說明）。
    item_category_rule_rows = repository.list_item_category_rules(db, property_id=property_id)
    item_category_rules = [
        {"category": r.category, "match_type": r.match_type, "pattern": r.pattern, "priority": r.priority}
        for r in item_category_rule_rows
    ]

    enriched = []
    for row in rows:
        item_name = row.get("itemName")
        views = row.get("itemsViewed", 0)
        add_to_cart = row.get("itemsAddedToCart", 0)
        purchased = row.get("itemsPurchased", 0)
        # 舊件數比（同一使用者重複瀏覽/加購會重複計）保留供回溯，前端不再顯示為主要欄位。
        add_to_cart_rate = (add_to_cart / views) if views else 0.0
        if used_fallback_conversion_metrics:
            cart_to_view_rate = add_to_cart_rate
            purchase_to_view_rate = (purchased / views) if views else 0.0
        else:
            cart_to_view_rate = row.get("cartToViewRate", 0.0)
            purchase_to_view_rate = row.get("purchaseToViewRate", 0.0)
        recent = recent_views.get(item_name, 0)
        prior = prior_views.get(item_name, 0)
        growth_rate = ((recent - prior) / prior) if prior else (1.0 if recent > 0 else 0.0)
        item_category, item_category_source = _facade_attr("classify_item_category", classify_item_category)(
            item_name, category_by_item.get(item_name), item_category_rules
        )
        enriched.append({
            **row,
            "add_to_cart_rate": add_to_cart_rate,
            "cart_to_view_rate": cart_to_view_rate,
            "purchase_to_view_rate": purchase_to_view_rate,
            "views_growth_rate": growth_rate,
            "views_recent_7d": recent,
            "views_prior_7d": prior,
            "item_category": item_category,
            "item_category_source": item_category_source,
            "is_potential": False,
        })

    category_counts: dict[str, int] = {}
    for row in enriched:
        category_counts[row["item_category"]] = category_counts.get(row["item_category"], 0) + 1

    # 潛力標記維持「全店相對」，用全體中位數（刻意決策，與第 5 波到達頁
    # 的同分類判定不同：itemCategory 高基數下單分類樣本常 <4，且潛力語意
    # 本就是跨分類比較「誰在全店裡值得加碼」，不強求跟到達頁一致）。
    if len(enriched) >= 4:
        growth_median = median(r["views_growth_rate"] for r in enriched)
        cart_rate_median = median(r["cart_to_view_rate"] for r in enriched)
        views_median = median(r["itemsViewed"] for r in enriched)
        for row in enriched:
            row["is_potential"] = (
                row["views_growth_rate"] > growth_median
                and row["cart_to_view_rate"] > cart_rate_median
                and row["itemsViewed"] < views_median
            )

    payload = {
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "items": enriched,
        "category_counts": category_counts,
        "used_fallback_conversion_metrics": used_fallback_conversion_metrics,
        "category_breakdown_error": breakdown_error,
        "cart_to_view_rate_definition": ITEM_CART_TO_VIEW_RATE_DEFINITION,
        "purchase_to_view_rate_definition": ITEM_PURCHASE_TO_VIEW_RATE_DEFINITION,
    }
    return repository.upsert_snapshot(
        db, property_id=property_id, kind="item", date=end_date, payload=payload, fetched_by=user.id,
    )


def list_item_category_rules(db, *, property_id: str):
    return repository.list_item_category_rules(db, property_id=property_id)


def upsert_item_category_rule(
    db, *, rule_id: str | None, user_id: str, property_id: str,
    category: str, match_type: str, pattern: str, priority: int,
):
    if rule_id:
        row = repository.get_item_category_rule(db, rule_id)
        if not row:
            return None
        row.property_id = property_id
        row.category = category
        row.match_type = match_type
        row.pattern = pattern
        row.priority = priority
        row.updated_at = datetime.utcnow()
        db.add(row)
        return row
    return repository.create_item_category_rule(
        db,
        property_id=property_id,
        category=category,
        match_type=match_type,
        pattern=pattern,
        priority=priority,
        created_by=user_id,
    )


def delete_item_category_rule(db, *, rule_id: str) -> bool:
    return repository.delete_item_category_rule(db, rule_id)
