"""Observation import routes for Meta Andromeda."""

from __future__ import annotations

from ._shared import *

router = APIRouter()


@router.post(
    "/evaluations/import/facebook-ads",
    response_model=FacebookAdObservedImportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def import_facebook_ad_observation(
    payload: FacebookAdObservedImportRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    _fb_ads_access: bool = Depends(require_fb_ads_module),
    _fb_ads_permission: bool = Depends(require_fb_ads_analytics_view),
    x_team_id: str | None = Header(default=None, alias="X-Team-ID"),
    db=Depends(get_db),
):
    try:
        request_payload = payload.model_dump()
        accepted = MetaAndromedaService.queue_observed_facebook_ad_import(request_payload)
        user_id = getattr(user, "google_id", None) or getattr(user, "id", None)

        # docs/24 Wave 2：web 角色優先把匯入 job 經 Redis stream 派給獨立 worker
        # process；未派工成功（非 web 角色，或 Redis 不可用）時退回本 process
        # 背景執行（Wave 1 的 to_thread 化已確保這不會卡住 event loop）。
        dispatched = MetaAndromedaService.dispatch_observed_facebook_ad_import(
            request_payload, user_id=user_id, team_id=x_team_id
        )
        if not dispatched:
            background_tasks.add_task(
                MetaAndromedaService.run_observed_facebook_ad_import_job,
                request_payload,
                user_id=user_id,
                team_id=x_team_id,
            )
        return accepted
    except MetaAndromedaValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get(
    "/evaluations/import/facebook-ads/{observed_creative_id}/status",
    response_model=FacebookAdObservedImportStatusResponse,
)
async def get_facebook_ad_observation_import_status(
    observed_creative_id: str,
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    _fb_ads_access: bool = Depends(require_fb_ads_module),
    _fb_ads_permission: bool = Depends(require_fb_ads_analytics_view),
    db=Depends(get_db),
):
    return MetaAndromedaService.get_observed_facebook_ad_import_status(db, observed_creative_id)


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
