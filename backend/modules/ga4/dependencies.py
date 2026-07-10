"""GA4 insights module dependencies."""

from modules.auth.dependencies import get_current_team, get_current_user, require_module, require_permission

require_ga4_module = require_module("ga4")
require_ga4_insights_view = require_permission("ga4:insights:view")
require_ga4_insights_manage_alerts = require_permission("ga4:insights:manage_alerts")

__all__ = [
    "get_current_team",
    "get_current_user",
    "require_ga4_module",
    "require_ga4_insights_view",
    "require_ga4_insights_manage_alerts",
]
