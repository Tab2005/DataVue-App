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
            "spend,impressions,reach,cpm,cpc,ctr,inline_link_clicks,"
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
                
            cur_data = cur_res.get("data", [{}])[0]
            
            # Calculate Previous Period Range
            # We use the date_start/date_stop returned by FB to be precise regarding timezone
            date_start = cur_data.get("date_start")
            date_stop = cur_data.get("date_stop")
            
            prev_params = {
                "fields": fields,
                "level": "account"
            }
            
            if date_start and date_stop:
                fmt = "%Y-%m-%d"
                d_start = datetime.strptime(date_start, fmt)
                d_stop = datetime.strptime(date_stop, fmt)
                delta = d_stop - d_start + timedelta(days=1) # inclusive days
                
                prev_start = (d_start - delta).strftime(fmt)
                prev_stop = (d_start - timedelta(days=1)).strftime(fmt)
                
                prev_params["time_range"] = f'{{"since":"{prev_start}","until":"{prev_stop}"}}'
            else:
                # Fallback if dates missing (unlikely)
                return None

            # Previous Data
            prev_res = requests.get(url, headers=headers, params=prev_params).json()
            prev_data = prev_res.get("data", [{}])[0]

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
                "charts": FacebookService._format_charts(trend_list)
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
        
        # Define the 8 Metrics mapping based on User's Screenshot
        # 1. Spend
        metrics = []
        
        def add_metric(label, key, is_currency=False, is_action=False, action_key=None, is_roas=False):
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

            val_str = f"${c_val:,.2f}" if is_currency else f"{c_val:,.0f}" if c_val > 10 else f"{c_val:.2f}"
            
            # Special formatting for ROAS, CTR, CPC
            if key == "cpc": val_str = f"${c_val:.2f}"
            if key == "cpm": val_str = f"${c_val:.2f}"
            if key == "ctr": val_str = f"{c_val:.2f}%"
            if is_roas: val_str = f"{c_val:.2f}"

            metrics.append({
                "label": label,
                "value": val_str,
                "sub_value": f"{p_val:,.2f}" if is_currency else f"{p_val:,.0f}", # Simplified sub-value
                "change": FacebookService._calculate_change(c_val, p_val),
                "isPositive": c_val >= p_val # Simple logic, can be refined (e.g. CPA down is positive)
            })

        # The 8 Grid Items
        add_metric("曝光 (Impressions)", "impressions")
        add_metric("點擊 (Clicks)", "clicks") # Note: 'clicks' (all) or 'inline_link_clicks'? Graph uses 'clicks' usually for general
        add_metric("CTR", "ctr")
        add_metric("CPC", "cpc")
        add_metric("費用 (Spend)", "spend", is_currency=True)
        add_metric("購買 (Purchases)", "", is_action=True, action_key="purchase")
        add_metric("購物車 (AddToCart)", "", is_action=True, action_key="add_to_cart")
        add_metric("ROAS", "", is_roas=True)

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
