"""Scoring assets routes for Meta Andromeda."""

from __future__ import annotations

from . import _shared

router = _shared.APIRouter()


@router.get("/assets/preview")
async def preview_asset(
    uri: str = _shared.Query(...),
    db=_shared.Depends(_shared.get_db),
):
    """
    提供素材的即時預覽與下載路由，安全地代理並提供檔案給前端。
    """
    asset = _shared.MetaAndromedaService.get_asset_by_uri(db, uri)
    if not asset:
        from database.models.meta_andromeda import MetaAndromedaAsset
        asset = db.query(MetaAndromedaAsset).filter(
            (MetaAndromedaAsset.asset_uri == uri) | 
            (MetaAndromedaAsset.source_filename == uri) |
            (MetaAndromedaAsset.storage_key.endswith(uri))
        ).first()

    if not asset:
        raise _shared.HTTPException(
            status_code=_shared.status.HTTP_404_NOT_FOUND,
            detail=f"Asset not found for URI: {uri}",
        )

    storage_backend = asset.storage_backend
    # 已經拿到需要的 metadata，立刻釋放 DB 連線——接下來的代理呼叫（跨服務
    # HTTP 打去 worker，逾時上限預設 10 秒）或 S3 讀取跟資料庫完全無關，
    # 若讓 FastAPI 的 db=Depends(get_db) 繼續握著連線等到整個 request 結束，
    # 審核佇列列表頁一次渲染最多 25 張縮圖、瀏覽器同時發出一批預覽請求時，
    # 疊加起來就會把連線池吃光（2026-08-07 事故：pool_size=10+overflow=10
    # 全部卡滿，逾時 30 秒）。asset 的純量欄位已在查詢時載入，關閉 session
    # 後仍可安全存取。
    db.close()

    if storage_backend == "filesystem":
        if _shared.settings.SERVICE_ROLE == "all":
            return _shared.build_asset_response(asset)
        try:
            return await _shared._facade_attr("proxy_asset_preview_response", _shared.proxy_asset_preview_response)(uri)
        except _shared.MetaAndromedaInternalWorkerGatewayError as exc:
            raise _shared.HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    if storage_backend == "s3_compatible":
        return _shared.build_asset_response(asset)

    raise _shared.HTTPException(
        status_code=_shared.status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported storage backend: {storage_backend}",
    )


@router.post("/assets:upload", response_model=_shared.AssetUploadResponse, status_code=_shared.status.HTTP_201_CREATED)
async def upload_asset(
    asset_type: str = _shared.Form(...),
    source_filename: str = _shared.Form(...),
    file: _shared.UploadFile = _shared.File(...),
    user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_operate),
    db=_shared.Depends(_shared.get_db),
):
    file_bytes = await file.read()
    try:
        if _shared.settings.SERVICE_ROLE == "all":
            return _shared.MetaAndromedaService.upload_asset(
                db,
                file_bytes=file_bytes,
                asset_type=asset_type,
                source_filename=source_filename,
                uploaded_by=getattr(user, "id", None),
                content_type=file.content_type,
            )
        # 這個分支完全不需要 db——但前面的 get_current_meta_andromeda_user /
        # require_meta_andromeda_operate 依賴已經用同一個 db session 查過
        # 使用者/權限，連線早已 checkout。提前釋放，才不會在代理上傳給
        # worker（檔案可能比縮圖大很多，等待時間更久）期間繼續占用連線池，
        # 跟 preview_asset 是同一個成因（見該函式的註解與 2026-08-07 事故）。
        uploaded_by = getattr(user, "id", None)
        db.close()
        return await _shared._facade_attr("proxy_asset_upload_response", _shared.proxy_asset_upload_response)(
            asset_type=asset_type,
            source_filename=source_filename,
            file_bytes=file_bytes,
            uploaded_by=uploaded_by,
            content_type=file.content_type,
        )
    except _shared.MetaAndromedaValidationError as exc:
        raise _shared.HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/scores", response_model=_shared.ReviewQueueDetailResponse, status_code=_shared.status.HTTP_201_CREATED)
async def create_score(
    payload: _shared.ScoreSubmitRequest,
    _user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_operate),
    db=_shared.Depends(_shared.get_db),
):
    created = _shared.MetaAndromedaService.create_score_event(db, payload.model_dump())
    runtime_job_id = _shared.get_meta_andromeda_score_job_id(created["score_event_id"])
    queued = _shared.MetaAndromedaService.assign_score_runtime_job(
        db,
        created["score_event_id"],
        runtime_job_id,
    )
    return _shared.MetaAndromedaService.enqueue_score_event(
        db,
        score_event_id=created["score_event_id"],
        runtime_job_id=runtime_job_id,
    )


@router.post(
    "/worker/score-events/{score_event_id}/callbacks",
    response_model=_shared.ExternalWorkerCallbackResponse,
)
async def external_worker_callback(
    score_event_id: str,
    payload: _shared.ExternalWorkerCallbackRequest,
    request: _shared.Request,
    x_meta_andromeda_worker_signature: str | None = _shared.Header(default=None, alias="X-Meta-Andromeda-Worker-Signature"),
    x_meta_andromeda_worker_token: str | None = _shared.Header(default=None, alias="X-Meta-Andromeda-Worker-Token"),
    db=_shared.Depends(_shared.get_db),
):
    try:
        _shared.MetaAndromedaService.verify_external_worker_callback(
            await request.body(),
            signature=x_meta_andromeda_worker_signature,
            worker_token=x_meta_andromeda_worker_token,
        )
    except PermissionError as exc:
        raise _shared.HTTPException(status_code=_shared.status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    try:
        updated = _shared.MetaAndromedaService.handle_external_worker_callback(
            db,
            score_event_id=score_event_id,
            payload=payload.model_dump(),
        )
    except KeyError as exc:
        raise _shared.HTTPException(
            status_code=_shared.status.HTTP_404_NOT_FOUND,
            detail=f"Score event not found: {score_event_id}",
        ) from exc
    except ValueError as exc:
        raise _shared.HTTPException(status_code=_shared.status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return {
        "accepted": True,
        "score_event_id": score_event_id,
        "event_type": payload.event_type,
        "current_status": updated["status"],
        "runtime_job_id": updated.get("runtime_job_id"),
    }


@router.get("/scores/{score_event_id}", response_model=_shared.ReviewQueueDetailResponse)
async def get_score(
    score_event_id: str,
    _user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_module),
    db=_shared.Depends(_shared.get_db),
):
    try:
        return _shared.MetaAndromedaService.get_score_detail(db, score_event_id)
    except KeyError as exc:
        raise _shared.HTTPException(
            status_code=_shared.status.HTTP_404_NOT_FOUND,
            detail=f"Score event not found: {score_event_id}",
        ) from exc


@router.get("/scores/{score_event_id}/feedback", response_model=_shared.FeedbackListResponse)
async def get_feedback(
    score_event_id: str,
    _user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_module),
    db=_shared.Depends(_shared.get_db),
):
    try:
        return _shared.MetaAndromedaService.list_feedback(db, score_event_id)
    except KeyError as exc:
        raise _shared.HTTPException(
            status_code=_shared.status.HTTP_404_NOT_FOUND,
            detail=f"Score event not found: {score_event_id}",
        ) from exc


@router.post(
    "/scores/{score_event_id}/feedback",
    response_model=_shared.FeedbackEntryResponse,
    status_code=_shared.status.HTTP_201_CREATED,
)
async def submit_feedback(
    score_event_id: str,
    payload: _shared.FeedbackSubmitRequest,
    user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_feedback),
    db=_shared.Depends(_shared.get_db),
):
    try:
        return _shared.MetaAndromedaService.submit_feedback(
            db,
            score_event_id=score_event_id,
            reviewer_id=payload.reviewer_id or getattr(user, "email", None) or "datavue_user",
            decision=payload.decision,
            reason_codes=payload.reason_codes,
            comment=payload.comment,
        )
    except KeyError as exc:
        raise _shared.HTTPException(
            status_code=_shared.status.HTTP_404_NOT_FOUND,
            detail=f"Score event not found: {score_event_id}",
        ) from exc
