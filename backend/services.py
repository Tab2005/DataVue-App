import requests
from datetime import datetime, timedelta
from auth import TokenManager

class FacebookService:
    BASE_URL = "https://graph.facebook.com/v18.0"

    @staticmethod
    def get_headers(user_id):
        token = TokenManager.get_user_token(user_id)
        if not token:
            return None
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def get_all_ad_accounts(user_id):
        """
        Fetches all ad accounts for the dropdown selector.
        Returns a list of dicts: {'id': 'act_123', 'name': 'My Account'}
        """
        headers = FacebookService.get_headers(user_id)
        if not headers:
            return [], "No access token found for this user."

        url = f"{FacebookService.BASE_URL}/me/adaccounts"
        params = {
            "fields": "name,account_id",
            "limit": 100
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            
            if "error" in data:
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
    def get_account_insights(account_id, user_id, days=7):
        """
        Fetches insights for the given account with comparison data.
        """
        headers = FacebookService.get_headers(user_id)
        if not headers:
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
                print(f"FB API Error (Current): {cur_res['error']}")
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
            print(f"Error fetching insights: {e}")
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
        add_metric("Spend", "spend", is_currency=True, is_inverse=True)
        add_metric("Impressions", "impressions")
        add_metric("CPM", "cpm", is_currency=True, is_inverse=True) 
        # Fix: Frontend expects 'link_clicks', API has 'inline_link_clicks'
        add_metric("Link Clicks", "link_clicks", source_key="inline_link_clicks") 
        add_metric("CPC", "cpc", is_currency=True, is_inverse=True)
        add_metric("CTR", "ctr", is_percent=True)
        # Fix: Frontend expects 'purchases', API action is 'purchase'
        add_metric("Purchases", "purchases", is_action=True, action_key="purchase") 
        
        # Calculate CPA manually
        spend_val = get_val(cur, "spend")
        prev_spend_val = get_val(prev, "spend")
        
        cur_purchases = cur_acts.get("purchase", 0)
        prev_purchases = prev_acts.get("purchase", 0)

        cpa_val = spend_val / cur_purchases if cur_purchases > 0 else 0.0
        prev_cpa_val = prev_spend_val / prev_purchases if prev_purchases > 0 else 0.0

        # Add CPA metric
        add_metric("Cost Per Purchase", "cpa", is_currency=True, is_inverse=True)
        # Manually update CPA values in the metrics dict
        if "cpa" in metrics:
            metrics["cpa"]["raw_value"] = cpa_val
            metrics["cpa"]["value"] = f"${cpa_val:,.2f}"
            metrics["cpa"]["previous"] = f"(${prev_cpa_val:,.2f})"
            
            diff_cpa = cpa_val - prev_cpa_val
            if prev_cpa_val == 0:
                percent_cpa = 100.0 if cpa_val > 0 else 0.0
            else:
                percent_cpa = (diff_cpa / prev_cpa_val) * 100.0
            
            if percent_cpa > 0:
                metrics["cpa"]["change"] = f"+{abs(percent_cpa):.1f}%"
            elif percent_cpa < 0:
                metrics["cpa"]["change"] = f"-{abs(percent_cpa):.1f}%"
            else:
                metrics["cpa"]["change"] = "0.0%"
            
            metrics["cpa"]["is_increase"] = (diff_cpa > 0) # CPA is inverse, so higher is worse
            if metrics["cpa"]["is_increase"]: metrics["cpa"]["is_increase"] = False
            else: metrics["cpa"]["is_increase"] = True


        # Add To Cart
        add_metric("Add to Cart", "add_to_cart", is_action=True, action_key="add_to_cart")
        
        # ROAS
        add_metric("ROAS", "roas", is_roas=True) 
        
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
    def get_custom_report(account_id, user_id, since, until, level="account"):
        """
        Flexible report fetcher for Analytics Page.
        Supports custom dates and different levels (campaign, adset, ad).
        """
        headers = FacebookService.get_headers(user_id)
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
                print(f"FB API Error (Report): {res['error']}")
                return None
                
            data = res.get("data", [])
            print(f"DEBUG_REPORT: Level={level} Period={since}~{until} Rows={len(data)}")
            
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
                    print(f"Error fetching ad metadata: {e}")

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
            print(f"Error fetching custom report: {e}")
            return None
