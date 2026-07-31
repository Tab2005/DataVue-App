"""GA4 insights module dependencies."""

import logging

from fastapi import Depends, Header, HTTPException, status

from cache import cache_get, cache_set, generate_cache_key
from database import User
from modules.auth.dependencies import get_current_team, get_current_user, get_db, require_module, require_permission

from .client import GA4Client
from .repository import repository

logger = logging.getLogger(__name__)

# 授權慢路徑（GA4 Admin API 屬性清單）的快取秒數。屬性存取權變動極少，但這是
# 授權判斷，撤銷權限最多延遲這麼久才生效，所以取比一般資料快取更短的 5 分鐘。
_PROPERTY_LIST_CACHE_TTL = 300

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


# ─── 屬性層級授權（docs/60；補 docs/59 P0-2 / P0-3 的 IDOR） ─────────
#
# `require_ga4_insights_*` 只確認「這個人能不能用洞察功能」，不確認「這筆
# 資料是不是他的」。查詢類端點（dashboard / landing-pages / items…）有隱性
# 門檻——它們一律用呼叫者自己的 GA4 OAuth 憑證打 Data API，讀不到的
# property 會直接錯誤；但快照類（ai-summary / share）與規則/KPI 類端點是
# 純本地資料表讀寫，沒有這層隱性門檻，任何有洞察權限的登入者只要拿到
# 別人的 snapshot_id / rule_id 就能改寫甚至對外發佈他人資料。
#
# 這裡補上的檢查沿用 contribution 模組（docs/27 任務 1.3）的同一套慣例：
#   - property_id 是顯式參數的端點 → 未授權回 403
#   - 資源 id 是路徑參數的端點     → 未授權回 404，且訊息與「不存在」相同，
#     避免探測者用狀態碼或訊息差異判斷某個 id 是否存在
def has_ga4_property_access(db, *, user: User, property_id: str) -> bool:
    """判斷 `user` 是否可存取 `property_id`。

    兩段式，先快後慢：

    1. 快路徑：查本地快照表有沒有「這個使用者自己抓過這個 property」的紀錄
       （`repository.user_has_fetched_property`）。實務上使用者一定是先載入
       某個分頁的數據、才會去存 AI 解讀或編輯規則，所以絕大多數請求在這裡
       就結束，不需要任何對外呼叫。
    2. 慢路徑：冷啟動（還沒載入過任何數據就先開規則清單）時改問 GA4 Admin
       API 該使用者可存取的 property 清單。查詢失敗一律保守拒絕（同
       contribution `resolve_accessible_account_ids` 的 error → 拒絕慣例）。
    """
    if repository.user_has_fetched_property(db, user_id=user.id, property_id=property_id):
        return True

    accessible = _accessible_property_ids(user, db)
    if accessible is None:
        return False
    return str(property_id) in accessible


def _accessible_property_ids(user: User, db) -> set[str] | None:
    """慢路徑：GA4 Admin API 的屬性清單，快取 `_PROPERTY_LIST_CACHE_TTL` 秒。

    `GA4Client.list_properties` 是 list_accounts + 每個 account 一次
    list_properties，帳號多時要好幾秒；而載入洞察頁時多支規則/KPI 清單請求
    幾乎同時發出，冷啟動不快取就會重複打好幾輪。查詢失敗**不寫入快取**，
    避免一次暫時性錯誤把使用者鎖在門外整個 TTL。

    回傳 None 表示查詢失敗（呼叫端應保守拒絕），與「查得到但清單為空」區分。
    """
    cache_key = generate_cache_key("ga4_accessible_properties", user.id)
    cached = cache_get(cache_key)
    if cached is not None:
        return set(cached)

    properties, error = GA4Client.list_properties(user, db)
    if error:
        logger.warning(
            "[GA4Insights] property access check fell back to Admin API and failed (user=%s): %s",
            user.id, error,
        )
        return None

    property_ids = [str(item.get("property_id")) for item in (properties or []) if item.get("property_id")]
    cache_set(cache_key, property_ids, ttl=_PROPERTY_LIST_CACHE_TTL)
    return set(property_ids)


def verify_ga4_property_access_or_403(db, *, user: User, property_id: str) -> None:
    """property_id 為顯式 query/body 參數的端點用；不可存取則 403。"""
    if not has_ga4_property_access(db, user=user, property_id=property_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"無權存取 GA4 屬性 {property_id}",
        )


# 資源 id → (repository 取用函式, 未授權/不存在共用的 404 訊息)。訊息刻意與
# 各端點原本「查無此資源」的 detail 逐字相同，讓兩種情況無法被外部區分。
_GA4_RESOURCE_LOOKUPS = {
    "snapshot": (repository.get_snapshot_by_id, "Snapshot not found"),
    "landing_page_rule": (repository.get_landing_page_rule, "Landing page rule not found"),
    "item_category_rule": (repository.get_item_category_rule, "Item category rule not found"),
    "channel_group_rule": (repository.get_channel_group_rule, "Channel group rule not found"),
    "kpi_target": (repository.get_kpi_target, "KPI target not found"),
}


def require_ga4_resource_access_or_404(db, *, user: User, resource: str, resource_id: str):
    """資源 id 為路徑/body 參數的端點用：取出該列並確認其 property 對呼叫者
    可存取，兩種失敗（不存在／無權）都回同一個 404。回傳取出的 ORM 列，
    呼叫端可直接沿用，不必再查一次。"""
    getter, detail = _GA4_RESOURCE_LOOKUPS[resource]
    row = getter(db, resource_id)
    if row is None or not has_ga4_property_access(db, user=user, property_id=row.property_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return row


__all__ = [
    "get_current_team",
    "get_current_user",
    "has_ga4_property_access",
    "require_ga4_module",
    "require_ga4_insights_view",
    "require_ga4_insights_manage_alerts",
    "require_ga4_resource_access_or_404",
    "verify_ga4_property_access_or_403",
]
