import requests
from auth import TokenManager

class FacebookService:
    BASE_URL = "https://graph.facebook.com/v18.0"

    @staticmethod
    def get_headers():
        token = TokenManager.get_access_token()
        if not token:
            return None
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def get_all_ad_accounts():
        """
        Fetches all ad accounts for the dropdown selector.
        Returns a list of dicts: {'id': 'act_123', 'name': 'My Account'}
        """
        headers = FacebookService.get_headers()
        if not headers:
            return [], "No access token."

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
    def get_smart_ad_account():
        """
        (Deprecated or used as fallback)
        Fetches all ad accounts and selects the best one based on:
        1. Account Status (ACTIVE = 1)
        2. Total Amount Spent (Descending)
        """
        # ... (Previous logic kept if needed, or we can rely solely on manual selection now)
        pass

    @staticmethod
    def get_account_insights(account_id):
        """
        Fetches insights for the given account.
        Returns KPI data and Trend data.
        """
        headers = FacebookService.get_headers()
        if not headers:
            return None
            
        # 1. Fetch KPI (Lifetime or last 30 days)
        # We'll use 'last_30d' for monthly snapshot.
        kpi_url = f"{FacebookService.BASE_URL}/{account_id}/insights"
        kpi_params = {
            "fields": "spend,impressions,clicks,reach,cpc,ctr",
            "date_preset": "last_30d",
            "level": "account"
        }
        
        # 2. Fetch Trends (Monthly breakdown for the last year)
        # We calculate the date range manually or use a large preset with time_increment
        trend_params = {
            "fields": "spend,impressions,clicks,reach",
            "date_preset": "last_year",
            "time_increment": "monthly",
            "level": "account"
        }

        try:
            # Execute KPI request
            kpi_res = requests.get(kpi_url, headers=headers, params=kpi_params).json()
            kpi_data = kpi_res.get("data", [{}])[0]

            # Execute Trend request
            trend_res = requests.get(kpi_url, headers=headers, params=trend_params).json()
            trend_list = trend_res.get("data", [])

            return {
                "kpi": FacebookService._format_kpi(kpi_data),
                "charts": FacebookService._format_charts(trend_list)
            }

        except Exception as e:
            print(f"Error fetching insights: {e}")
            return None

    @staticmethod
    def _format_kpi(data):
        # Fallback to 0 if data is missing
        spend = float(data.get("spend", 0))
        impressions = int(data.get("impressions", 0))
        clicks = int(data.get("clicks", 0))
        reach = int(data.get("reach", 0))
        
        # Map to the format frontend expects
        # Frontend currently expects: label, value, change, isPositive
        # We don't have "Change vs previous period" yet without a second API call. 
        # For MVP, we will hardcode 'change' or disable it, OR simpler: just show the value.
        
        return [
            {"label": "Spend (30d)", "value": f"${spend:,.2f}", "change": "---", "isPositive": True},
            {"label": "Impressions", "value": f"{impressions:,}", "change": "---", "isPositive": True},
            {"label": "Clicks", "value": f"{clicks:,}", "change": "---", "isPositive": True},
            {"label": "Reach", "value": f"{reach:,}", "change": "---", "isPositive": True},
        ]

    @staticmethod
    def _format_charts(data_list):
        # Format for Recharts: name (Month), followers (mapped to spend?), engagement (mapped to clicks?)
        # The frontend chart is "TrendsChart". Let's map "Spend" and "Impressions" or "Clicks".
        
        formatted = []
        for item in data_list:
            # date_start is like "2023-01-01"
            date_str = item.get("date_start", "")
            month_name = date_str[:7] # "2023-01"
            
            formatted.append({
                "name": month_name, 
                "followers": float(item.get("spend", 0)), # Mapping Spend to "Followers" line for now (should rename in frontend later)
                "engagement": int(item.get("clicks", 0))  # Mapping Clicks to "Engagement" line
            })
        
        # Sort by date just in case
        formatted.sort(key=lambda x: x["name"])
        return formatted
