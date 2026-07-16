"""Review queue routes for Meta Andromeda."""

from __future__ import annotations

from ._shared import *

router = APIRouter()


@router.get("/review-queue", response_model=ReviewQueueListResponse)
async def review_queue(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
    has_observation: bool | None = Query(default=None),
    roas_band: str | None = Query(default=None),
    search: str | None = Query(default=None),
    source: str | None = Query(default=None),
    scoring_engine: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
):
    """Evaluation record list endpoint — returns scored assets with observation match status."""
    return MetaAndromedaService.list_review_queue(
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


@router.post("/review-queue/batch-delete", response_model=ScoreEventBatchDeleteResponse)
async def batch_delete_review_queue_items(
    body: ScoreEventBatchDeleteRequest,
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_operate),
    db=Depends(get_db),
):
    """Batch delete score events by ID list (max 200 per request)."""
    return MetaAndromedaService.batch_delete_score_events(db, body.score_event_ids)


@router.delete("/review-queue/{score_event_id}", response_model=ScoreEventDeleteResponse)
async def delete_review_queue_item(
    score_event_id: str,
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_operate),
    db=Depends(get_db),
):
    """Delete a single score event and its associated feedback/worker events."""
    try:
        return MetaAndromedaService.delete_score_event(db, score_event_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review queue item not found: {score_event_id}",
        ) from exc
