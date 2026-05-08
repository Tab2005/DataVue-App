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
from cache import generate_cache_key, cache_get, cache_set, analytics_cache


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

    # Metrics that require expressions (Virtual Metrics)
    VIRTUAL_METRICS = {
        "averageEngagementTime": "userEngagementDuration/activeUsers",
    }

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
            scopes=GA4Service.SCOPES,
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
        creds = GA4Service.get_credentials(user, db)
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
        dimensions: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        db: Session = None
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
            db: 資料庫 session（可選，用於更新 token）

        Returns:
            tuple: (analytics_data, error_message)
        """
        creds = GA4Service.get_credentials(user, db)
        if not creds:
            return None, "No GA4 credentials found"

        try:
            # Ensure end_date does not exceed today (Google Analytics Data API rejects future dates)
            today_str = datetime.now().strftime("%Y-%m-%d")
            effective_end_date = min(end_date, today_str) if end_date > today_str else end_date
            
            if effective_end_date != end_date:
                print(f"[GA4] Capping end_date from {end_date} to {effective_end_date} for API request")
            
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

            # GA4 API Limit: Max 10 metrics per request.
            # If we have more than 10, we split and merge.
            if len(metrics) > 10:
                print(f"[GA4] Large request detected ({len(metrics)} metrics). Splitting into multiple requests...")
                
                # Split metrics into chunks of 10
                metric_chunks = [metrics[i:i + 10] for i in range(0, len(metrics), 10)]
                combined_results = None
                
                for chunk in metric_chunks:
                    chunk_result, chunk_err = GA4Service.get_analytics(
                        user=user,
                        property_id=property_id,
                        start_date=start_date,
                        end_date=end_date,
                        metrics=chunk,
                        dimensions=dimensions,
                        limit=limit,
                        offset=offset,
                        db=db
                    )
                    
                    if chunk_err:
                        return None, chunk_err
                        
                    if combined_results is None:
                        combined_results = chunk_result
                    else:
                        # Merge rows based on dimensions
                        # Assume rows are in the same order if limit/offset/dimensions are the same
                        # For extra safety, we could use dimension values as keys, but GA4 returns ordered results.
                        for i, row in enumerate(chunk_result.get("rows", [])):
                            if i < len(combined_results["rows"]):
                                combined_results["rows"][i].update(row)
                        
                        # Update metrics list in metadata
                        combined_results["metrics"].extend(chunk)
                
                return combined_results, None

            # 允許空的 dimensions 來獲取去重的總數
            # 如果 dimensions 是 None，使用預設值；如果是空列表或空字串，則不使用 dimension
            use_dimensions = True
            if dimensions is None:
                dimensions = ["date"]
            elif isinstance(dimensions, list) and len(dimensions) == 0:
                use_dimensions = False
            elif isinstance(dimensions, list) and len(dimensions) == 1 and dimensions[0] == '':
                use_dimensions = False

            # Use Analytics Data API
            data_client = BetaAnalyticsDataClient(credentials=creds)

            # Cache keys
            base_cache_key = generate_cache_key(
                "ga4_analytics",
                property_id,
                start_date,
                end_date,
                json.dumps(metrics, sort_keys=True),
                json.dumps(dimensions, sort_keys=True)
            )

            page_cache_key = None
            effective_limit = None
            if (limit is not None and limit > 0) or (offset and offset > 0):
                effective_limit = limit if limit is not None else 1000
                page_cache_key = generate_cache_key(
                    "ga4_analytics_page",
                    property_id,
                    start_date,
                    end_date,
                    json.dumps(metrics, sort_keys=True),
                    json.dumps(dimensions, sort_keys=True),
                    str(offset or 0),
                    str(effective_limit) if effective_limit is not None else ""
                )

            use_redis = bool(os.getenv("REDIS_URL"))
            redis_ttl = int(os.getenv("GA4_REDIS_TTL_SECONDS", "900"))

            def _convert_rows(rows):
                converted = []
                for row in rows:
                    row_data = {}

                    # Add dimension values
                    for i, dimension in enumerate(dimensions):
                        value = row.dimension_values[i].value
                        # 特殊處理日期格式：GA4 返回 YYYYMMDD -> 轉換為 YYYY-MM-DD
                        if dimension == "date" and len(value) == 8 and value.isdigit():
                            value = f"{value[:4]}-{value[4:6]}-{value[6:]}"
                        row_data[dimension] = value

                    # Add metric values
                    for i, metric in enumerate(metrics):
                        value = row.metric_values[i].value
                        # Convert string values to appropriate types
                        if metric in [
                            "activeUsers", "totalUsers", "newUsers", "sessions", "screenPageViews", 
                            "engagedSessions", "addToCarts", "ecommercePurchases", "itemsViewed", 
                            "itemsAddedToCart", "itemsPurchased", "totalPurchasers", "checkouts", 
                            "firstTimePurchasers", "conversions", "eventCount"
                        ]:
                            row_data[metric] = int(value)
                        elif metric in [
                            "averageSessionDuration", "bounceRate", "engagementRate", 
                            "purchaseRevenue", "itemRevenue", "totalRevenue",
                            "sessionConversionRate", "userConversionRate",
                            "averageEngagementTime", "screenPageViewsPerSession", "sessionsPerUser"
                        ]:
                            row_data[metric] = float(value)
                        else:
                            row_data[metric] = value

                    converted.append(row_data)
                return converted

            def _build_result(rows, total_row_count=None, limit_value=None, offset_value=0):
                return {
                    "property_id": property_id,
                    "date_range": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "dimensions": dimensions,
                    "metrics": metrics,
                    "row_count": len(rows),
                    "total_row_count": total_row_count if total_row_count is not None else len(rows),
                    "limit": limit_value,
                    "offset": offset_value,
                    "rows": rows
                }

            def _slice_cached(cached_result):
                all_rows = cached_result.get("rows", [])
                start = offset or 0
                slice_limit = limit if limit is not None else effective_limit
                end = start + slice_limit if slice_limit else None
                sliced = all_rows[start:end]
                total_row_count = cached_result.get("total_row_count", len(all_rows))
                result = {
                    **cached_result,
                    "rows": sliced,
                    "row_count": len(sliced),
                    "total_row_count": total_row_count,
                    "limit": slice_limit,
                    "offset": start
                }
                return result

            # Check cache（cache_get 自動處理 L1+L2 雙層快取、Redis 不可用時自動降級）
            if use_dimensions and (limit is not None or (offset and offset > 0)):
                cached_full = cache_get(base_cache_key)
                if cached_full is not None:
                    print(f"[GA4 CACHE HIT] Returning {len(cached_full.get('rows', []))} rows (full cached).")
                    return _slice_cached(cached_full), None

                if page_cache_key:
                    cached_page = cache_get(page_cache_key)
                    if cached_page is not None:
                        print(f"[GA4 CACHE HIT] Returning {len(cached_page.get('rows', []))} rows (page cached).")
                        return cached_page, None
            else:
                cached_data = cache_get(base_cache_key)
                if cached_data is not None:
                    print(f"[GA4 CACHE HIT] Returning {len(cached_data.get('rows', []))} rows.")
                    return cached_data, None

            # Helper to build metrics with expressions
            def _build_api_metrics(m_keys):
                return [
                    Metric(name=m, expression=GA4Service.VIRTUAL_METRICS[m]) if m in GA4Service.VIRTUAL_METRICS else Metric(name=m)
                    for m in m_keys
                ]

            # Build and execute the request(s)
            if not use_dimensions:
                # 不帶 dimension 的請求，會返回整個期間的去重總數
                request = RunReportRequest(
                    property=f"properties/{property_id}",
                    date_ranges=[DateRange(start_date=start_date, end_date=effective_end_date)],
                    metrics=_build_api_metrics(metrics),
                )
                dimensions = []  # 確保後續處理正確
                response = data_client.run_report(request)
                rows = _convert_rows(response.rows)
                total_row_count = getattr(response, "row_count", None)
                result = _build_result(rows, total_row_count, None, 0)

            elif limit is not None or (offset and offset > 0):
                request_limit = effective_limit if effective_limit is not None else limit
                request = RunReportRequest(
                    property=f"properties/{property_id}",
                    date_ranges=[DateRange(start_date=start_date, end_date=effective_end_date)],
                    dimensions=[Dimension(name=dim) for dim in dimensions],
                    metrics=_build_api_metrics(metrics),
                    limit=request_limit,
                    offset=offset
                )
                response = data_client.run_report(request)
                rows = _convert_rows(response.rows)
                total_row_count = getattr(response, "row_count", None)
                result = _build_result(rows, total_row_count, request_limit, offset)
            else:
                all_rows = []
                page_offset = 0
                page_limit = 100000
                total_row_count = None

                while True:
                    request = RunReportRequest(
                        property=f"properties/{property_id}",
                        date_ranges=[DateRange(start_date=start_date, end_date=effective_end_date)],
                        dimensions=[Dimension(name=dim) for dim in dimensions],
                        metrics=_build_api_metrics(metrics),
                        limit=page_limit,
                        offset=page_offset
                    )

                    response = data_client.run_report(request)
                    if total_row_count is None:
                        total_row_count = getattr(response, "row_count", None)

                    current_rows = _convert_rows(response.rows)
                    if not current_rows:
                        break

                    all_rows.extend(current_rows)

                    if len(response.rows) < page_limit:
                        break

                    page_offset += page_limit

                result = _build_result(all_rows, total_row_count, None, 0)

            # Cache result（cache_set 自動處理 L1+L2 雙層快取）
            _cache_ttl = redis_ttl if use_redis else int(analytics_cache.ttl)
            if use_dimensions and (limit is not None or (offset and offset > 0)):
                if page_cache_key:
                    cache_set(page_cache_key, result, _cache_ttl)
            else:
                cache_set(base_cache_key, result, _cache_ttl)
            print(f"[GA4 CACHE SET] Cached {result.get('row_count', 0)} rows (ttl={_cache_ttl}s).")

            print(f"[GA4] Analytics data retrieved: {len(result.get('rows', []))} rows")
            return result, None

        except Exception as e:
            print(f"[GA4] Error getting analytics: {e}")
            return None, str(e)

    @staticmethod
    async def get_weekly_report_data(
        user: User,
        property_id: str,
        since: str,
        until: str,
        selected_metrics: List[str],
        db: Session = None
    ) -> Dict[str, Any]:
        """
        取得週報所需的 GA4 數據格式 (Summary + Comparison + Trends)
        """
        # 推算前一期日期 (Comparison Period)
        since_dt = datetime.strptime(since, '%Y-%m-%d')
        until_dt = datetime.strptime(until, '%Y-%m-%d')
        duration = (until_dt - since_dt).days + 1
        prev_until = (since_dt - timedelta(days=1)).strftime('%Y-%m-%d')
        prev_since = (since_dt - timedelta(days=duration)).strftime('%Y-%m-%d')

        # 1. 抓取當前總計 (Summary) - 不帶 dimension
        current_summary_data, err = GA4Service.get_analytics(
            user=user, property_id=property_id, 
            start_date=since, end_date=until,
            metrics=selected_metrics, dimensions=[], db=db
        )
        if err: raise Exception(f"GA4 Summary Error: {err}")

        # 2. 抓取前期總計 (Prev Summary)
        prev_summary_data, err = GA4Service.get_analytics(
            user=user, property_id=property_id, 
            start_date=prev_since, end_date=prev_until,
            metrics=selected_metrics, dimensions=[], db=db
        )
        # 前期資料若抓取失敗，給予空物件但不報錯
        prev_summary = prev_summary_data["rows"][0] if prev_summary_data and prev_summary_data.get("rows") else {}

        # 3. 抓取趨勢資料 (Trends) - 帶 date dimension
        trend_data_raw, err = GA4Service.get_analytics(
            user=user, property_id=property_id, 
            start_date=since, end_date=until,
            metrics=selected_metrics, dimensions=["date"], db=db
        )

        # 4. 抓取表格明細資料 (Table Data) - 以 sessionSourceMedium 為維度 (常用於網站週報)
        table_data_raw, err = GA4Service.get_analytics(
            user=user, property_id=property_id, 
            start_date=since, end_date=until,
            metrics=selected_metrics, dimensions=["sessionSourceMedium"], db=db
        )

        return {
            "summary": current_summary_data["rows"][0] if current_summary_data["rows"] else {},
            "prev_summary": prev_summary,
            "trends": trend_data_raw["rows"] if trend_data_raw else [],
            "table_data": table_data_raw["rows"] if table_data_raw else []
        }