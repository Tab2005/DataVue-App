"""Shared imports for Meta Andromeda API routers."""

from __future__ import annotations

import asyncio
import sys

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Header, HTTPException, Query, Request, UploadFile, status

from core.config import settings
from core.scheduler import get_meta_andromeda_score_job_id
from database import get_db
from ..dependencies import (
    get_current_meta_andromeda_user,
    require_fb_ads_analytics_view,
    require_fb_ads_module,
    require_meta_andromeda_feedback,
    require_meta_andromeda_module,
    require_meta_andromeda_operate,
    require_meta_andromeda_release,
)
from ..schemas import (
    AssetUploadResponse,
    CalibrationSyncRequest,
    CalibrationSyncResponse,
    DriftReportResponse,
    DriftTrendResponse,
    DriftTriggerRequest,
    ObservedAccountListResponse,
    ExternalWorkerCallbackRequest,
    ExternalWorkerCallbackResponse,
    FacebookAdObservedImportRequest,
    FacebookAdObservedImportResponse,
    FacebookAdObservedImportStatusResponse,
    FeedbackEntryResponse,
    FeedbackListResponse,
    FeedbackSubmitRequest,
    MaintenanceCleanupRequest,
    MaintenanceCleanupResponse,
    ModelCandidateValidationResponse,
    MonitoringTimelineResponse,
    AiReadyResponse,
    ScoreEventBatchDeleteRequest,
    ScoreEventBatchDeleteResponse,
    ScoreEventDeleteResponse,
    ScoringProfileBacktestResponse,
    ScoringProfileListResponse,
    ScoringProfilePromoteResponse,
    BacktestModelUpdateRequest,
    BacktestRunCreateRequest,
    BacktestRunListResponse,
    BacktestRunResponse,
    EffectiveScoringStatusResponse,
    ModelRegistryEntryResponse,
    ModelRegistryListResponse,
    OverviewResponse,
    PingResponse,
    ReleaseActionRequest,
    ReleaseActionResponse,
    ReleaseCandidateCreateRequest,
    ReleaseCandidateResponse,
    ReleaseMetricPairsResponse,
    ReleaseMetricsRefreshResponse,
    ReleaseOverviewResponse,
    ReviewQueueDetailResponse,
    ReviewQueueListResponse,
    RuntimeHealthResponse,
    ScoreSubmitRequest,
)
from ..asset_delivery import build_asset_response
from ..internal_asset_gateway import (
    MetaAndromedaInternalWorkerGatewayError,
    proxy_asset_preview_response,
    proxy_asset_upload_response,
)
from ..service import MetaAndromedaService, MetaAndromedaValidationError


def _facade_attr(name: str, fallback):
    facade = sys.modules.get("modules.meta_andromeda.router")
    return getattr(facade, name, fallback) if facade is not None else fallback


__all__ = [name for name in globals() if not name.startswith("__")]
