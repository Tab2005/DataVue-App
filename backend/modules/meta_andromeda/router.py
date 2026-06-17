"""
Meta Andromeda Module - Router
"""

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, Request, UploadFile, status

from core.scheduler import get_meta_andromeda_score_job_id
from database import get_db
from .dependencies import (
    get_current_meta_andromeda_user,
    require_fb_ads_analytics_view,
    require_fb_ads_module,
    require_meta_andromeda_feedback,
    require_meta_andromeda_module,
    require_meta_andromeda_operate,
    require_meta_andromeda_release,
)
from .schemas import (
    AssetUploadResponse,
    CalibrationSyncRequest,
    CalibrationSyncResponse,
    DriftReportResponse,
    DriftTriggerRequest,
    ExternalWorkerCallbackRequest,
    ExternalWorkerCallbackResponse,
    FacebookAdObservedImportRequest,
    FacebookAdObservedImportResponse,
    FeedbackEntryResponse,
    FeedbackListResponse,
    FeedbackSubmitRequest,
    MonitoringTimelineResponse,
    OverviewResponse,
    PingResponse,
    ReleaseActionRequest,
    ReleaseActionResponse,
    ReleaseOverviewResponse,
    ReviewQueueDetailResponse,
    ReviewQueueListResponse,
    RuntimeHealthResponse,
    ScoreSubmitRequest,
)
from .service import MetaAndromedaService

router = APIRouter()


@router.get("/ping", response_model=PingResponse)
async def ping(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
):
    """Minimal health endpoint for the first integration slice."""
    return MetaAndromedaService.get_ping_payload()


@router.get("/overview", response_model=OverviewResponse)
async def overview(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    """Read-only overview endpoint for the second integration slice."""
    return MetaAndromedaService.get_overview_payload()


@router.get("/review-queue", response_model=ReviewQueueListResponse)
async def review_queue(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
    reviewed: bool | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
):
    """Read-only review queue endpoint for the third integration slice."""
    return MetaAndromedaService.list_review_queue(
        db,
        status=status_filter,
        reviewed=reviewed,
        limit=limit,
    )


@router.get("/review-queue/{score_event_id}", response_model=ReviewQueueDetailResponse)
async def review_queue_detail(
    score_event_id: str,
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    """Read-only review queue detail endpoint for the third integration slice."""
    try:
        return MetaAndromedaService.get_review_queue_detail(db, score_event_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review queue item not found: {score_event_id}",
        ) from exc


@router.get("/monitoring/summary")
async def monitoring_summary(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    """Read-only monitoring summary endpoint for the fourth integration slice."""
    return MetaAndromedaService.get_monitoring_summary(db)


@router.get("/monitoring/score-events/{score_event_id}/timeline", response_model=MonitoringTimelineResponse)
async def monitoring_timeline(
    score_event_id: str,
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    try:
        return MetaAndromedaService.get_monitoring_timeline(db, score_event_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score event not found: {score_event_id}",
        ) from exc


@router.post("/drift:trigger", response_model=DriftReportResponse, status_code=status.HTTP_201_CREATED)
async def trigger_drift_report(
    payload: DriftTriggerRequest,
    user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_operate),
    db=Depends(get_db),
):
    return MetaAndromedaService.trigger_drift_report(
        db,
        window_kind=payload.window_kind,
        triggered_by=getattr(user, "email", None) or "datavue_operator",
        note=payload.note,
        since=payload.since,
        until=payload.until,
    )


@router.get("/runtime/health", response_model=RuntimeHealthResponse)
async def runtime_health(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    """Shared-runtime readiness summary for Meta Andromeda on the current host."""
    return MetaAndromedaService.get_runtime_health(db)


@router.get("/release/overview", response_model=ReleaseOverviewResponse)
async def release_overview(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    """Read-only release overview endpoint for the fifth integration slice."""
    return MetaAndromedaService.get_release_overview(db)


@router.post(
    "/evaluations/import/facebook-ads",
    response_model=FacebookAdObservedImportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def import_facebook_ad_observation(
    payload: FacebookAdObservedImportRequest,
    user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    _fb_ads_access: bool = Depends(require_fb_ads_module),
    _fb_ads_permission: bool = Depends(require_fb_ads_analytics_view),
    x_team_id: str | None = Header(default=None, alias="X-Team-ID"),
    db=Depends(get_db),
):
    return await MetaAndromedaService.import_observed_facebook_ad(
        db,
        payload.model_dump(),
        user_id=getattr(user, "google_id", None) or getattr(user, "id", None),
        team_id=x_team_id,
    )


@router.post(
    "/calibration/sync",
    response_model=CalibrationSyncResponse,
    status_code=status.HTTP_201_CREATED,
)
async def sync_calibration_dataset(
    payload: CalibrationSyncRequest,
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_operate),
    db=Depends(get_db),
):
    """將觀測資料打包同步為模型校準資料集"""
    return MetaAndromedaService.sync_calibration_dataset(
        db,
        window_kind=payload.window_kind,
        excluded_observed_ids=payload.excluded_observed_ids,
    )


@router.post("/assets:upload", response_model=AssetUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_asset(
    asset_type: str = Form(...),
    source_filename: str = Form(...),
    file: UploadFile = File(...),
    user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_operate),
    db=Depends(get_db),
):
    file_bytes = await file.read()
    return MetaAndromedaService.upload_asset(
        db,
        file_bytes=file_bytes,
        asset_type=asset_type,
        source_filename=source_filename,
        uploaded_by=getattr(user, "id", None),
        content_type=file.content_type,
    )


@router.post("/scores", response_model=ReviewQueueDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_score(
    payload: ScoreSubmitRequest,
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_operate),
    db=Depends(get_db),
):
    created = MetaAndromedaService.create_score_event(db, payload.model_dump())
    runtime_job_id = get_meta_andromeda_score_job_id(created["score_event_id"])
    queued = MetaAndromedaService.assign_score_runtime_job(
        db,
        created["score_event_id"],
        runtime_job_id,
    )
    return MetaAndromedaService.enqueue_score_event(
        db,
        score_event_id=created["score_event_id"],
        runtime_job_id=runtime_job_id,
    )


@router.post(
    "/worker/score-events/{score_event_id}/callbacks",
    response_model=ExternalWorkerCallbackResponse,
)
async def external_worker_callback(
    score_event_id: str,
    payload: ExternalWorkerCallbackRequest,
    request: Request,
    x_meta_andromeda_worker_signature: str | None = Header(default=None, alias="X-Meta-Andromeda-Worker-Signature"),
    x_meta_andromeda_worker_token: str | None = Header(default=None, alias="X-Meta-Andromeda-Worker-Token"),
    db=Depends(get_db),
):
    try:
        MetaAndromedaService.verify_external_worker_callback(
            await request.body(),
            signature=x_meta_andromeda_worker_signature,
            worker_token=x_meta_andromeda_worker_token,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    try:
        updated = MetaAndromedaService.handle_external_worker_callback(
            db,
            score_event_id=score_event_id,
            payload=payload.model_dump(),
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score event not found: {score_event_id}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return {
        "accepted": True,
        "score_event_id": score_event_id,
        "event_type": payload.event_type,
        "current_status": updated["status"],
        "runtime_job_id": updated.get("runtime_job_id"),
    }


@router.get("/scores/{score_event_id}", response_model=ReviewQueueDetailResponse)
async def get_score(
    score_event_id: str,
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    try:
        return MetaAndromedaService.get_score_detail(db, score_event_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score event not found: {score_event_id}",
        ) from exc


@router.get("/scores/{score_event_id}/feedback", response_model=FeedbackListResponse)
async def get_feedback(
    score_event_id: str,
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    try:
        return MetaAndromedaService.list_feedback(db, score_event_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score event not found: {score_event_id}",
        ) from exc


@router.post(
    "/scores/{score_event_id}/feedback",
    response_model=FeedbackEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_feedback(
    score_event_id: str,
    payload: FeedbackSubmitRequest,
    user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_feedback),
    db=Depends(get_db),
):
    try:
        return MetaAndromedaService.submit_feedback(
            db,
            score_event_id=score_event_id,
            reviewer_id=payload.reviewer_id or getattr(user, "email", None) or "datavue_user",
            decision=payload.decision,
            reason_codes=payload.reason_codes,
            comment=payload.comment,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score event not found: {score_event_id}",
        ) from exc


@router.post("/release/approve", response_model=ReleaseActionResponse)
async def approve_release(
    payload: ReleaseActionRequest,
    user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_release),
    db=Depends(get_db),
):
    try:
        return MetaAndromedaService.perform_release_action(
            db,
            action="approve",
            model_version=payload.model_version,
            actor=getattr(user, "email", None) or "datavue_operator",
            note=payload.note,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Release candidate not found: {payload.model_version}",
        ) from exc


@router.post("/release/reject", response_model=ReleaseActionResponse)
async def reject_release(
    payload: ReleaseActionRequest,
    user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_release),
    db=Depends(get_db),
):
    try:
        return MetaAndromedaService.perform_release_action(
            db,
            action="reject",
            model_version=payload.model_version,
            actor=getattr(user, "email", None) or "datavue_operator",
            note=payload.note,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Release candidate not found: {payload.model_version}",
        ) from exc


@router.post("/release/rollback", response_model=ReleaseActionResponse)
async def rollback_release(
    payload: ReleaseActionRequest,
    user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_release),
    db=Depends(get_db),
):
    return MetaAndromedaService.perform_release_action(
        db,
        action="rollback",
        model_version=payload.model_version,
        actor=getattr(user, "email", None) or "datavue_operator",
        note=payload.note,
    )
