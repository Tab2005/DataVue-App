"""Ad Library - 資料存取（docs/73、docs/74）。全部為同步函式，async 呼叫端須包 to_thread。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import Text, or_
from sqlalchemy.orm import Session

from database.models.ad_library import (
    AdLibraryAdset,
    AdLibraryCampaign,
    AdLibraryItem,
    AdLibraryRefreshJob,
)
from database.models.meta_andromeda import MetaAndromedaAsset

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


def _upsert(db: Session, model, key: str, rows: list[dict]) -> int:
    """以 (account_id, key) upsert 同一帳號的一批列；回傳寫入筆數。"""
    if not rows:
        return 0
    account_id = rows[0]["account_id"]
    key_column = getattr(model, key)
    existing = {
        getattr(obj, key): obj
        for obj in db.query(model).filter(
            model.account_id == account_id, key_column.in_([r[key] for r in rows])
        )
    }
    now = _utcnow()
    for row in rows:
        obj = existing.get(row[key])
        if obj is None:
            db.add(model(**row, first_seen_at=now, last_seen_at=now, fetched_at=now))
        else:
            for field, value in row.items():
                setattr(obj, field, value)
            obj.last_seen_at = now
            obj.fetched_at = now
    db.commit()
    return len(rows)


def upsert_items(db: Session, rows: list[dict]) -> int:
    return _upsert(db, AdLibraryItem, "ad_id", rows)


def upsert_campaigns(db: Session, rows: list[dict]) -> int:
    return _upsert(db, AdLibraryCampaign, "campaign_id", rows)


def upsert_adsets(db: Session, rows: list[dict]) -> int:
    return _upsert(db, AdLibraryAdset, "adset_id", rows)


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
) -> tuple[list[AdLibraryItem], int]:
    query = db.query(AdLibraryItem).filter(AdLibraryItem.account_id == account_id)
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
