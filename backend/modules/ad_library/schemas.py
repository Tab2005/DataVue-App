"""Ad Library - API schemas（docs/73）。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RefreshRequest(BaseModel):
    account_id: str


class RefreshJobResponse(BaseModel):
    job_id: str
    account_id: str
    status: str
    ads_fetched: int
    media_stored: int
    error: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class MediaItem(BaseModel):
    kind: str
    asset_id: str | None = None
    # 未落地時退回 FB CDN 原網址（可能已過期）
    fb_url: str | None = None


class AdLibraryItemResponse(BaseModel):
    id: str
    account_id: str
    ad_id: str
    ad_name: str | None = None
    campaign_id: str | None = None
    campaign_name: str | None = None
    adset_name: str | None = None
    objective: str | None = None
    effective_status: str | None = None
    media_type: str
    primary_texts: list[str]
    headlines: list[str]
    descriptions: list[str]
    cta_types: list[str]
    link_url: str | None = None
    media: list[MediaItem]
    preview_link: str | None = None
    impressions: int
    reach: int
    clicks: int
    spend: float
    ctr: float
    ad_created_at: datetime | None = None
    ad_updated_at: datetime | None = None
    fetched_at: datetime | None = None


class AdLibraryListResponse(BaseModel):
    items: list[AdLibraryItemResponse]
    total: int
    page: int
    page_size: int
    latest_job: RefreshJobResponse | None = None
