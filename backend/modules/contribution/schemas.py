"""
Contribution Module - Request / Response Schemas（docs/21 第 3.5 節）

第 1 波任務 1.1：僅定義骨架所需的 schema，端點本波回 501。
分析結果的細節 schema（貢獻區間、邊際轉換、診斷）於任務 1.2–1.4 隨引擎
輸出定型後再補強；本檔先以 dict / list 承載 JSON 欄位，避免過早綁死形狀。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PingResponse(BaseModel):
    status: str
    module: str
    message: str


class CampaignSummary(BaseModel):
    campaign_id: str
    campaign_name: str | None = None
    spend: float = 0.0
    impressions: int = 0
    conversions: float = 0.0
    conversion_value: float = 0.0
    active_days: int = 0


class CampaignListResponse(BaseModel):
    account_id: str
    campaigns: list[CampaignSummary]
    total: int


class CampaignGroup(BaseModel):
    group_key: str
    group_name: str
    campaign_ids: list[str] = Field(default_factory=list)
    source: str = "auto"


class GroupsResponse(BaseModel):
    account_id: str
    groups: list[CampaignGroup]
    source: str  # auto / manual


class GroupsUpdateRequest(BaseModel):
    account_id: str
    groups: list[CampaignGroup]


class GroupsUpdateResponse(BaseModel):
    account_id: str
    groups: list[CampaignGroup]
    updated_count: int


class AnalysisCreateRequest(BaseModel):
    account_id: str
    date_start: str
    date_end: str
    metric_key: str = "omni_purchase"
    n_restarts: int | None = Field(default=None, ge=1, le=20)
    holdout_days: int | None = Field(default=None, ge=7, le=180)
    marginal_step: float | None = Field(default=None, gt=0)


class AnalysisCreateResponse(BaseModel):
    snapshot_id: str
    status: str
    account_id: str
    queue_host: str
    message: str


class AnalysisSummary(BaseModel):
    snapshot_id: str
    account_id: str
    status: str
    date_start: str
    date_end: str
    created_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    has_ai_summary: bool = False


class AnalysisListResponse(BaseModel):
    account_id: str
    analyses: list[AnalysisSummary]
    total: int


class AnalysisDetailResponse(BaseModel):
    snapshot_id: str
    account_id: str
    status: str
    date_start: str
    date_end: str
    config: dict[str, Any] = Field(default_factory=dict)
    results: dict[str, Any] | None = None
    diagnostics: dict[str, Any] | None = None
    error_message: str | None = None
    runtime_job_id: str | None = None
    ai_summary: str | None = None
    ai_summary_generated_at: datetime | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class AiSummaryUpdateRequest(BaseModel):
    ai_summary: str = Field(..., min_length=1, max_length=20000)


class AiSummaryUpdateResponse(BaseModel):
    snapshot_id: str
    ai_summary: str
    ai_summary_generated_at: datetime


class DataRefreshResponse(BaseModel):
    account_id: str
    status: str
    message: str
