"""Items helpers for GA4 insights."""

from __future__ import annotations

import hashlib

from ._shared import *
from .channel_groups import get_channel_group_match_conditions
from ._parallel import resolve_ga4_credentials, run_parallel


def get_items(
    db, *, user: User, property_id: str, days: int = 7,
    channel_dimension: str | None = None, channel_value: str | None = None,
    channel_group: str | None = None, compare: bool = False,
):
    # docs/45：商品渠道篩選，比照到達頁（42+44）同一套驗證/OR 篩選邏輯。
    # 刻意只套用在主查詢（瀏覽/加購/購買數與比率），近7天/前7天瀏覽成長
    # 比較與 itemCategory 分類拆解維持全渠道不受篩選影響（跟使用者確認過：
    # 成長比較本來就已經是「固定期間、與上方期間選擇無關」的獨立指標，
    # 分類拆解也只是給「商品該分到哪一類」用的靜態依據，非渠道相關指標）。
    if channel_value and channel_group:
        raise ValueError("channel_value and channel_group are mutually exclusive")
    if (channel_value or channel_group) and not channel_dimension:
        raise ValueError("channel_dimension is required when channel_value or channel_group is provided")
    if channel_dimension and not channel_value and not channel_group:
        raise ValueError("channel_dimension requires channel_value or channel_group")
    if channel_dimension and channel_dimension not in CHANNEL_DIMENSION_MAP:
        raise ValueError(f"Unsupported channel_dimension: {channel_dimension}")

    ga4_channel_dimension = CHANNEL_DIMENSION_MAP[channel_dimension][0] if channel_dimension else None
    if channel_group:
        conditions = get_channel_group_match_conditions(
            db, property_id=property_id, channel_dimension=channel_dimension, group_label=channel_group,
        )
        if not conditions:
            raise ValueError(f"Unknown channel_group: {channel_group}")
        dimension_filter = [
            (ga4_channel_dimension, match_type, pattern) for match_type, pattern in conditions
        ]
    elif channel_value:
        dimension_filter = (ga4_channel_dimension, channel_value)
    else:
        dimension_filter = None

    start_date, end_date = _service_attr("_trailing_period", _trailing_period)(days)

    # 瀏覽成長比較固定用「近 7 天 vs 前 7 天」（3.4 節），與 days 參數（表格期間）無關
    recent_start, recent_end = _service_attr("_trailing_period", _trailing_period)(7)
    prior_end = (datetime.strptime(recent_start, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    prior_start = (datetime.strptime(recent_start, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")

    credentials = resolve_ga4_credentials(user, db)

    def _fetch_main():
        """主查詢鍰：官方比率指標 →（失敗才）退回基礎指標。

        鍰內兩步有相依（第二步要看第一步的錯誤），整段因此當成一個 task，
        鍰內仍然循序。回傳值帶上「有沒有退回 fallback」，比較查詢要拿它決定指標。
        """
        data, error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=ITEM_METRICS_WITH_OFFICIAL_RATES, dimensions=["itemName"], credentials=credentials,
            dimension_filter=dimension_filter,
        )
        if not error:
            return data, False
        logger.warning(
            "[GA4Insights] items official rate metrics failed %s: %s; falling back to local ratios",
            property_id, error,
        )
        data, error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=ITEM_METRICS_FALLBACK, dimensions=["itemName"], credentials=credentials,
            dimension_filter=dimension_filter,
        )
        if error:
            raise RuntimeError(error)
        return data, True

    # docs/65：主查詢鍰、近 7 天、前 7 天、分類拆解彼此無資料相依，一次並行送出。
    # 比較期間要等主查詢的 fallback 結果才能決定指標，放第二階段。
    # credentials 在請求執行緒先解析好，worker thread 因此不碰 db/user。
    phase1 = run_parallel({
        "main": _fetch_main,
        "recent": lambda: GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=recent_start, end_date=recent_end,
            metrics=["itemsViewed"], dimensions=["itemName"], credentials=credentials,
        ),
        "prior": lambda: GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=prior_start, end_date=prior_end,
            metrics=["itemsViewed"], dimensions=["itemName"], credentials=credentials,
        ),
        "breakdown": lambda: GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=start_date, end_date=end_date,
            metrics=["itemsViewed"], dimensions=["itemName", "itemCategory"], credentials=credentials,
        ),
    })

    data, used_fallback_conversion_metrics = phase1["main"]
    rows = (data or {}).get("rows", [])
    recent_data, _ = phase1["recent"]
    prior_data, _ = phase1["prior"]
    recent_views = {row["itemName"]: row.get("itemsViewed", 0) for row in (recent_data or {}).get("rows", [])}
    prior_views = {row["itemName"]: row.get("itemsViewed", 0) for row in (prior_data or {}).get("rows", [])}

    # docs/54：跟上一期比較（開關預設關閉），跟上面「固定近7天/前7天瀏覽
    # 成長」是兩件獨立並存的事——這裡跟著使用者選的天數（days）走，也沿用
    # 主查詢當下的渠道篩選，確保比較的是同一組篩選條件下的兩期；用跟主查詢
    # 同一組指標（官方比率或本地 fallback，取決於上面 used_fallback_
    # conversion_metrics 的結果）避免兩期口徑不一致。
    compare_start_date = compare_end_date = None
    compare_item_map: dict[str, dict] = {}
    compare_query_error = None
    if compare:
        compare_end_obj = datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=1)
        compare_start_obj = compare_end_obj - timedelta(days=days - 1)
        compare_start_date = compare_start_obj.strftime("%Y-%m-%d")
        compare_end_date = compare_end_obj.strftime("%Y-%m-%d")

        compare_metrics = ITEM_METRICS_FALLBACK if used_fallback_conversion_metrics else ITEM_METRICS_WITH_OFFICIAL_RATES
        compare_data, compare_error = GA4Service.get_analytics(
            user=user, property_id=property_id, start_date=compare_start_date, end_date=compare_end_date,
            metrics=compare_metrics, dimensions=["itemName"], credentials=credentials,
            dimension_filter=dimension_filter,
        )
        if compare_error:
            logger.warning("[GA4Insights] items compare query failed %s: %s", property_id, compare_error)
            compare_query_error = compare_error
        else:
            compare_item_map = {row.get("itemName", ""): row for row in (compare_data or {}).get("rows", [])}

    def _growth_rate(current: float, prior: float) -> float:
        return ((current - prior) / prior) if prior else (1.0 if current > 0 else 0.0)

    # 商品主要分類：itemName × itemCategory，同商品多分類時取瀏覽量最高者
    # （查詢失敗只記警告、不中斷主表格，同第 5 波分項查詢容錯慣例）。
    # `category_breakdown_error` 進 payload：讓前端能分辨「查詢真的失敗」
    # 跟「GA4 本來就沒有 item_category 資料（網站未回傳）」，否則兩種情況
    # 在畫面上都是一片「未分類」，使用者無從判斷是系統問題還是自家網站
    # 的 GA4/GTM 電子商務事件沒有設定商品分類。
    category_by_item: dict[str, str] = {}
    best_views_by_item: dict[str, int] = {}
    breakdown_data, breakdown_error = phase1["breakdown"]
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

        # docs/54：is_new 只有在「查詢成功、且這個商品在上一期完全沒出現」
        # 時才成立；查詢失敗時不誤標新商品，比較欄位維持 None。
        is_new = False
        views_prior = revenue_prior = cart_to_view_rate_prior = purchase_to_view_rate_prior = None
        views_compare_growth_rate = revenue_growth_rate = None
        cart_to_view_rate_delta_pp = purchase_to_view_rate_delta_pp = None
        if compare and not compare_query_error:
            prior_item_row = compare_item_map.get(item_name)
            if prior_item_row is None:
                is_new = True
            else:
                views_prior = prior_item_row.get("itemsViewed", 0)
                revenue_prior = prior_item_row.get("itemRevenue", 0.0)
                if used_fallback_conversion_metrics:
                    prior_cart = prior_item_row.get("itemsAddedToCart", 0)
                    prior_purchased = prior_item_row.get("itemsPurchased", 0)
                    cart_to_view_rate_prior = (prior_cart / views_prior) if views_prior else 0.0
                    purchase_to_view_rate_prior = (prior_purchased / views_prior) if views_prior else 0.0
                else:
                    cart_to_view_rate_prior = prior_item_row.get("cartToViewRate", 0.0)
                    purchase_to_view_rate_prior = prior_item_row.get("purchaseToViewRate", 0.0)
                views_compare_growth_rate = _growth_rate(views, views_prior)
                revenue_growth_rate = _growth_rate(row.get("itemRevenue", 0.0), revenue_prior)
                # 比率型指標（加購率/購買率）改用百分點差異，不是相對成長率，
                # 跟到達頁「轉換率/跳出率」同一套判斷（docs/54）。
                cart_to_view_rate_delta_pp = (cart_to_view_rate - cart_to_view_rate_prior) * 100
                purchase_to_view_rate_delta_pp = (purchase_to_view_rate - purchase_to_view_rate_prior) * 100

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
            "is_new": is_new,
            "views_prior": views_prior,
            "views_compare_growth_rate": views_compare_growth_rate,
            "revenue_prior": revenue_prior,
            "revenue_growth_rate": revenue_growth_rate,
            "cart_to_view_rate_prior": cart_to_view_rate_prior,
            "cart_to_view_rate_delta_pp": cart_to_view_rate_delta_pp,
            "purchase_to_view_rate_prior": purchase_to_view_rate_prior,
            "purchase_to_view_rate_delta_pp": purchase_to_view_rate_delta_pp,
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
        "channel_dimension": channel_dimension,
        "channel_value": channel_value,
        "channel_group": channel_group,
        "items": enriched,
        "category_counts": category_counts,
        "used_fallback_conversion_metrics": used_fallback_conversion_metrics,
        "category_breakdown_error": breakdown_error,
        "cart_to_view_rate_definition": ITEM_CART_TO_VIEW_RATE_DEFINITION,
        "purchase_to_view_rate_definition": ITEM_PURCHASE_TO_VIEW_RATE_DEFINITION,
        "compare_enabled": compare,
        "compare_start_date": compare_start_date,
        "compare_end_date": compare_end_date,
        "compare_query_error": compare_query_error,
    }
    # kind 命名比照到達頁（42+44）：channel_group 用 "chg_" 前綴、精確值篩選
    # 用 "ch_" 前綴的雜湊，避免自由文字撐爆欄位長度或截斷後誤判成同一筆快照。
    kind = "item"
    if channel_group:
        filter_digest = hashlib.md5(f"{channel_dimension}:group:{channel_group}".encode()).hexdigest()[:10]
        kind += f":chg_{filter_digest}"
    elif channel_dimension:
        filter_digest = hashlib.md5(f"{channel_dimension}:{channel_value}".encode()).hexdigest()[:10]
        kind += f":ch_{filter_digest}"
    # docs/54：跟上一期比較是完全獨立的一份 payload，用 ":cmp" 後綴分開存
    # 快照，AI 解讀不會跟「沒開比較」的那份互相覆寫。
    if compare:
        kind += ":cmp"
    return repository.upsert_snapshot(
        db, property_id=property_id, kind=kind, date=end_date, payload=payload, fetched_by=user.id,
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
