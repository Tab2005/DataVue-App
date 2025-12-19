import requests
from datetime import datetime, timedelta
from auth import TokenManager
import sys

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
            print("[FB] get_all_ad_accounts: No token available", file=sys.stderr)
            return [], "No access token found for this user."

        url = f"{FacebookService.BASE_URL}/me/adaccounts"
        params = {
            "fields": "name,account_id",
            "limit": 100
        }

        try:
            print(f"[FB] Fetching Ad Accounts...", file=sys.stderr)
            response = requests.get(url, headers=headers, params=params, timeout=10)
            print(f"[FB] Response Status: {response.status_code}", file=sys.stderr)
            data = response.json()
            # print(f"Facebook API Response Body: {data}", file=sys.stderr) # Debug only

            if "error" in data:
                print(f"[FB] API Error: {data['error'].get('message', 'Unknown error')}", file=sys.stderr)
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
            "spend,impressions,reach,cpm,cpc,ctr,inline_link_clicks,clicks,"
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
            cur_res = requests.get(url, headers=headers, params=current_params).json()
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
            prev_res = requests.get(url, headers=headers, params=prev_params).json()
            prev_data_list = prev_res.get("data", [])
            prev_data = prev_data_list[0] if prev_data_list else {}

            # 2. Fetch Daily Trend (for the Chart) - Current Range Only
            trend_params = {
                "fields": "spend",
                "date_preset": date_preset,
                "time_increment": "1", # Daily breakdown
                "level": "account"
            }
            trend_res = requests.get(url, headers=headers, params=trend_params).json()
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
        """
        Parses 'actions' and 'action_values' lists into a dictionary.
        e.g. actions: [{'action_type': 'purchase', 'value': '10'}] -> {'purchase': 10}
        """
        result = {}
        
        # Process Counts
        if "actions" in data:
            for item in data["actions"]:
                result[item["action_type"]] = float(item["value"])
                
        # Process Values (Revenue)
        # We append '_val' suffix for distinction, e.g. 'purchase_val'
        if "action_values" in data:
            for item in data["action_values"]:
                result[f"{item['action_type']}_val"] = float(item["value"])
                
        return result

    @staticmethod
    def _calculate_change(current, previous):
        """
        Returns string percentage change. e.g. "+15.0%", "-1.2%", or "0%"
        """
        if previous == 0:
            return "+0%" if current == 0 else "+100%" # Simplified infinity handling
            
        change = ((current - previous) / previous) * 100
        sign = "+" if change > 0 else ""
        return f"{sign}{change:.2f}%"

    @staticmethod
    def _format_kpi(cur, prev):
        # Helper to safely get float values
        def get_val(d, key, default=0.0):
            return float(d.get(key, default))

        # Process complex action lists
        cur_acts = FacebookService._process_actions(cur)
        prev_acts = FacebookService._process_actions(prev)
        
        # metrics = [] -> Changed to Dict
        metrics = {}
        
        def add_metric(label, key, source_key=None, is_currency=False, is_action=False, action_key=None, is_roas=False, is_percent=False, is_inverse=False):
            # 1. Get Values
            if is_action:
                c_val = cur_acts.get(action_key, 0)
                p_val = prev_acts.get(action_key, 0)
            elif is_roas:
                # ROAS is usually 'purchase_roas' list
                c_roas_list = cur.get("purchase_roas", [])
                p_roas_list = prev.get("purchase_roas", [])
                c_val = float(c_roas_list[0]["value"]) if c_roas_list else 0.0
                p_val = float(p_roas_list[0]["value"]) if p_roas_list else 0.0
            else:
                # Use source_key if provided, else key
                fetch_key = source_key if source_key else key
                c_val = get_val(cur, fetch_key)
                p_val = get_val(prev, fetch_key)

            # 2. Calculate Diff and Percent
            diff = c_val - p_val
            if p_val == 0:
                percent = 100.0 if c_val > 0 else 0.0
            else:
                percent = (diff / p_val) * 100.0

            # 3. Format Strings
            def fmt_num(n, for_display=True):
                if is_currency: 
                    return f"${n:,.0f}" if for_display else n 
                if is_percent: 
                    return f"{n:.2f}%" if for_display else n
                if is_roas: 
                    return f"{n:.2f}" if for_display else n
                return f"{n:,.0f}" if for_display else n

            # Value Formatting
            val_str = fmt_num(c_val)
            
            # Prev Value (in parens)
            prev_str = f"({fmt_num(p_val)})"
            
            # Diff String
            diff_str = fmt_num(diff)
            if is_currency: diff_str = diff_str.replace('$-', '-$') 
            if diff > 0: diff_str = "+" + diff_str

            # Change String (Percent)
            if percent > 0:
                change_str = f"+{abs(percent):.1f}%"
            elif percent < 0:
                change_str = f"-{abs(percent):.1f}%"
            else:
                change_str = "0.0%"

            # Boolean for color (Higher is better, unless inverse)
            is_increase = (diff > 0)

            metrics[key] = {
                "label": label,
                "value": val_str,
                "previous": prev_str,
                "diff": diff_str,
                "change": change_str,
                "is_increase": is_increase,
                "raw_value": c_val
            }

        # Add Metrics (Keys must match Frontend kpiKeys)
        # Helper to calculate derived metric
        def calc_derived(numerator_key, denominator_key, multiplier=1.0, default=0.0):
            num = get_val(cur, numerator_key)
            den = get_val(cur, denominator_key)
            return (num / den * multiplier) if den > 0 else default

        def calc_derived_prev(numerator_key, denominator_key, multiplier=1.0, default=0.0):
            num = get_val(prev, numerator_key)
            den = get_val(prev, denominator_key)
            return (num / den * multiplier) if den > 0 else default
        
        # Base Metrics
        add_metric("Spend", "spend", is_currency=True, is_inverse=True)
        add_metric("Impressions", "impressions")
        add_metric("Link Clicks", "link_clicks", source_key="inline_link_clicks")
        add_metric("Purchases", "purchases", is_action=True, action_key="purchase")
        add_metric("Add to Cart", "add_to_cart", is_action=True, action_key="add_to_cart")
        
        # Derived Metrics - Manually Calculate to match Table logic
        
        # 1. CPM = Spend / Impressions * 1000
        cur["cpm_calc"] = calc_derived("spend", "impressions", 1000.0)
        prev["cpm_calc"] = calc_derived_prev("spend", "impressions", 1000.0)
        add_metric("CPM", "cpm", source_key="cpm_calc", is_currency=True, is_inverse=True)

        # 2. CPC = Spend / Link Clicks
        cur["cpc_calc"] = calc_derived("spend", "inline_link_clicks")
        prev["cpc_calc"] = calc_derived_prev("spend", "inline_link_clicks")
        add_metric("CPC", "cpc", source_key="cpc_calc", is_currency=True, is_inverse=True)

        # 3. CTR = Link Clicks / Impressions * 100
        cur["ctr_calc"] = calc_derived("inline_link_clicks", "impressions", 100.0)
        prev["ctr_calc"] = calc_derived_prev("inline_link_clicks", "impressions", 100.0)
        add_metric("CTR", "ctr", source_key="ctr_calc", is_percent=True)

        # 4. ROAS = Purchase Value / Spend
        # Need to get purchase value first
        cur_purch_val = cur_acts.get("purchase_val", 0)
        prev_purch_val = prev_acts.get("purchase_val", 0)
        cur_spend = get_val(cur, "spend")
        prev_spend = get_val(prev, "spend")
        
        cur["roas_calc"] = (cur_purch_val / cur_spend) if cur_spend > 0 else 0.0
        prev["roas_calc"] = (prev_purch_val / prev_spend) if prev_spend > 0 else 0.0
        add_metric("ROAS", "roas", source_key="roas_calc", is_roas=True) # Use customized source_key logic modification below

        # 5. CPA = Spend / Purchases
        cur_purchases = cur_acts.get("purchase", 0)
        prev_purchases = prev_acts.get("purchase", 0)
        
        cur["cpa_calc"] = (cur_spend / cur_purchases) if cur_purchases > 0 else 0.0
        prev["cpa_calc"] = (prev_spend / prev_purchases) if prev_purchases > 0 else 0.0
        add_metric("CPA", "cpa", source_key="cpa_calc", is_currency=True, is_inverse=True)
        
        # 6. Purchase Value
        # We need to add this to metrics dict manually or via helper if we want it displayed
        # The frontend asks for specific keys. If 'purchase_value' is needed in KPI cards:
        add_metric("Purchase Value", "purchase_value", is_action=True, action_key="purchase_val", is_currency=True)
        
        # 7. Add to Cart Value
        add_metric("ATC Value", "atc_value", is_action=True, action_key="add_to_cart_val", is_currency=True)
        
        # 8. Cost Per ATC
        cur_atc = cur_acts.get("add_to_cart", 0)
        prev_atc = prev_acts.get("add_to_cart", 0)
        cur["cost_per_atc_calc"] = (cur_spend / cur_atc) if cur_atc > 0 else 0.0
        prev["cost_per_atc_calc"] = (prev_spend / prev_atc) if prev_atc > 0 else 0.0
        add_metric("Cost Per ATC", "cost_per_atc", source_key="cost_per_atc_calc", is_currency=True, is_inverse=True)

        return metrics

    @staticmethod
    def _format_charts(data_list):
        # Format for Recharts: Daily Trend
        formatted = []
        for item in data_list:
            # date_start is "YYYY-MM-DD"
            date_str = item.get("date_start", "")[5:] # Remove Year -> "MM-DD"
            formatted.append({
                "name": date_str, 
                "spend": float(item.get("spend", 0))
            })
        
        # Sort by date
        formatted.sort(key=lambda x: x["name"])
        return formatted

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
            "spend,impressions,reach,cpm,cpc,ctr,inline_link_clicks,clicks,"
            "actions,action_values,purchase_roas,"
            "quality_ranking,engagement_rate_ranking,conversion_rate_ranking," # Quality Diagnosis
            "catalog_segment_value,catalog_segment_actions" # CPAS Metrics
        )

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
            res = requests.get(url, headers=headers, params=params).json()
            if "error" in res:
                print(f"[FB] API Error (Report): {res['error'].get('message', 'Unknown')}", file=sys.stderr)
                return None
                
            data = res.get("data", [])
            print(f"[FB] Report: Level={level} Rows={len(data)}", file=sys.stderr)
            
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
                    c_res = requests.get(c_url, headers=headers, params=c_params).json()
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
                    print(f"[FB] Error fetching ad metadata", file=sys.stderr)

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
                    "clicks": int(row.get("clicks", 0)),
                    "link_clicks": int(row.get("inline_link_clicks", 0)),
                    "ctr": float(row.get("ctr", 0)),
                    "cpc": float(row.get("cpc", 0)),
                    "cpm": float(row.get("cpm", 0)),
                    "roas": float(row.get("purchase_roas", [{}])[0].get("value", 0) if row.get("purchase_roas") else 0),
                    
                    "image_url": meta.get("image_url"), # From Meta Map
                    
                    # Quality Diagnosis
                    "quality_ranking": row.get("quality_ranking", "-"),
                    "engagement_rate_ranking": row.get("engagement_rate_ranking", "-"),
                    "conversion_rate_ranking": row.get("conversion_rate_ranking", "-"),
                    
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

                # 2.1 Engagement Metrics (New)
                flat["post_comments"] = acts.get("comment", 0)
                flat["post_saves"] = acts.get("post_save", 0)
                flat["post_shares"] = acts.get("post", 0) # 'post' usually represents shares in actions list
                flat["post_engagement"] = acts.get("post_engagement", 0)
                flat["post_reactions"] = acts.get("post_reaction", 0)
                flat["page_likes"] = acts.get("like", 0)

                # 2.2 CPAS Metrics (Collaborative Ads)
                # Parse catalog_segment_actions/values which have same structure as actions
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
            print(f"[FB] Error fetching custom report", file=sys.stderr)
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
                res = requests.get(url, headers=headers, params=params).json()
                return res.get("data", [])
            except Exception as e:
                print(f"[FB] Error in trend fetch", file=sys.stderr)
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
