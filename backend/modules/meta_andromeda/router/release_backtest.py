"""Release backtest routes for Meta Andromeda."""

from __future__ import annotations

from . import _shared

router = _shared.APIRouter()


@router.get("/release/overview", response_model=_shared.ReleaseOverviewResponse)
async def release_overview(
    _user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_module),
    db=_shared.Depends(_shared.get_db),
):
    """Read-only release overview endpoint for the fifth integration slice."""
    return _shared.MetaAndromedaService.get_release_overview(db)


@router.post("/backtest/runs", response_model=_shared.BacktestRunResponse, status_code=_shared.status.HTTP_201_CREATED)
async def create_backtest_run(
    payload: _shared.BacktestRunCreateRequest,
    _user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_operate),
    db=_shared.Depends(_shared.get_db),
):
    """Create an isolated model backtest run. Backtest score events are marked
    with scoring_purpose=backtest and excluded from live review/monitoring/release metrics."""
    return _shared.MetaAndromedaService.create_backtest_run(
        db,
        provider_model=payload.provider_model,
        sample_limit=payload.sample_limit,
        note=payload.note,
    )


@router.get("/backtest/runs", response_model=_shared.BacktestRunListResponse)
async def list_backtest_runs(
    _user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_release),
    db=_shared.Depends(_shared.get_db),
    limit: int = _shared.Query(default=20, ge=1, le=100),
):
    return _shared.MetaAndromedaService.list_backtest_runs(db, limit=limit)


@router.get("/backtest/runs/{run_id}", response_model=_shared.BacktestRunResponse)
async def get_backtest_run(
    run_id: str,
    _user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_release),
    db=_shared.Depends(_shared.get_db),
):
    try:
        return _shared.MetaAndromedaService.get_backtest_run(db, run_id)
    except KeyError as exc:
        raise _shared.HTTPException(
            status_code=_shared.status.HTTP_404_NOT_FOUND,
            detail=f"Backtest run not found: {run_id}",
        ) from exc


@router.post("/release/candidates", response_model=_shared.ReleaseCandidateResponse, status_code=_shared.status.HTTP_201_CREATED)
async def create_release_candidate(
    payload: _shared.ReleaseCandidateCreateRequest,
    user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_release),
    db=_shared.Depends(_shared.get_db),
):
    """新增一筆候選版本，讓正式評分模型也能像回測模型一樣自由指定要試哪個
    model_version——過去唯一能建立 candidate 的地方是一次性種子資料，approve/
    rollback 因此被鎖死在種子時期固定的兩三筆版本。核准/回滾的稽核流程完全
    不變，這裡只是補上「新增候選」這個原本缺少的入口。"""
    from ..repository import ReleaseCandidateExistsError, repository as _repo
    try:
        return _repo.create_release_candidate(
            db,
            model_version=payload.model_version,
            provider=payload.provider,
            provider_model=payload.provider_model,
            scoring_profile=payload.scoring_profile,
            actor=getattr(user, "email", None) or "datavue_operator",
            note=payload.note,
        )
    except ReleaseCandidateExistsError as exc:
        raise _shared.HTTPException(
            status_code=_shared.status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post("/release/approve", response_model=_shared.ReleaseActionResponse)
async def approve_release(
    payload: _shared.ReleaseActionRequest,
    user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_release),
    db=_shared.Depends(_shared.get_db),
):
    try:
        return _shared.MetaAndromedaService.perform_release_action(
            db,
            action="approve",
            model_version=payload.model_version,
            actor=getattr(user, "email", None) or "datavue_operator",
            note=payload.note,
            force=payload.force,
        )
    except KeyError as exc:
        raise _shared.HTTPException(
            status_code=_shared.status.HTTP_404_NOT_FOUND,
            detail=f"Release candidate not found: {payload.model_version}",
        ) from exc
    except Exception as exc:
        from ..repository import ReleaseGateError
        if isinstance(exc, ReleaseGateError):
            raise _shared.HTTPException(
                status_code=exc.status_code,
                detail={"code": exc.code, "message": exc.message, "details": exc.details},
            ) from exc
        raise


@router.post("/release/reject", response_model=_shared.ReleaseActionResponse)
async def reject_release(
    payload: _shared.ReleaseActionRequest,
    user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_release),
    db=_shared.Depends(_shared.get_db),
):
    try:
        return _shared.MetaAndromedaService.perform_release_action(
            db,
            action="reject",
            model_version=payload.model_version,
            actor=getattr(user, "email", None) or "datavue_operator",
            note=payload.note,
        )
    except KeyError as exc:
        raise _shared.HTTPException(
            status_code=_shared.status.HTTP_404_NOT_FOUND,
            detail=f"Release candidate not found: {payload.model_version}",
        ) from exc


@router.post("/release/rollback", response_model=_shared.ReleaseActionResponse)
async def rollback_release(
    payload: _shared.ReleaseActionRequest,
    user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_release),
    db=_shared.Depends(_shared.get_db),
):
    return _shared.MetaAndromedaService.perform_release_action(
        db,
        action="rollback",
        model_version=payload.model_version,
        actor=getattr(user, "email", None) or "datavue_operator",
        note=payload.note,
    )


@router.post(
    "/release/{model_version}/refresh-metrics",
    response_model=_shared.ReleaseMetricsRefreshResponse,
)
async def refresh_release_metrics(
    model_version: str,
    _user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_release),
    db=_shared.Depends(_shared.get_db),
):
    """Compute real pairwise ranking accuracy / mean band error for this model_version
    from drift-matched history and write it onto any release record referencing it,
    clearing its is_demo_data flag once enough data exists."""
    return _shared.MetaAndromedaService.refresh_release_metrics(db, model_version)


@router.get(
    "/release/{model_version}/metric-pairs",
    response_model=_shared.ReleaseMetricPairsResponse,
)
async def list_release_metric_pairs(
    model_version: str,
    sort: str = _shared.Query(default="mismatch"),
    limit: int = _shared.Query(default=50, ge=1, le=500),
    _user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_release),
    db=_shared.Depends(_shared.get_db),
):
    """配對明細（docs/32 任務 1.1）：release 指標背後的逐筆「觀測素材 × AI 評分」
    對照，與 refresh-metrics 的 sample_count 同一份配對邏輯。預設 mismatch 排序
    讓「高分低效」浮最上面，供人工歸因抽樣。"""
    return _shared.MetaAndromedaService.list_release_metric_pairs(db, model_version, sort=sort, limit=limit)
