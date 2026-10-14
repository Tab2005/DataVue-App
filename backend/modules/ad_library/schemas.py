"""Ad Library - API schemas（docs/73、docs/74）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RefreshRequest(BaseModel):
    account_id: str


class RefreshJobResponse(BaseModel):
    job_id: str
    account_id: str
    status: str
    ads_fetched: int
    campaigns_fetched: int = 0
    adsets_fetched: int = 0
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
    adset_id: str | None = None
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


class AdLibraryTreeResponse(BaseModel):
    """docs/74：行銷活動 → 廣告組合 → 廣告。節點欄位見 hierarchy.py。"""

    account_id: str
    campaigns: list[dict[str, Any]]
    latest_job: RefreshJobResponse | None = None


class CampaignDetailResponse(BaseModel):
    campaign: dict[str, Any]
    adsets: list[dict[str, Any]]


class AdsetDetailResponse(BaseModel):
    adset: dict[str, Any]
    ads: list[dict[str, Any]]
