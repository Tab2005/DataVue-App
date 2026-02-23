"""
Facebook Batch API Service

Provides batch request functionality for Facebook Graph API.
Combines multiple API calls into a single HTTP request for improved performance.

Reference: https://developers.facebook.com/docs/graph-api/batch-requests/
"""
import httpx
import json
import asyncio
from typing import List, Dict, Any, Optional
from modules.auth.service import TokenManager
import sys
import logging

logger = logging.getLogger(__name__)


class FacebookBatchService:
    """
    Service for making batch requests to Facebook Graph API.
    
    Batch requests allow up to 50 operations per request,
    reducing network overhead and API rate limit consumption.
    """
    
    BASE_URL = "https://graph.facebook.com/v24.0"
    BATCH_LIMIT = 50  # Facebook limit per batch
    TIMEOUT = 60.0    # Longer timeout for batch requests
    
    @staticmethod
    def get_access_token(user_id: int, team_id: int = None) -> Optional[str]:
        """Get access token for batch requests."""
        if team_id:
            return TokenManager.get_team_token(team_id)
        return TokenManager.get_user_token(user_id, allow_fallback=True)
    
    @staticmethod
    def build_batch_request(requests: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Build batch request payload from individual requests.
        
        Args:
            requests: List of request configurations
            
        Example:
            requests = [
                {"method": "GET", "relative_url": "act_123/insights?fields=spend"},
                {"method": "GET", "relative_url": "act_123/campaigns?fields=name"}
            ]
        """
        batch = []
        for req in requests[:FacebookBatchService.BATCH_LIMIT]:
            batch_item = {
                "method": req.get("method", "GET"),
                "relative_url": req.get("relative_url", "")
            }
            
            # Add optional name for result identification
            if "name" in req:
                batch_item["name"] = req["name"]
            
            # Add body for POST requests
            if req.get("body"):
                batch_item["body"] = req["body"]
            
            batch.append(batch_item)
        
        return batch
    
    @staticmethod
    async def execute_batch(
        requests: List[Dict[str, Any]],
        user_id: int,
        team_id: int = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a batch of requests to Facebook Graph API.
        
        Args:
            requests: List of request configurations
            user_id: User ID for authentication
            team_id: Optional team ID for team-based token
            
        Returns:
            List of response objects, each containing:
            - code: HTTP status code
            - body: Response body (JSON string)
            - headers: Response headers (optional)
        """
        access_token = FacebookBatchService.get_access_token(user_id, team_id)
        if not access_token:
            logger.warning("[BATCH] No access token available")
            return [{"code": 401, "body": json.dumps({"error": "No access token"})}
                    for _ in requests]
        
        batch_payload = FacebookBatchService.build_batch_request(requests)
        
        url = FacebookBatchService.BASE_URL
        data = {
            "access_token": access_token,
            "batch": json.dumps(batch_payload)
        }
        
        try:
            logger.info(f"[BATCH] Executing batch of {len(batch_payload)} requests...")
            
            async with httpx.AsyncClient(timeout=FacebookBatchService.TIMEOUT) as client:
                response = await client.post(url, data=data)
                
            if response.status_code != 200:
                logger.error(f"[BATCH] HTTP Error: {response.status_code}")
                return [{"code": response.status_code, "body": response.text}
                        for _ in requests]
            
            results = response.json()
            logger.debug(f"[BATCH] Received {len(results)} responses")
            
            return results
            
        except Exception as e:
            logger.error("[BATCH] Error executing batch request", exc_info=True)
            return [{"code": 500, "body": json.dumps({"error": str(e)})}
                    for _ in requests]
    
    @staticmethod
    def parse_batch_response(response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a single batch response item.
        
        Args:
            response: Single response from batch results
            
        Returns:
            Parsed JSON body or None if error
        """
        if not response:
            return None
        
        code = response.get("code", 500)
        body = response.get("body", "{}")
        
        if code != 200:
            logger.warning(f"[BATCH] Request failed with code {code}")
            return None
        
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None
    
    @staticmethod
    async def get_dashboard_data_batch(
        account_id: str,
        user_id: int,
        days: int = 7,
        team_id: int = None
    ) -> Dict[str, Any]:
        """
        Fetch all dashboard data in a single batch request.
        
        Combines:
        - Current period insights
        - Previous period insights  
        - Daily trend data
        
        Args:
            account_id: Ad account ID (e.g., 'act_123')
            user_id: User ID
            days: Number of days for date range
            team_id: Optional team ID
            
        Returns:
            Combined dashboard data
        """
        from datetime import datetime, timedelta
        
        today = datetime.now()
        end_date = today - timedelta(days=1)
        start_date = end_date - timedelta(days=days-1)
        
        # Previous period
        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days-1)
        
        date_fmt = "%Y-%m-%d"
        current_range = f'{{"since":"{start_date.strftime(date_fmt)}","until":"{end_date.strftime(date_fmt)}"}}'
        prev_range = f'{{"since":"{prev_start.strftime(date_fmt)}","until":"{prev_end.strftime(date_fmt)}"}}'
        
        fields = (
            "spend,impressions,reach,cpm,cpc,ctr,inline_link_clicks,clicks,"
            "actions,action_values,purchase_roas"
        )
        
        # Build batch requests
        batch_requests = [
            {
                "name": "current_insights",
                "method": "GET",
                "relative_url": f"{account_id}/insights?fields={fields}&time_range={current_range}&level=account"
            },
            {
                "name": "previous_insights",
                "method": "GET",
                "relative_url": f"{account_id}/insights?fields={fields}&time_range={prev_range}&level=account"
            },
            {
                "name": "daily_trend",
                "method": "GET",
                "relative_url": f"{account_id}/insights?fields=spend,impressions,clicks&time_range={current_range}&time_increment=1&level=account"
            }
        ]
        
        # Execute batch
        results = await FacebookBatchService.execute_batch(batch_requests, user_id, team_id)
        
        # Parse results
        parsed = {}
        for i, req in enumerate(batch_requests):
            name = req.get("name", f"result_{i}")
            if i < len(results):
                data = FacebookBatchService.parse_batch_response(results[i])
                parsed[name] = data.get("data", []) if data else []
            else:
                parsed[name] = []
        
        return {
            "current": parsed.get("current_insights", [{}])[0] if parsed.get("current_insights") else {},
            "previous": parsed.get("previous_insights", [{}])[0] if parsed.get("previous_insights") else {},
            "daily": parsed.get("daily_trend", []),
            "date_range": {
                "start": start_date.strftime(date_fmt),
                "end": end_date.strftime(date_fmt)
            }
        }
    
    @staticmethod
    async def get_analytics_data_batch(
        account_id: str,
        user_id: int,
        since: str,
        until: str,
        prev_since: str = None,
        prev_until: str = None,
        level: str = "account",
        team_id: int = None
    ) -> Dict[str, Any]:
        """
        Fetch analytics page data in a single batch request.
        
        Combines:
        - Report data for selected level
        - Ad metadata (if level is 'ad')
        - Trend data for current and previous periods
        """
        fields = (
            "campaign_id,adset_id,ad_id,"
            "campaign_name,adset_name,ad_name,"
            "spend,impressions,reach,cpm,cpc,ctr,inline_link_clicks,clicks,"
            "actions,action_values,purchase_roas,"
            "quality_ranking,engagement_rate_ranking,conversion_rate_ranking,"
            "catalog_segment_value,catalog_segment_actions"
        )
        
        current_range = f'{{"since":"{since}","until":"{until}"}}'
        
        batch_requests = [
            {
                "name": "report_data",
                "method": "GET",
                "relative_url": f"{account_id}/insights?fields={fields}&time_range={current_range}&level={level}&time_increment=all_days&limit=500"
            },
            {
                "name": "current_trend",
                "method": "GET",
                "relative_url": f"{account_id}/insights?fields={fields}&time_range={current_range}&time_increment=1&level=account&limit=100"
            }
        ]
        
        # Add ad metadata request if level is 'ad'
        if level == "ad":
            batch_requests.append({
                "name": "ad_metadata",
                "method": "GET",
                "relative_url": f"{account_id}/ads?fields=id,effective_status,creative{{thumbnail_url,image_url}}&limit=1000"
            })
        
        # Add previous period trend if provided
        if prev_since and prev_until:
            prev_range = f'{{"since":"{prev_since}","until":"{prev_until}"}}'
            batch_requests.append({
                "name": "previous_trend",
                "method": "GET",
                "relative_url": f"{account_id}/insights?fields={fields}&time_range={prev_range}&time_increment=1&level=account&limit=100"
            })
        
        # Execute batch
        results = await FacebookBatchService.execute_batch(batch_requests, user_id, team_id)
        
        # Parse results
        parsed = {}
        for i, req in enumerate(batch_requests):
            name = req.get("name", f"result_{i}")
            if i < len(results):
                data = FacebookBatchService.parse_batch_response(results[i])
                parsed[name] = data.get("data", []) if data else []
            else:
                parsed[name] = []
        
        return {
            "report": parsed.get("report_data", []),
            "current_trend": parsed.get("current_trend", []),
            "previous_trend": parsed.get("previous_trend", []),
            "ad_metadata": parsed.get("ad_metadata", [])
        }
