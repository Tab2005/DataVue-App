# backend/modules/fb_ads/analytics_service.py
"""
自訂報告（Custom Report）服務。
對應原 AsyncFacebookService.get_custom_report。
"""

import sys
import asyncio
import logging
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

from cache import get_analytics_cache, set_analytics_cache
from modules.fb_ads._base import BASE_URL, TIMEOUT, get_headers
from modules.fb_ads.metrics_registry import build_fb_fields


def _process_flat_row(row: dict, level: str, ad_meta_map: dict) -> dict:
    """將原始 Facebook API 資料列轉換為扁平化字典"""
    from services import FacebookService

    # 判斷名稱與 ID
    name = "Account Total"
    row_id = "total"

    if level == "ad":
        name = row.get("ad_name")
        row_id = row.get("ad_id")
    elif level == "adset":
        name = row.get("adset_name")
        row_id = row.get("adset_id")
    elif level == "campaign":
        name = row.get("campaign_name")
        row_id = row.get("campaign_id")

    if not name:
        name = (
            row.get("campaign_name") or row.get("adset_name")
            or row.get("ad_name") or "Unknown"
        )

    # 根據層級取得對應的元數據 (狀態與圖片)
    lookup_id = row_id
    if level == "ad":
        lookup_id = row.get("ad_id")
    elif level == "adset":
        lookup_id = row.get("adset_id")
    elif level == "campaign":
        lookup_id = row.get("campaign_id")

    meta = ad_meta_map.get(lookup_id, {})

    flat = {
        "id": row_id or row.get("campaign_id") or row.get("adset_id") or row.get("ad_id") or "total",
        "campaign_id": row.get("campaign_id"),
        "adset_id": row.get("adset_id"),
        "ad_id": row.get("ad_id"),
        "name": name,
        "spend": float(row.get("spend", 0)),
        "impressions": int(row.get("impressions", 0)),
        "reach": int(row.get("reach", 0)),
        "frequency": float(row.get("frequency", 0)),
        "clicks": int(row.get("clicks", 0)),
        "link_clicks": int(row.get("inline_link_clicks", 0)),
        "unique_clicks": int(row.get("unique_clicks", 0)),
        "ctr": float(row.get("ctr", 0)),
        "cpc": float(row.get("cpc", 0)),
        "cpm": float(row.get("cpm", 0)),
        "roas": float(
            row.get("purchase_roas", [{}])[0].get("value", 0)
            if row.get("purchase_roas") else 0
        ),
        "image_url": meta.get("image_url"),
        "quality_ranking": row.get("quality_ranking", "-"),
        "engagement_rate_ranking": row.get("engagement_rate_ranking", "-"),
        "conversion_rate_ranking": row.get("conversion_rate_ranking", "-"),
        "objective": row.get("objective", "-"),
        "status": meta.get("status", "UNKNOWN"),
    }

    acts = FacebookService._process_actions(row)

    flat["view_content"] = acts.get("view_content", 0)
    flat["add_to_cart"] = acts.get("add_to_cart", 0)
    flat["initiate_checkout"] = acts.get("initiate_checkout", 0)
    flat["add_payment_info"] = acts.get("add_payment_info", 0)
    flat["purchases"] = acts.get("purchase", 0)
    flat["purchase_value"] = acts.get("purchase_val", 0)
    flat["atc_value"] = acts.get("add_to_cart_val", 0)

    flat["post_comments"] = acts.get("comment", 0)
    flat["post_saves"] = acts.get("post_save", 0)
    flat["post_shares"] = acts.get("post", 0)
    flat["post_engagement"] = acts.get("post_engagement", 0)
    flat["post_reactions"] = acts.get("post_reaction", 0)
    flat["page_likes"] = acts.get("like", 0)

    cpas_acts = FacebookService._process_actions({"actions": row.get("catalog_segment_actions", [])})
    cpas_vals = FacebookService._process_actions({"action_values": row.get("catalog_segment_value", [])})

    flat["shared_purchases"] = cpas_acts.get("purchase", 0)
    flat["shared_purchase_value"] = cpas_vals.get("purchase_val", 0)
    flat["shared_add_to_cart"] = cpas_acts.get("add_to_cart", 0)
    flat["shared_atc_value"] = cpas_vals.get("add_to_cart_val", 0)
    flat["shared_view_content"] = cpas_acts.get("view_content", 0)
    flat["shared_roas"] = (flat["shared_purchase_value"] / flat["spend"]) if flat["spend"] > 0 else 0

    flat["cpa"] = flat["spend"] / flat["purchases"] if flat["purchases"] > 0 else 0
    flat["cost_per_atc"] = flat["spend"] / flat["add_to_cart"] if flat["add_to_cart"] > 0 else 0
    flat["cvr"] = (flat["purchases"] / flat["link_clicks"] * 100) if flat["link_clicks"] > 0 else 0
    flat["view_to_cart"] = (flat["add_to_cart"] / flat["view_content"] * 100) if flat["view_content"] > 0 else 0

    if flat["add_to_cart"] > 0:
        flat["cart_conversion"] = (flat["purchases"] / flat["add_to_cart"]) * 100
        flat["cart_dropoff"] = (1 - (flat["purchases"] / flat["add_to_cart"])) * 100
    else:
        flat["cart_conversion"] = 0
        flat["cart_dropoff"] = 0

    flat["cart_value_realization"] = (flat["purchase_value"] / flat["atc_value"] * 100) if flat["atc_value"] > 0 else 0

    # Video Metrics
    flat["video_views"] = acts.get("video_view", 0)
    flat["video_thruplay"] = acts.get("video_view", 0)

    def get_video_metric(field_name):
        video_data = row.get(field_name, [])
        if isinstance(video_data, list) and len(video_data) > 0:
            return int(video_data[0].get("value", 0))
        return 0

    flat["video_p25_watched"] = get_video_metric("video_p25_watched_actions")
    flat["video_p50_watched"] = get_video_metric("video_p50_watched_actions")
    flat["video_p75_watched"] = get_video_metric("video_p75_watched_actions")
    flat["video_p100_watched"] = get_video_metric("video_p100_watched_actions")

    video_avg_data = row.get("video_avg_time_watched_actions", [])
    flat["video_avg_time_watched"] = (
        float(video_avg_data[0].get("value", 0))
        if isinstance(video_avg_data, list) and video_avg_data else 0
    )

    flat["cost_per_thruplay"] = float(
        row.get("cost_per_thruplay", [{}])[0].get("value", 0)
        if row.get("cost_per_thruplay") else 0
    )

    # Messaging Metrics
    flat["messaging_first_reply"] = acts.get("onsite_conversion.messaging_first_reply", 0)
    flat["messaging_conversation_started"] = acts.get("onsite_conversion.messaging_conversation_started_7d", 0)
    flat["cost_per_message"] = flat["spend"] / flat["messaging_first_reply"] if flat["messaging_first_reply"] > 0 else 0

    # Lead Metrics
    flat["leads"] = acts.get("lead", 0)
    flat["onsite_leads"] = acts.get("onsite_conversion.lead_grouped", 0)
    flat["cost_per_lead"] = flat["spend"] / flat["leads"] if flat["leads"] > 0 else 0

    # App Metrics
    flat["app_installs"] = acts.get("mobile_app_install", 0)
    flat["app_events"] = acts.get("app_custom_event", 0)
    flat["cost_per_install"] = flat["spend"] / flat["app_installs"] if flat["app_installs"] > 0 else 0

    # Derivative Cost Metrics
    flat["cpp"] = (flat["spend"] / flat["reach"]) * 1000 if flat["reach"] > 0 else 0
    flat["cost_per_unique_click"] = flat["spend"] / flat["unique_clicks"] if flat["unique_clicks"] > 0 else 0
    flat["cost_per_inline_link_click"] = flat["spend"] / flat["link_clicks"] if flat["link_clicks"] > 0 else 0

    # Outbound Clicks
    outbound_clicks = 0
    outbound_clicks_list = row.get("outbound_clicks", [])
    if isinstance(outbound_clicks_list, list) and outbound_clicks_list:
        outbound_clicks = int(outbound_clicks_list[0].get("value", 0))
    if outbound_clicks == 0:
        outbound_clicks = acts.get("outbound_click", 0)
    flat["outbound_clicks"] = outbound_clicks
    flat["cost_per_outbound_click"] = flat["spend"] / outbound_clicks if outbound_clicks > 0 else 0

    flat["unique_ctr"] = float(row.get("unique_ctr", 0))
    flat["inline_link_click_ctr"] = float(row.get("inline_link_click_ctr", 0))

    ob_ctr = row.get("outbound_clicks_ctr", [])
    flat["outbound_clicks_ctr"] = (
        float(ob_ctr[0].get("value", 0)) if isinstance(ob_ctr, list) and ob_ctr
        else float(ob_ctr or 0)
    )

    flat["instant_experience_open"] = int(row.get("instant_experience_clicks_to_open", 0))
    flat["instant_experience_start"] = int(row.get("instant_experience_clicks_to_start", 0))
    flat["cost_per_conversion"] = flat["cpa"]
    flat["social_spend"] = float(row.get("social_spend", 0))

    return flat


async def get_custom_report(
    account_id,
    user_id,
    since,
    until,
    level="account",
    team_id=None,
    custom_fields=None,
    strict_token=False,
    ad_id=None,
):
    """
    非同步取得自訂廣告報告（含快取、動態欄位選擇）。

    Args:
        account_id: Facebook Ad Account ID
        user_id: Google User ID（用於認證）
        since: 開始日期（YYYY-MM-DD）
        until: 結束日期（YYYY-MM-DD）
        level: 分析層級（account / campaign / adset / ad）
        team_id: 可選的團隊 ID
        custom_fields: 可選，逗號分隔的指標鍵值
        strict_token: True 則禁止 Fallback 至管理員 Token
        ad_id: 可選，指定特定廣告 ID 進行專屬查詢
    """
    cache_key_suffix = f"_{custom_fields}" if custom_fields else ""
    cached = None if ad_id else get_analytics_cache(account_id, since, until, level + cache_key_suffix)
    if cached is not None:
        return cached

    headers = get_headers(user_id, team_id, allow_fallback=not strict_token)
    if not headers:
        return None

    try:
        with open("debug_fields.log", "a") as f:
            f.write(f"[{datetime.now()}] Requesting fields: {custom_fields}\n")
    except Exception:
        pass

    dynamic_fields = build_fb_fields(custom_fields, level=level)

    if dynamic_fields:
        api_fields = dynamic_fields
        logger.debug(f"[FB ASYNC] Using DYNAMIC fields: {api_fields[:100]}...")
    else:
        api_fields = (
            "campaign_id,adset_id,ad_id,"
            "campaign_name,adset_name,ad_name,"
            "spend,impressions,reach,frequency,cpm,cpc,ctr,inline_link_clicks,clicks,unique_clicks,"
            "unique_ctr,inline_link_click_ctr,outbound_clicks,outbound_clicks_ctr,"
            "instant_experience_clicks_to_open,instant_experience_clicks_to_start,"
            "actions,action_values,purchase_roas,"
            "catalog_segment_value,catalog_segment_actions,"
            "video_p25_watched_actions,video_p50_watched_actions,video_p75_watched_actions,"
            "video_p100_watched_actions,video_avg_time_watched_actions"
        )
        if level == "ad":
            api_fields += ",quality_ranking,engagement_rate_ranking,conversion_rate_ranking"

    if ad_id:
        url = f"{BASE_URL}/{ad_id}/insights"
    else:
        url = f"{BASE_URL}/{account_id}/insights"

    params = {
        "fields": api_fields,
        "level": level,
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "time_increment": "all_days",
        "limit": 500,
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            insights_task = client.get(url, headers=headers, params=params)

            ad_meta_task = None
            if level == "ad":
                c_url = f"{BASE_URL}/{account_id}/ads"
                c_params = {
                    "fields": "id,effective_status,creative{thumbnail_url,image_url}",
                    "limit": 1000,
                }
                ad_meta_task = client.get(c_url, headers=headers, params=c_params)
            elif level == "adset":
                c_url = f"{BASE_URL}/{account_id}/adsets"
                c_params = {
                    "fields": "id,effective_status",
                    "limit": 1000,
                }
                ad_meta_task = client.get(c_url, headers=headers, params=c_params)
            elif level == "campaign":
                c_url = f"{BASE_URL}/{account_id}/campaigns"
                c_params = {
                    "fields": "id,effective_status",
                    "limit": 1000,
                }
                ad_meta_task = client.get(c_url, headers=headers, params=c_params)

            if ad_meta_task:
                insights_response, ad_meta_response = await asyncio.gather(
                    insights_task, ad_meta_task
                )
                ad_meta_data = ad_meta_response.json().get("data", [])
            else:
                insights_response = await insights_task
                ad_meta_data = []

            res = insights_response.json()

        if "error" in res:
            logger.error("[FB ASYNC] API Error (Report)")
            return None

        data = res.get("data", [])
        logger.info(f"[FB ASYNC] Report: Level={level} Rows={len(data)}")

        # 建立廣告素材元資料對應表
        ad_meta_map = {}
        for ad in ad_meta_data:
            creative = ad.get("creative", {})
            img = creative.get("image_url") or creative.get("thumbnail_url")
            ad_meta_map[ad["id"]] = {
                "image_url": img,
                "status": ad.get("effective_status", "UNKNOWN"),
            }

        processed_rows = [_process_flat_row(row, level, ad_meta_map) for row in data]

        if not ad_id:
            set_analytics_cache(account_id, since, until, level + cache_key_suffix, processed_rows)
        return processed_rows

    except Exception as e:
        logger.error("[FB ASYNC] Error fetching custom report", exc_info=True)
        return None
