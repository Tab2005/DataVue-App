"""Observation import routes for Meta Andromeda."""

from __future__ import annotations

from . import _shared

router = _shared.APIRouter()


@router.post(
    "/evaluations/import/facebook-ads",
    response_model=_shared.FacebookAdObservedImportResponse,
    status_code=_shared.status.HTTP_202_ACCEPTED,
)
async def import_facebook_ad_observation(
    payload: _shared.FacebookAdObservedImportRequest,
    background_tasks: _shared.BackgroundTasks,
    user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_module),
    _fb_ads_access: bool = _shared.Depends(_shared.require_fb_ads_module),
    _fb_ads_permission: bool = _shared.Depends(_shared.require_fb_ads_analytics_view),
    x_team_id: str | None = _shared.Header(default=None, alias="X-Team-ID"),
    db=_shared.Depends(_shared.get_db),
):
    try:
        request_payload = payload.model_dump()
        accepted = _shared.MetaAndromedaService.queue_observed_facebook_ad_import(request_payload)
        # docs/68 B5：已有 in-flight 的同一筆匯入時 queue_observed_facebook_ad_import()
        # 不會重新標記 queued，這裡就不能再派工，否則會排出重複 job（見該函式內註解）。
        dispatch_needed = accepted.pop("_dispatch_needed", True)
        user_id = getattr(user, "google_id", None) or getattr(user, "id", None)

        if dispatch_needed:
            # docs/24 Wave 2：web 角色優先把匯入 job 經 Redis stream 派給獨立 worker
            # process；未派工成功（非 web 角色，或 Redis 不可用）時退回本 process
            # 背景執行（Wave 1 的 to_thread 化已確保這不會卡住 event loop）。
            dispatched = _shared.MetaAndromedaService.dispatch_observed_facebook_ad_import(
                request_payload, user_id=user_id, team_id=x_team_id
            )
            if not dispatched:
                background_tasks.add_task(
                    _shared.MetaAndromedaService.run_observed_facebook_ad_import_job,
                    request_payload,
                    user_id=user_id,
                    team_id=x_team_id,
                )
        return accepted
    except _shared.MetaAndromedaValidationError as exc:
        raise _shared.HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post(
    "/evaluations/import/facebook-ads/batch",
    response_model=_shared.FacebookAdBatchObservedImportResponse,
    status_code=_shared.status.HTTP_202_ACCEPTED,
)
async def import_facebook_ad_observations_batch(
    payload: _shared.FacebookAdBatchObservedImportRequest,
    background_tasks: _shared.BackgroundTasks,
    user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_module),
    _fb_ads_access: bool = _shared.Depends(_shared.require_fb_ads_module),
    _fb_ads_permission: bool = _shared.Depends(_shared.require_fb_ads_analytics_view),
    x_team_id: str | None = _shared.Header(default=None, alias="X-Team-ID"),
    db=_shared.Depends(_shared.get_db),
):
    """docs/68 B2 第二層：批次觀測匯入，一次預熱報告快取再逐筆派工，
    取代前端對同一批廣告逐筆各自呼叫單筆端點（見
    queue_observed_facebook_ad_import_batch 的完整說明）。"""
    try:
        user_id = getattr(user, "google_id", None) or getattr(user, "id", None)
        items = await _shared.MetaAndromedaService.queue_observed_facebook_ad_import_batch(
            payload.model_dump(),
            user_id=user_id,
            team_id=x_team_id,
            background_tasks=background_tasks,
        )
        return {"items": items}
    except _shared.MetaAndromedaValidationError as exc:
        raise _shared.HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get(
    "/evaluations/import/facebook-ads/{observed_creative_id}/status",
    response_model=_shared.FacebookAdObservedImportStatusResponse,
)
async def get_facebook_ad_observation_import_status(
    observed_creative_id: str,
    _user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_module),
    _fb_ads_access: bool = _shared.Depends(_shared.require_fb_ads_module),
    _fb_ads_permission: bool = _shared.Depends(_shared.require_fb_ads_analytics_view),
    db=_shared.Depends(_shared.get_db),
):
    return _shared.MetaAndromedaService.get_observed_facebook_ad_import_status(db, observed_creative_id)


@router.post(
    "/calibration/sync",
    response_model=_shared.CalibrationSyncResponse,
    status_code=_shared.status.HTTP_201_CREATED,
)
async def sync_calibration_dataset(
    payload: _shared.CalibrationSyncRequest,
    _user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_operate),
    db=_shared.Depends(_shared.get_db),
):
    """將觀測資料打包同步為模型校準資料集"""
    return _shared.MetaAndromedaService.sync_calibration_dataset(
        db,
        window_kind=payload.window_kind,
        excluded_observed_ids=payload.excluded_observed_ids,
    )
