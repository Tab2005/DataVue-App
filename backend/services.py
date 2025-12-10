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
        
        metrics = []
        
        def add_metric(label, key, is_currency=False, is_action=False, action_key=None, is_roas=False, is_percent=False, is_inverse=False):
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
                c_val = get_val(cur, key)
                p_val = get_val(prev, key)

            # 2. Calculate Diff and Percent
            diff = c_val - p_val
            if p_val == 0:
                percent = 100.0 if c_val > 0 else 0.0
            else:
                percent = (diff / p_val) * 100.0

            # 3. Format Strings
            def fmt_num(n):
                if is_currency: return f"${abs(n):,.2f}" if key in ['cpc', 'cpm'] else f"${abs(n):,.0f}" # Condense big numbers
                if is_percent: return f"{abs(n):.2f}%"
                if is_roas: return f"{abs(n):.2f}"
                return f"{abs(n):,.0f}"

            # Value Formatting (No Abs for main value, though metrics usually +ve)
            val_str = fmt_num(c_val).replace('$-', '-$') # Handle negative currency visual if ever needed
            if c_val < 0: val_str = "-" + val_str
            else: val_str = fmt_num(c_val) # Re-format to strip potential double negative logic or just keep simple
            
            # Simple main value format (positive)
            if is_currency: 
                val_str = f"${c_val:,.2f}" # Force 2 decimals for currency like CPC? Or 0 for Spend? 
                # Screenshot shows Spend $14,816.00 and CPC $2.90. So always 2 decimals?
                # Let's clean up:
                if key in ['cpc', 'cpm', 'ctr'] or is_roas: pass # keep precision
                else: val_str = f"${c_val:,.0f}" # Integers for big spend? Screenshot shows .00
                val_str = f"${c_val:,.2f}"
            elif is_percent:
                 val_str = f"{c_val:.2f}%"
            elif is_roas:
                 val_str = f"{c_val:.2f}"
            else:
                 val_str = f"{c_val:,.0f}"

            # Prev Value (in parens)
            prev_str = f"({fmt_num(p_val)})"
            
            # Diff String (Value difference)
            diff_str = fmt_num(diff)

            # Percent String
            percent_str = f"{abs(percent):.1f}%" # Screenshot shows 1 decimals e.g. 39.6%


            metrics.append({
                "label": label,
                "value": val_str,
                "sub_value": prev_str,
                "diff": diff_str,
                "percent": percent_str,
                "is_increase": diff >= 0,
                "is_inverse": is_inverse # True = Increase is Bad (Red)
            })

        # The 8 Grid Items mapping
        # Inverse: Spend, CPC, CPM, CPA (Cost related)
        # Normal: Impressions, Clicks, CTR, Actions, ROAS
        
        add_metric("曝光 (Impressions)", "impressions")
        add_metric("連結點擊次數 (Link Clicks)", "inline_link_clicks") 
        add_metric("CTR", "ctr", is_percent=True)
        add_metric("CPC", "cpc", is_currency=True, is_inverse=True)
        add_metric("費用 (Spend)", "spend", is_currency=True, is_inverse=True)
        add_metric("購買 (Purchases)", "", is_action=True, action_key="purchase")
        add_metric("購物車 (AddToCart)", "", is_action=True, action_key="add_to_cart")
        add_metric("ROAS", "", is_roas=True) # ROAS is Normal (Higher is Better)

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
                "value": float(item.get("spend", 0))
            })
        
        # Sort by date
        formatted.sort(key=lambda x: x["name"])
        return formatted
