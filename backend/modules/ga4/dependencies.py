"""GA4 insights module dependencies."""

from fastapi import Depends, Header

from database import User
from modules.auth.dependencies import get_current_team, get_current_user, get_db, require_module, require_permission

require_ga4_module = require_module("ga4")


def _require_ga4_insights_permission(permission_key: str):
    """
    ga4:insights:* 權限守門。

    `PermissionService.check_permission` 對「個人工作區」（無 X-Team-ID）的
    細項權限一律預設拒絕（見 `services/permission_service.py` 步驟 5、
    `tests/test_permissions.py::test_require_permission_uses_x_team_id_for_team_role_permissions`
    的既有測試契約）——這是團隊情境下用來區分成員角色的刻意設計，但 GA4 是
    per-user OAuth（docs/22 2.1 節），洞察頁本就該讓「沒有團隊、自己接 GA4」
    的個人工作區使用者可用，比照既有 `/api/ga4/report`（只掛
    `require_module("ga4")`，無細項權限）的慣例。

    因此這裡分流：有 X-Team-ID（團隊工作區）才走 `require_permission`（沿用
    角色權限矩陣，team_member/viewer 只有 view、team_admin 才有
    manage_alerts）；沒有 X-Team-ID（個人工作區）則退回只檢查模組存取，
    與 `/api/ga4/report` 一致，不因為新增細項權限反而讓個人工作區用不了。
    """
    permission_checker = require_permission(permission_key)
    module_checker = require_module("ga4")

    def checker(
        user: User = Depends(get_current_user),
        db=Depends(get_db),
        x_team_id: str | None = Header(default=None),
    ):
        if not x_team_id:
            return module_checker(user=user, db=db, x_team_id=x_team_id)
        return permission_checker(user=user, db=db, x_team_id=x_team_id)

    return checker


require_ga4_insights_view = _require_ga4_insights_permission("ga4:insights:view")
require_ga4_insights_manage_alerts = _require_ga4_insights_permission("ga4:insights:manage_alerts")

__all__ = [
    "get_current_team",
    "get_current_user",
    "require_ga4_module",
    "require_ga4_insights_view",
    "require_ga4_insights_manage_alerts",
]
