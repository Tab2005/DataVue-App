"""
  此模組已棄用（Deprecated）。
    原 async_services.py（834 行）已重構至 modules/fb_ads/ 套件。

遷移指引：
    舊版                                 新版
    
    from async_services import          from modules.fb_ads import (
        AsyncFacebookService                AsyncFacebookService,
                                            get_all_ad_accounts,
                                            get_account_insights,
                                            get_custom_report,
                                            get_analytics_trend,
                                        )
    METRICS_REGISTRY                    from modules.fb_ads.metrics_registry import METRICS_REGISTRY
    build_fb_fields                     from modules.fb_ads.metrics_registry import build_fb_fields

此橋接層維持向後相容性，未來版本將移除。
"""

#  向後相容再匯出 

from modules.fb_ads import (          # noqa: E402
    AsyncFacebookService,
    METRICS_REGISTRY,
    build_fb_fields,
    get_headers,
    get_all_ad_accounts,
    get_account_insights,
    get_custom_report,
    get_analytics_trend,
)

__all__ = [
    "AsyncFacebookService",
    "METRICS_REGISTRY",
    "build_fb_fields",
    "get_headers",
    "get_all_ad_accounts",
    "get_account_insights",
    "get_custom_report",
    "get_analytics_trend",
]
