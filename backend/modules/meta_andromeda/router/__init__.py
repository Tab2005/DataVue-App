"""Meta Andromeda API router facade."""

from __future__ import annotations

from fastapi import APIRouter

from . import core, monitoring, observation_import, release_backtest, review_queue, scoring_assets
from ._shared import asyncio, proxy_asset_preview_response, proxy_asset_upload_response

router = APIRouter()
router.include_router(core.router)
router.include_router(review_queue.router)
router.include_router(monitoring.router)
router.include_router(observation_import.router)
router.include_router(scoring_assets.router)
router.include_router(release_backtest.router)

__all__ = [
    "asyncio",
    "proxy_asset_preview_response",
    "proxy_asset_upload_response",
    "router",
]
