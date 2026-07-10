"""
GA4 Module - Service
Google Analytics 4 報表組裝服務

負責 RunReport 結果的快取、分頁、大量指標拆分、型別轉換，以及週報所需的
Summary/Comparison/Trends 資料組裝。低階 OAuth / RunReport 呼叫見 client.py
（docs/22 第 0 波重構，自 ga4_service.py 抽出，行為需與抽出前完全一致）。
"""
from datetime import datetime, timedelta
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension
from sqlalchemy.orm import Session

from database import User
from cache import generate_cache_key, cache_get, cache_set, analytics_cache
from .client import GA4Client


class GA4AnalyticsService:
    """GA4 報表資料組裝：快取、分頁、指標拆分、Summary/Trends 組裝。"""

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
        creds = GA4Client.get_credentials(user, db)
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
                    chunk_result, chunk_err = GA4AnalyticsService.get_analytics(
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
            data_client = GA4Client.build_data_client(creds)

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
                        # GA4 支援「單一事件口徑」的動態指標，如 keyEvents:purchase、
                        # sessionKeyEventRate:purchase（docs/22 第 5 波）；型別判斷要看
                        # 冒號前的基礎指標名，冒號後的事件名不影響型別。
                        base_metric = metric.split(":", 1)[0]
                        # Convert string values to appropriate types
                        if base_metric in [
                            "activeUsers", "totalUsers", "newUsers", "sessions", "screenPageViews",
                            "engagedSessions", "addToCarts", "ecommercePurchases", "itemsViewed",
                            "itemsAddedToCart", "itemsPurchased", "totalPurchasers", "checkouts",
                            "firstTimePurchasers", "conversions", "eventCount", "keyEvents"
                        ]:
                            row_data[metric] = int(value)
                        elif base_metric in [
                            "averageSessionDuration", "bounceRate", "engagementRate",
                            "purchaseRevenue", "itemRevenue", "totalRevenue",
                            "sessionConversionRate", "userConversionRate", "sessionKeyEventRate",
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
                return GA4Client.build_metrics(m_keys)

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
        current_summary_data, err = GA4AnalyticsService.get_analytics(
            user=user, property_id=property_id,
            start_date=since, end_date=until,
            metrics=selected_metrics, dimensions=[], db=db
        )
        if err: raise Exception(f"GA4 Summary Error: {err}")

        # 2. 抓取前期總計 (Prev Summary)
        prev_summary_data, err = GA4AnalyticsService.get_analytics(
            user=user, property_id=property_id,
            start_date=prev_since, end_date=prev_until,
            metrics=selected_metrics, dimensions=[], db=db
        )
        # 前期資料若抓取失敗，給予空物件但不報錯
        prev_summary = prev_summary_data["rows"][0] if prev_summary_data and prev_summary_data.get("rows") else {}

        # 3. 抓取趨勢資料 (Trends) - 帶 date dimension
        trend_data_raw, err = GA4AnalyticsService.get_analytics(
            user=user, property_id=property_id,
            start_date=since, end_date=until,
            metrics=selected_metrics, dimensions=["date"], db=db
        )

        # 4. 抓取表格明細資料 (Table Data) - 以 sessionSourceMedium 為維度 (常用於網站週報)
        table_data_raw, err = GA4AnalyticsService.get_analytics(
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
