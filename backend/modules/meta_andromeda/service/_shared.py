"""Shared dependencies for Meta Andromeda service mixins."""

import asyncio
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from mimetypes import guess_extension
from pathlib import Path
from urllib.parse import urlparse

import httpx
import logging

from core.config import settings
from core.scheduler import get_meta_andromeda_score_job_id, scheduler
from database import SessionLocal, User
from database.models.meta_andromeda import MetaAndromedaDeadLetter, MetaAndromedaObservedCreative, MetaAndromedaScoreEvent, MetaAndromedaWorkerEvent
from ..schemas import ObservedCreativeCandidate
from ..concurrency import DistributedSemaphore
from ..import_status_store import (
    clear_import_status_by_score_event_ids,
    get_import_status,
    set_import_status,
)
from ..importers.facebook_ads_importer import fetch_observed_creative_candidate
from ..model_registry import model_registry
from ..objective_routing import resolve_objective_group
from ..queue_host import queue_host_adapter
from ..repository import repository
from ..runtime import runtime_adapter
from ..storage import storage_adapter
from redis_cache import get_redis_client

logger = logging.getLogger(__name__)

_score_event_semaphore = DistributedSemaphore("ma_score_event", settings.META_ANDROMEDA_SCORE_MAX_CONCURRENCY)
_observation_import_semaphore = DistributedSemaphore(
    "ma_observation_import", settings.META_ANDROMEDA_OBSERVATION_MAX_CONCURRENCY
)


class MetaAndromedaValidationError(ValueError):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code



__all__ = [name for name in globals() if not name.startswith("__")]
