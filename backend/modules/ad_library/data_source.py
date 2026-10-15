"""
Ad Library - Graph API 抓取（docs/73、docs/74）

  GET /{act_id}?fields=currency,timezone_name          帳號幣別（docs/74）
  GET /{act_id}/campaigns、/{act_id}/adsets、/{act_id}/ads?fields=...&limit=100
  → 依 paging.next 逐頁抓，每頁交給 on_page 回呼（邊抓邊寫，不在記憶體堆積
    整個帳號的廣告——同 contribution 2026-07-08 記憶體事故的教訓）
  → 達 max_items 上限或遇 rate limit 即停止並回報 truncated

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
DEFAULT_MAX_CAMPAIGNS = 1000
DEFAULT_MAX_ADSETS = 3000
# FB rate limit 類錯誤碼：4 app、17 user、32 page、613 call、80004 ads management
RATE_LIMIT_CODES = {4, 17, 32, 613, 80004}

_INSIGHTS_FIELD = "insights.date_preset(maximum){impressions,reach,spend,clicks,ctr}"

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
    _INSIGHTS_FIELD,
])

CAMPAIGN_FIELDS = ",".join([
    "id",
    "name",
    "objective",
    "status",
    "effective_status",
    "buying_type",
    "bid_strategy",
    "daily_budget",
    "lifetime_budget",
    "budget_remaining",
    "special_ad_categories",
    "smart_promotion_type",
    "start_time",
    "stop_time",
    "created_time",
    "updated_time",
    _INSIGHTS_FIELD,
])

ADSET_FIELDS = ",".join([
    "id",
    "name",
    "campaign_id",
    "status",
    "effective_status",
    "optimization_goal",
    "billing_event",
    "bid_strategy",
    "bid_amount",
    "daily_budget",
    "lifetime_budget",
    "budget_remaining",
    "targeting",
    "promoted_object",
    "attribution_spec",
    "destination_type",
    "is_dynamic_creative",
    "start_time",
    "end_time",
    "created_time",
    "updated_time",
    _INSIGHTS_FIELD,
])

ACCOUNT_FIELDS = "currency,timezone_name"


class AdLibraryDataSourceError(Exception):
    """Base exception。"""


class AdLibraryTokenError(AdLibraryDataSourceError):
    """找不到可用的 FB token。"""


class AdLibraryAPIError(AdLibraryDataSourceError):
    def __init__(self, message: str, *, fb_code: int | None = None):
        self.fb_code = fb_code
        super().__init__(message)


async def _get_headers(user_id: str, team_id: str | None, strict_token: bool) -> dict:
    headers = await asyncio.to_thread(get_headers, user_id, team_id, not strict_token)
    if not headers:
        raise AdLibraryTokenError("找不到可用的 Facebook 存取權杖，請重新連結 Facebook 帳號。")
    return headers


async def _get_json(http, url: str, headers: dict, params: dict | None) -> dict:
    try:
        resp = await http.get(url, headers=headers, params=params)
        return resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise AdLibraryAPIError(f"FB API 連線失敗：{type(exc).__name__}") from exc


async def fetch_account_info(
    account_id: str,
    *,
    user_id: str,
    team_id: str | None,
    strict_token: bool,
    client: httpx.AsyncClient | None = None,
) -> dict:
    """抓帳號幣別與時區；同時用來確認 token 對此帳號可用。"""
    headers = await _get_headers(user_id, team_id, strict_token)
    own_client = client is None
    http = client or httpx.AsyncClient(timeout=TIMEOUT)
    try:
        data = await _get_json(http, f"{BASE_URL}/{account_id}", headers, {"fields": ACCOUNT_FIELDS})
    finally:
        if own_client:
            await http.aclose()
    if "error" in data:
        err = data["error"] or {}
        raise AdLibraryAPIError(err.get("message") or "FB API 錯誤", fb_code=err.get("code"))
    return {"currency": data.get("currency"), "timezone_name": data.get("timezone_name")}


async def _fetch_edge(
    account_id: str,
    edge: str,
    fields: str,
    *,
    user_id: str,
    team_id: str | None,
    strict_token: bool,
    on_page: Callable[[list[dict[str, Any]]], Awaitable[None]],
    max_items: int,
    client: httpx.AsyncClient | None,
) -> dict:
    """逐頁抓取 /{act_id}/{edge} 並交給 on_page。

    Returns:
        {"fetched": int, "truncated": bool, "rate_limited": bool}
    """
    headers = await _get_headers(user_id, team_id, strict_token)

    url: str | None = f"{BASE_URL}/{account_id}/{edge}"
    params: dict | None = {"fields": fields, "limit": PAGE_LIMIT}
    fetched = 0
    truncated = False
    rate_limited = False

    own_client = client is None
    http = client or httpx.AsyncClient(timeout=TIMEOUT)
    try:
        while url:
            data = await _get_json(http, url, headers, params)

            if "error" in data:
                err = data["error"] or {}
                code = err.get("code")
                if code in RATE_LIMIT_CODES and fetched > 0:
                    logger.warning("[AdLibrary] %s/%s rate limited after %d items", account_id, edge, fetched)
                    rate_limited = True
                    break
                raise AdLibraryAPIError(err.get("message") or "FB API 錯誤", fb_code=code)

            page = data.get("data") or []
            remaining = max_items - fetched
            if len(page) > remaining:
                page = page[:remaining]
                truncated = True
            if page:
                await on_page(page)
                fetched += len(page)
            if truncated or fetched >= max_items:
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
    return await _fetch_edge(
        account_id, "ads", AD_FIELDS,
        user_id=user_id, team_id=team_id, strict_token=strict_token,
        on_page=on_page, max_items=max_ads, client=client,
    )


async def fetch_campaigns(
    account_id: str,
    *,
    user_id: str,
    team_id: str | None,
    strict_token: bool,
    on_page: Callable[[list[dict[str, Any]]], Awaitable[None]],
    max_items: int = DEFAULT_MAX_CAMPAIGNS,
    client: httpx.AsyncClient | None = None,
) -> dict:
    return await _fetch_edge(
        account_id, "campaigns", CAMPAIGN_FIELDS,
        user_id=user_id, team_id=team_id, strict_token=strict_token,
        on_page=on_page, max_items=max_items, client=client,
    )


async def fetch_adsets(
    account_id: str,
    *,
    user_id: str,
    team_id: str | None,
    strict_token: bool,
    on_page: Callable[[list[dict[str, Any]]], Awaitable[None]],
    max_items: int = DEFAULT_MAX_ADSETS,
    client: httpx.AsyncClient | None = None,
) -> dict:
    return await _fetch_edge(
        account_id, "adsets", ADSET_FIELDS,
        user_id=user_id, team_id=team_id, strict_token=strict_token,
        on_page=on_page, max_items=max_items, client=client,
    )


TOKEN_ERROR_CODES = {190}
VIDEO_IDS_PER_CALL = 50


async def fetch_video_pictures(
    video_ids: list[str],
    *,
    user_id: str,
    team_id: str | None,
    strict_token: bool,
    client: httpx.AsyncClient | None = None,
) -> dict[str, str]:
    """動態素材的 asset_feed_spec 不一定帶影片縮圖：以 `/?ids=...&fields=picture`
    批次補抓（每次 50 支）。失敗不影響刷新，回傳拿得到的 {video_id: 縮圖網址}。
    """
    if not video_ids:
        return {}
    headers = await _get_headers(user_id, team_id, strict_token)
    own_client = client is None
    http = client or httpx.AsyncClient(timeout=TIMEOUT)
    out: dict[str, str] = {}
    try:
        for start in range(0, len(video_ids), VIDEO_IDS_PER_CALL):
            chunk = video_ids[start:start + VIDEO_IDS_PER_CALL]
            try:
                data = await _get_json(http, f"{BASE_URL}/", headers, {"ids": ",".join(chunk), "fields": "picture"})
            except AdLibraryAPIError:
                continue
            if "error" in data:
                logger.warning("[AdLibrary] video pictures skipped: code=%s", (data["error"] or {}).get("code"))
                continue
            for video_id, node in data.items():
                picture = (node or {}).get("picture") if isinstance(node, dict) else None
                if picture:
                    out[str(video_id)] = picture
    finally:
        if own_client:
            await http.aclose()
    return out


async def fetch_ad_asset_insights(
    ad_id: str,
    breakdowns: list[str],
    *,
    user_id: str,
    team_id: str | None,
    strict_token: bool,
    fields: str,
    client: httpx.AsyncClient | None = None,
) -> dict[str, list[dict]]:
    """docs/74 第 3 階段：逐一查詢動態素材廣告的元件 breakdown。

    單一 breakdown 回錯（例如此廣告不支援該元件）只略過該 breakdown；
    rate limit 與 token 錯誤則往外拋，由呼叫端決定是否停止。

    Returns:
        {breakdown: [rows]}
    """
    headers = await _get_headers(user_id, team_id, strict_token)
    own_client = client is None
    http = client or httpx.AsyncClient(timeout=TIMEOUT)
    out: dict[str, list[dict]] = {}
    try:
        for breakdown in breakdowns:
            url: str | None = f"{BASE_URL}/{ad_id}/insights"
            params: dict | None = {
                "fields": fields,
                "breakdowns": breakdown,
                "date_preset": "maximum",
                "limit": PAGE_LIMIT,
            }
            rows: list[dict] = []
            while url:
                data = await _get_json(http, url, headers, params)
                if "error" in data:
                    err = data["error"] or {}
                    code = err.get("code")
                    if code in RATE_LIMIT_CODES or code in TOKEN_ERROR_CODES:
                        raise AdLibraryAPIError(err.get("message") or "FB API 錯誤", fb_code=code)
                    logger.warning("[AdLibrary] ad %s breakdown %s skipped: code=%s", ad_id, breakdown, code)
                    rows = []
                    break
                rows.extend(data.get("data") or [])
                url = (data.get("paging") or {}).get("next")
                params = None
            out[breakdown] = rows
            await asyncio.sleep(INTER_PAGE_SLEEP_SEC)
    finally:
        if own_client:
            await http.aclose()
    return out


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
