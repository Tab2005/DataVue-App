# backend/modules/fb_ads/accounts_service.py
"""
廣告帳號查詢服務。
提供取得使用者所有廣告帳號的非同步函式。
"""

import asyncio
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
