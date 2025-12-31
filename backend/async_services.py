"""
Async Facebook Service Module
Provides async API calls to Facebook Graph API with caching support.
Uses httpx for async HTTP requests.
"""
import httpx
import asyncio
from datetime import datetime, timedelta
from auth import TokenManager
import sys
from cache import (
    get_account_cache, set_account_cache,
    get_insights_cache, set_insights_cache,
    get_analytics_cache, set_analytics_cache,
    get_trend_cache, set_trend_cache
)


# ============================================================================
# METRICS REGISTRY - Python version of frontend metricsRegistry.js
# Used for dynamic field building when custom fields are requested
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
    'cost_per_thruplay': {'source': 'direct', 'fb_field': 'cost_per_thruplay'},
    
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


def build_fb_fields(custom_fields: str = None) -> str:
    """
    Build Facebook API fields string based on requested custom fields.
    
    Args:
        custom_fields: Comma-separated list of metric keys (e.g., "spend,roas,video_p25_watched")
    
    Returns:
        Comma-separated string of Facebook API fields to request
    """
    # Base fields always included for structure (IDs and names)
    base_structure = [
        "campaign_id", "adset_id", "ad_id",
        "campaign_name", "adset_name", "ad_name"
    ]
    
    if not custom_fields:
        # Return default fields (backward compatible)
        return None  # Signal to use original hardcoded fields
    
    requested_keys = [k.strip() for k in custom_fields.split(",") if k.strip()]
    
    # Collect Facebook API fields based on requested metrics
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
        # 'calculated' metrics don't need additional fields (derived from other metrics)
    
    # Add aggregate fields as needed
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


class AsyncFacebookService:
    BASE_URL = "https://graph.facebook.com/v24.0"
    TIMEOUT = 30.0

    @staticmethod
    def get_headers(user_id, team_id=None, allow_fallback=True):
        """Get authorization headers (sync - uses existing TokenManager)"""
        if team_id:
            token = TokenManager.get_team_token(team_id)
        else:
            token = TokenManager.get_user_token(user_id, allow_fallback=allow_fallback)
        
        if not token:
            return None
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    async def get_all_ad_accounts(user_id, team_id=None, strict_token=False):
        """
        Async version of get_all_ad_accounts with caching.
        Returns a list of dicts: {'id': 'act_123', 'name': 'My Account'}
        """
        # Check cache first
        cached = get_account_cache(user_id, team_id)
        if cached is not None:
            return cached, None

        headers = AsyncFacebookService.get_headers(user_id, team_id, allow_fallback=not strict_token)
        if not headers:
            print("[FB ASYNC] get_all_ad_accounts: No token available", file=sys.stderr)
            return [], "No access token found for this user."

        url = f"{AsyncFacebookService.BASE_URL}/me/adaccounts"
        params = {
            "fields": "name,account_id",
            "limit": 100
        }

        try:
            print(f"[FB ASYNC] Fetching Ad Accounts...", file=sys.stderr)
            async with httpx.AsyncClient(timeout=AsyncFacebookService.TIMEOUT) as client:
                response = await client.get(url, headers=headers, params=params)
                print(f"[FB ASYNC] Response Status: {response.status_code}", file=sys.stderr)
                data = response.json()

            if "error" in data:
                print(f"Facebook API Error: {data['error']}", file=sys.stderr)
                return [], data["error"].get("message")

            accounts = data.get("data", [])
            formatted = [
                {"id": acc.get("id"), "name": acc.get("name", "Unknown Account")}
                for acc in accounts
            ]
            formatted.sort(key=lambda x: x["name"])
            
            # Store in cache
            set_account_cache(user_id, team_id, formatted)
            
            return formatted, None

        except Exception as e:
            print(f"[FB ASYNC] Error in get_all_ad_accounts", file=sys.stderr)
            return [], str(e)

    @staticmethod
    async def get_account_insights(account_id, user_id, days=7, team_id=None, strict_token=False):
        """
        Async version of get_account_insights with parallel fetching.
        """
        # Check cache
        cached = get_insights_cache(account_id, days)
        if cached is not None:
            return cached

        headers = AsyncFacebookService.get_headers(user_id, team_id, allow_fallback=not strict_token)
        if not headers:
            return None
            
        date_preset = "last_7d" if days == 7 else "last_30d"
        fields = (
            "spend,impressions,reach,cpm,cpc,ctr,inline_link_clicks,clicks,"
            "actions,action_values,purchase_roas"
        )
        
        url = f"{AsyncFacebookService.BASE_URL}/{account_id}/insights"
        
        current_params = {
            "fields": fields,
            "date_preset": date_preset,
            "level": "account"
        }
        
        try:
            async with httpx.AsyncClient(timeout=AsyncFacebookService.TIMEOUT) as client:
                # Fetch current data first to get date range
                cur_response = await client.get(url, headers=headers, params=current_params)
                cur_res = cur_response.json()
                
                if "error" in cur_res:
                    print(f"[FB ASYNC] API Error in insights", file=sys.stderr)
                    return None
                    
                cur_data_list = cur_res.get("data", [])
                cur_data = cur_data_list[0] if cur_data_list else {}
                
                # Calculate date range
                date_start = cur_data.get("date_start")
                date_stop = cur_data.get("date_stop")
                fmt = "%Y-%m-%d"
                
                if not date_start or not date_stop:
                    today = datetime.now()
                    d_stop = today - timedelta(days=1)
                    d_start = d_stop - timedelta(days=days-1)
                    date_start = d_start.strftime(fmt)
                    date_stop = d_stop.strftime(fmt)
                    cur_data["date_start"] = date_start
                    cur_data["date_stop"] = date_stop

                d_start = datetime.strptime(date_start, fmt)
                d_stop = datetime.strptime(date_stop, fmt)
                delta = d_stop - d_start + timedelta(days=1)
                
                prev_start = (d_start - delta).strftime(fmt)
                prev_stop = (d_start - timedelta(days=1)).strftime(fmt)
                
                prev_params = {
                    "fields": fields,
                    "level": "account",
                    "time_range": f'{{"since":"{prev_start}","until":"{prev_stop}"}}'
                }
                
                trend_fields = (
                    "spend,impressions,inline_link_clicks,ctr,cpc,"
                    "actions,action_values,purchase_roas"
                )
                trend_params = {
                    "fields": trend_fields,
                    "date_preset": date_preset,
                    "time_increment": "1",
                    "level": "account"
                }

                # Parallel fetch: previous data + trend data
                prev_task = client.get(url, headers=headers, params=prev_params)
                trend_task = client.get(url, headers=headers, params=trend_params)
                
                prev_response, trend_response = await asyncio.gather(prev_task, trend_task)
                
                prev_res = prev_response.json()
                trend_res = trend_response.json()

            prev_data_list = prev_res.get("data", [])
            prev_data = prev_data_list[0] if prev_data_list else {}
            trend_list = trend_res.get("data", [])

            # Import processing functions from sync service
            from services import FacebookService
            
            result = {
                "kpi": FacebookService._format_kpi(cur_data, prev_data),
                "charts": FacebookService._format_charts(trend_list),
                "date_range": {
                    "start": date_start,
                    "stop": date_stop
                }
            }
            
            # Store in cache
            set_insights_cache(account_id, days, result)
            
            return result

        except Exception as e:
            print(f"[FB ASYNC] Error fetching insights", file=sys.stderr)
            return None

    @staticmethod
    async def get_custom_report(account_id, user_id, since, until, level="account", team_id=None, custom_fields=None, strict_token=False):
        """
        Async version of get_custom_report with caching.
        
        Args:
            account_id: Facebook Ad Account ID
            user_id: Google User ID for authentication
            since: Start date (YYYY-MM-DD)
            until: End date (YYYY-MM-DD)
            level: Analysis level (account/campaign/adset/ad)
            team_id: Optional team ID for team-scoped token
            custom_fields: Optional comma-separated list of metric keys for dynamic field selection
            strict_token: If True, blocks fallback to Admin Token (Prevents data leak)
        """
        # Build cache key including custom_fields for proper cache isolation
        cache_key_suffix = f"_{custom_fields}" if custom_fields else ""
        cached = get_analytics_cache(account_id, since, until, level + cache_key_suffix)
        if cached is not None:
            return cached

        headers = AsyncFacebookService.get_headers(user_id, team_id, allow_fallback=not strict_token)
        if not headers:
            return None
        
        # Determine which fields to request from Facebook API
        try:
            with open("debug_fields.log", "a") as f:
                f.write(f"[{datetime.now()}] Requesting fields: {custom_fields}\n")
        except: pass

        dynamic_fields = build_fb_fields(custom_fields)
        
        if dynamic_fields:
            # Use dynamically built fields
            api_fields = dynamic_fields
            print(f"[FB ASYNC] Using DYNAMIC fields: {api_fields[:100]}...", file=sys.stderr)
        else:
            # Use default hardcoded fields (backward compatible)
            api_fields = (
                "campaign_id,adset_id,ad_id,"
                "campaign_name,adset_name,ad_name,"
                "spend,impressions,reach,frequency,cpm,cpc,ctr,inline_link_clicks,clicks,unique_clicks,"  # Added frequency, unique_clicks
                "actions,action_values,purchase_roas,"
                "quality_ranking,engagement_rate_ranking,conversion_rate_ranking,"
                "catalog_segment_value,catalog_segment_actions,"
                "video_p25_watched_actions,video_p50_watched_actions,video_p75_watched_actions,video_p100_watched_actions,"
                "video_avg_time_watched_actions,cost_per_thruplay"
            )

        url = f"{AsyncFacebookService.BASE_URL}/{account_id}/insights"
        
        params = {
            "fields": api_fields,
            "level": level,
            "time_range": f'{{"since":"{since}","until":"{until}"}}',
            "time_increment": "all_days",
            "limit": 500
        }
        
        try:
            async with httpx.AsyncClient(timeout=AsyncFacebookService.TIMEOUT) as client:
                # Parallel fetch: insights + ad metadata (if level is ad)
                insights_task = client.get(url, headers=headers, params=params)
                
                ad_meta_task = None
                if level == "ad":
                    c_url = f"{AsyncFacebookService.BASE_URL}/{account_id}/ads"
                    c_params = {
                        "fields": "id,effective_status,creative{thumbnail_url,image_url}",
                        "limit": 1000 
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
                print(f"[FB ASYNC] API Error (Report)", file=sys.stderr)
                return None
                
            data = res.get("data", [])
            print(f"[FB ASYNC] Report: Level={level} Rows={len(data)}", file=sys.stderr)
            
            # Build ad metadata map
            ad_meta_map = {}
            for ad in ad_meta_data:
                creative = ad.get("creative", {})
                img = creative.get("image_url") or creative.get("thumbnail_url")
                ad_meta_map[ad["id"]] = {
                    "image_url": img,
                    "status": ad.get("effective_status", "UNKNOWN")
                }

            # Import processing function from sync service
            from services import FacebookService
            
            processed_rows = []
            for row in data:
                # Determine Name based on Level
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
                    name = row.get("campaign_name") or row.get("adset_name") or row.get("ad_name") or "Unknown"

                meta = ad_meta_map.get(row.get("ad_id"), {}) if level == "ad" else {}

                flat = {
                    "id": row_id or row.get("campaign_id") or row.get("adset_id") or row.get("ad_id") or "total",
                    "campaign_id": row.get("campaign_id"), 
                    "adset_id": row.get("adset_id"),
                    "ad_id": row.get("ad_id"),
                    "name": name,
                    "spend": float(row.get("spend", 0)),
                    "impressions": int(row.get("impressions", 0)),
                    "reach": int(row.get("reach", 0)),
                    "frequency": float(row.get("frequency", 0)),  # NEW
                    "clicks": int(row.get("clicks", 0)),
                    "link_clicks": int(row.get("inline_link_clicks", 0)),
                    "unique_clicks": int(row.get("unique_clicks", 0)),  # NEW
                    "ctr": float(row.get("ctr", 0)),
                    "cpc": float(row.get("cpc", 0)),
                    "cpm": float(row.get("cpm", 0)),
                    "roas": float(row.get("purchase_roas", [{}])[0].get("value", 0) if row.get("purchase_roas") else 0),
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

                # Video Metrics Processing
                # video_views and video_thruplay come from actions array
                flat["video_views"] = acts.get("video_view", 0)
                flat["video_thruplay"] = acts.get("video_view", 0)  # ThruPlay is also video_view action type
                
                # Video percentage watched metrics (special format: array with value field)
                def get_video_metric(field_name):
                    """Extract value from video metric array format"""
                    video_data = row.get(field_name, [])
                    if isinstance(video_data, list) and len(video_data) > 0:
                        return int(video_data[0].get("value", 0))
                    return 0
                
                flat["video_p25_watched"] = get_video_metric("video_p25_watched_actions")
                flat["video_p50_watched"] = get_video_metric("video_p50_watched_actions")
                flat["video_p75_watched"] = get_video_metric("video_p75_watched_actions")
                flat["video_p100_watched"] = get_video_metric("video_p100_watched_actions")
                
                # Video average time watched (in seconds, special format)
                video_avg_data = row.get("video_avg_time_watched_actions", [])
                if isinstance(video_avg_data, list) and len(video_avg_data) > 0:
                    flat["video_avg_time_watched"] = float(video_avg_data[0].get("value", 0))
                else:
                    flat["video_avg_time_watched"] = 0
                
                # Cost per ThruPlay
                flat["cost_per_thruplay"] = float(row.get("cost_per_thruplay", [{}])[0].get("value", 0) if row.get("cost_per_thruplay") else 0)
                
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

                # --- NEW COST & SPEND METRICS (Backfill for Table) ---
                # CPP (Cost per 1000 People Reached)
                if flat["reach"] > 0:
                    flat["cpp"] = (flat["spend"] / flat["reach"]) * 1000
                else:
                    flat["cpp"] = float(row.get("cpp", 0))

                # Cost Per Unique Click
                if flat["unique_clicks"] > 0:
                    flat["cost_per_unique_click"] = flat["spend"] / flat["unique_clicks"]
                else:
                    flat["cost_per_unique_click"] = float(row.get("cost_per_unique_click", 0))

                # Cost Per Inline Link Click
                if flat["link_clicks"] > 0:
                    flat["cost_per_inline_link_click"] = flat["spend"] / flat["link_clicks"]
                else:
                    flat["cost_per_inline_link_click"] = float(row.get("cost_per_inline_link_click", 0))

                # Cost Per Outbound Click
                # Outbound clicks usually come from actions list with type 'outbound_click'
                # But 'outbound_clicks' field might be available in top level for some versions or aggregated views
                # We check actions first
                outbound_clicks = acts.get("outbound_click", 0) 
                if outbound_clicks == 0:
                     # fallback to checking top level if it exists (though rare for this specific key format in actions)
                     outbound_clicks_list = row.get("outbound_clicks", [])
                     if isinstance(outbound_clicks_list, list) and outbound_clicks_list:
                         outbound_clicks = int(outbound_clicks_list[0].get("value", 0))
                
                flat["outbound_clicks"] = outbound_clicks
                
                if outbound_clicks > 0:
                    flat["cost_per_outbound_click"] = flat["spend"] / outbound_clicks
                else:
                     flat["cost_per_outbound_click"] = float(row.get("cost_per_outbound_click", [{}])[0].get("value", 0) if isinstance(row.get("cost_per_outbound_click"), list) else row.get("cost_per_outbound_click", 0))

                # Cost Per Conversion (CPA) - Already calculated as 'cpa' above, but mapping to key expected by frontend 'cost_per_conversion'
                flat["cost_per_conversion"] = flat["cpa"]

                # Social Spend
                flat["social_spend"] = float(row.get("social_spend", 0))

                # Cost per ThruPlay is already handled above at line 571, but ensuring consistency
                # (Line 571: flat["cost_per_thruplay"] = ...)

                processed_rows.append(flat)
            
            # Store in cache (include custom_fields in key)
            set_analytics_cache(account_id, since, until, level + cache_key_suffix, processed_rows)
            
            return processed_rows

        except Exception as e:
            print(f"[FB ASYNC] Error fetching custom report", file=sys.stderr)
            return None

    @staticmethod
    async def get_analytics_trend(account_id, user_id, since, until, prev_since=None, prev_until=None, team_id=None, strict_token=False):
        """
        Async version of get_analytics_trend with parallel fetching.
        """
        # Check cache
        cached = get_trend_cache(account_id, since, until, prev_since, prev_until)
        if cached is not None:
            return cached

        headers = AsyncFacebookService.get_headers(user_id, team_id, allow_fallback=not strict_token)
        if not headers:
            return None

        url = f"{AsyncFacebookService.BASE_URL}/{account_id}/insights"
        
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
                "limit": 100
            }
            try:
                response = await client.get(url, headers=headers, params=params)
                return response.json().get("data", [])
            except Exception as e:
                print(f"[FB ASYNC] Error in trend fetch", file=sys.stderr)
                return []

        try:
            async with httpx.AsyncClient(timeout=AsyncFacebookService.TIMEOUT) as client:
                # Parallel fetch: current and previous
                tasks = [fetch_daily(client, since, until)]
                if prev_since and prev_until:
                    tasks.append(fetch_daily(client, prev_since, prev_until))
                
                results = await asyncio.gather(*tasks)
                
                cur_data = results[0]
                prev_data = results[1] if len(results) > 1 else []

            # Import processing function from sync service
            from services import FacebookService
            
            def process_daily_item(item):
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
                    "roas": float(item.get("purchase_roas", [{}])[0].get("value", 0) if item.get("purchase_roas") else 0),
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
                
                row["cart_value_realization"] = (row["purchase_value"] / row["atc_value"] * 100) if row["atc_value"] > 0 else 0

                return row

            max_len = max(len(cur_data), len(prev_data)) if prev_data else len(cur_data)
            merged = []

            for i in range(max_len):
                c_item = cur_data[i] if i < len(cur_data) else {}
                p_item = prev_data[i] if i < len(prev_data) else {}
                
                c_metrics = process_daily_item(c_item)
                p_metrics = process_daily_item(p_item)
                
                final_row = {
                    "index": i,
                    "date": c_item.get("date_start", f"Day {i+1}"),
                    "prev_date": p_item.get("date_start", ""),
                }
                
                for k, v in c_metrics.items():
                    final_row[k] = v
                    
                for k, v in p_metrics.items():
                    final_row[f"{k}_prev"] = v

                merged.append(final_row)

            # Store in cache
            set_trend_cache(account_id, since, until, prev_since, prev_until, merged)
            
            return merged

        except Exception as e:
            print(f"[FB ASYNC] Error in get_analytics_trend", file=sys.stderr)
            return None
