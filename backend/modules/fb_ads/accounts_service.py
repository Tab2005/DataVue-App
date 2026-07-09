# backend/modules/fb_ads/accounts_service.py
"""
廣告帳號查詢服務。
提供取得使用者所有廣告帳號的非同步函式。
"""

import asyncio
import json
import sys
import logging
import httpx

logger = logging.getLogger(__name__)

from cache import get_account_cache, set_account_cache
from modules.fb_ads._base import BASE_URL, TIMEOUT, get_headers


async def get_all_ad_accounts(user_id, team_id=None, strict_token=False):
    """
    非同步取得所有廣告帳號（含快取）。

    同步段落（Redis 快取、TokenManager 的 DB 查詢+解密）一律包 to_thread：
    本函式跑在 event loop 上，同步 DB/Redis 呼叫遇到鎖等待或連線池耗盡時
    會凍結整個 backend（2026-07-08 事故，本函式兩度是凍結前最後一條日誌）。

    Returns:
        (accounts: list[dict], error: str | None)
        accounts 格式：[{'id': 'act_123', 'name': 'My Account'}]
    """
    # 先查快取
    cached = await asyncio.to_thread(get_account_cache, user_id, team_id)
    if cached is not None:
        return cached, None

    headers = await asyncio.to_thread(
        get_headers, user_id, team_id, not strict_token
    )
    if not headers:
        logger.warning("[FB ASYNC] get_all_ad_accounts: No token available")
        return [], "No access token found for this user."

    url = f"{BASE_URL}/me/adaccounts"
    params = {
        "fields": "name,account_id",
        "limit": 100,
    }

    try:
        logger.info("[FB ASYNC] Fetching Ad Accounts...")
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(url, headers=headers, params=params)
            logger.debug(f"[FB ASYNC] Response Status: {response.status_code}")
            data = response.json()

        if "error" in data:
            logger.error(f"Facebook API Error: {data['error']}")
            return [], data["error"].get("message")

        accounts = data.get("data", [])
        formatted = [
            {"id": acc.get("id"), "name": acc.get("name", "Unknown Account")}
            for acc in accounts
        ]
        formatted.sort(key=lambda x: x["name"])

        await asyncio.to_thread(set_account_cache, user_id, team_id, formatted)
        return formatted, None

    except Exception as e:
        logger.error("[FB ASYNC] Error in get_all_ad_accounts", exc_info=True)
        return [], str(e)


def _normalize_account_id_variants(raw_id: str) -> set[str]:
    """回傳 'act_123' 與 '123' 兩種型式，供白名單/可視集合比對時不受前綴差異影響。"""
    raw_id = str(raw_id or "")
    if not raw_id:
        return set()
    bare = raw_id[4:] if raw_id.startswith("act_") else raw_id
    return {raw_id, bare, f"act_{bare}"}


async def resolve_accessible_account_ids(current_user, team) -> tuple[set, str | None]:
    """回傳目前使用者（依 team context）可視的廣告帳號 ID 集合，供各模組做帳號
    層級授權檢查沿用（docs/27 任務 1.3）——複製 `routers/facebook.py`
    `get_ad_accounts` 端點的可視範圍判斷邏輯（owner 見自己 FB token 下的
    全部帳號；非 owner 依 `team.visible_ad_account_ids` 白名單過濾），但只
    回傳 ID 集合而非完整帳號資訊，且不依賴 request-scoped DB session（純以
    傳入的 ORM 物件屬性運算，呼叫端可在背景執行緒以 `asyncio.run` 呼叫）。

    contribution 模組讀寫本地快取表，不像 fb_ads 有「用自己 token 打 Meta
    API」的隱性授權門檻——任何有模組權限的使用者原本可用任意 account_id
    讀到其他團隊帳號的快取資料，此函式即用以補上這層檢查。

    回傳 (account_id 集合, error)；error 不為 None 時集合視為空，呼叫端應
    保守拒絕（不可放行）。集合內同時含 'act_123' 與 '123' 兩種型式。

    若此函式的邏輯與 `routers/facebook.py get_ad_accounts` 的可視範圍判斷
    未來分岔，兩處應一併檢視同步。
    """
    is_owner = bool(team) and str(team.owner_id) == str(current_user.id)
    fetch_team_id = team.id if (team and not is_owner) else None
    use_strict = is_owner or (fetch_team_id is None)

    accounts, error = await get_all_ad_accounts(
        current_user.google_id, team_id=fetch_team_id, strict_token=use_strict
    )
    if (not accounts or error) and is_owner:
        accounts, error = await get_all_ad_accounts(
            current_user.google_id, team_id=team.id if team else None
        )
    if error:
        return set(), error

    ids: set = set()
    for acc in accounts or []:
        acc_id = acc.get("id")
        if not acc_id:
            continue
        ids |= _normalize_account_id_variants(acc_id)

    if team and not is_owner and team.visible_ad_account_ids:
        try:
            whitelist = json.loads(team.visible_ad_account_ids)
        except (TypeError, ValueError):
            logger.warning(
                "[Contribution] resolve_accessible_account_ids: team %s "
                "visible_ad_account_ids 格式異常，保守回空集合",
                team.id,
            )
            return set(), None
        if not isinstance(whitelist, list):
            return set(), None
        whitelist_ids: set = set()
        for w in whitelist:
            whitelist_ids |= _normalize_account_id_variants(w)
        ids &= whitelist_ids

    return ids, None
