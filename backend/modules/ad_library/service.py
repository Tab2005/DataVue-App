"""
Ad Library - 刷新流程編排（docs/73、docs/74）

`run_refresh` 由 router 以 BackgroundTasks 排程：
  1. job → running
  2. 抓帳號幣別（同時決定用哪個 token：owner 自己的失效時退回團隊 token）
  3. 依序抓行銷活動 → 廣告組合 → 廣告，每頁 normalize 後 upsert；
     廣告另做圖片落地（依 image_hash／fb_url 去重，限制並發）
  4. 對有曝光的動態素材廣告抓元件 breakdown（docs/74 第 3 階段，依花費取前
     MAX_ASSET_INSIGHT_ADS 則）
  5. job → succeeded / partial（被截斷或撞 rate limit）/ failed
     撞 rate limit 後不再抓後面的層級（再打也只會繼續被擋）

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
from .asset_insights import INSIGHT_FIELDS, breakdowns_for_ad, parse_asset_rows
from .data_source import (
    RATE_LIMIT_CODES,
    AdLibraryAPIError,
    AdLibraryDataSourceError,
    download_image,
    fetch_account_info,
    fetch_ad_asset_insights,
    fetch_adsets,
    fetch_ads,
    fetch_campaigns,
    fetch_video_pictures,
)
from .media import store_image
from .normalizer import normalize_ad, normalize_adset, normalize_campaign

logger = logging.getLogger(__name__)

MEDIA_CONCURRENCY = 4
# 每則動態素材廣告最多 5 次 breakdown 呼叫，上限 100 則 ≈ 500 次
MAX_ASSET_INSIGHT_ADS = 100
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


STAGE_LABELS = {"campaigns": "行銷活動", "adsets": "廣告組合", "ads": "廣告"}


async def _run_stage(fetch, **kwargs) -> dict:
    """執行一個層級的抓取；第一頁就撞 rate limit 時視為 rate_limited 而非整個失敗。"""
    try:
        return await fetch(**kwargs)
    except AdLibraryAPIError as exc:
        if exc.fb_code in RATE_LIMIT_CODES:
            return {"fetched": 0, "truncated": False, "rate_limited": True}
        raise


async def _refresh_asset_insights(*, account_id, google_id, token, on_progress, counts) -> tuple[bool, list[str]]:
    """docs/74 第 3 階段：抓動態素材廣告的元件成效。回傳 (是否部分完成, 附註)。

    這一層失敗不讓整個刷新失敗（前面的資料都已存好），只標 partial 並附上原因。
    """
    ads, total = await _db(repository.dynamic_ads_for_asset_insights, account_id, MAX_ASSET_INSIGHT_ADS)
    notes: list[str] = []
    if total > len(ads):
        notes.append(f"動態素材廣告共 {total} 則，元件成效只分析花費最高的 {len(ads)} 則")
    skipped_total = 0
    for ad in ads:
        breakdowns = breakdowns_for_ad(ad)
        if not breakdowns:
            continue
        try:
            result = await fetch_ad_asset_insights(
                ad["ad_id"], breakdowns, user_id=google_id, fields=INSIGHT_FIELDS, **token
            )
        except AdLibraryAPIError as exc:
            if exc.fb_code in RATE_LIMIT_CODES:
                notes.append("抓取動態素材元件成效時 Facebook API 達到請求上限，已先儲存目前抓到的資料，請稍後再刷新")
            else:
                notes.append(f"動態素材元件成效抓取中斷：{exc}")
            return True, notes
        entries: list[dict] = []
        for breakdown, rows in result.items():
            parsed, skipped = parse_asset_rows(breakdown, rows)
            entries.extend(parsed)
            skipped_total += skipped
        await _db(repository.replace_asset_insights, account_id, ad["ad_id"], entries)
        counts["asset_ads"] += 1
        await on_progress()
    if skipped_total:
        logger.info("[AdLibrary] %s asset insights: skipped %d unidentifiable rows", account_id, skipped_total)
    return False, notes


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
    """背景任務：抓取帳號的行銷活動、廣告組合與廣告並落庫。錯誤一律記入 job，不往外拋。"""
    await _db(repository.update_job, job_id, status="running", started_at=_utcnow())

    counts = {"campaigns": 0, "adsets": 0, "ads": 0, "asset_ads": 0}
    resolver: _MediaResolver | None = None

    def _progress() -> dict:
        return {
            "campaigns_fetched": counts["campaigns"],
            "adsets_fetched": counts["adsets"],
            "ads_fetched": counts["ads"],
            "asset_insights_ads": counts["asset_ads"],
            "media_stored": resolver.stored if resolver else 0,
        }

    try:
        token = {"team_id": token_team_id, "strict_token": strict_token}
        try:
            info = await fetch_account_info(account_id, user_id=google_id, **token)
        except AdLibraryDataSourceError:
            # owner 自己的 token 失效時，比照 resolve_accessible_account_ids 退回團隊 token
            if not fallback_team_id:
                raise
            token = {"team_id": fallback_team_id, "strict_token": False}
            info = await fetch_account_info(account_id, user_id=google_id, **token)
        currency = info.get("currency")

        async def on_campaigns(page: list[dict]) -> None:
            rows = [normalize_campaign(c, account_id=account_id, currency=currency) for c in page if c.get("id")]
            await _db(repository.upsert_campaigns, rows)
            counts["campaigns"] += len(rows)
            await _db(repository.update_job, job_id, **_progress())

        async def on_adsets(page: list[dict]) -> None:
            rows = [normalize_adset(a, account_id=account_id, currency=currency) for a in page if a.get("id")]
            await _db(repository.upsert_adsets, rows)
            counts["adsets"] += len(rows)
            await _db(repository.update_job, job_id, **_progress())

        known = await _db(repository.known_image_assets, account_id)
        notes: list[str] = []
        partial = False
        stopped = False
        async with httpx.AsyncClient(timeout=MEDIA_DOWNLOAD_TIMEOUT) as media_client:
            resolver = _MediaResolver(known=known, uploaded_by=user_id, client=media_client)

            video_pictures: dict[str, str] = {}

            async def fill_video_thumbnails(rows: list[dict]) -> None:
                """asset_feed_spec 沒帶縮圖的影片，補抓 picture 後交給 resolver 落地。"""
                missing = sorted({
                    m["video_id"] for row in rows for m in row["media"]
                    if m.get("kind") == "video_thumbnail" and m.get("video_id") and not m.get("fb_url")
                    and m["video_id"] not in video_pictures
                })
                if missing:
                    video_pictures.update(await fetch_video_pictures(missing, user_id=google_id, **token))
                for row in rows:
                    for m in row["media"]:
                        if m.get("kind") == "video_thumbnail" and not m.get("fb_url") and m.get("video_id"):
                            m["fb_url"] = video_pictures.get(m["video_id"])

            async def on_ads(ads: list[dict]) -> None:
                rows = [normalize_ad(ad, account_id=account_id) for ad in ads if ad.get("id")]
                await fill_video_thumbnails(rows)
                await asyncio.gather(*(resolver.resolve(m) for row in rows for m in row["media"]))
                await _db(repository.upsert_items, rows)
                counts["ads"] += len(rows)
                await _db(repository.update_job, job_id, **_progress())

            stages = (
                ("campaigns", fetch_campaigns, on_campaigns),
                ("adsets", fetch_adsets, on_adsets),
                ("ads", fetch_ads, on_ads),
            )
            for stage, fetch, on_page in stages:
                result = await _run_stage(
                    fetch, account_id=account_id, user_id=google_id, on_page=on_page, **token
                )
                label = STAGE_LABELS[stage]
                if result["truncated"]:
                    partial = True
                    notes.append(f"{label}已達單次上限，只抓取前 {result['fetched']} 筆")
                if result["rate_limited"]:
                    partial = True
                    notes.append(
                        f"抓取{label}時 Facebook API 達到請求上限，已先儲存目前抓到的資料，請稍後再刷新"
                    )
                    stopped = True
                    break

        if not stopped:
            asset_partial, asset_notes = await _refresh_asset_insights(
                account_id=account_id, google_id=google_id, token=token,
                on_progress=lambda: _db(repository.update_job, job_id, **_progress()),
                counts=counts,
            )
            partial = partial or asset_partial
            notes.extend(asset_notes)

        await _db(
            repository.update_job, job_id,
            status="partial" if partial else "succeeded",
            error="；".join(notes) or None,
            finished_at=_utcnow(),
            **_progress(),
        )
        logger.info(
            "[AdLibrary] refresh %s done: campaigns=%d adsets=%d ads=%d media=%d partial=%s",
            account_id, counts["campaigns"], counts["adsets"], counts["ads"],
            resolver.stored if resolver else 0, partial,
        )
    except AdLibraryDataSourceError as exc:
        logger.error("[AdLibrary] refresh %s failed: %s", account_id, exc)
        await _db(
            repository.update_job, job_id,
            status="failed", error=str(exc), finished_at=_utcnow(), **_progress(),
        )
    except Exception as exc:  # 防背景任務將錯誤吞掉
        logger.error("[AdLibrary] refresh %s unexpected error", account_id, exc_info=True)
        await _db(
            repository.update_job, job_id,
            status="failed", error=f"內部錯誤：{type(exc).__name__}", finished_at=_utcnow(), **_progress(),
        )
