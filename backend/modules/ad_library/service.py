"""
Ad Library - 刷新流程編排（docs/73）

`run_refresh` 由 router 以 BackgroundTasks 排程：
  1. job → running
  2. data_source.fetch_ads 逐頁抓取，每頁：
       normalize → 圖片落地（依 image_hash／fb_url 去重，限制並發）→ upsert
  3. job → succeeded / partial（被截斷或撞 rate limit）/ failed

全程不持有長生命週期 DB session：每段同步 DB 操作在 to_thread 內開關短 session
（2026-07-08 連線池耗盡事故的慣例）。
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timezone

import httpx

from . import repository
from .data_source import AdLibraryDataSourceError, download_image, fetch_ads
from .media import store_image
from .normalizer import normalize_ad

logger = logging.getLogger(__name__)

MEDIA_CONCURRENCY = 4
MEDIA_DOWNLOAD_TIMEOUT = 20.0


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _with_session(fn, *args, **kwargs):
    from database import SessionLocal

    db = SessionLocal()
    try:
        return fn(db, *args, **kwargs)
    finally:
        db.close()


async def _db(fn, *args, **kwargs):
    return await asyncio.to_thread(_with_session, fn, *args, **kwargs)


class _MediaResolver:
    """把 media entry 對應到已落地的 asset；同一張圖（hash 或 URL）只下載、存一次。"""

    def __init__(self, *, known: dict[str, dict], uploaded_by: str | None, client: httpx.AsyncClient):
        self._known = known
        self._inflight: dict[str, asyncio.Task] = {}
        self._sem = asyncio.Semaphore(MEDIA_CONCURRENCY)
        self._uploaded_by = uploaded_by
        self._client = client
        self.stored = 0

    @staticmethod
    def _keys(entry: dict) -> list[str]:
        keys = []
        if entry.get("image_hash"):
            keys.append(f"hash:{entry['image_hash']}")
        if entry.get("fb_url"):
            keys.append(f"url:{entry['fb_url']}")
        return keys

    async def resolve(self, entry: dict) -> None:
        keys = self._keys(entry)
        for key in keys:
            if key in self._known:
                entry.update(self._known[key])
                return
        if not entry.get("fb_url"):
            return

        primary = keys[0]
        task = self._inflight.get(primary)
        if task is None:
            task = asyncio.create_task(self._download_and_store(entry))
            self._inflight[primary] = task
        ref = await task
        if ref:
            entry.update(ref)
            for key in keys:
                self._known.setdefault(key, ref)

    async def _download_and_store(self, entry: dict) -> dict | None:
        async with self._sem:
            downloaded = await download_image(entry["fb_url"], client=self._client)
            if not downloaded:
                return None
            file_bytes, content_type = downloaded
            stem = "adlib_" + (
                entry.get("image_hash")
                or hashlib.sha1(entry["fb_url"].encode("utf-8")).hexdigest()[:16]
            )
            ref = await store_image(
                file_bytes=file_bytes,
                content_type=content_type or "image/jpeg",
                filename_stem=stem,
                uploaded_by=self._uploaded_by,
            )
            if ref:
                self.stored += 1
            return ref


async def run_refresh(
    *,
    job_id: str,
    account_id: str,
    google_id: str,
    user_id: str,
    token_team_id: str | None,
    strict_token: bool,
    fallback_team_id: str | None = None,
) -> None:
    """背景任務：抓取帳號全部廣告並落庫。錯誤一律記入 job，不往外拋。"""
    await _db(repository.update_job, job_id, status="running", started_at=_utcnow())

    fetched_total = 0
    resolver: _MediaResolver | None = None
    try:
        known = await _db(repository.known_image_assets, account_id)
        async with httpx.AsyncClient(timeout=MEDIA_DOWNLOAD_TIMEOUT) as media_client:
            resolver = _MediaResolver(known=known, uploaded_by=user_id, client=media_client)

            async def on_page(ads: list[dict]) -> None:
                nonlocal fetched_total
                rows = [normalize_ad(ad, account_id=account_id) for ad in ads if ad.get("id")]
                await asyncio.gather(*(resolver.resolve(m) for row in rows for m in row["media"]))
                await _db(repository.upsert_items, rows)
                fetched_total += len(rows)
                await _db(
                    repository.update_job, job_id,
                    ads_fetched=fetched_total, media_stored=resolver.stored,
                )

            async def _fetch(team_id, strict):
                return await fetch_ads(
                    account_id,
                    user_id=google_id,
                    team_id=team_id,
                    strict_token=strict,
                    on_page=on_page,
                )

            try:
                result = await _fetch(token_team_id, strict_token)
            except AdLibraryDataSourceError:
                # owner 自己的 token 失效時，比照 resolve_accessible_account_ids 退回團隊 token
                if not fallback_team_id or fetched_total:
                    raise
                result = await _fetch(fallback_team_id, False)

        partial = result["truncated"] or result["rate_limited"]
        note = None
        if result["truncated"]:
            note = f"已達單次上限，只抓取前 {result['fetched']} 支廣告"
        elif result["rate_limited"]:
            note = "Facebook API 達到請求上限，已先儲存目前抓到的廣告，請稍後再刷新"
        await _db(
            repository.update_job, job_id,
            status="partial" if partial else "succeeded",
            ads_fetched=fetched_total,
            media_stored=resolver.stored,
            error=note,
            finished_at=_utcnow(),
        )
        logger.info(
            "[AdLibrary] refresh %s done: ads=%d media=%d partial=%s",
            account_id, fetched_total, resolver.stored, partial,
        )
    except AdLibraryDataSourceError as exc:
        logger.error("[AdLibrary] refresh %s failed: %s", account_id, exc)
        await _db(
            repository.update_job, job_id,
            status="failed", error=str(exc), ads_fetched=fetched_total,
            media_stored=resolver.stored if resolver else 0, finished_at=_utcnow(),
        )
    except Exception as exc:  # 防背景任務將錯誤吞掉
        logger.error("[AdLibrary] refresh %s unexpected error", account_id, exc_info=True)
        await _db(
            repository.update_job, job_id,
            status="failed", error=f"內部錯誤：{type(exc).__name__}", ads_fetched=fetched_total,
            media_stored=resolver.stored if resolver else 0, finished_at=_utcnow(),
        )
