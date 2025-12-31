"""
Facebook Graph API Client

This module contains pure API interaction methods for Facebook Graph API.
Separated from business logic for better maintainability and testability.
"""
import requests
import sys
from auth import TokenManager


class FacebookAPIClient:
    """Low-level client for Facebook Graph API calls."""
    
    BASE_URL = "https://graph.facebook.com/v24.0"
    TIMEOUT = 30  # seconds
    
    # Standard fields for API requests
    ACCOUNT_FIELDS = "id,name,account_status,currency,timezone_name"
    INSIGHTS_FIELDS = (
        "impressions,clicks,spend,ctr,cpc,cpm,cpp,reach,frequency,"
        "unique_clicks,inline_link_clicks,"
        "cost_per_unique_click,cost_per_inline_link_click,cost_per_outbound_click,"
        "cost_per_thruplay,social_spend,cost_per_conversion,"
        "actions,action_values,cost_per_action_type"
    )
    
    @staticmethod
    def get_headers(user_id: int, team_id: int = None, allow_fallback: bool = True) -> dict:
        """
        Get authorization headers with Facebook access token.
        
        Args:
            user_id: User ID to get token for
            team_id: Optional team ID for team-based token lookup
            allow_fallback: If True, fall back to admin token if user token not found
            
        Returns:
            dict with Authorization header, or None if no token found
        """
        token = TokenManager.get_token(user_id, team_id=team_id)
        if not token and allow_fallback:
            token = TokenManager.get_admin_token()
        if not token:
            return None
        return {"Authorization": f"Bearer {token}"}
    
    @staticmethod
    def fetch_ad_accounts(headers: dict) -> tuple:
        """
        Fetch all ad accounts accessible to the user.
        
        Args:
            headers: Authorization headers
            
        Returns:
            tuple: (accounts_list, error_message)
        """
        url = f"{FacebookAPIClient.BASE_URL}/me/adaccounts"
        params = {"fields": FacebookAPIClient.ACCOUNT_FIELDS}
        
        try:
            print(f"[FB API] Fetching Ad Accounts...", file=sys.stderr)
            response = requests.get(url, headers=headers, params=params, timeout=FacebookAPIClient.TIMEOUT)
            print(f"[FB API] Response Status: {response.status_code}", file=sys.stderr)
            data = response.json()
            
            if "error" in data:
                print(f"[FB API] Error: {data['error'].get('message', 'Unknown')}", file=sys.stderr)
                return [], data["error"].get("message")
            
            accounts = data.get("data", [])
            formatted = [{"id": acc["id"], "name": acc.get("name", acc["id"])} for acc in accounts]
            return formatted, None
            
        except Exception as e:
            print(f"[FB API] Exception in fetch_ad_accounts", file=sys.stderr)
            return [], str(e)
    
    @staticmethod
    def fetch_insights(
        account_id: str, 
        headers: dict, 
        since: str, 
        until: str,
        level: str = "account",
        time_increment: str = None
    ) -> dict:
        """
        Fetch insights data from Facebook API.
        
        Args:
            account_id: Ad account ID (e.g., 'act_123')
            headers: Authorization headers
            since: Start date (YYYY-MM-DD)
            until: End date (YYYY-MM-DD)
            level: Aggregation level ('account', 'campaign', 'adset', 'ad')
            time_increment: Time breakdown ('1' for daily, None for aggregate)
            
        Returns:
            dict: API response data or error dict
        """
        url = f"{FacebookAPIClient.BASE_URL}/{account_id}/insights"
        params = {
            "fields": FacebookAPIClient.INSIGHTS_FIELDS,
            "time_range": f'{{"since":"{since}","until":"{until}"}}',
            "level": level
        }
        
        if time_increment:
            params["time_increment"] = time_increment
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=FacebookAPIClient.TIMEOUT)
            return response.json()
        except Exception as e:
            print(f"[FB API] Exception in fetch_insights", file=sys.stderr)
            return {"error": {"message": str(e)}}
    
    @staticmethod
    def fetch_campaigns(account_id: str, headers: dict) -> list:
        """Fetch campaigns for an ad account."""
        url = f"{FacebookAPIClient.BASE_URL}/{account_id}/campaigns"
        params = {"fields": "id,name,status,objective"}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=FacebookAPIClient.TIMEOUT)
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            print(f"[FB API] Exception in fetch_campaigns", file=sys.stderr)
            return []
    
    @staticmethod
    def fetch_adsets(account_id: str, headers: dict) -> list:
        """Fetch ad sets for an ad account."""
        url = f"{FacebookAPIClient.BASE_URL}/{account_id}/adsets"
        params = {"fields": "id,name,status,campaign_id"}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=FacebookAPIClient.TIMEOUT)
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            print(f"[FB API] Exception in fetch_adsets", file=sys.stderr)
            return []
    
    @staticmethod
    def fetch_ads(account_id: str, headers: dict) -> list:
        """Fetch ads for an ad account."""
        url = f"{FacebookAPIClient.BASE_URL}/{account_id}/ads"
        params = {"fields": "id,name,status,adset_id,creative"}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=FacebookAPIClient.TIMEOUT)
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            print(f"[FB API] Exception in fetch_ads", file=sys.stderr)
            return []
