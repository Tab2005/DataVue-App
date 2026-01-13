"""
GA4 Service
Google Analytics 4 整合服務

實作 GA4 的 OAuth 認證、屬性列表、分析資料等功能。
使用 Google Analytics Admin API 和 Google Analytics Data API。
"""
from datetime import datetime, timedelta
import os
import sys
import json
from typing import List, Dict, Any, Optional, Tuple
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build
from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.data import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Dimension,
    Metric,
    FilterExpression,
    Filter
)
from sqlalchemy.orm import Session
from database import User


class GA4Service:
    """
    Google Analytics 4 Service
    處理 GA4 API 的所有操作
    """

    # Scopes required for GA4
    SCOPES = [
        'https://www.googleapis.com/auth/analytics.readonly',
        'https://www.googleapis.com/auth/analytics.edit',  # For property management
        'openid',
        'email',
        'profile'
    ]

    @staticmethod
    def exchange_code(user: User, code: str, db: Session) -> Tuple[bool, str]:
        """
        交換授權碼取得 GA4 access token 和 refresh token

        Args:
            user: User 物件
            code: 授權碼
            db: 資料庫 session

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            import requests

            client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

            if not client_id or not client_secret:
                return False, "Google OAuth credentials not configured"

            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": "postmessage",
                "grant_type": "authorization_code"
            }

            print(f"[GA4] Attempting token exchange...")
            print(f"[GA4] Auth Code Length: {len(code)}")

            # Try multiple redirect_uris to handle different frontend configurations
            redirect_uris = [
                "postmessage",
                "http://localhost:5173",
                "http://localhost:5173/"
            ]

            response = None
            success = False

            # 1. Standard attempts with Secret
            for uri in redirect_uris:
                print(f"[GA4] Trying URI='{uri}' WITH SECRET")
                data["redirect_uri"] = uri
                data["client_secret"] = client_secret

                response = requests.post(token_url, data=data, timeout=30)
                print(f"[GA4] Status: {response.status_code}")

                if response.status_code == 200:
                    success = True
                    break

                err = response.json().get('error')
                print(f"[GA4] Error: {err}")

            # 2. If all failed, try WITHOUT Secret (in case it's treated as Public Client)
            if not success:
                print("[GA4] Trying attempts WITHOUT SECRET")
                del data["client_secret"]
                for uri in redirect_uris:
                    print(f"[GA4] Trying URI='{uri}' NO SECRET")
                    data["redirect_uri"] = uri
                    response = requests.post(token_url, data=data, timeout=30)
                    print(f"[GA4] Status: {response.status_code}")
                    if response.status_code == 200:
                        success = True
                        break
                    print(f"[GA4] Error: {response.json().get('error')}")

            if not success:
                error_detail = response.json() if response else {"error": "Unknown"}
                print(f"[GA4] ERROR BODY: {error_detail}")
                return False, f"Google Auth Error: {error_detail.get('error')} - {error_detail.get('error_description')}"

            tokens = response.json()

            # Update User with GA4 tokens
            user.ga4_access_token = tokens.get("access_token")
            if "refresh_token" in tokens:
                user.ga4_refresh_token = tokens.get("refresh_token")
            user.ga4_expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))

            db.commit()
            print("[GA4] Successfully connected to Google Analytics 4")
            return True, "Successfully connected to Google Analytics 4"

        except Exception as e:
            import traceback
            print("[GA4] === AUTH ERROR START ===")
            traceback.print_exc()
            print("[GA4] === AUTH ERROR END ===")
            return False, str(e)

    @staticmethod
    def get_credentials(user: User) -> Optional[Credentials]:
        """
        取得 Google Credentials 物件
        處理 token refresh 如果過期

        Args:
            user: User 物件

        Returns:
            Credentials 物件或 None
        """
        if not user.ga4_access_token or not user.ga4_refresh_token:
            return None

        token = user.ga4_access_token
        refresh_token = user.ga4_refresh_token

        creds = Credentials(
            token=token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=GA4Service.SCOPES
        )

        # Check if token is expired and refresh if needed
        if creds.expired:
            try:
                creds.refresh(GoogleAuthRequest())
                print("[GA4] Token refreshed successfully")
            except Exception as e:
                print(f"[GA4] Token refresh failed: {e}")
                return None

        return creds

    @staticmethod
    def list_properties(user: User) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        列出用戶的 GA4 屬性
        使用 Google Analytics Admin API

        Args:
            user: User 物件

        Returns:
            tuple: (properties_list, error_message)
        """
        creds = GA4Service.get_credentials(user)
        if not creds:
            return [], "No GA4 credentials found"

        try:
            # Use Analytics Admin API to list properties
            admin_client = AnalyticsAdminServiceClient(credentials=creds)

            def _ts_to_str(value: Any) -> Optional[str]:
                if value is None:
                    return None
                try:
                    return value.ToJsonString()
                except Exception:
                    return str(value)

            # Google Admin API v1alpha 的 properties.list 需要 filter
            # 先列出可存取的 accounts，再針對每個 account 以 parent filter 列出 properties
            properties_by_id: Dict[str, Dict[str, Any]] = {}

            accounts_pager = admin_client.list_accounts()
            accounts = list(accounts_pager)
            print(f"[GA4][DEBUG] list_accounts -> {len(accounts)} accounts")
            if accounts:
                account_names = [getattr(a, "name", "<unknown>") for a in accounts]
                print(f"[GA4][DEBUG] account names: {account_names}")
            if not accounts:
                return [], "No GA4 accounts found"

            for account in accounts:
                # account.name 會是像 "accounts/123" 的資源名稱
                filter_value = f"parent:{account.name}"
                print(f"[GA4][DEBUG] list_properties filter={filter_value}")
                props_pager = admin_client.list_properties(request={"filter": filter_value})

                count_for_account = 0
                for prop in props_pager:
                    count_for_account += 1
                    prop_id = prop.name.split("/")[-1]
                    properties_by_id[prop_id] = {
                        "property_id": prop_id,
                        "display_name": getattr(prop, "display_name", None),
                        "property_name": prop.name,
                        "create_time": _ts_to_str(getattr(prop, "create_time", None)),
                        "update_time": _ts_to_str(getattr(prop, "update_time", None)),
                        "currency_code": getattr(prop, "currency_code", None),
                        "time_zone": getattr(prop, "time_zone", None),
                        "parent": getattr(prop, "parent", None),
                    }

                print(f"[GA4][DEBUG] properties under {account.name}: {count_for_account}")

            properties = list(properties_by_id.values())

            print(f"[GA4] Found {len(properties)} properties")
            return properties, None

        except Exception as e:
            print(f"[GA4] Error listing properties: {e}")
            return [], str(e)

    @staticmethod
    def get_analytics(
        user: User,
        property_id: str,
        start_date: str,
        end_date: str,
        metrics: Optional[List[str]] = None,
        dimensions: Optional[List[str]] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        取得 GA4 分析資料
        使用 Google Analytics Data API

        Args:
            user: User 物件
            property_id: GA4 屬性 ID
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            metrics: 指標列表，預設使用常見指標
            dimensions: 維度列表，預設使用日期

        Returns:
            tuple: (analytics_data, error_message)
        """
        creds = GA4Service.get_credentials(user)
        if not creds:
            return None, "No GA4 credentials found"

        try:
            # Default metrics and dimensions if not provided
            if metrics is None:
                metrics = [
                    "activeUsers",      # 活躍用戶
                    "totalUsers",       # 總用戶
                    "newUsers",         # 新用戶
                    "sessions",         # 工作階段
                    "screenPageViews",  # 頁面瀏覽
                    "averageSessionDuration",  # 平均工作階段持續時間
                    "bounceRate"        # 跳出率
                ]

            if dimensions is None:
                dimensions = ["date"]

            # Use Analytics Data API
            data_client = BetaAnalyticsDataClient(credentials=creds)

            # Build the request
            request = RunReportRequest(
                property=f"properties/{property_id}",
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimensions=[Dimension(name=dim) for dim in dimensions],
                metrics=[Metric(name=met) for met in metrics],
            )

            # Execute the report
            response = data_client.run_report(request)

            # Format the response
            result = {
                "property_id": property_id,
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "dimensions": dimensions,
                "metrics": metrics,
                "row_count": len(response.rows),
                "rows": []
            }

            # Process each row
            for row in response.rows:
                row_data = {}

                # Add dimension values
                for i, dimension in enumerate(dimensions):
                    row_data[dimension] = row.dimension_values[i].value

                # Add metric values
                for i, metric in enumerate(metrics):
                    value = row.metric_values[i].value
                    # Convert string values to appropriate types
                    if metric in ["activeUsers", "totalUsers", "newUsers", "sessions", "screenPageViews"]:
                        row_data[metric] = int(value)
                    elif metric in ["averageSessionDuration"]:
                        row_data[metric] = float(value)
                    elif metric in ["bounceRate"]:
                        row_data[metric] = float(value)
                    else:
                        row_data[metric] = value

                result["rows"].append(row_data)

            print(f"[GA4] Analytics data retrieved: {len(result['rows'])} rows")
            return result, None

        except Exception as e:
            print(f"[GA4] Error getting analytics: {e}")
            return None, str(e)