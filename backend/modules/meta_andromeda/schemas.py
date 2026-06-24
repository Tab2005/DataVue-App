"""
Meta Andromeda Module - Request / Response Schemas
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PingResponse(BaseModel):
    status: str
    module: str
    message: str


class OverviewModule(BaseModel):
    key: str
    name: str
    status: str
    phase: str


class OverviewSummary(BaseModel):
    integration_status: str
    current_slice: str
    next_slice: str


class OverviewCapability(BaseModel):
    key: str
    label: str
    status: str


class OverviewResponse(BaseModel):
    module: OverviewModule
    summary: OverviewSummary
    capabilities: list[OverviewCapability]
    notes: list[str]


class RuntimeHealthResponse(BaseModel):
    status: str
    queue_host: str
    checks: dict
    notes: list[str]


class MonitoringWorkerEventResponse(BaseModel):
    worker_event_id: str
    score_event_id: str
    event_type: str
    queue_host: str
    runtime_job_id: str | None = None
    status: str
    attempt_count: int
    message: str | None = None
    event_payload: dict = Field(default_factory=dict)
    created_at: str | None = None


class MonitoringDeadLetterResponse(BaseModel):
    dead_letter_id: str
    score_event_id: str
    queue_host: str
    runtime_job_id: str | None = None
    final_error_message: str
    failure_stage: str
    attempt_count: int
    dead_letter_payload: dict = Field(default_factory=dict)
    created_at: str | None = None


class DriftReportResponse(BaseModel):
    drift_report_id: str
    window_kind: str
    drift_status: str
    summary: str
    severity: str
    triggered_by: str | None = None
    note: str | None = None
    report_payload: dict = Field(default_factory=dict)
    created_at: str | None = None


class MonitoringTimelineResponse(BaseModel):
    score_event: dict
    worker_events: list[MonitoringWorkerEventResponse]
    dead_letters: list[MonitoringDeadLetterResponse]
    feedback: list[dict]


class DriftTriggerRequest(BaseModel):
    window_kind: Literal["last_24h", "last_7d", "last_30d", "lifetime", "custom"] = "last_24h"
    since: str | None = None
    until: str | None = None
    note: str | None = None
    account_id: str | None = None


class CalibrationSyncRequest(BaseModel):
    window_kind: str
    excluded_observed_ids: list[str] = Field(default_factory=list)


class CalibrationSyncResponse(BaseModel):
    dataset_id: str
    synced_count: int
    status: str
    item_count: int | None = None
    label_policy_version: str | None = None


class ReviewQueueItemResponse(BaseModel):
    score_event_id: str
    status: str
    runtime_job_id: str | None = None
    created_at: datetime
    queued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    updated_at: datetime
    asset_uri: str
    asset_type: str
    asset_id: str | None
    preview_url: str | None
    request_mode: str
    objective: str
    placement_family: str
    market: str
    prediction_mode: str | None
    overall_score: int | None
    roas_band: str | None
    model_version: str | None
    reviewed: bool
    feedback_count: int
    latest_feedback_decision: str | None
    feature_manifest_id: str | None
    error_message: str | None
    attempt_count: int


class ReviewQueueListSummaryResponse(BaseModel):
    total: int
    status_filter: str | None
    reviewed_filter: bool | None


class ReviewQueueListResponse(BaseModel):
    items: list[ReviewQueueItemResponse]
    summary: ReviewQueueListSummaryResponse


class RoasPredictionResponse(BaseModel):
    eligible: bool
    band: str | None
    confidence: float | None
    reason_if_unavailable: str | None


class ScoreExplanationResponse(BaseModel):
    summary: str
    top_positive_drivers: list[str]
    top_risks: list[str]
    diagnostic_evidence: dict[str, Any]


class ReviewQueueDetailResponse(BaseModel):
    score_event_id: str
    status: str
    runtime_job_id: str | None = None
    queued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    asset_uri: str
    asset_type: str
    asset_id: str | None
    preview_url: str | None
    prediction_mode: str | None
    overall_score: int | None
    diagnostic_breakdown: dict[str, str]
    roas_prediction: RoasPredictionResponse | None
    risk_tags: list[str]
    top_positive_drivers: list[str]
    top_negative_drivers: list[str]
    explanations: ScoreExplanationResponse | None
    model_version: str | None
    feature_manifest_id: str | None
    lineage: dict[str, str | None]
    error_message: str | None
    attempt_count: int
    created_at: datetime


class AssetUploadResponse(BaseModel):
    asset_uri: str
    asset_id: str
    storage_backend: str
    storage_key: str
    asset_type: str
    checksum_sha256: str
    upload_status: str
    source_filename: str
    file_size_bytes: int
    public_url: str | None = None
    uploaded_at: str


class ScoreSubmitRequest(BaseModel):
    asset_uri: str
    asset_type: Literal["image", "video"]
    asset_id: str | None = None
    request_mode: str = "auto"
    objective: str = "purchase"
    placement_family: str = "all"
    market: str = "TW"
    primary_text: str | None = None
    headline: str | None = None
    cta: str | None = None


class FacebookAdObservedImportRequest(BaseModel):
    account_id: str
    ad_id: str
    observation_window_kind: Literal["last_7d", "last_30d", "lifetime", "custom"]
    since: str | None = None
    until: str | None = None
    market: str = "TW"
    placement_family: str = "all"
    primary_text: str | None = None
    headline: str | None = None
    cta: str | None = None


class ObservationWindowResponse(BaseModel):
    kind: str
    start: str
    end: str


class ObservationSourceResponse(BaseModel):
    platform: str
    account_id: str
    ad_id: str


class FacebookAdObservedImportResponse(BaseModel):
    observed_creative_id: str
    status: str
    asset_uri: str | None = None
    score_event_id: str | None = None
    score_status: str | None = None
    runtime_job_id: str | None = None
    source: ObservationSourceResponse
    observation_window: ObservationWindowResponse
    performance_snapshot: dict = Field(default_factory=dict)


class FacebookAdObservedImportStatusResponse(BaseModel):
    observed_creative_id: str
    observation_status: str
    observation_message: str | None = None
    asset_uri: str | None = None
    score_event_id: str | None = None
    score_status: str | None = None
    runtime_job_id: str | None = None
    updated_at: str | None = None


class ObservedCreativeCandidate(BaseModel):
    source_platform: str
    source_account_id: str
    campaign_id: str | None = None
    adset_id: str | None = None
    ad_id: str
    ad_name: str | None = None
    objective: str | None = None
    placement_family: str
    market: str
    primary_text: str | None = None
    headline: str | None = None
    cta: str | None = None
    media_url: str | None = None
    media_type: Literal["image", "video", "unknown"] = "unknown"
    performance_snapshot: dict = Field(default_factory=dict)
    observation_window_kind: str
    observation_window_start: str
    observation_window_end: str
    source_fetched_at: str


class ExternalWorkerScoreResultRequest(BaseModel):
    prediction_mode: str | None = None
    overall_score: int | None = None
    roas_band: str | None = None
    model_version: str | None = None
    feature_manifest_id: str | None = None
    error_message: str | None = None
    diagnostic_breakdown: dict[str, str] = Field(default_factory=dict)
    roas_prediction: dict = Field(default_factory=dict)
    risk_tags: list[str] = Field(default_factory=list)
    top_positive_drivers: list[str] = Field(default_factory=list)
    top_negative_drivers: list[str] = Field(default_factory=list)
    explanations: dict = Field(default_factory=dict)
    lineage: dict[str, str | None] = Field(default_factory=dict)


class ExternalWorkerCallbackRequest(BaseModel):
    event_type: Literal["accepted", "processing", "completed", "failed"]
    queue_host: str = "external_webhook"
    runtime_job_id: str | None = None
    worker_id: str | None = None
    receipt_id: str | None = None
    attempt_count: int | None = None
    error_message: str | None = None
    retryable: bool = False
    retry_delay_seconds: float | None = None
    result_payload: ExternalWorkerScoreResultRequest | None = None
    callback_metadata: dict = Field(default_factory=dict)


class ExternalWorkerCallbackResponse(BaseModel):
    accepted: bool
    score_event_id: str
    event_type: str
    current_status: str
    runtime_job_id: str | None = None


class FeedbackEntryResponse(BaseModel):
    feedback_event_id: str
    score_event_id: str
    reviewer_id: str
    decision: str
    reason_codes: list[str]
    comment: str | None
    created_at: str


class FeedbackListResponse(BaseModel):
    score_event_id: str
    feedback: list[FeedbackEntryResponse]


class FeedbackSubmitRequest(BaseModel):
    reviewer_id: str | None = None
    decision: Literal["approve", "revise", "reject"]
    reason_codes: list[str] = Field(default_factory=list)
    comment: str | None = None


class ReleaseRecordResponse(BaseModel):
    model_version: str
    release_status: str
    approved_by: str
    approved_at: str
    pairwise_ranking_accuracy: float
    mean_band_error: float


class ReleaseCandidateResponse(BaseModel):
    model_version: str
    release_status: str
    created_at: str
    pairwise_ranking_accuracy: float
    mean_band_error: float
    promotion_gate_summary: dict[str, bool]


class ReleaseHistoryEntryResponse(BaseModel):
    action: str
    model_version: str
    actor: str
    created_at: str
    note: str


class ReleaseOverviewResponse(BaseModel):
    current_production: ReleaseRecordResponse
    previous_production: ReleaseRecordResponse
    candidates: list[ReleaseCandidateResponse]
    history: list[ReleaseHistoryEntryResponse]
    notes: list[str]


class ReleaseActionRequest(BaseModel):
    model_version: str
    note: str | None = None


class ReleaseActionResponse(BaseModel):
    status: str
    action: str
    model_version: str
    actor: str
    created_at: str
    note: str | None = None


class MaintenanceCleanupRequest(BaseModel):
    older_than_minutes: int | None = Field(default=None, ge=5, le=10080)
    include_queued: bool = True
    purge_worker_events: bool = False
    purge_dead_letters: bool = False
    limit: int = Field(default=500, ge=1, le=5000)


class MaintenanceCleanupResponse(BaseModel):
    cleaned_total: int
    cleaned_score_event_ids: list[str]
    include_statuses: list[str]
    older_than_minutes: int
    cutoff_timestamp: str
    removed_scheduler_jobs: int
    cleared_memory_statuses: int
    deleted_worker_events: int
    deleted_dead_letters: int
    notes: list[str]


class ScoringProfileEntry(BaseModel):
    profile_name: str
    source: str
    base_profile_name: str | None = None
    calibration_dataset_id: str | None = None
    is_promoted: bool
    promoted_at: str | None = None
    bias_summary: dict | None = None
    calibration_guidance: str | None = None
    few_shot_example_count: int
    created_at: str | None = None


class ScoringProfileListResponse(BaseModel):
    profiles: list[ScoringProfileEntry]
    total: int


class ScoringProfilePromoteResponse(BaseModel):
    profile_name: str
    is_promoted: bool
    promoted_at: str


class ObservedAccountEntry(BaseModel):
    account_id: str
    platform: str
    total_creatives: int
    last_imported_at: str | None = None


class ObservedAccountListResponse(BaseModel):
    accounts: list[ObservedAccountEntry]
    total: int


class DriftTrendEntry(BaseModel):
    drift_report_id: str
    window_kind: str
    drift_status: str
    note: str | None = None
    account_id: str | None = None
    spearman_r: float | None = None
    perf_median: float | None = None
    dominant_metric: str | None = None
    period_state: str | None = None
    period_label: str | None = None
    creative_explained_variance: float | None = None
    total_matched: int | None = None
    since: str | None = None
    until: str | None = None
    created_at: str | None = None


class DriftTrendResponse(BaseModel):
    entries: list[DriftTrendEntry]
    total: int
