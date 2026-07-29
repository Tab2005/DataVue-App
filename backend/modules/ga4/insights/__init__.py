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
from .sharing import create_share_link, get_snapshot_by_share_token


class GA4InsightsService:
    list_rules = staticmethod(list_rules)
    create_rule = staticmethod(create_rule)
    update_rule = staticmethod(update_rule)
    delete_rule = staticmethod(delete_rule)
    list_events = staticmethod(list_events)
    acknowledge_event = staticmethod(acknowledge_event)
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
    _kpi_period_bounds = staticmethod(_kpi_period_bounds)
    compute_kpi_pacing = staticmethod(compute_kpi_pacing)
    get_kpi_targets_with_pacing = staticmethod(get_kpi_targets_with_pacing)
    upsert_kpi_target = staticmethod(upsert_kpi_target)
    delete_kpi_target = staticmethod(delete_kpi_target)


__all__ = [name for name in globals() if not name.startswith("__")]
