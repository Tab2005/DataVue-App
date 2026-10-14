"""Ad Library - 資料存取（docs/73、docs/74）。全部為同步函式，async 呼叫端須包 to_thread。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import Text, func, or_
from sqlalchemy.orm import Session

from database.models.ad_library import (
    AdLibraryAdContent,
    AdLibraryAdset,
    AdLibraryAssetInsight,
    AdLibraryCampaign,
    AdLibraryContent,
    AdLibraryItem,
    AdLibraryRefreshJob,
)
from database.models.meta_andromeda import MetaAndromedaAsset

from .fingerprint import extract_components

ACTIVE_JOB_STATUSES = ("queued", "running")
# 服務重啟會讓執行中的背景任務消失、job 永遠停在 running；超過此時間視為已失效，
# 不再擋住同帳號的下一次刷新
STALE_JOB_AFTER = timedelta(minutes=30)
SORT_COLUMNS = {
    "impressions": AdLibraryItem.impressions,
    "spend": AdLibraryItem.spend,
    "ctr": AdLibraryItem.ctr,
    "created": AdLibraryItem.ad_created_at,
}
# 對應 FB effective_status 的篩選群組
STATUS_GROUPS = {
    "active": ("ACTIVE",),
    "paused": ("PAUSED", "CAMPAIGN_PAUSED", "ADSET_PAUSED"),
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── refresh jobs ───────────────────────────────────────────────────────
def get_active_job(db: Session, account_id: str) -> AdLibraryRefreshJob | None:
    return (
        db.query(AdLibraryRefreshJob)
        .filter(
            AdLibraryRefreshJob.account_id == account_id,
            AdLibraryRefreshJob.status.in_(ACTIVE_JOB_STATUSES),
            AdLibraryRefreshJob.created_at >= _utcnow() - STALE_JOB_AFTER,
        )
        .order_by(AdLibraryRefreshJob.created_at.desc())
        .first()
    )


def create_job(db: Session, *, account_id: str, team_id: str | None, requested_by: str) -> AdLibraryRefreshJob:
    job = AdLibraryRefreshJob(
        account_id=account_id,
        team_id=team_id,
        requested_by=requested_by,
        status="queued",
        ads_fetched=0,
        campaigns_fetched=0,
        adsets_fetched=0,
        media_stored=0,
        created_at=_utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> AdLibraryRefreshJob | None:
    return db.query(AdLibraryRefreshJob).filter(AdLibraryRefreshJob.id == job_id).first()


def get_latest_job(db: Session, account_id: str) -> AdLibraryRefreshJob | None:
    return (
        db.query(AdLibraryRefreshJob)
        .filter(AdLibraryRefreshJob.account_id == account_id)
        .order_by(AdLibraryRefreshJob.created_at.desc())
        .first()
    )


def update_job(db: Session, job_id: str, **fields) -> None:
    job = get_job(db, job_id)
    if job is None:
        return
    for key, value in fields.items():
        setattr(job, key, value)
    db.commit()


# ── items ──────────────────────────────────────────────────────────────
def known_image_assets(db: Session, account_id: str) -> dict[str, dict]:
    """回傳此帳號已落地的圖片對照：{image_hash 或 fb_url: {asset_id, asset_uri}}，供去重。"""
    out: dict[str, dict] = {}
    rows = db.query(AdLibraryItem.media).filter(AdLibraryItem.account_id == account_id).all()
    for (media,) in rows:
        for m in media or []:
            if not m.get("asset_id"):
                continue
            ref = {"asset_id": m["asset_id"], "asset_uri": m.get("asset_uri")}
            if m.get("image_hash"):
                out.setdefault(f"hash:{m['image_hash']}", ref)
            if m.get("fb_url"):
                out.setdefault(f"url:{m['fb_url']}", ref)
    return out


def _upsert(db: Session, model, key: str, rows: list[dict], *, commit: bool = True) -> list:
    """以 (account_id, key) upsert 同一帳號的一批列；回傳寫入的 ORM 物件。"""
    if not rows:
        return []
    account_id = rows[0]["account_id"]
    key_column = getattr(model, key)
    existing = {
        getattr(obj, key): obj
        for obj in db.query(model).filter(
            model.account_id == account_id, key_column.in_([r[key] for r in rows])
        )
    }
    now = _utcnow()
    objs = []
    for row in rows:
        obj = existing.get(row[key])
        if obj is None:
            obj = model(**row, first_seen_at=now, last_seen_at=now, fetched_at=now)
            db.add(obj)
        else:
            for field, value in row.items():
                setattr(obj, field, value)
            obj.last_seen_at = now
            obj.fetched_at = now
        objs.append(obj)
    if commit:
        db.commit()
    return objs


def upsert_items(db: Session, rows: list[dict]) -> int:
    """upsert 廣告並同步其內容元件與 copy_key / media_key（docs/74 第二節）。"""
    items = _upsert(db, AdLibraryItem, "ad_id", rows, commit=False)
    db.flush()  # 新廣告取得 id
    _sync_contents(db, items)
    db.commit()
    return len(items)


def upsert_campaigns(db: Session, rows: list[dict]) -> int:
    return len(_upsert(db, AdLibraryCampaign, "campaign_id", rows))


def upsert_adsets(db: Session, rows: list[dict]) -> int:
    return len(_upsert(db, AdLibraryAdset, "adset_id", rows))


# ── 內容元件（docs/74 第二節）────────────────────────────────────────────
REBUILD_CHUNK = 200


def _item_payload(item: AdLibraryItem) -> dict:
    return {
        "primary_texts": item.primary_texts,
        "headlines": item.headlines,
        "descriptions": item.descriptions,
        "media": item.media,
        "media_type": item.media_type,
    }


def _ensure_content_rows(
    db: Session, account_id: str, components: dict[tuple[str, str], dict]
) -> dict[tuple[str, str], AdLibraryContent]:
    """取得或建立元件列（以 (kind, fingerprint) 對應），flush 後回傳對照表。不 commit。"""
    contents: dict[tuple[str, str], AdLibraryContent] = {}
    if not components:
        return contents
    fingerprints = {fp for _kind, fp in components}
    for row in db.query(AdLibraryContent).filter(
        AdLibraryContent.account_id == account_id, AdLibraryContent.fingerprint.in_(fingerprints)
    ):
        contents[(row.kind, row.fingerprint)] = row

    now = _utcnow()
    for key, comp in components.items():
        row = contents.get(key)
        if row is None:
            row = AdLibraryContent(
                account_id=account_id,
                kind=comp["kind"],
                fingerprint=comp["fingerprint"],
                text_value=comp.get("text_value"),
                image_hash=comp.get("image_hash"),
                video_id=comp.get("video_id"),
                asset_id=comp.get("asset_id"),
                first_seen_at=now,
                last_seen_at=now,
            )
            db.add(row)
            contents[key] = row
        else:
            row.last_seen_at = now
            if comp.get("asset_id") and not row.asset_id:
                row.asset_id = comp["asset_id"]
    db.flush()
    return contents


def _sync_contents(db: Session, items: list[AdLibraryItem]) -> None:
    """重建這批廣告（同一帳號）的元件關聯，並寫回 copy_key / media_key。不 commit。"""
    if not items:
        return
    account_id = items[0].account_id
    extracted = {item.id: extract_components(_item_payload(item)) for item in items}

    first_seen: dict[tuple[str, str], dict] = {}
    for result in extracted.values():
        for comp in result["components"]:
            first_seen.setdefault((comp["kind"], comp["fingerprint"]), comp)
    contents = _ensure_content_rows(db, account_id, first_seen)

    item_ids = [item.id for item in items]
    db.query(AdLibraryAdContent).filter(AdLibraryAdContent.item_id.in_(item_ids)).delete(
        synchronize_session=False
    )
    for item in items:
        result = extracted[item.id]
        item.copy_key = result["copy_key"]
        item.media_key = result["media_key"]
        for comp in result["components"]:
            db.add(AdLibraryAdContent(
                item_id=item.id,
                content_id=contents[(comp["kind"], comp["fingerprint"])].id,
                position=comp["position"],
            ))


def rebuild_contents(db: Session, account_id: str) -> int:
    """不打 FB，依已存的廣告欄位重建整個帳號的元件；回傳處理的廣告數。"""
    total = 0
    offset = 0
    while True:
        items = (
            db.query(AdLibraryItem)
            .filter(AdLibraryItem.account_id == account_id)
            .order_by(AdLibraryItem.id)
            .offset(offset)
            .limit(REBUILD_CHUNK)
            .all()
        )
        if not items:
            break
        _sync_contents(db, items)
        db.commit()
        total += len(items)
        offset += REBUILD_CHUNK
    return total


def ensure_contents(db: Session, account_id: str) -> bool:
    """docs/74 第二階段上線前抓的廣告沒有元件資料：偵測到就就地補建一次。

    回傳是否執行了補建。判斷條件為「帳號有廣告，但沒有任何一則有元件關聯」。
    """
    has_items = db.query(AdLibraryItem.id).filter(AdLibraryItem.account_id == account_id).first()
    if not has_items:
        return False
    has_links = (
        db.query(AdLibraryAdContent.item_id)
        .join(AdLibraryItem, AdLibraryItem.id == AdLibraryAdContent.item_id)
        .filter(AdLibraryItem.account_id == account_id)
        .first()
    )
    if has_links:
        return False
    rebuild_contents(db, account_id)
    return True


# ── hierarchy（docs/74）─────────────────────────────────────────────────
def load_hierarchy(db: Session, account_id: str):
    """回傳 (campaigns, adsets, items)，交給 hierarchy.build_tree 組樹。"""
    campaigns = db.query(AdLibraryCampaign).filter(AdLibraryCampaign.account_id == account_id).all()
    adsets = db.query(AdLibraryAdset).filter(AdLibraryAdset.account_id == account_id).all()
    items = db.query(AdLibraryItem).filter(AdLibraryItem.account_id == account_id).all()
    return campaigns, adsets, items


def get_campaign(db: Session, row_id: str) -> AdLibraryCampaign | None:
    return db.query(AdLibraryCampaign).filter(AdLibraryCampaign.id == row_id).first()


def get_adset(db: Session, row_id: str) -> AdLibraryAdset | None:
    return db.query(AdLibraryAdset).filter(AdLibraryAdset.id == row_id).first()


def list_adsets_for_campaign(db: Session, account_id: str, campaign_id: str) -> list[AdLibraryAdset]:
    return (
        db.query(AdLibraryAdset)
        .filter(AdLibraryAdset.account_id == account_id, AdLibraryAdset.campaign_id == campaign_id)
        .all()
    )


def list_items_for_adset(db: Session, account_id: str, adset_id: str) -> list[AdLibraryItem]:
    return (
        db.query(AdLibraryItem)
        .filter(AdLibraryItem.account_id == account_id, AdLibraryItem.adset_id == adset_id)
        .all()
    )


def list_items(
    db: Session,
    *,
    account_id: str,
    status: str | None = None,
    media_type: str | None = None,
    q: str | None = None,
    sort: str = "impressions",
    order: str = "desc",
    page: int = 1,
    page_size: int = 24,
    copy_key: str | None = None,
    media_key: str | None = None,
) -> tuple[list[AdLibraryItem], int]:
    query = db.query(AdLibraryItem).filter(AdLibraryItem.account_id == account_id)
    if copy_key:
        query = query.filter(AdLibraryItem.copy_key == copy_key)
    if media_key:
        query = query.filter(AdLibraryItem.media_key == media_key)
    if status in STATUS_GROUPS:
        query = query.filter(AdLibraryItem.effective_status.in_(STATUS_GROUPS[status]))
    elif status == "other":
        all_grouped = [s for group in STATUS_GROUPS.values() for s in group]
        query = query.filter(
            or_(AdLibraryItem.effective_status.is_(None), ~AdLibraryItem.effective_status.in_(all_grouped))
        )
    if media_type:
        query = query.filter(AdLibraryItem.media_type == media_type)
    if q:
        for term in q.lower().split():
            query = query.filter(AdLibraryItem.search_text.contains(term, autoescape=True))

    total = query.count()
    column = SORT_COLUMNS.get(sort, AdLibraryItem.impressions)
    ordering = column.asc() if order == "asc" else column.desc()
    query = query.order_by(ordering, AdLibraryItem.ad_id.desc())
    if page_size:
        query = query.offset(max(page - 1, 0) * page_size).limit(page_size)
    return query.all(), total


def get_item(db: Session, item_id: str) -> AdLibraryItem | None:
    return db.query(AdLibraryItem).filter(AdLibraryItem.id == item_id).first()


def find_media_owner(db: Session, asset_id: str) -> tuple[set[str], MetaAndromedaAsset] | None:
    """找出引用此 asset 的廣告帳號集合（用於授權）與 asset 紀錄。

    只在 ad_library_items.media 有引用時才回傳，避免把本端點變成讀取任意
    Meta Andromeda 素材的後門。
    """
    asset = db.query(MetaAndromedaAsset).filter(MetaAndromedaAsset.id == asset_id).first()
    if asset is None:
        return None
    # JSON 欄位跨 SQLite/PostgreSQL 不易直接查詢，先以字串包含粗篩再精確比對
    candidates = (
        db.query(AdLibraryItem.account_id, AdLibraryItem.media)
        .filter(AdLibraryItem.media.cast(Text).contains(asset_id, autoescape=True))
        .all()
    )
    owners = {
        account_id
        for account_id, media in candidates
        if any((m or {}).get("asset_id") == asset_id for m in media or [])
    }
    if not owners:
        return None
    return owners, asset


def same_key_counts(db: Session, account_id: str, items: list[AdLibraryItem]) -> dict[str, dict[str, int]]:
    """回傳 {"copy": {copy_key: 使用數}, "media": {media_key: 使用數}}，供卡片顯示「同文案 N 則」。"""
    out: dict[str, dict[str, int]] = {"copy": {}, "media": {}}
    for label, column in (("copy", AdLibraryItem.copy_key), ("media", AdLibraryItem.media_key)):
        keys = {getattr(i, column.key) for i in items if getattr(i, column.key)}
        if not keys:
            continue
        rows = (
            db.query(column, func.count(AdLibraryItem.id))
            .filter(AdLibraryItem.account_id == account_id, column.in_(keys))
            .group_by(column)
            .all()
        )
        out[label] = {key: count for key, count in rows}
    return out


def list_comparison_items(db: Session, account_id: str) -> list[AdLibraryItem]:
    return db.query(AdLibraryItem).filter(AdLibraryItem.account_id == account_id).all()


CONTENT_SORTS = ("ads", "spend", "impressions", "ctr")


def list_contents(
    db: Session,
    *,
    account_id: str,
    kind: str | None = None,
    q: str | None = None,
    sort: str = "ads",
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[tuple], int]:
    """元件清單，附使用此元件的廣告數、廣告組合數、行銷活動數與彙總成效。

    回傳 [(content, ad_count, adset_count, campaign_count, impressions, clicks, spend)], total
    """
    ad_count = func.count(func.distinct(AdLibraryItem.id))
    impressions = func.coalesce(func.sum(AdLibraryItem.impressions), 0)
    clicks = func.coalesce(func.sum(AdLibraryItem.clicks), 0)
    spend = func.coalesce(func.sum(AdLibraryItem.spend), 0.0)
    query = (
        db.query(
            AdLibraryContent,
            ad_count,
            func.count(func.distinct(AdLibraryItem.adset_id)),
            func.count(func.distinct(AdLibraryItem.campaign_id)),
            impressions,
            clicks,
            spend,
        )
        .join(AdLibraryAdContent, AdLibraryAdContent.content_id == AdLibraryContent.id)
        .join(AdLibraryItem, AdLibraryItem.id == AdLibraryAdContent.item_id)
        .filter(AdLibraryContent.account_id == account_id)
        .group_by(AdLibraryContent.id)
    )
    if kind:
        query = query.filter(AdLibraryContent.kind == kind)
    if q:
        for term in q.split():
            query = query.filter(AdLibraryContent.text_value.contains(term, autoescape=True))

    total = query.count()
    if sort == "spend":
        ordering = spend.desc()
    elif sort == "impressions":
        ordering = impressions.desc()
    elif sort == "ctr":
        # PostgreSQL 的 DESC 會把 NULL 排最前面，沒有曝光的元件以 0 計
        ordering = func.coalesce(clicks * 1.0 / func.nullif(impressions, 0), 0).desc()
    else:
        ordering = ad_count.desc()
    rows = (
        query.order_by(ordering, AdLibraryContent.id)
        .offset(max(page - 1, 0) * page_size)
        .limit(page_size)
        .all()
    )
    return rows, total


def get_content(db: Session, content_id: str) -> AdLibraryContent | None:
    return db.query(AdLibraryContent).filter(AdLibraryContent.id == content_id).first()


def list_items_for_content(db: Session, content_id: str) -> list[AdLibraryItem]:
    # 以子查詢取代 DISTINCT：PostgreSQL 的 json 欄位無法做 DISTINCT
    item_ids = db.query(AdLibraryAdContent.item_id).filter(AdLibraryAdContent.content_id == content_id)
    return db.query(AdLibraryItem).filter(AdLibraryItem.id.in_(item_ids)).all()


# ── 動態素材元件成效（docs/74 第 3 階段）──────────────────────────────────
def dynamic_ads_for_asset_insights(db: Session, account_id: str, limit: int) -> tuple[list[dict], int]:
    """有曝光的動態素材廣告，依花費由高到低取前 limit 則；回傳 (清單, 符合條件的總數)。"""
    query = db.query(AdLibraryItem).filter(
        AdLibraryItem.account_id == account_id,
        AdLibraryItem.media_type == "dynamic",
        AdLibraryItem.impressions > 0,
    )
    total = query.count()
    items = query.order_by(AdLibraryItem.spend.desc(), AdLibraryItem.ad_id).limit(limit).all()
    return [
        {
            "ad_id": item.ad_id,
            "primary_texts": item.primary_texts,
            "headlines": item.headlines,
            "descriptions": item.descriptions,
            "media": item.media,
        }
        for item in items
    ], total


def replace_asset_insights(db: Session, account_id: str, ad_id: str, entries: list[dict]) -> int:
    """以本次抓到的元件成效取代該廣告的舊資料；回傳寫入列數。"""
    contents = _ensure_content_rows(
        db, account_id, {(e["kind"], e["fingerprint"]): e for e in entries}
    )
    db.query(AdLibraryAssetInsight).filter(
        AdLibraryAssetInsight.account_id == account_id, AdLibraryAssetInsight.ad_id == ad_id
    ).delete(synchronize_session=False)
    now = _utcnow()
    for e in entries:
        db.add(AdLibraryAssetInsight(
            account_id=account_id,
            ad_id=ad_id,
            content_id=contents[(e["kind"], e["fingerprint"])].id,
            kind=e["kind"],
            fb_asset_id=e.get("fb_asset_id"),
            impressions=e["impressions"],
            reach=e["reach"],
            clicks=e["clicks"],
            spend=e["spend"],
            fetched_at=now,
        ))
    db.commit()
    return len(entries)


def asset_insights_for_ad(db: Session, account_id: str, ad_id: str) -> list[tuple]:
    """[(AdLibraryAssetInsight, AdLibraryContent)]，依曝光由高到低。"""
    return (
        db.query(AdLibraryAssetInsight, AdLibraryContent)
        .join(AdLibraryContent, AdLibraryContent.id == AdLibraryAssetInsight.content_id)
        .filter(AdLibraryAssetInsight.account_id == account_id, AdLibraryAssetInsight.ad_id == ad_id)
        .order_by(AdLibraryAssetInsight.impressions.desc(), AdLibraryAssetInsight.id)
        .all()
    )


def asset_metrics_for_contents(db: Session, content_ids: list[str]) -> dict[str, dict]:
    """元件在動態素材廣告中的實際成效（可直接歸給元件），供 /contents 一併回傳。"""
    if not content_ids:
        return {}
    rows = (
        db.query(
            AdLibraryAssetInsight.content_id,
            func.count(func.distinct(AdLibraryAssetInsight.ad_id)),
            func.coalesce(func.sum(AdLibraryAssetInsight.impressions), 0),
            func.coalesce(func.sum(AdLibraryAssetInsight.clicks), 0),
            func.coalesce(func.sum(AdLibraryAssetInsight.spend), 0.0),
        )
        .filter(AdLibraryAssetInsight.content_id.in_(content_ids))
        .group_by(AdLibraryAssetInsight.content_id)
        .all()
    )
    return {
        content_id: {
            "ads": ads,
            "impressions": int(impressions or 0),
            "clicks": int(clicks or 0),
            "spend": float(spend or 0.0),
            "ctr": (clicks / impressions * 100) if impressions else 0.0,
        }
        for content_id, ads, impressions, clicks, spend in rows
    }
