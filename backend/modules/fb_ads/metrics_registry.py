# backend/modules/fb_ads/metrics_registry.py
"""
Facebook 廣告指標註冊表（Python 版 metricsRegistry.js）。
定義所有可用指標的資料來源對應關係，並提供動態欄位建構邏輯。
"""

import sys

# ============================================================================
# METRICS REGISTRY
# ============================================================================
METRICS_REGISTRY = {
    # --- General Metrics ---
    'spend': {'source': 'direct', 'fb_field': 'spend'},
    'impressions': {'source': 'direct', 'fb_field': 'impressions'},
    'reach': {'source': 'direct', 'fb_field': 'reach'},
    'frequency': {'source': 'direct', 'fb_field': 'frequency'},
    'cpc': {'source': 'direct', 'fb_field': 'cpc'},
    'cpm': {'source': 'direct', 'fb_field': 'cpm'},
    'ctr': {'source': 'direct', 'fb_field': 'ctr'},
    'clicks': {'source': 'direct', 'fb_field': 'clicks'},
    'link_clicks': {'source': 'direct', 'fb_field': 'inline_link_clicks'},
    'unique_clicks': {'source': 'direct', 'fb_field': 'unique_clicks'},

    # --- General Cost Metrics ---
    'cpp': {'source': 'calculated'},
    'cost_per_unique_click': {'source': 'calculated'},
    'cost_per_inline_link_click': {'source': 'calculated'},
    'cost_per_outbound_click': {'source': 'calculated'},
    'cost_per_conversion': {'source': 'calculated'},
    'outbound_clicks': {'source': 'direct', 'fb_field': 'outbound_clicks'},
    'unique_ctr': {'source': 'direct', 'fb_field': 'unique_ctr'},
    'outbound_clicks_ctr': {'source': 'direct', 'fb_field': 'outbound_clicks_ctr'},
    'inline_link_click_ctr': {'source': 'direct', 'fb_field': 'inline_link_click_ctr'},
    'instant_experience_open': {'source': 'direct', 'fb_field': 'instant_experience_clicks_to_open'},
    'instant_experience_start': {'source': 'direct', 'fb_field': 'instant_experience_clicks_to_start'},

    # --- E-commerce Metrics ---
    'roas': {'source': 'purchase_roas', 'fb_field': 'purchase_roas'},
    'purchases': {'source': 'actions', 'action_type': 'purchase'},
    'purchase_value': {'source': 'action_values', 'action_type': 'purchase'},
    'cpa': {'source': 'calculated'},
    'add_to_cart': {'source': 'actions', 'action_type': 'add_to_cart'},
    'atc_value': {'source': 'action_values', 'action_type': 'add_to_cart'},
    'cost_per_atc': {'source': 'calculated'},
    'initiate_checkout': {'source': 'actions', 'action_type': 'initiate_checkout'},
    'add_payment_info': {'source': 'actions', 'action_type': 'add_payment_info'},
    'view_content': {'source': 'actions', 'action_type': 'view_content'},

    # --- Funnel Metrics (all calculated) ---
    'cvr': {'source': 'calculated'},
    'view_to_cart': {'source': 'calculated'},
    'cart_conversion': {'source': 'calculated'},
    'cart_dropoff': {'source': 'calculated'},
    'cart_value_realization': {'source': 'calculated'},

    # --- Engagement Metrics ---
    'post_comments': {'source': 'actions', 'action_type': 'comment'},
    'post_saves': {'source': 'actions', 'action_type': 'onsite_conversion.post_save'},
    'post_shares': {'source': 'actions', 'action_type': 'post'},
    'post_engagement': {'source': 'actions', 'action_type': 'post_engagement'},
    'post_reactions': {'source': 'actions', 'action_type': 'post_reaction'},
    'page_likes': {'source': 'actions', 'action_type': 'like'},

    # --- Video Metrics ---
    'video_views': {'source': 'actions', 'action_type': 'video_view'},
    'video_thruplay': {'source': 'actions', 'action_type': 'video_view'},
    'video_p25_watched': {'source': 'direct', 'fb_field': 'video_p25_watched_actions'},
    'video_p50_watched': {'source': 'direct', 'fb_field': 'video_p50_watched_actions'},
    'video_p75_watched': {'source': 'direct', 'fb_field': 'video_p75_watched_actions'},
    'video_p100_watched': {'source': 'direct', 'fb_field': 'video_p100_watched_actions'},
    'video_avg_time_watched': {'source': 'direct', 'fb_field': 'video_avg_time_watched_actions'},
    'cost_per_thruplay': {'source': 'calculated'},

    # --- Messaging Metrics ---
    'messaging_first_reply': {'source': 'actions', 'action_type': 'onsite_conversion.messaging_first_reply'},
    'messaging_conversation_started': {'source': 'actions', 'action_type': 'onsite_conversion.messaging_conversation_started_7d'},
    'cost_per_message': {'source': 'calculated'},

    # --- Lead Gen Metrics ---
    'leads': {'source': 'actions', 'action_type': 'lead'},
    'cost_per_lead': {'source': 'calculated'},
    'onsite_leads': {'source': 'actions', 'action_type': 'onsite_conversion.lead_grouped'},

    # --- App Metrics ---
    'app_installs': {'source': 'actions', 'action_type': 'mobile_app_install'},
    'cost_per_install': {'source': 'calculated'},
    'app_events': {'source': 'actions', 'action_type': 'app_custom_event'},

    # --- Quality Metrics ---
    'quality_ranking': {'source': 'direct', 'fb_field': 'quality_ranking'},
    'engagement_rate_ranking': {'source': 'direct', 'fb_field': 'engagement_rate_ranking'},
    'conversion_rate_ranking': {'source': 'direct', 'fb_field': 'conversion_rate_ranking'},

    # --- CPAS Metrics ---
    'shared_purchases': {'source': 'catalog_segment_actions', 'action_type': 'purchase'},
    'shared_purchase_value': {'source': 'catalog_segment_value', 'action_type': 'purchase'},
    'shared_roas': {'source': 'calculated'},
    'shared_add_to_cart': {'source': 'catalog_segment_actions', 'action_type': 'add_to_cart'},
    'shared_atc_value': {'source': 'catalog_segment_value', 'action_type': 'add_to_cart'},
    'shared_view_content': {'source': 'catalog_segment_actions', 'action_type': 'view_content'},
}


def build_fb_fields(custom_fields: str = None, level: str = "account") -> str:
    """
    依照請求的 custom_fields 動態建構 Facebook API fields 字串。

    Args:
        custom_fields: 逗號分隔的指標鍵值（e.g. "spend,roas,video_p25_watched"）
        level: 分析層級（account / campaign / adset / ad）

    Returns:
        逗號分隔的 Facebook API fields 字串；若無 custom_fields 則回傳 None（使用預設欄位）
    """
    base_structure = [
        "campaign_id", "adset_id", "ad_id",
        "campaign_name", "adset_name", "ad_name",
    ]

    if not custom_fields:
        return None  # 通知呼叫方使用原有硬編碼欄位

    requested_keys = [k.strip() for k in custom_fields.split(",") if k.strip()]

    fb_fields = set(base_structure)
    needs_actions = False
    needs_action_values = False
    needs_purchase_roas = False
    needs_catalog_segment_actions = False
    needs_catalog_segment_value = False

    for key in requested_keys:
        if key not in METRICS_REGISTRY:
            print(f"[WARN] Unknown metric key: {key}", file=sys.stderr)
            continue

        metric = METRICS_REGISTRY[key]
        source = metric.get('source')

        if source == 'direct':
            fb_field = metric.get('fb_field')
            if fb_field:
                # 品質排名指標僅在 ad 層級可用
                if fb_field in ["quality_ranking", "engagement_rate_ranking", "conversion_rate_ranking"]:
                    if level == "ad":
                        fb_fields.add(fb_field)
                else:
                    fb_fields.add(fb_field)
        elif source == 'actions':
            needs_actions = True
        elif source == 'action_values':
            needs_action_values = True
        elif source == 'purchase_roas':
            needs_purchase_roas = True
        elif source == 'catalog_segment_actions':
            needs_catalog_segment_actions = True
        elif source == 'catalog_segment_value':
            needs_catalog_segment_value = True
        # 'calculated' 指標不需要額外欄位（由其他指標計算得出）

    if needs_actions:
        fb_fields.add("actions")
    if needs_action_values:
        fb_fields.add("action_values")
    if needs_purchase_roas:
        fb_fields.add("purchase_roas")
    if needs_catalog_segment_actions:
        fb_fields.add("catalog_segment_actions")
    if needs_catalog_segment_value:
        fb_fields.add("catalog_segment_value")

    result = ",".join(fb_fields)
    print(f"[FB DYNAMIC] Built fields: {result}", file=sys.stderr)
    return result
