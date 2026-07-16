"""Deprecated synchronous Facebook Ads service compatibility layer.

Runtime routes use modules.fb_ads via async_services; this class is kept for
legacy maintenance scripts and for helper-method compatibility.
"""

import requests
import logging
from datetime import datetime, timedelta
from modules.auth.service import TokenManager
from modules.fb_ads.actions_parsing import (
    calculate_change,
    format_charts,
    format_kpi,
    get_video_action_value,
    process_actions,
)

logger = logging.getLogger(__name__)

class FacebookService:
    BASE_URL = "https://graph.facebook.com/v24.0"

    @staticmethod
    def get_headers(user_id, team_id=None, allow_fallback=True):
        if team_id:
            token = TokenManager.get_team_token(team_id)
        else:
            token = TokenManager.get_user_token(user_id, allow_fallback=allow_fallback)
        
        if not token:
            return None
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def get_all_ad_accounts(user_id, team_id=None, strict_token=False):
        """
        Fetches all ad accounts for the dropdown selector.
        Returns a list of dicts: {'id': 'act_123', 'name': 'My Account'}
        strict_token: If True, blocks fallback to Admin Token (Prevents data leak)
        """
        headers = FacebookService.get_headers(user_id, team_id, allow_fallback=not strict_token)
        if not headers:
            logger.warning("[FB] get_all_ad_accounts: No token available")
            return [], "No access token found for this user."

        url = f"{FacebookService.BASE_URL}/me/adaccounts"
        params = {
            "fields": "name,account_id",
            "limit": 100
        }

        try:
            logger.info("[FB] Fetching Ad Accounts...")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            logger.debug(f"[FB] Response Status: {response.status_code}")
            data = response.json()
            # print(f"Facebook API Response Body: {data}", file=sys.stderr) # Debug only

            if "error" in data:
                logger.error(f"[FB] API Error: {data['error'].get('message', 'Unknown error')}")
                return [], data["error"].get("message")

            accounts = data.get("data", [])
            # Format nicely
            formatted = [
                {"id": acc.get("id"), "name": acc.get("name", "Unknown Account")}
                for acc in accounts
            ]
            # Sort by name
            formatted.sort(key=lambda x: x["name"])
            return formatted, None

        except Exception as e:
            return [], str(e)

    @staticmethod
    def get_account_insights(account_id, user_id, days=7, team_id=None):
        """
        Fetches insights for the given account with comparison data.
        """
        headers = FacebookService.get_headers(user_id, team_id)
        if not headers:
            try:
                with open("debug_insights_error.log", "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now()}] Missing Headers for {account_id}\n")
            except: pass
            return None
            
        # Determine Date Presets
        date_preset = "last_7d" if days == 7 else "last_30d"
        
        # Fields to fetch
        fields = (
            "spend,impressions,reach,cpm,cpc,ctr,inline_link_clicks,clicks,unique_clicks,unique_ctr,"
            "inline_link_click_ctr,outbound_clicks,outbound_clicks_ctr,"
            "actions,action_values,purchase_roas"
        )
        
        url = f"{FacebookService.BASE_URL}/{account_id}/insights"
        
        # 1. Fetch Current Period
        current_params = {
            "fields": fields,
            "date_preset": date_preset,
            "level": "account"
        }
        
        try:
            # Current Data
            cur_res = requests.get(url, headers=headers, params=current_params, timeout=30).json()
            if "error" in cur_res:
                # print(f"FB API Error (Current): {cur_res['error']}")
                try:
                    with open("debug_insights_error.log", "a", encoding="utf-8") as f:
                        f.write(f"[{datetime.now()}] API Error: {cur_res['error']}\n")
                except: pass
                return None
                
            cur_data_list = cur_res.get("data", [])
            cur_data = cur_data_list[0] if cur_data_list else {}
            
            # Calculate Previous Period Range
            # Try to use FB returned dates first, otherwise fallback to manual calculation
            date_start = cur_data.get("date_start")
            date_stop = cur_data.get("date_stop")
            
            fmt = "%Y-%m-%d"
            
            if not date_start or not date_stop:
                # Manual Fallback: today - days
                today = datetime.now()
                # Note: FB 'last_7d' usually excludes today or includes? 
                # Standard FB logic: last_x_days excludes today.
                d_stop = today - timedelta(days=1)
                d_start = d_stop - timedelta(days=days-1)
                
                date_start = d_start.strftime(fmt)
                date_stop = d_stop.strftime(fmt)
                
                # Mock date in cur_data if missing so we don't error later
                cur_data["date_start"] = date_start
                cur_data["date_stop"] = date_stop

            # Prepare Prev Params
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

            # Previous Data
            prev_res = requests.get(url, headers=headers, params=prev_params, timeout=30).json()
            prev_data_list = prev_res.get("data", [])
            prev_data = prev_data_list[0] if prev_data_list else {}

            # 2. Fetch Daily Trend (for the Chart) - Current Range Only
            trend_fields = (
                "spend,impressions,inline_link_clicks,ctr,cpc,"
                "actions,action_values,purchase_roas"
            )
            trend_params = {
                "fields": trend_fields,
                "date_preset": date_preset,
                "time_increment": "1", # Daily breakdown
                "level": "account"
            }
            trend_res = requests.get(url, headers=headers, params=trend_params, timeout=30).json()
            trend_list = trend_res.get("data", [])

            return {
                "kpi": FacebookService._format_kpi(cur_data, prev_data),
                "charts": FacebookService._format_charts(trend_list),
                "date_range": {
                    "start": date_start,
                    "stop": date_stop
                }
            }

        except Exception as e:
            # print(f"Error fetching insights: {e}")
            try:
                with open("debug_insights_error.log", "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now()}] Insight Error: {e}\n")
            except: pass
            return None

    @staticmethod
    def _process_actions(data):
        return process_actions(data)

    @staticmethod
    def _get_video_action_value(row, field_name):
        return get_video_action_value(row, field_name)

    @staticmethod
    def _calculate_change(current, previous):
        return calculate_change(current, previous)

    @staticmethod
    def _format_kpi(cur, prev):
        return format_kpi(cur, prev)

    @staticmethod
    def _format_charts(data_list):
        return format_charts(data_list)

    @staticmethod
    def get_custom_report(account_id, user_id, since, until, level="account", team_id=None):
        """
        Flexible report fetcher for Analytics Page.
        Supports custom dates and different levels (campaign, adset, ad).
        """
        headers = FacebookService.get_headers(user_id, team_id)
        if not headers:
            return None
            
        base_fields = (
            "campaign_id,adset_id,ad_id," # ID fields
            "campaign_name,adset_name,ad_name," # Identity fields
            "spend,impressions,reach,frequency,cpm,cpc,ctr,inline_link_clicks,clicks,unique_clicks,unique_ctr,"  # Core metrics
            "inline_link_click_ctr,outbound_clicks,outbound_clicks_ctr," # Clicks & CTR
            "instant_experience_clicks_to_open,instant_experience_clicks_to_start," # IE
            "actions,action_values,purchase_roas,"  # Actions and ROAS
            "catalog_segment_value,catalog_segment_actions," # CPAS Metrics
            "video_p25_watched_actions,video_p50_watched_actions,video_p75_watched_actions,video_p100_watched_actions," # Video metrics
            "video_avg_time_watched_actions" # Video derived
        )
        
        # Special fields only for Ad level
        if level == "ad":
            base_fields += ",quality_ranking,engagement_rate_ranking,conversion_rate_ranking"

        # Removed 'objective,effective_status' from Insights API to prevent errors.
        # We will fetch status separately for Ads.

        url = f"{FacebookService.BASE_URL}/{account_id}/insights"
        
        params = {
            "fields": base_fields,
            "level": level,
            "time_range": f'{{"since":"{since}","until":"{until}"}}',
            "time_increment": "all_days", # Aggregate all data
            "limit": 500
        }
        
        try:
            res = requests.get(url, headers=headers, params=params, timeout=30).json()
            if "error" in res:
                logger.error(f"[FB] API Error (Report): {res['error'].get('message', 'Unknown')}")
                return None
                
            data = res.get("data", [])
            logger.info(f"[FB] Report: Level={level} Rows={len(data)}")
            
            # Process each row
            
            # If Level is Ad, fetch Creative Images AND Status separately
            ad_meta_map = {} # Stores {id: {image_url: ..., status: ...}}
            if level == "ad":
                try:
                    # Fetch Ads with Creative fields AND Status
                    c_url = f"{FacebookService.BASE_URL}/{account_id}/ads"
                    c_params = {
                        "fields": "id,effective_status,creative{thumbnail_url,image_url}",
                        "limit": 1000 
                    }
                    c_res = requests.get(c_url, headers=headers, params=c_params, timeout=30).json()
                    c_data = c_res.get("data", [])
                    
                    for ad in c_data:
                        # Creative
                        creative = ad.get("creative", {})
                        img = creative.get("image_url") or creative.get("thumbnail_url")
                        
                        ad_meta_map[ad["id"]] = {
                            "image_url": img,
                            "status": ad.get("effective_status", "UNKNOWN")
                        }
                            
                except Exception as e:
                    logger.error("[FB] Error fetching ad metadata", exc_info=True)

            processed_rows = []
            for row in data:
                # ... (Naming logic) ...
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

                # Get Metadata (Ad Level)
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
                    
                    "image_url": meta.get("image_url"), # From Meta Map
                    
                    # Quality Diagnosis
                    "quality_ranking": row.get("quality_ranking", "-"),
                    "engagement_rate_ranking": row.get("engagement_rate_ranking", "-"),
                    "conversion_rate_ranking": row.get("conversion_rate_ranking", "-"),
                    
                    # Video Metrics (NEW)
                    "video_p25_watched": FacebookService._get_video_action_value(row, "video_p25_watched_actions"),
                    "video_p50_watched": FacebookService._get_video_action_value(row, "video_p50_watched_actions"),
                    "video_p75_watched": FacebookService._get_video_action_value(row, "video_p75_watched_actions"),
                    "video_p100_watched": FacebookService._get_video_action_value(row, "video_p100_watched_actions"),
                    "video_avg_time_watched": FacebookService._get_video_action_value(row, "video_avg_time_watched_actions"),
                    "cost_per_thruplay": float(row.get("cost_per_thruplay", [{}])[0].get("value", 0) if row.get("cost_per_thruplay") else 0),
                    
                    # Metadata
                    "objective": row.get("objective", "-"), # This might be missing now, acceptable.
                    "status": meta.get("status", "UNKNOWN"), # From Meta Map
                }
                
                # 2. Process Actions
                acts = FacebookService._process_actions(row)
                
                flat["view_content"] = acts.get("view_content", 0)
                flat["add_to_cart"] = acts.get("add_to_cart", 0)
                flat["initiate_checkout"] = acts.get("initiate_checkout", 0)
                flat["add_payment_info"] = acts.get("add_payment_info", 0)
                flat["purchases"] = acts.get("purchase", 0)
                
                flat["purchase_value"] = acts.get("purchase_val", 0)
                flat["atc_value"] = acts.get("add_to_cart_val", 0)

                # 2.1 Engagement Metrics
                flat["post_comments"] = acts.get("comment", 0)
                flat["post_saves"] = acts.get("onsite_conversion.post_save", 0)  # Fixed action type
                flat["post_shares"] = acts.get("post", 0)
                flat["post_engagement"] = acts.get("post_engagement", 0)
                flat["post_reactions"] = acts.get("post_reaction", 0)
                flat["page_likes"] = acts.get("like", 0)

                # 2.2 Video Metrics (from actions)
                flat["video_views"] = acts.get("video_view", 0)
                flat["video_thruplay"] = acts.get("video_view", 0)  # ThruPlay uses same action type

                # 2.3 Messaging Metrics
                flat["messaging_first_reply"] = acts.get("onsite_conversion.messaging_first_reply", 0)
                flat["messaging_conversation_started"] = acts.get("onsite_conversion.messaging_conversation_started_7d", 0)
                
                # 2.4 Lead Gen Metrics
                flat["leads"] = acts.get("lead", 0)
                flat["onsite_leads"] = acts.get("onsite_conversion.lead_grouped", 0)
                
                # 2.5 App Metrics
                flat["app_installs"] = acts.get("mobile_app_install", 0)
                flat["app_events"] = acts.get("app_custom_event", 0)

                # 2.6 CPAS Metrics (Collaborative Ads)
                cpas_acts = FacebookService._process_actions({"actions": row.get("catalog_segment_actions", [])})
                cpas_vals = FacebookService._process_actions({"action_values": row.get("catalog_segment_value", [])})

                flat["shared_purchases"] = cpas_acts.get("purchase", 0)
                flat["shared_purchase_value"] = cpas_vals.get("purchase_val", 0)
                flat["shared_add_to_cart"] = cpas_acts.get("add_to_cart", 0)
                flat["shared_atc_value"] = cpas_vals.get("add_to_cart_val", 0)
                flat["shared_view_content"] = cpas_acts.get("view_content", 0)
                
                # Derived CPAS ROAS
                flat["shared_roas"] = (flat["shared_purchase_value"] / flat["spend"]) if flat["spend"] > 0 else 0

                
                # 3. Derived Metrics
                flat["cpa"] = flat["spend"] / flat["purchases"] if flat["purchases"] > 0 else 0
                flat["cost_per_atc"] = flat["spend"] / flat["add_to_cart"] if flat["add_to_cart"] > 0 else 0
                flat["cvr"] = (flat["purchases"] / flat["link_clicks"] * 100) if flat["link_clicks"] > 0 else 0
                
                # Cost per Message
                flat["cost_per_message"] = flat["spend"] / flat["messaging_first_reply"] if flat["messaging_first_reply"] > 0 else 0
                
                # Cost per Lead
                flat["cost_per_lead"] = flat["spend"] / flat["leads"] if flat["leads"] > 0 else 0
                
                # Cost per Install
                flat["cost_per_install"] = flat["spend"] / flat["app_installs"] if flat["app_installs"] > 0 else 0

                # Backfill Purchase Value if missing but ROAS exists (Fix for 0 ROAS in Summary)
                if flat["purchase_value"] == 0 and flat["roas"] > 0 and flat["spend"] > 0:
                    flat["purchase_value"] = flat["roas"] * flat["spend"]
                
                # Funnel Rates
                # 1. View to Cart (ATC / View Content)
                flat["view_to_cart"] = (flat["add_to_cart"] / flat["view_content"] * 100) if flat["view_content"] > 0 else 0
                
                # 2. Cart Purchase Rate (Purchases / ATC) - Inverse of Dropoff
                if flat["add_to_cart"] > 0:
                    flat["cart_conversion"] = (flat["purchases"] / flat["add_to_cart"]) * 100
                    flat["cart_dropoff"] = (1 - (flat["purchases"] / flat["add_to_cart"])) * 100
                else:
                    flat["cart_conversion"] = 0
                    flat["cart_dropoff"] = 0
                    
                # 3. Cart Value Realization (Purchase Value / ATC Value)
                flat["cart_value_realization"] = (flat["purchase_value"] / flat["atc_value"] * 100) if flat["atc_value"] > 0 else 0

                processed_rows.append(flat)
                
            return processed_rows

        except Exception as e:
            logger.error("[FB] Error fetching custom report", exc_info=True)
            return None

    @staticmethod
    def get_analytics_trend(account_id, user_id, since, until, prev_since=None, prev_until=None, team_id=None):
        """
        Fetches DAILY trend data for current and optional previous period.
        Merges them by relative Day Index.
        Calculates ALL metrics (CPAS, Funnel, Engagement) to match Table data.
        """
        headers = FacebookService.get_headers(user_id, team_id)
        if not headers:
            return None

        url = f"{FacebookService.BASE_URL}/{account_id}/insights"
        
        # Use SAME base fields as report to ensure all data is available
        fields = (
            "spend,impressions,reach,cpm,cpc,ctr,inline_link_clicks,clicks,"
            "actions,action_values,purchase_roas,"
            "catalog_segment_value,catalog_segment_actions" # CPAS
        )

        def fetch_daily(s, u):
            params = {
                "fields": fields,
                "level": "account",
                "time_range": f'{{"since":"{s}","until":"{u}"}}',
                "time_increment": "1", # Daily
                "limit": 100
            }
            try:
                res = requests.get(url, headers=headers, params=params, timeout=30).json()
                return res.get("data", [])
            except Exception as e:
                logger.error("[FB] Error in trend fetch", exc_info=True)
                return []

        # 1. Fetch Current & Previous
        cur_data = fetch_daily(since, until)
        
        prev_data = []
        if prev_since and prev_until:
            prev_data = fetch_daily(prev_since, prev_until)

        # 2. Helper to Process a Single Day Item (Identical logic to get_custom_report)
        def process_daily_item(item):
            if not item: return {}
            
            # Base values
            row = {
                "spend": float(item.get("spend", 0)),
                "impressions": int(item.get("impressions", 0)),
                "reach": int(item.get("reach", 0)),
                "link_clicks": int(item.get("inline_link_clicks", 0)),
                "clicks": int(item.get("clicks", 0)),
                "cpc": float(item.get("cpc", 0)),
                "ctr": float(item.get("ctr", 0)),
                "cpm": float(item.get("cpm", 0)),
                
                # ROAS (Standard)
                "roas": float(item.get("purchase_roas", [{}])[0].get("value", 0) if item.get("purchase_roas") else 0),
            } 
            
            # Actions parsing
            acts = FacebookService._process_actions(item)
            
            row["view_content"] = acts.get("view_content", 0)
            row["add_to_cart"] = acts.get("add_to_cart", 0)
            row["initiate_checkout"] = acts.get("initiate_checkout", 0)
            row["add_payment_info"] = acts.get("add_payment_info", 0)
            row["purchases"] = acts.get("purchase", 0)
            row["purchase_value"] = acts.get("purchase_val", 0)
            row["atc_value"] = acts.get("add_to_cart_val", 0)
            
            # Engagement
            row["post_comments"] = acts.get("comment", 0)
            row["post_saves"] = acts.get("post_save", 0)
            row["post_shares"] = acts.get("post", 0)
            row["post_engagement"] = acts.get("post_engagement", 0)
            row["post_reactions"] = acts.get("post_reaction", 0)
            row["page_likes"] = acts.get("like", 0)
            
            # CPAS
            cpas_acts = FacebookService._process_actions({"actions": item.get("catalog_segment_actions", [])})
            cpas_vals = FacebookService._process_actions({"action_values": item.get("catalog_segment_value", [])})

            row["shared_purchases"] = cpas_acts.get("purchase", 0)
            row["shared_purchase_value"] = cpas_vals.get("purchase_val", 0)
            row["shared_add_to_cart"] = cpas_acts.get("add_to_cart", 0)
            row["shared_atc_value"] = cpas_vals.get("add_to_cart_val", 0)
            row["shared_view_content"] = cpas_acts.get("view_content", 0)
            row["shared_roas"] = (row["shared_purchase_value"] / row["spend"]) if row["spend"] > 0 else 0
            
            # Derived Metrics
            row["cpa"] = row["spend"] / row["purchases"] if row["purchases"] > 0 else 0
            row["cost_per_atc"] = row["spend"] / row["add_to_cart"] if row["add_to_cart"] > 0 else 0
            row["cvr"] = (row["purchases"] / row["link_clicks"] * 100) if row["link_clicks"] > 0 else 0
            
            # Funnel
            row["view_to_cart"] = (row["add_to_cart"] / row["view_content"] * 100) if row["view_content"] > 0 else 0
            if row["add_to_cart"] > 0:
                row["cart_conversion"] = (row["purchases"] / row["add_to_cart"]) * 100
                row["cart_dropoff"] = (1 - (row["purchases"] / row["add_to_cart"])) * 100
            else:
                row["cart_conversion"] = 0
                row["cart_dropoff"] = 0
            
            row["cart_value_realization"] = (row["purchase_value"] / row["atc_value"] * 100) if row["atc_value"] > 0 else 0

            return row

        # 3. Merge by Index
        max_len = max(len(cur_data), len(prev_data))
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
            
            # Flatten Current Metrics
            for k, v in c_metrics.items():
                final_row[k] = v
                
            # Flatten Previous Metrics (with _prev suffix)
            for k, v in p_metrics.items():
                final_row[f"{k}_prev"] = v

            merged.append(final_row)

        return merged
