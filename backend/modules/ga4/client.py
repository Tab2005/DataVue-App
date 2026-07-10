"""
GA4 Module - Client
Google Analytics 4 低階 API 封裝

負責 OAuth 授權碼交換、token 刷新、Admin API 屬性列表、以及 Data API
RunReport 呼叫所需的底層物件（credentials / data client / metric 建構）。

不含快取、報表組裝、分頁邏輯 —— 那些是 service.py 的職責（docs/22 第 0 波重構，
自 ga4_service.py 抽出，行為需與抽出前完全一致）。
"""
from datetime import datetime, timedelta
import os
from typing import Any, Dict, List, Optional, Tuple

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.data import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import Metric
from sqlalchemy.orm import Session

from database import User

# Scopes required for GA4
SCOPES = [
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/analytics.edit',  # For property management
    'openid',
    'email',
    'profile'
]

# Metrics that require expressions (Virtual Metrics)
VIRTUAL_METRICS = {
    "averageEngagementTime": "userEngagementDuration/activeUsers",
}


class GA4Client:
    """低階 GA4 API 封裝：OAuth / Admin API / Data API RunReport 呼叫。"""

    SCOPES = SCOPES
    VIRTUAL_METRICS = VIRTUAL_METRICS

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
    def get_credentials(user: User, db: Session = None) -> Optional[Credentials]:
        """
        取得 Google Credentials 物件
        處理 token refresh 如果過期，並回寫資料庫

        Args:
            user: User 物件
            db: 資料庫 session（可選，用於更新 token）

        Returns:
            Credentials 物件或 None
        """
        if not user.ga4_access_token or not user.ga4_refresh_token:
            return None

        token = user.ga4_access_token
        refresh_token = user.ga4_refresh_token

        # 取得 expiry 時間（如果有的話）
        expiry = user.ga4_expires_at if hasattr(user, 'ga4_expires_at') else None

        creds = Credentials(
            token=token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=GA4Client.SCOPES,
            expiry=expiry  # 加入 expiry 讓 expired 檢查正確運作
        )

        # Check if token is expired or will expire soon (within 5 minutes)
        # Note: creds.expired 需要 expiry 才能正確判斷
        # 如果沒有 expiry 或 token 過期，嘗試刷新
        needs_refresh = False
        if expiry:
            # 檢查是否已過期或即將在 5 分鐘內過期
            if creds.expired or (expiry - datetime.utcnow()).total_seconds() < 300:
                needs_refresh = True
        else:
            # 沒有 expiry 資訊，嘗試呼叫 API 前先刷新
            needs_refresh = True

        if needs_refresh:
            try:
                creds.refresh(GoogleAuthRequest())
                print("[GA4] Token refreshed successfully")
                # 回寫新 token 到資料庫
                if db:
                    user.ga4_access_token = creds.token
                    user.ga4_expires_at = datetime.utcnow() + timedelta(seconds=3600)
                    db.commit()
                    print("[GA4] New token saved to database")
            except Exception as e:
                print(f"[GA4] Token refresh failed: {e}")
                return None

        return creds

    @staticmethod
    def list_properties(user: User, db: Session = None) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        列出用戶的 GA4 屬性
        使用 Google Analytics Admin API

        Args:
            user: User 物件
            db: 資料庫 session（可選，用於更新 token）

        Returns:
            tuple: (properties_list, error_message)
        """
        creds = GA4Client.get_credentials(user, db)
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
    def build_data_client(credentials: Credentials) -> BetaAnalyticsDataClient:
        """建立 Analytics Data API client（RunReport / RunRealtimeReport 共用）。"""
        return BetaAnalyticsDataClient(credentials=credentials)

    @staticmethod
    def build_metrics(metric_keys: List[str]) -> List[Metric]:
        """把指標名稱轉為 Data API 的 `Metric` 物件，虛擬指標帶入 expression。"""
        return [
            Metric(name=m, expression=GA4Client.VIRTUAL_METRICS[m]) if m in GA4Client.VIRTUAL_METRICS else Metric(name=m)
            for m in metric_keys
        ]
