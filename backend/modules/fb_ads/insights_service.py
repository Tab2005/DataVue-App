# backend/modules/fb_ads/insights_service.py
"""
廣告帳號洞察數據（KPI + 趨勢圖表）服務。
對應原 AsyncFacebookService.get_account_insights。
"""

import sys
import asyncio
import httpx
from datetime import datetime, timedelta

from cache import get_insights_cache, set_insights_cache
from modules.fb_ads._base import BASE_URL, TIMEOUT, get_headers


async def get_account_insights(account_id, user_id, days=7, team_id=None, strict_token=False):
    """
    非同步取得帳號廣告洞察（含快取、並行抓取前後期資料與趨勢）。

    Returns:
        dict | None：含 kpi、chart_data、date_range 的結構化結果
    """
    # 先查快取
    cached = get_insights_cache(account_id, days)
    if cached is not None:
        return cached

    headers = get_headers(user_id, team_id, allow_fallback=not strict_token)
    if not headers:
        return None

    date_preset = "last_7d" if days == 7 else "last_30d"
    fields = (
        "spend,impressions,reach,cpm,cpc,ctr,inline_link_clicks,clicks,unique_clicks,unique_ctr,"
        "inline_link_click_ctr,outbound_clicks,outbound_clicks_ctr,"
        "actions,action_values,purchase_roas"
    )

    url = f"{BASE_URL}/{account_id}/insights"
    current_params = {
        "fields": fields,
        "date_preset": date_preset,
        "level": "account",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            cur_response = await client.get(url, headers=headers, params=current_params)
            cur_res = cur_response.json()

            if "error" in cur_res:
                print("[FB ASYNC] API Error in insights", file=sys.stderr)
                return None

            cur_data_list = cur_res.get("data", [])
            cur_data = cur_data_list[0] if cur_data_list else {}

            # 計算日期範圍
            date_start = cur_data.get("date_start")
            date_stop = cur_data.get("date_stop")
            fmt = "%Y-%m-%d"

            if not date_start or not date_stop:
                today = datetime.now()
                d_stop = today - timedelta(days=1)
                d_start = d_stop - timedelta(days=days - 1)
                date_start = d_start.strftime(fmt)
                date_stop = d_stop.strftime(fmt)
                cur_data["date_start"] = date_start
                cur_data["date_stop"] = date_stop

            d_start = datetime.strptime(date_start, fmt)
            d_stop = datetime.strptime(date_stop, fmt)
            delta = d_stop - d_start + timedelta(days=1)

            prev_start = (d_start - delta).strftime(fmt)
            prev_stop = (d_start - timedelta(days=1)).strftime(fmt)

            prev_params = {
                "fields": fields,
                "level": "account",
                "time_range": f'{{"since":"{prev_start}","until":"{prev_stop}"}}',
            }

            trend_fields = (
                "spend,impressions,inline_link_clicks,ctr,cpc,unique_clicks,unique_ctr,"
                "inline_link_click_ctr,outbound_clicks,outbound_clicks_ctr,"
                "actions,action_values,purchase_roas"
            )
            trend_params = {
                "fields": trend_fields,
                "date_preset": date_preset,
                "time_increment": "1",
                "level": "account",
            }

            # 並行抓取前期資料 + 趨勢資料
            prev_response, trend_response = await asyncio.gather(
                client.get(url, headers=headers, params=prev_params),
                client.get(url, headers=headers, params=trend_params),
            )

            prev_res = prev_response.json()
            trend_res = trend_response.json()

        prev_data_list = prev_res.get("data", [])
        prev_data = prev_data_list[0] if prev_data_list else {}
        trend_list = trend_res.get("data", [])

        from services import FacebookService

        result = {
            "kpi": FacebookService._format_kpi(cur_data, prev_data),
            "chart_data": FacebookService._format_charts(trend_list),
            "date_range": {
                "start": date_start,
                "stop": date_stop,
            },
        }

        set_insights_cache(account_id, days, result)
        return result

    except Exception as e:
        print("[FB ASYNC] Error fetching insights", file=sys.stderr)
        return None
