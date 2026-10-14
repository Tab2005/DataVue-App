"""Ad Library - API schemas（docs/73、docs/74）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RefreshRequest(BaseModel):
    account_id: str


class RefreshJobResponse(BaseModel):
    job_id: str
    account_id: str
    status: str
    ads_fetched: int
    campaigns_fetched: int = 0
    adsets_fetched: int = 0
    asset_insights_ads: int = 0
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
    # docs/74 第二節：文案／素材指紋，以及同帳號內「其他」使用相同文案／素材的廣告數
    copy_key: str | None = None
    media_key: str | None = None
    same_copy_count: int = 0
    same_media_count: int = 0
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


class ComparisonsResponse(BaseModel):
    """docs/74 第二節：文案測試／素材測試／重複投放。組結構見 comparisons.py。"""

    account_id: str
    scope: str
    counts: dict[str, int]
    groups: list[dict[str, Any]]
    coverage: dict[str, int]
    note: str


class ContentResponse(BaseModel):
    id: str
    kind: str
    text_value: str | None = None
    image_hash: str | None = None
    video_id: str | None = None
    asset_id: str | None = None
    ad_count: int = 0
    adset_count: int = 0
    campaign_count: int = 0
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    ctr: float = 0.0
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    # docs/74 第 3 階段：此元件在動態素材廣告中的實際元件成效（可直接歸給元件）
    asset_metrics: dict[str, Any] | None = None


class ContentListResponse(BaseModel):
    items: list[ContentResponse]
    total: int
    page: int
    page_size: int
    # 一則廣告含多個元件時，成效會重複計入每個元件（動態素材尤其明顯）
    note: str


class ContentDetailResponse(BaseModel):
    content: ContentResponse
    ads: list[dict[str, Any]]


class AssetInsightEntry(BaseModel):
    content_id: str
    kind: str
    text_value: str | None = None
    image_hash: str | None = None
    video_id: str | None = None
    asset_id: str | None = None
    impressions: int
    reach: int
    clicks: int
    spend: float
    ctr: float


class AdAssetInsightsResponse(BaseModel):
    """docs/74 第 3 階段：單一動態素材廣告的元件成效，依 kind 分組。"""

    item_id: str
    ad_id: str
    fetched_at: datetime | None = None
    entries: dict[str, list[AssetInsightEntry]]
    note: str


class AiAnalysisRequest(BaseModel):
    """docs/75：model 省略時使用使用者在設定頁選的模型。"""

    account_id: str
    campaign_id: str = Field(..., max_length=64)
    model: str | None = Field(None, max_length=128)
