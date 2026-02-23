# backend/modules/fb_ads/accounts_service.py
"""
廣告帳號查詢服務。
提供取得使用者所有廣告帳號的非同步函式。
"""

import sys
import logging
import httpx

logger = logging.getLogger(__name__)

from cache import get_account_cache, set_account_cache
from modules.fb_ads._base import BASE_URL, TIMEOUT, get_headers


async def get_all_ad_accounts(user_id, team_id=None, strict_token=False):
    """
    非同步取得所有廣告帳號（含快取）。

    Returns:
        (accounts: list[dict], error: str | None)
        accounts 格式：[{'id': 'act_123', 'name': 'My Account'}]
    """
    # 先查快取
    cached = get_account_cache(user_id, team_id)
    if cached is not None:
        return cached, None

    headers = get_headers(user_id, team_id, allow_fallback=not strict_token)
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

        set_account_cache(user_id, team_id, formatted)
        return formatted, None

    except Exception as e:
        logger.error("[FB ASYNC] Error in get_all_ad_accounts", exc_info=True)
        return [], str(e)
