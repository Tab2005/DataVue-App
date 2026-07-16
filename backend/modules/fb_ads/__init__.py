# backend/modules/fb_ads/__init__.py
"""
Facebook Ads 服務模組。
提供廣告帳號查詢、洞察數據、自訂報告、趨勢分析等功能。

模組結構：
  _base.py             — 共用常數（BASE_URL, TIMEOUT）與 get_headers
  metrics_registry.py  — METRICS_REGISTRY, build_fb_fields
  actions_parsing.py   — process_actions, format_kpi, format_charts
  accounts_service.py  — get_all_ad_accounts
  insights_service.py  — get_account_insights
  analytics_service.py — get_custom_report
  trends_service.py    — get_analytics_trend
"""

from modules.fb_ads._base import BASE_URL, TIMEOUT, get_headers
from modules.fb_ads.metrics_registry import METRICS_REGISTRY, build_fb_fields
from modules.fb_ads.actions_parsing import format_charts, format_kpi, process_actions
from modules.fb_ads.accounts_service import get_all_ad_accounts
from modules.fb_ads.insights_service import get_account_insights
from modules.fb_ads.analytics_service import get_custom_report
from modules.fb_ads.trends_service import get_analytics_trend


class AsyncFacebookService:
    """
    向後相容的 Facebook 廣告服務類別。
    所有方法均委派至對應的服務模組函式（staticmethod wrapper）。
    """

    BASE_URL = BASE_URL
    TIMEOUT = TIMEOUT

    @staticmethod
    def get_headers(user_id, team_id=None, allow_fallback=True):
        return get_headers(user_id, team_id, allow_fallback)

    @staticmethod
    async def get_all_ad_accounts(user_id, team_id=None, strict_token=False):
        return await get_all_ad_accounts(user_id, team_id, strict_token)

    @staticmethod
    async def get_account_insights(account_id, user_id, days=7, team_id=None, strict_token=False):
        return await get_account_insights(account_id, user_id, days, team_id, strict_token)

    @staticmethod
    async def get_custom_report(
        account_id, user_id, since, until,
        level="account", team_id=None, custom_fields=None, strict_token=False,
    ):
        return await get_custom_report(
            account_id, user_id, since, until, level, team_id, custom_fields, strict_token
        )

    @staticmethod
    async def get_analytics_trend(
        account_id, user_id, since, until,
        prev_since=None, prev_until=None, team_id=None, strict_token=False,
    ):
        return await get_analytics_trend(
            account_id, user_id, since, until, prev_since, prev_until, team_id, strict_token
        )


__all__ = [
    "AsyncFacebookService",
    "METRICS_REGISTRY",
    "build_fb_fields",
    "format_charts",
    "format_kpi",
    "get_headers",
    "get_all_ad_accounts",
    "get_account_insights",
    "get_custom_report",
    "get_analytics_trend",
    "process_actions",
]
