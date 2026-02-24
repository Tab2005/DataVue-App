# backend/modules/fb_ads/trends_service.py
"""
廣告趨勢數據服務（每日時間序列比較）。
對應原 AsyncFacebookService.get_analytics_trend。
"""

import sys
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)

from cache import get_trend_cache, set_trend_cache
from modules.fb_ads._base import BASE_URL, TIMEOUT, get_headers


def _process_daily_item(item: dict) -> dict:
    """將每日資料列轉換為標準化指標字典"""
    from services import FacebookService

    if not item:
        return {}

    row = {
        "spend": float(item.get("spend", 0)),
        "impressions": int(item.get("impressions", 0)),
        "reach": int(item.get("reach", 0)),
        "link_clicks": int(item.get("inline_link_clicks", 0)),
        "clicks": int(item.get("clicks", 0)),
        "cpc": float(item.get("cpc", 0)),
        "ctr": float(item.get("ctr", 0)),
        "cpm": float(item.get("cpm", 0)),
        "roas": float(
            item.get("purchase_roas", [{}])[0].get("value", 0)
            if item.get("purchase_roas") else 0
        ),
    }

    acts = FacebookService._process_actions(item)

    row["view_content"] = acts.get("view_content", 0)
    row["add_to_cart"] = acts.get("add_to_cart", 0)
    row["initiate_checkout"] = acts.get("initiate_checkout", 0)
    row["add_payment_info"] = acts.get("add_payment_info", 0)
    row["purchases"] = acts.get("purchase", 0)
    row["purchase_value"] = acts.get("purchase_val", 0)
    row["atc_value"] = acts.get("add_to_cart_val", 0)

    row["post_comments"] = acts.get("comment", 0)
    row["post_saves"] = acts.get("post_save", 0)
    row["post_shares"] = acts.get("post", 0)
    row["post_engagement"] = acts.get("post_engagement", 0)
    row["post_reactions"] = acts.get("post_reaction", 0)
    row["page_likes"] = acts.get("like", 0)

    cpas_acts = FacebookService._process_actions({"actions": item.get("catalog_segment_actions", [])})
    cpas_vals = FacebookService._process_actions({"action_values": item.get("catalog_segment_value", [])})

    row["shared_purchases"] = cpas_acts.get("purchase", 0)
    row["shared_purchase_value"] = cpas_vals.get("purchase_val", 0)
    row["shared_add_to_cart"] = cpas_acts.get("add_to_cart", 0)
    row["shared_atc_value"] = cpas_vals.get("add_to_cart_val", 0)
    row["shared_view_content"] = cpas_acts.get("view_content", 0)
    row["shared_roas"] = (row["shared_purchase_value"] / row["spend"]) if row["spend"] > 0 else 0

    row["cpa"] = row["spend"] / row["purchases"] if row["purchases"] > 0 else 0
    row["cost_per_atc"] = row["spend"] / row["add_to_cart"] if row["add_to_cart"] > 0 else 0
    row["cvr"] = (row["purchases"] / row["link_clicks"] * 100) if row["link_clicks"] > 0 else 0
    row["view_to_cart"] = (row["add_to_cart"] / row["view_content"] * 100) if row["view_content"] > 0 else 0

    if row["add_to_cart"] > 0:
        row["cart_conversion"] = (row["purchases"] / row["add_to_cart"]) * 100
        row["cart_dropoff"] = (1 - (row["purchases"] / row["add_to_cart"])) * 100
    else:
        row["cart_conversion"] = 0
        row["cart_dropoff"] = 0

    row["cart_value_realization"] = (
        (row["purchase_value"] / row["atc_value"] * 100) if row["atc_value"] > 0 else 0
    )

    return row


async def get_analytics_trend(
    account_id,
    user_id,
    since,
    until,
    prev_since=None,
    prev_until=None,
    team_id=None,
    strict_token=False,
):
    """
    非同步取得廣告趨勢時間序列（並行抓取本期 & 前期，支援快取）。

    Returns:
        list[dict] | None：合併本期與前期的每日指標列表
    """
    cached = get_trend_cache(account_id, since, until, prev_since, prev_until)
    if cached is not None:
        return cached

    headers = get_headers(user_id, team_id, allow_fallback=not strict_token)
    if not headers:
        return None

    url = f"{BASE_URL}/{account_id}/insights"
    fields = (
        "spend,impressions,reach,cpm,cpc,ctr,inline_link_clicks,clicks,"
        "actions,action_values,purchase_roas,"
        "catalog_segment_value,catalog_segment_actions"
    )

    async def fetch_daily(client, s, u):
        params = {
            "fields": fields,
            "level": "account",
            "time_range": f'{{"since":"{s}","until":"{u}"}}',
            "time_increment": "1",
            "limit": 100,
        }
        try:
            response = await client.get(url, headers=headers, params=params)
            return response.json().get("data", [])
        except Exception:
            logger.error("[FB ASYNC] Error in trend fetch", exc_info=True)
            return []

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            tasks = [fetch_daily(client, since, until)]
            if prev_since and prev_until:
                tasks.append(fetch_daily(client, prev_since, prev_until))

            results = await asyncio.gather(*tasks)

        cur_data = results[0]
        prev_data = results[1] if len(results) > 1 else []

        max_len = max(len(cur_data), len(prev_data)) if prev_data else len(cur_data)
        merged = []

        for i in range(max_len):
            c_item = cur_data[i] if i < len(cur_data) else {}
            p_item = prev_data[i] if i < len(prev_data) else {}

            c_metrics = _process_daily_item(c_item)
            p_metrics = _process_daily_item(p_item)

            final_row = {
                "index": i,
                "date": c_item.get("date_start", f"Day {i + 1}"),
                "prev_date": p_item.get("date_start", ""),
            }
            for k, v in c_metrics.items():
                final_row[k] = v
            for k, v in p_metrics.items():
                final_row[f"{k}_prev"] = v

            merged.append(final_row)

        set_trend_cache(account_id, since, until, prev_since, prev_until, merged)
        return merged

    except Exception as e:
        logger.error("[FB ASYNC] Error in get_analytics_trend", exc_info=True)
        return None
