"""Monitoring routes for Meta Andromeda."""

from __future__ import annotations

from ._shared import *

router = APIRouter()


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


@router.get("/monitoring/observed-accounts", response_model=ObservedAccountListResponse)
async def list_observed_accounts(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    from ..repository import repository as _repo
    accounts = _repo.list_observed_accounts(db)
    return {"accounts": accounts, "total": len(accounts)}


@router.get("/monitoring/drift-trend", response_model=DriftTrendResponse)
async def monitoring_drift_trend(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    account_id: str | None = Query(default=None),
):
    from ..repository import repository as _repo
    entries = _repo.get_drift_trend(db, limit=limit, account_id=account_id)
    return {"entries": entries, "total": len(entries)}


@router.get("/monitoring/scoring-profiles", response_model=ScoringProfileListResponse)
async def list_scoring_profiles(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    from ..repository import repository as _repo
    profiles = _repo.list_scoring_profiles(db)
    return {"profiles": profiles, "total": len(profiles)}


@router.post(
    "/monitoring/scoring-profiles/{profile_name}/backtest",
    response_model=ScoringProfileBacktestResponse,
)
async def backtest_scoring_profile(
    profile_name: str,
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_operate),
    db=Depends(get_db),
):
    """Re-score this profile's holdout set and record the result on the profile
    (bias_summary.holdout_backtest), gating whether /promote will accept it."""
    return await MetaAndromedaService.run_holdout_backtest(db, profile_name)


@router.post(
    "/monitoring/scoring-profiles/{profile_name}/promote",
    response_model=ScoringProfilePromoteResponse,
)
async def promote_scoring_profile(
    profile_name: str,
    force: bool = Query(False, description="Bypass the holdout backtest gate (not recommended)"),
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_operate),
    db=Depends(get_db),
):
    from ..repository import PromotionGateError, repository as _repo
    try:
        return _repo.promote_scoring_profile(db, profile_name, force=force)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PromotionGateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": exc.code, "message": exc.message},
        ) from exc


@router.get("/monitoring/model-registry", response_model=ModelRegistryListResponse)
async def list_model_registry(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    """List all model registry entries (interactive/production + backtest reference).
    Scoring/interactive model selection is changed via the release approve/rollback
    workflow only — this endpoint is read-only for that channel."""
    from ..repository import repository as _repo
    entries = _repo.list_model_registry_entries(db)
    return {"entries": entries}


@router.get("/monitoring/model-registry/effective", response_model=EffectiveScoringStatusResponse)
async def get_effective_scoring_status(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    """目前實際生效的互動評分設定 vs. 資料庫 registry 標記的 production 列。

    背景：`META_ANDROMEDA_SCORING_PROVIDER` / `_MODEL` / `_MODEL_VERSION` 這幾個
    env override 完全不寫資料庫、只在記憶體即時生效——只看版本總覽/監控總覽
    畫面（讀 DB 表）的人會誤以為「改了環境變數但畫面沒變，是不是沒生效」。
    此端點回傳兩邊實際解析出的值供前端標示是否一致，而不是要求使用者自己
    比對畫面上的模型名稱與部署環境變數。"""
    from ..repository import repository as _repo
    return _repo.get_effective_scoring_status(db)


@router.get("/monitoring/model-registry/validate-candidate", response_model=ModelCandidateValidationResponse)
async def validate_candidate_model(
    model_id: str = Query(..., min_length=1),
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
):
    """換模型（不管是要改版本總覽的候選，還是要設 META_ANDROMEDA_SCORING_MODEL
    env var 覆寫）前先查：這個 model id 在 OpenRouter 是否真的存在、支不支援評分
    需要的圖片輸入、實際 context/輸出上限多大（2026-07-10 事故後新增，見 docs）。
    純查詢外部公開 API，不寫資料庫、不需要 operate 權限。"""
    from ..model_catalog import validate_candidate_model as _validate

    return await asyncio.to_thread(_validate, model_id)


@router.put("/monitoring/model-registry/backtest-model", response_model=ModelRegistryEntryResponse)
async def update_backtest_model(
    payload: BacktestModelUpdateRequest,
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_operate),
    db=Depends(get_db),
):
    """Set which model evaluate_profile_on_holdout() re-scores holdout items with
    (docs/20 P2-3). Independent of the interactive/production model — changing this
    never affects live scoring, only future backtest runs."""
    from ..repository import repository as _repo
    from ..model_registry import invalidate_registry_cache

    result = _repo.set_backtest_reference_model(db, payload.provider, payload.provider_model)
    invalidate_registry_cache()
    return result


@router.post("/maintenance/cleanup-stale-score-events", response_model=MaintenanceCleanupResponse)
async def cleanup_stale_score_events(
    payload: MaintenanceCleanupRequest,
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_operate),
    db=Depends(get_db),
):
    return MetaAndromedaService.cleanup_stale_score_events(
        db,
        older_than_minutes=payload.older_than_minutes,
        include_queued=payload.include_queued,
        purge_worker_events=payload.purge_worker_events,
        purge_dead_letters=payload.purge_dead_letters,
        limit=payload.limit,
    )


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
        account_id=payload.account_id,
    )


@router.get("/monitoring/feedback/calibration-candidates")
async def list_feedback_calibration_candidates(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    """Score events whose human review (approve/reject) diverged from the AI's
    own score direction — candidates an operator can manually fold into the
    next prompt calibration round."""
    return MetaAndromedaService.list_feedback_calibration_candidates(db)


@router.get("/monitoring/feedback/reason-code-analysis")
async def analyze_feedback_reason_codes(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    """For each feedback reason_code, how often the reviewer's implied judgment
    (reject/revise = weak, approve = strong) agreed with the later-observed
    market band — validates whether a given reason_code is a trustworthy signal."""
    return MetaAndromedaService.analyze_feedback_reason_codes(db)
