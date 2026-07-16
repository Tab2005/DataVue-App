"""Scoring assets routes for Meta Andromeda."""

from __future__ import annotations

from ._shared import *

router = APIRouter()


@router.get("/assets/preview")
async def preview_asset(
    uri: str = Query(...),
    db=Depends(get_db),
):
    """
    提供素材的即時預覽與下載路由，安全地代理並提供檔案給前端。
    """
    asset = MetaAndromedaService.get_asset_by_uri(db, uri)
    if not asset:
        from database.models.meta_andromeda import MetaAndromedaAsset
        asset = db.query(MetaAndromedaAsset).filter(
            (MetaAndromedaAsset.asset_uri == uri) | 
            (MetaAndromedaAsset.source_filename == uri) |
            (MetaAndromedaAsset.storage_key.endswith(uri))
        ).first()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset not found for URI: {uri}",
        )

    if asset.storage_backend == "filesystem":
        if settings.SERVICE_ROLE == "all":
            return build_asset_response(asset)
        try:
            return await _facade_attr("proxy_asset_preview_response", proxy_asset_preview_response)(uri)
        except MetaAndromedaInternalWorkerGatewayError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    if asset.storage_backend == "s3_compatible":
        return build_asset_response(asset)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported storage backend: {asset.storage_backend}",
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
    try:
        if settings.SERVICE_ROLE == "all":
            return MetaAndromedaService.upload_asset(
                db,
                file_bytes=file_bytes,
                asset_type=asset_type,
                source_filename=source_filename,
                uploaded_by=getattr(user, "id", None),
                content_type=file.content_type,
            )
        return await _facade_attr("proxy_asset_upload_response", proxy_asset_upload_response)(
            asset_type=asset_type,
            source_filename=source_filename,
            file_bytes=file_bytes,
            uploaded_by=getattr(user, "id", None),
            content_type=file.content_type,
        )
    except MetaAndromedaValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


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
