"""GA4 insights service facade."""

from __future__ import annotations

from ._shared import *
from .anomaly_rules import (
    _send_email_if_possible,
    acknowledge_event,
    build_alert_message,
    create_rule,
    delete_rule,
    evaluate_rule,
    list_available_key_events,
    list_events,
    list_rules,
    update_rule,
)
from .channel_groups import (
    delete_channel_group_rule,
    get_channel_group_match_conditions,
    list_channel_group_rules,
    list_channel_groups,
    upsert_channel_group_rule,
)
from .channels import _get_attribution_model, get_channels
from .dashboard import (
    MAX_CONVERSION_EVENTS,
    _compute_metric_baseline,
    _fetch_intraday_dashboard_payload,
    _refresh_dashboard_snapshot,
    get_dashboard,
    get_realtime,
    refresh_dashboard,
)
from .item_landing_cross import get_item_landing_cross
from .items import (
    delete_item_category_rule,
    get_items,
    list_item_category_rules,
    upsert_item_category_rule,
)
from .kpi import (
    _kpi_period_bounds,
    compute_kpi_pacing,
    delete_kpi_target,
    get_kpi_targets_with_pacing,
    save_ai_summary,
    upsert_kpi_target,
)
from .landing_pages import (
    delete_landing_page_rule,
    get_landing_pages,
    list_landing_page_rules,
    upsert_landing_page_rule,
)
from .sharing import create_share_link, get_snapshot_by_share_token, revoke_share_links


class GA4InsightsService:
    list_rules = staticmethod(list_rules)
    create_rule = staticmethod(create_rule)
    update_rule = staticmethod(update_rule)
    delete_rule = staticmethod(delete_rule)
    list_events = staticmethod(list_events)
    acknowledge_event = staticmethod(acknowledge_event)
    list_available_key_events = staticmethod(list_available_key_events)
    _format_metric_value = staticmethod(_format_metric_value)
    build_alert_message = staticmethod(build_alert_message)
    _fetch_metric_total = staticmethod(_fetch_metric_total)
    _historical_dates = staticmethod(_historical_dates)
    _send_email_if_possible = staticmethod(_send_email_if_possible)
    evaluate_rule = staticmethod(evaluate_rule)

    _fetch_intraday_dashboard_payload = staticmethod(_fetch_intraday_dashboard_payload)
    _compute_metric_baseline = staticmethod(_compute_metric_baseline)
    _refresh_dashboard_snapshot = staticmethod(_refresh_dashboard_snapshot)
    get_dashboard = staticmethod(get_dashboard)
    refresh_dashboard = staticmethod(refresh_dashboard)
    get_realtime = staticmethod(get_realtime)

    _trailing_period = staticmethod(_trailing_period)
    _get_attribution_model = staticmethod(_get_attribution_model)
    get_channels = staticmethod(get_channels)

    get_landing_pages = staticmethod(get_landing_pages)
    list_landing_page_rules = staticmethod(list_landing_page_rules)
    upsert_landing_page_rule = staticmethod(upsert_landing_page_rule)
    delete_landing_page_rule = staticmethod(delete_landing_page_rule)

    list_channel_group_rules = staticmethod(list_channel_group_rules)
    upsert_channel_group_rule = staticmethod(upsert_channel_group_rule)
    delete_channel_group_rule = staticmethod(delete_channel_group_rule)
    list_channel_groups = staticmethod(list_channel_groups)
    get_channel_group_match_conditions = staticmethod(get_channel_group_match_conditions)

    get_items = staticmethod(get_items)
    list_item_category_rules = staticmethod(list_item_category_rules)
    upsert_item_category_rule = staticmethod(upsert_item_category_rule)
    delete_item_category_rule = staticmethod(delete_item_category_rule)

    get_item_landing_cross = staticmethod(get_item_landing_cross)

    save_ai_summary = staticmethod(save_ai_summary)
    create_share_link = staticmethod(create_share_link)
    get_snapshot_by_share_token = staticmethod(get_snapshot_by_share_token)
    revoke_share_links = staticmethod(revoke_share_links)
    _kpi_period_bounds = staticmethod(_kpi_period_bounds)
    compute_kpi_pacing = staticmethod(compute_kpi_pacing)
    get_kpi_targets_with_pacing = staticmethod(get_kpi_targets_with_pacing)
    upsert_kpi_target = staticmethod(upsert_kpi_target)
    delete_kpi_target = staticmethod(delete_kpi_target)


# docs/59 P2-5：明列對外的 API。之前的 globals() 推導式會把 `os`、`smtplib`、
# `datetime` 這些經由 `from ._shared import *` 帶進來的符號一起匯出，
# `insights_service.py` 再 `from .insights import *`，一層一層放大。
#
# 注意：測試用 `mocker.patch("modules.ga4.insights.dashboard.X")` 這種子模組路徑
# 不受 `__all__` 影響（那是模組屬性，不是星號匯出）；受影響的是
# `modules.ga4.insights_service.GA4Service` 這種靠星號傳遞下來的名字。
# docs/59 P2-5：明列對外的 API。之前的 globals() 推導式會把 `os`、`smtplib`、
# `datetime`、`median` 這些經由 `from ._shared import *` 帶進來的符號一起匯出，
# `insights_service.py` 再 `from .insights import *`，一層一層放大。
#
# 下半部那組是從 `_shared` 星號帶下來、但外部（insights_router / scheduler /
# 測試）確實會用到的，不能漏——漏了會是 import 時就爆的 ImportError。
#
# 注意：`mocker.patch("modules.ga4.insights.dashboard.X")` 這種子模組路徑不受
# `__all__` 影響（那是模組屬性，不是星號匯出）。
__all__ = [
    "ATTRIBUTION_SETTINGS_DATE",
    "ATTRIBUTION_SETTINGS_KIND",
    "CHANNEL_MIN_SAMPLE",
    "DASHBOARD_KIND",
    "GA4Client",
    "GA4InsightsService",
    "GA4Service",
    "LANDING_PAGE_KEY_EVENT_PATTERN",
    "MAX_CONVERSION_EVENTS",
    "_compute_metric_baseline",
    "_fetch_intraday_dashboard_payload",
    "_get_attribution_model",
    "_kpi_period_bounds",
    "_percentile",
    "_refresh_dashboard_snapshot",
    "_send_email_if_possible",
    "_trailing_period",
    "acknowledge_event",
    "build_alert_message",
    "classify_item_category",
    "classify_landing_page",
    "compute_kpi_pacing",
    "create_rule",
    "create_share_link",
    "delete_channel_group_rule",
    "delete_item_category_rule",
    "delete_kpi_target",
    "delete_landing_page_rule",
    "delete_rule",
    "evaluate_rule",
    "get_channel_group_match_conditions",
    "get_channels",
    "get_dashboard",
    "get_item_landing_cross",
    "get_items",
    "get_kpi_targets_with_pacing",
    "get_landing_pages",
    "get_realtime",
    "get_snapshot_by_share_token",
    "list_available_key_events",
    "list_channel_group_rules",
    "list_channel_groups",
    "list_events",
    "list_item_category_rules",
    "list_landing_page_rules",
    "list_rules",
    "refresh_dashboard",
    "repository",
    "revoke_share_links",
    "save_ai_summary",
    "update_rule",
    "upsert_channel_group_rule",
    "upsert_item_category_rule",
    "upsert_kpi_target",
    "upsert_landing_page_rule",
]
