"""
Ad Library - Graph API 抓取（docs/73）

  GET /{act_id}/ads?fields=...&limit=100
  → 依 paging.next 逐頁抓，每頁交給 on_page 回呼（邊抓邊寫，不在記憶體堆積
    整個帳號的廣告——同 contribution 2026-07-08 記憶體事故的教訓）
  → 達 max_ads 上限或遇 rate limit 即停止並回報 truncated

沿用 `modules/fb_ads/_base.py` 的 `BASE_URL` / `get_headers()`；錯誤訊息與
log 一律不落明文 token。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

import httpx

from modules.fb_ads._base import BASE_URL, TIMEOUT, get_headers

logger = logging.getLogger(__name__)

PAGE_LIMIT = 100
INTER_PAGE_SLEEP_SEC = 0.3
DEFAULT_MAX_ADS = 2000
# FB rate limit 類錯誤碼：4 app、17 user、32 page、613 call、80004 ads management
RATE_LIMIT_CODES = {4, 17, 32, 613, 80004}

AD_FIELDS = ",".join([
    "id",
    "name",
    "effective_status",
    "created_time",
    "updated_time",
    "preview_shareable_link",
    "campaign{id,name,objective}",
    "adset{id,name}",
    "creative{id,body,title,object_story_spec,asset_feed_spec,call_to_action_type,"
    "image_url,image_hash,thumbnail_url,video_id,effective_object_story_id}",
    "insights.date_preset(maximum){impressions,reach,spend,clicks,ctr}",
])


class AdLibraryDataSourceError(Exception):
    """Base exception。"""


class AdLibraryTokenError(AdLibraryDataSourceError):
    """找不到可用的 FB token。"""


class AdLibraryAPIError(AdLibraryDataSourceError):
    def __init__(self, message: str, *, fb_code: int | None = None):
        self.fb_code = fb_code
        super().__init__(message)


async def fetch_ads(
    account_id: str,
    *,
    user_id: str,
    team_id: str | None,
    strict_token: bool,
    on_page: Callable[[list[dict[str, Any]]], Awaitable[None]],
    max_ads: int = DEFAULT_MAX_ADS,
    client: httpx.AsyncClient | None = None,
) -> dict:
    """逐頁抓取帳號的廣告並交給 on_page。

    Returns:
        {"fetched": int, "truncated": bool, "rate_limited": bool}
    """
    headers = await asyncio.to_thread(get_headers, user_id, team_id, not strict_token)
    if not headers:
        raise AdLibraryTokenError("找不到可用的 Facebook 存取權杖，請重新連結 Facebook 帳號。")

    url: str | None = f"{BASE_URL}/{account_id}/ads"
    params: dict | None = {"fields": AD_FIELDS, "limit": PAGE_LIMIT}
    fetched = 0
    truncated = False
    rate_limited = False

    own_client = client is None
    http = client or httpx.AsyncClient(timeout=TIMEOUT)
    try:
        while url:
            try:
                resp = await http.get(url, headers=headers, params=params)
                data = resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise AdLibraryAPIError(f"FB API 連線失敗：{type(exc).__name__}") from exc

            if "error" in data:
                err = data["error"] or {}
                code = err.get("code")
                if code in RATE_LIMIT_CODES and fetched > 0:
                    logger.warning("[AdLibrary] %s rate limited after %d ads", account_id, fetched)
                    rate_limited = True
                    break
                raise AdLibraryAPIError(err.get("message") or "FB API 錯誤", fb_code=code)

            page = data.get("data") or []
            remaining = max_ads - fetched
            if len(page) > remaining:
                page = page[:remaining]
                truncated = True
            if page:
                await on_page(page)
                fetched += len(page)
            if truncated or fetched >= max_ads:
                truncated = truncated or bool((data.get("paging") or {}).get("next"))
                break

            url = (data.get("paging") or {}).get("next")
            params = None  # next 連結已含完整 query string
            if url:
                await asyncio.sleep(INTER_PAGE_SLEEP_SEC)
    finally:
        if own_client:
            await http.aclose()

    return {"fetched": fetched, "truncated": truncated, "rate_limited": rate_limited}


async def download_image(url: str, *, client: httpx.AsyncClient, max_bytes: int = 15 * 1024 * 1024) -> tuple[bytes, str | None] | None:
    """下載 FB CDN 圖片；失敗或過大回 None（不阻斷刷新）。"""
    try:
        resp = await client.get(url, follow_redirects=True)
    except httpx.HTTPError:
        return None
    if resp.status_code != 200:
        return None
    content_type = (resp.headers.get("content-type") or "").split(";")[0].strip() or None
    if content_type and not content_type.startswith("image/"):
        return None
    if len(resp.content) > max_bytes:
        return None
    return resp.content, content_type
