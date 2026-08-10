"""Review queue routes for Meta Andromeda."""

from __future__ import annotations

from . import _shared

router = _shared.APIRouter()


@router.get("/review-queue", response_model=_shared.ReviewQueueListResponse)
async def review_queue(
    _user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_module),
    db=_shared.Depends(_shared.get_db),
    status_filter: str | None = _shared.Query(default=None, alias="status"),
    has_observation: bool | None = _shared.Query(default=None),
    roas_band: str | None = _shared.Query(default=None),
    search: str | None = _shared.Query(default=None),
    source: str | None = _shared.Query(default=None),
    scoring_engine: str | None = _shared.Query(default=None),
    page: int = _shared.Query(default=1, ge=1),
    page_size: int = _shared.Query(default=25, ge=1, le=100),
):
    """Evaluation record list endpoint — returns scored assets with observation match status."""
    return _shared.MetaAndromedaService.list_review_queue(
        db,
        status=status_filter,
        has_observation=has_observation,
        roas_band=roas_band,
        limit=page_size,
        page=page,
        search=search or None,
        source=source or None,
        scoring_engine=scoring_engine or None,
    )


@router.get("/review-queue/{score_event_id}", response_model=_shared.ReviewQueueDetailResponse)
async def review_queue_detail(
    score_event_id: str,
    _user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_module),
    db=_shared.Depends(_shared.get_db),
):
    """Read-only review queue detail endpoint for the third integration slice."""
    try:
        return _shared.MetaAndromedaService.get_review_queue_detail(db, score_event_id)
    except KeyError as exc:
        raise _shared.HTTPException(
            status_code=_shared.status.HTTP_404_NOT_FOUND,
            detail=f"Review queue item not found: {score_event_id}",
        ) from exc


@router.post("/review-queue/batch-delete", response_model=_shared.ScoreEventBatchDeleteResponse)
async def batch_delete_review_queue_items(
    body: _shared.ScoreEventBatchDeleteRequest,
    _user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_operate),
    db=_shared.Depends(_shared.get_db),
):
    """Batch delete score events by ID list (max 200 per request)."""
    return _shared.MetaAndromedaService.batch_delete_score_events(db, body.score_event_ids)


@router.delete("/review-queue/{score_event_id}", response_model=_shared.ScoreEventDeleteResponse)
async def delete_review_queue_item(
    score_event_id: str,
    _user=_shared.Depends(_shared.get_current_meta_andromeda_user),
    _access: bool = _shared.Depends(_shared.require_meta_andromeda_operate),
    db=_shared.Depends(_shared.get_db),
):
    """Delete a single score event and its associated feedback/worker events."""
    try:
        return _shared.MetaAndromedaService.delete_score_event(db, score_event_id)
    except KeyError as exc:
        raise _shared.HTTPException(
            status_code=_shared.status.HTTP_404_NOT_FOUND,
            detail=f"Review queue item not found: {score_event_id}",
        ) from exc
