"""
Meta Andromeda Module - Service
"""

import asyncio
import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from mimetypes import guess_extension
from pathlib import Path
from urllib.parse import urlparse

import httpx
import logging

from core.config import settings
from core.scheduler import get_meta_andromeda_score_job_id, scheduler
from database import SessionLocal, User
from database.models.meta_andromeda import MetaAndromedaDeadLetter, MetaAndromedaScoreEvent, MetaAndromedaWorkerEvent
from .schemas import ObservedCreativeCandidate
from .concurrency import DistributedSemaphore
from .import_status_store import (
    clear_import_status_by_score_event_ids,
    get_import_status,
    set_import_status,
)
from .importers.facebook_ads_importer import fetch_observed_creative_candidate
from .model_registry import model_registry
from .objective_routing import resolve_objective_group
from .queue_host import queue_host_adapter
from .repository import repository
from .runtime import runtime_adapter
from .storage import storage_adapter
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


class MetaAndromedaService:
    """Service layer for the current DataVue integration slice."""

    @staticmethod
    def get_ping_payload() -> dict:
        return {
            "status": "ok",
            "module": "meta_andromeda",
            "message": "Meta Andromeda module is mounted",
        }

    @staticmethod
    def get_overview_payload() -> dict:
        return {
            "module": {
                "key": "meta_andromeda",
                "name": "Meta Andromeda",
                "status": "active",
                "phase": "phase_3_prompt_calibration",
            },
            "summary": {
                "integration_status": "in_progress",
                "current_slice": "db_backed_scoring_profiles_and_calibration_pipeline",
                "next_slice": "external_queue_host_and_shared_storage_rollout",
            },
            "capabilities": [
                {
                    "key": "creative_scoring",
                    "label": "Creative Scoring",
                    "status": "registry_backed",
                },
                {
                    "key": "review_queue",
                    "label": "Review Queue",
                    "status": "interactive",
                },
                {
                    "key": "monitoring",
                    "label": "Monitoring",
                    "status": "worker_observable",
                },
                {
                    "key": "release_console",
                    "label": "Release Console",
                    "status": "registry_aware",
                },
                {
                    "key": "calibration",
                    "label": "Drift Calibration",
                    "status": "active",
                },
                {
                    "key": "scoring_profiles",
                    "label": "Scoring Profiles",
                    "status": "db_backed_promotable",
                },
            ],
            "notes": [
                "Meta Andromeda is being integrated into DataVue incrementally.",
                "Overview, review queue, monitoring, and release paths are mounted in DataVue.",
                "Scoring runtime resolves provider and model metadata from the local Meta Andromeda registry.",
                "Queue host dispatch, worker audit, and dead-letter observability are persisted in DataVue DB.",
                "Scoring profiles are stored in DB and dynamically loaded at runtime; the promoted profile is used globally.",
                "Calibration pipeline auto-generates corrected profiles when ≥10 mismatch items are synced.",
                "Shared object storage and external worker deployment are still pending host alignment.",
            ],
        }

    @staticmethod
    def list_review_queue(
        db,
        status: str | None = None,
        has_observation: bool | None = None,
        roas_band: str | None = None,
        limit: int = 25,
        page: int = 1,
        search: str | None = None,
        source: str | None = None,
        scoring_engine: str | None = None,
    ) -> dict:
        return repository.list_review_queue(db, status=status, has_observation=has_observation, roas_band=roas_band, limit=limit, page=page, search=search, source=source, scoring_engine=scoring_engine)

    @staticmethod
    def get_review_queue_detail(db, score_event_id: str) -> dict:
        return repository.get_review_queue_detail(db, score_event_id)

    @staticmethod
    def delete_score_event(db, score_event_id: str) -> dict:
        return repository.delete_score_event(db, score_event_id)

    @staticmethod
    def batch_delete_score_events(db, score_event_ids: list[str]) -> dict:
        return repository.batch_delete_score_events(db, score_event_ids)

    @staticmethod
    def get_monitoring_summary(db) -> dict:
        summary = repository.get_monitoring_summary(db)
        summary.setdefault("worker_host", {})
        summary["worker_host"]["active_host"] = queue_host_adapter.get_active_host()
        summary["worker_host"]["host_strategy"] = "shared_queue_host_adapter"
        return summary

    @staticmethod
    def get_monitoring_timeline(db, score_event_id: str) -> dict:
        return repository.get_score_event_timeline(db, score_event_id)

    @staticmethod
    def trigger_drift_report(
        db,
        window_kind: str,
        triggered_by: str | None = None,
        note: str | None = None,
        since: str | None = None,
        until: str | None = None,
        account_id: str | None = None,
    ) -> dict:
        return repository.create_drift_report(
            db,
            window_kind=window_kind,
            triggered_by=triggered_by,
            note=note,
            since=since,
            until=until,
            account_id=account_id,
        )

    @staticmethod
    def get_runtime_health(db) -> dict:
        queue_host = queue_host_adapter.get_active_host()
        checks: dict = {
            "database": "ok",
            "queue_host": queue_host,
            "model_registry": "ok",
        }
        notes: list[str] = []
        status = "healthy"

        try:
            repository.list_review_queue(db, limit=1)
        except Exception as exc:
            checks["database"] = f"error: {exc}"
            status = "unhealthy"

        try:
            registry_entry = model_registry.get_entry()
            checks["model_registry"] = {
                "model_version": registry_entry.model_version,
                "provider": registry_entry.provider,
                "feature_manifest_id": registry_entry.feature_manifest_id,
                "source_of_truth": registry_entry.source_of_truth,
            }
        except Exception as exc:
            checks["model_registry"] = f"error: {exc}"
            status = "unhealthy"

        storage_backend = settings.META_ANDROMEDA_STORAGE_BACKEND
        storage_check: dict | str
        if storage_backend == "filesystem":
            storage_root = Path(settings.META_ANDROMEDA_STORAGE_ROOT)
            probe_dir = storage_root if storage_root.exists() else storage_root.parent
            writable = probe_dir.exists() and probe_dir.is_dir()
            storage_check = {
                "backend": "filesystem",
                "root": str(storage_root),
                "probe_dir": str(probe_dir),
                "writable_probe_present": writable,
            }
            if not writable:
                status = "degraded" if status == "healthy" else status
                notes.append("filesystem storage root is not present yet; upload path has not been validated on this host.")
        elif storage_backend == "s3_compatible":
            missing = [
                key
                for key, value in {
                    "bucket": settings.META_ANDROMEDA_STORAGE_S3_BUCKET,
                    "region": settings.META_ANDROMEDA_STORAGE_S3_REGION,
                    "access_key_id": settings.META_ANDROMEDA_STORAGE_S3_ACCESS_KEY_ID,
                    "secret_access_key": settings.META_ANDROMEDA_STORAGE_S3_SECRET_ACCESS_KEY,
                }.items()
                if not value
            ]
            try:
                storage_adapter._build_s3_client()
                client_ready = True
            except Exception as exc:
                client_ready = False
                notes.append(f"s3_compatible client init failed: {exc}")
            storage_check = {
                "backend": "s3_compatible",
                "bucket": settings.META_ANDROMEDA_STORAGE_S3_BUCKET,
                "region": settings.META_ANDROMEDA_STORAGE_S3_REGION,
                "endpoint_url": settings.META_ANDROMEDA_STORAGE_S3_ENDPOINT_URL,
                "key_prefix": settings.META_ANDROMEDA_STORAGE_KEY_PREFIX,
                "missing_required": missing,
                "client_ready": client_ready,
            }
            if missing or not client_ready:
                status = "degraded" if status == "healthy" else status
                notes.append("shared object storage is configured but not fully verified on this host.")
        else:
            storage_check = f"unsupported backend: {storage_backend}"
            status = "unhealthy"
        checks["storage"] = storage_check

        if queue_host in {"redis_stream", "database_queue"}:
            try:
                redis = get_redis_client()
                if redis:
                    redis.ping()
                    checks["redis_runtime"] = "ok"
                else:
                    checks["redis_runtime"] = "not_configured"
                    status = "degraded" if status == "healthy" else status
            except Exception as exc:
                checks["redis_runtime"] = f"error: {exc}"
                status = "degraded" if status == "healthy" else status

        if queue_host == "external_webhook":
            callback_auth_configured = bool(
                settings.META_ANDROMEDA_EXTERNAL_WORKER_SHARED_SECRET
                or settings.META_ANDROMEDA_EXTERNAL_WORKER_TOKEN
            )
            checks["external_worker"] = {
                "dispatch_endpoint": settings.META_ANDROMEDA_EXTERNAL_QUEUE_ENDPOINT,
                "callback_auth_configured": callback_auth_configured,
            }
            if not settings.META_ANDROMEDA_EXTERNAL_QUEUE_ENDPOINT or not callback_auth_configured:
                status = "degraded" if status == "healthy" else status
                notes.append("external worker mode requires both dispatch endpoint and callback auth to be configured.")

        if queue_host == "unavailable":
            status = "degraded" if status == "healthy" else status
            notes.append("queue host is unavailable on this host; scoring relies on another worker or environment-specific queue mode.")

        if not notes:
            notes.append("Meta Andromeda shared-runtime checks are configured for this host.")

        return {
            "status": status,
            "queue_host": queue_host,
            "checks": checks,
            "notes": notes,
        }

    @staticmethod
    def get_release_overview(db) -> dict:
        return repository.get_release_overview(db)

    @staticmethod
    def get_asset_by_uri(db, asset_uri: str):
        return repository.get_asset_by_uri(db, asset_uri)

    @staticmethod
    def upload_asset(
        db,
        file_bytes: bytes,
        asset_type: str,
        source_filename: str,
        uploaded_by: str | None = None,
        content_type: str | None = None,
    ) -> dict:
        # 自動壓縮圖片素材，避免過大導致 AI 服務超載或超時
        if asset_type == "image":
            file_bytes = MetaAndromedaService._compress_image(file_bytes, source_filename, content_type)

        MetaAndromedaService._validate_uploaded_asset(
            file_bytes=file_bytes,
            asset_type=asset_type,
            source_filename=source_filename,
            content_type=content_type,
        )
        asset_record = storage_adapter.store_asset(
            file_bytes=file_bytes,
            asset_type=asset_type,
            source_filename=source_filename,
            uploaded_by=uploaded_by,
            content_type=content_type,
        )
        return repository.create_uploaded_asset(db, asset_record=asset_record)

    @staticmethod
    def _compress_image(file_bytes: bytes, filename: str, content_type: str | None = None) -> bytes:
        import io
        from PIL import Image
        from pathlib import Path

        # 如果檔案本身就小於 400KB，直接保留原圖以保證最高精度與速度
        if len(file_bytes) < 400 * 1024:
            logger.info("[MetaAndromeda] Image size is %d bytes (<400KB), skipping compression.", len(file_bytes))
            return file_bytes

        try:
            img = Image.open(io.BytesIO(file_bytes))
            orig_format = img.format
            width, height = img.size
            
            fmt_lower = (orig_format or "").lower()
            if not fmt_lower:
                suffix = Path(filename).suffix.lower()
                if suffix in (".jpg", ".jpeg"):
                    fmt_lower = "jpeg"
                elif suffix == ".webp":
                    fmt_lower = "webp"
                else:
                    fmt_lower = "png"

            # 設定最長邊最大寬高為 1200 像素
            max_size = 1200
            if width > max_size or height > max_size:
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                
                logger.info(
                    "[MetaAndromeda] Resizing image from %dx%d to %dx%d (max_size=%d)",
                    width, height, new_width, new_height, max_size
                )
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            out_buf = io.BytesIO()
            save_kwargs = {}
            
            if fmt_lower in ("jpeg", "jpg"):
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                save_kwargs = {"quality": 85, "optimize": True}
                save_format = "JPEG"
            elif fmt_lower == "webp":
                save_kwargs = {"quality": 85, "method": 6}
                save_format = "WEBP"
            else:
                save_kwargs = {"optimize": True}
                save_format = "PNG"

            img.save(out_buf, format=save_format, **save_kwargs)
            compressed_bytes = out_buf.getvalue()
            
            logger.info(
                "[MetaAndromeda] Image compressed. Before: %d bytes, After: %d bytes (Ratio: %.1f%%)",
                len(file_bytes), len(compressed_bytes), (len(compressed_bytes) / len(file_bytes)) * 100
            )
            
            if len(compressed_bytes) >= len(file_bytes):
                logger.info("[MetaAndromeda] Compressed image is larger or equal, keeping original.")
                return file_bytes
                
            return compressed_bytes

        except Exception as e:
            logger.warning("[MetaAndromeda] Image compression failed: %s. Using original bytes.", e)
            return file_bytes

    @staticmethod
    def _validate_uploaded_asset(
        *,
        file_bytes: bytes,
        asset_type: str,
        source_filename: str,
        content_type: str | None,
    ) -> None:
        if not file_bytes:
            raise MetaAndromedaValidationError("upload_empty_file", status_code=400)
        if len(file_bytes) > settings.META_ANDROMEDA_UPLOAD_MAX_BYTES:
            raise MetaAndromedaValidationError("upload_file_too_large", status_code=413)

        allowed = {
            "image": {
                "mimes": {"image/png", "image/jpeg", "image/webp"},
                "exts": {".png", ".jpg", ".jpeg", ".webp"},
            },
            "video": {
                "mimes": {"video/mp4", "video/quicktime"},
                "exts": {".mp4", ".mov"},
            },
        }
        spec = allowed.get((asset_type or "").strip().lower())
        if spec is None:
            raise MetaAndromedaValidationError("unsupported_asset_type", status_code=415)

        content_type_normalized = (content_type or "").split(";")[0].strip().lower()
        ext = Path(source_filename or "").suffix.lower()
        if ext not in spec["exts"]:
            raise MetaAndromedaValidationError("upload_extension_not_allowed", status_code=415)
        if content_type_normalized not in spec["mimes"]:
            raise MetaAndromedaValidationError("upload_mime_not_allowed", status_code=415)

    @staticmethod
    def _is_allowed_media_host(hostname: str | None) -> bool:
        if not hostname:
            return False
        host = hostname.lower()
        for allowed in settings.META_ANDROMEDA_ALLOWED_MEDIA_HOSTS:
            normalized = allowed.lstrip(".")
            if host == normalized or host.endswith(f".{normalized}"):
                return True
        return False

    @staticmethod
    async def _fetch_observed_facebook_ad_candidate(
        *,
        payload: dict,
        user_id: str,
        team_id: str | None = None,
    ):
        return await fetch_observed_creative_candidate(
            account_id=payload["account_id"],
            ad_id=payload["ad_id"],
            user_id=user_id,
            observation_window_kind=payload["observation_window_kind"],
            market=payload["market"],
            placement_family=payload["placement_family"],
            primary_text=payload.get("primary_text"),
            headline=payload.get("headline"),
            cta=payload.get("cta"),
            team_id=team_id,
            since=payload.get("since"),
            until=payload.get("until"),
        )

    @staticmethod
    def build_observed_creative_id(ad_id: str, observation_window_kind: str) -> str:
        today = datetime.now(UTC).date()
        return f"ma_obs_{today.strftime('%Y%m%d')}_{ad_id[-6:]}_{observation_window_kind}"

    @staticmethod
    def _set_observation_import_status(observed_creative_id: str, **updates) -> dict:
        return set_import_status(observed_creative_id, **updates)

    @staticmethod
    def queue_observed_facebook_ad_import(payload: dict) -> dict:
        observed_creative_id = MetaAndromedaService.build_observed_creative_id(
            payload["ad_id"],
            payload["observation_window_kind"],
        )
        MetaAndromedaService._set_observation_import_status(
            observed_creative_id,
            observation_status="queued",
            observation_message="Observation import queued",
            asset_uri=None,
            score_event_id=None,
            score_status="pending_observation",
            runtime_job_id=None,
        )
        return {
            "observed_creative_id": observed_creative_id,
            "status": "accepted",
            "asset_uri": None,
            "score_event_id": None,
            "score_status": "pending_observation",
            "runtime_job_id": None,
            "source": {
                "platform": "facebook_ads",
                "account_id": payload["account_id"],
                "ad_id": payload["ad_id"],
            },
            "observation_window": {
                "kind": payload["observation_window_kind"],
                "start": payload.get("since") or "",
                "end": payload.get("until") or "",
            },
            "performance_snapshot": {},
        }

    @staticmethod
    async def _download_observed_asset_snapshot(
        *,
        media_url: str,
        ad_id: str,
        media_type: str,
    ) -> dict:
        parsed = urlparse(media_url)
        if parsed.scheme != "https":
            raise MetaAndromedaValidationError("observed_media_url_must_use_https", status_code=400)
        if not MetaAndromedaService._is_allowed_media_host(parsed.hostname):
            raise MetaAndromedaValidationError("observed_media_url_host_not_allowed", status_code=400)
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(media_url)
            response.raise_for_status()

        content_type = response.headers.get("content-type", "").split(";")[0].strip() or None
        if len(response.content) > settings.META_ANDROMEDA_OBSERVED_DOWNLOAD_MAX_BYTES:
            raise MetaAndromedaValidationError("observed_media_too_large", status_code=413)
        if media_type == "image" and content_type not in {"image/png", "image/jpeg", "image/webp"}:
            raise MetaAndromedaValidationError("observed_media_mime_not_allowed", status_code=415)
        if media_type == "video" and content_type not in {"video/mp4", "video/quicktime"}:
            raise MetaAndromedaValidationError("observed_media_mime_not_allowed", status_code=415)
        path_name = Path(parsed.path).name
        if path_name:
            source_filename = path_name
        else:
            extension = guess_extension(content_type or "") if content_type else None
            if not extension:
                extension = ".png" if media_type == "image" else ".mp4" if media_type == "video" else ".bin"
            source_filename = f"{ad_id}{extension}"

        asset_type = media_type if media_type in {"image", "video"} else "image"
        return {
            "file_bytes": response.content,
            "source_filename": source_filename,
            "content_type": content_type,
            "asset_type": asset_type,
        }

    @staticmethod
    async def import_observed_facebook_ad(
        db,
        payload: dict,
        *,
        user_id: str,
        team_id: str | None = None,
    ) -> dict:
        candidate = await MetaAndromedaService._fetch_observed_facebook_ad_candidate(
            payload=payload,
            user_id=user_id,
            team_id=team_id,
        )
        candidate = ObservedCreativeCandidate.model_validate(candidate)
        
        # 查詢 User 資料表，將外部 google_id 轉換為內部 User.id (UUID)，防止外鍵約束衝突
        db_user = db.query(User).filter(User.google_id == user_id).first()
        user_db_id = db_user.id if db_user else user_id

        observed_creative_id = MetaAndromedaService.build_observed_creative_id(
            candidate.ad_id,
            candidate.observation_window_kind,
        )
        stored_asset = None

        if candidate.media_url and candidate.media_type in {"image", "video"}:
            try:
                snapshot = await MetaAndromedaService._download_observed_asset_snapshot(
                    media_url=candidate.media_url,
                    ad_id=candidate.ad_id,
                    media_type=candidate.media_type,
                )
                asset_record = storage_adapter.store_asset(
                    file_bytes=snapshot["file_bytes"],
                    asset_type=snapshot["asset_type"],
                    source_filename=snapshot["source_filename"],
                    uploaded_by=user_db_id,
                    content_type=snapshot["content_type"],
                )
                stored_asset = repository.create_uploaded_asset(db, asset_record=asset_record)
            except MetaAndromedaValidationError:
                raise
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"[Observation Import] Failed to download or store asset from {candidate.media_url} for ad_id {candidate.ad_id}: {e}",
                    exc_info=True
                )

        observed_record = repository.create_observed_creative(
            db,
            observed_record={
                "id": observed_creative_id,
                "asset_id": stored_asset["asset_id"] if stored_asset else None,
                "asset_uri": stored_asset["asset_uri"] if stored_asset else None,
                "source_platform": candidate.source_platform,
                "source_account_id": candidate.source_account_id,
                "campaign_id": candidate.campaign_id,
                "adset_id": candidate.adset_id,
                "ad_id": candidate.ad_id,
                "ad_name": candidate.ad_name,
                "objective": candidate.objective,
                "placement_family": candidate.placement_family,
                "market": candidate.market,
                "primary_text": candidate.primary_text,
                "headline": candidate.headline,
                "cta": candidate.cta,
                "media_url": candidate.media_url,
                "media_type": candidate.media_type,
                "performance_snapshot": candidate.performance_snapshot,
                "observation_window_kind": candidate.observation_window_kind,
                "observation_window_start": candidate.observation_window_start,
                "observation_window_end": candidate.observation_window_end,
                "source_fetched_at": candidate.source_fetched_at,
                "lineage": {
                    "source_platform": candidate.source_platform,
                    "source_account_id": candidate.source_account_id,
                    "campaign_id": candidate.campaign_id,
                    "adset_id": candidate.adset_id,
                    "ad_id": candidate.ad_id,
                    "objective_group": resolve_objective_group(candidate.objective),
                },
            },
        )

        score_event_id = None
        score_status = "skipped_no_asset"
        runtime_job_id = None
        auto_score_payload = None

        if observed_record.get("asset_uri") and observed_record.get("asset_id") and observed_record.get("media_type") in {"image", "video"}:
            score_status = "queued_background"
            auto_score_payload = {
                "asset_uri": observed_record["asset_uri"],
                "asset_type": observed_record["media_type"],
                "asset_id": observed_record["asset_id"],
                "request_mode": "auto",
                "objective": observed_record.get("objective") or "purchase",
                "placement_family": observed_record.get("placement_family") or "all",
                "market": observed_record.get("market") or "TW",
                "primary_text": observed_record.get("primary_text"),
                "headline": observed_record.get("headline"),
                "cta": observed_record.get("cta"),
                "observed_creative_id": observed_record["observed_creative_id"],
            }

        return {
            "observed_creative_id": observed_record["observed_creative_id"],
            "status": "accepted",
            "asset_uri": observed_record["asset_uri"],
            "score_event_id": score_event_id,
            "score_status": score_status,
            "runtime_job_id": runtime_job_id,
            "source": {
                "platform": candidate.source_platform,
                "account_id": candidate.source_account_id,
                "ad_id": candidate.ad_id,
            },
            "observation_window": {
                "kind": candidate.observation_window_kind,
                "start": candidate.observation_window_start,
                "end": candidate.observation_window_end,
            },
            "performance_snapshot": candidate.performance_snapshot,
            "_auto_score_payload": auto_score_payload,
        }

    @staticmethod
    def create_score_event(db, payload: dict) -> dict:
        score_payload = runtime_adapter.build_score_submission(payload)
        if payload.get("request_context"):
            score_payload.setdefault("request_context", {}).update(payload["request_context"])
        return repository.create_score_event(db, score_payload)

    @staticmethod
    def create_and_enqueue_score_event_for_observation(auto_score_payload: dict | None) -> dict | None:
        if not auto_score_payload:
            return None

        from database.models.meta_andromeda import MetaAndromedaScoreEvent as _ScoreEvent
        from sqlalchemy.orm.attributes import flag_modified

        db = SessionLocal()
        observed_creative_id = auto_score_payload.get("observed_creative_id") or "unknown_observation"
        asset_uri = auto_score_payload.get("asset_uri")
        try:
            # 同一素材可能在多個觀測窗口（last_7d/last_30d/lifetime）各匯入一次；只要該素材已有
            # 「AI 模式、completed」的最新評分就重用，不必每個窗口都重新呼叫 AI 評一次分。
            # request_context.observed_creative_id 保留原本第一個連結的觀測（相容現有單值查詢），
            # 完整的多對一關聯改記在 lineage.linked_observation_ids（新增、不影響既有查詢）。
            existing = None
            if asset_uri:
                existing = (
                    db.query(_ScoreEvent)
                    .filter(
                        _ScoreEvent.asset_uri == asset_uri,
                        _ScoreEvent.status == "completed",
                    )
                    .order_by(_ScoreEvent.completed_at.desc())
                    .all()
                )
                existing = next(
                    (evt for evt in existing if (evt.lineage or {}).get("scoring_mode") == "ai"),
                    None,
                )

            if existing:
                rc = dict(existing.request_context or {})
                rc.setdefault("observed_creative_id", observed_creative_id)

                lineage = dict(existing.lineage or {})
                linked_ids = list(lineage.get("linked_observation_ids") or [])
                if observed_creative_id not in linked_ids:
                    linked_ids.append(observed_creative_id)
                lineage["linked_observation_ids"] = linked_ids
                existing.lineage = lineage
                existing.request_context = rc
                flag_modified(existing, "request_context")
                flag_modified(existing, "lineage")
                db.commit()
                MetaAndromedaService._set_observation_import_status(
                    observed_creative_id,
                    score_event_id=existing.id,
                    score_status="completed",
                    runtime_job_id=existing.runtime_job_id,
                )
                logger.info(
                    "[Observation Import] Linked existing score event %s → observed_creative_id %s (skipped re-score, now linked to %d observations)",
                    existing.id,
                    observed_creative_id,
                    len(linked_ids),
                )
                return {"score_event_id": existing.id, "status": "completed"}

            # 無既有預評，正常建立並排入評分
            payload = {
                key: value
                for key, value in auto_score_payload.items()
                if key != "observed_creative_id"
            }
            payload.setdefault("request_context", {})
            payload["request_context"]["observed_creative_id"] = observed_creative_id
            payload["request_context"]["origin"] = "analytics"
            created_score = MetaAndromedaService.create_score_event(db, payload)
            score_event_id = created_score["score_event_id"]
            runtime_job_id = get_meta_andromeda_score_job_id(score_event_id)
            MetaAndromedaService.assign_score_runtime_job(db, score_event_id, runtime_job_id)
            queued_score = MetaAndromedaService.enqueue_score_event(
                db,
                score_event_id=score_event_id,
                runtime_job_id=runtime_job_id,
            )
            logger.info(
                "[Observation Import] Background auto score-event queued for observed_creative_id %s: %s",
                observed_creative_id,
                score_event_id,
            )
            MetaAndromedaService._set_observation_import_status(
                observed_creative_id,
                score_event_id=score_event_id,
                score_status=queued_score.get("status") or "queued",
                runtime_job_id=queued_score.get("runtime_job_id") or runtime_job_id,
            )
            return queued_score
        except Exception as exc:
            logger.warning(
                "[Observation Import] Background auto score-event creation failed for observed_creative_id %s: %s",
                observed_creative_id,
                exc,
                exc_info=True,
            )
            MetaAndromedaService._set_observation_import_status(
                observed_creative_id,
                score_status="failed",
                observation_message=str(exc),
            )
            return None
        finally:
            db.close()

    @staticmethod
    async def run_observed_facebook_ad_import_job(payload: dict, *, user_id: str, team_id: str | None = None) -> None:
        observed_creative_id = MetaAndromedaService.build_observed_creative_id(
            payload["ad_id"],
            payload["observation_window_kind"],
        )
        MetaAndromedaService._set_observation_import_status(
            observed_creative_id,
            observation_status="queued",
            observation_message="Observation import queued, waiting for concurrency slot",
            score_status="pending_observation",
        )

        async with _observation_import_semaphore.acquire():
            MetaAndromedaService._set_observation_import_status(
                observed_creative_id,
                observation_status="processing",
                observation_message="Observation import processing",
                score_status="pending_observation",
            )
            db = SessionLocal()
            try:
                response = await MetaAndromedaService.import_observed_facebook_ad(
                    db,
                    payload,
                    user_id=user_id,
                    team_id=team_id,
                )
                auto_score_payload = response.pop("_auto_score_payload", None)
                MetaAndromedaService._set_observation_import_status(
                    observed_creative_id,
                    observation_status="completed",
                    observation_message="Observation imported",
                    asset_uri=response.get("asset_uri"),
                    score_status=response.get("score_status"),
                    runtime_job_id=response.get("runtime_job_id"),
                    score_event_id=response.get("score_event_id"),
                )
                if auto_score_payload:
                    MetaAndromedaService.create_and_enqueue_score_event_for_observation(auto_score_payload)
                elif response.get("score_status") == "skipped_no_asset":
                    MetaAndromedaService._set_observation_import_status(
                        observed_creative_id,
                        score_status="skipped_no_asset",
                    )
            except Exception as exc:
                logger.warning(
                    "[Observation Import] Background observation import failed for %s: %s",
                    observed_creative_id,
                    exc,
                    exc_info=True,
                )
                MetaAndromedaService._set_observation_import_status(
                    observed_creative_id,
                    observation_status="failed",
                    observation_message=str(exc),
                    score_status="blocked_by_observation_failure",
                )
            finally:
                db.close()

    @staticmethod
    def get_observed_facebook_ad_import_status(db, observed_creative_id: str) -> dict:
        observed = repository.get_observed_creative(db, observed_creative_id)
        memory_status = get_import_status(observed_creative_id)
        if observed is None:
            if memory_status:
                return {
                    "observed_creative_id": observed_creative_id,
                    "observation_status": memory_status.get("observation_status", "queued"),
                    "observation_message": memory_status.get("observation_message"),
                    "asset_uri": memory_status.get("asset_uri"),
                    "score_event_id": memory_status.get("score_event_id"),
                    "score_status": memory_status.get("score_status"),
                    "runtime_job_id": memory_status.get("runtime_job_id"),
                    "updated_at": memory_status.get("updated_at"),
                }
            return {
                "observed_creative_id": observed_creative_id,
                "observation_status": "not_found",
                "observation_message": "Observation import not found",
                "asset_uri": None,
                "score_event_id": None,
                "score_status": None,
                "runtime_job_id": None,
                "updated_at": None,
            }

        latest_score = repository.get_latest_score_event_for_observation(db, observed_creative_id)
        memory_score_status = memory_status.get("score_status")
        if latest_score:
            score_status = latest_score.get("status")
            score_event_id = latest_score.get("score_event_id")
            runtime_job_id = latest_score.get("runtime_job_id")
        else:
            score_status = memory_score_status or ("pending_score_event" if observed.get("asset_uri") else "skipped_no_asset")
            score_event_id = memory_status.get("score_event_id")
            runtime_job_id = memory_status.get("runtime_job_id")

        return {
            "observed_creative_id": observed_creative_id,
            "observation_status": "completed",
            "observation_message": memory_status.get("observation_message") or "Observation imported",
            "asset_uri": observed.get("asset_uri"),
            "score_event_id": score_event_id,
            "score_status": score_status,
            "runtime_job_id": runtime_job_id,
            "updated_at": memory_status.get("updated_at") or observed.get("created_at"),
        }

    @staticmethod
    def assign_score_runtime_job(db, score_event_id: str, runtime_job_id: str) -> dict:
        return repository.assign_runtime_job(db, score_event_id, runtime_job_id)

    @staticmethod
    def enqueue_score_event(
        db,
        score_event_id: str,
        runtime_job_id: str,
        delay_seconds: float = 1.0,
        event_type: str = "dispatch_requested",
    ) -> dict:
        current = repository.get_review_queue_detail(db, score_event_id)
        dispatch = queue_host_adapter.enqueue_score_event(score_event_id, delay_seconds=delay_seconds)
        repository.log_worker_event(
            db,
            score_event_id=score_event_id,
            event_type=event_type,
            queue_host=dispatch["queue_host"],
            runtime_job_id=runtime_job_id,
            status="queued" if dispatch["accepted"] else "dispatch_failed",
            attempt_count=current["attempt_count"],
            message=dispatch["dispatch_mode"],
            event_payload=dispatch,
        )
        if dispatch["accepted"]:
            return repository.get_review_queue_detail(db, score_event_id)
        return repository.get_review_queue_detail(db, score_event_id)

    @staticmethod
    def _build_external_worker_signature(raw_body: bytes) -> str | None:
        secret = settings.META_ANDROMEDA_EXTERNAL_WORKER_SHARED_SECRET
        if not secret:
            return None
        return hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    @staticmethod
    def verify_external_worker_callback(
        raw_body: bytes,
        signature: str | None = None,
        worker_token: str | None = None,
    ) -> None:
        expected_signature = MetaAndromedaService._build_external_worker_signature(raw_body)
        expected_token = settings.META_ANDROMEDA_EXTERNAL_WORKER_TOKEN

        if expected_signature:
            if not signature or not hmac.compare_digest(signature, expected_signature):
                raise PermissionError("invalid_worker_signature")
            return

        if expected_token:
            if not worker_token or not hmac.compare_digest(worker_token, expected_token):
                raise PermissionError("invalid_worker_token")
            return

        raise PermissionError("external_worker_callback_auth_not_configured")

    @staticmethod
    def _ensure_external_processing_state(db, score_event_id: str) -> dict:
        current = repository.get_review_queue_detail(db, score_event_id)
        if current["status"] == "queued":
            claimed = repository.mark_score_processing(db, score_event_id)
            return claimed or repository.get_review_queue_detail(db, score_event_id)
        return current

    @staticmethod
    def _external_worker_event_name(event_type: str) -> str:
        return f"external_worker_{event_type}"

    @staticmethod
    def _is_duplicate_external_callback(
        db,
        score_event_id: str,
        *,
        event_type: str,
        runtime_job_id: str | None,
        receipt_id: str | None,
    ) -> bool:
        return (
            repository.find_worker_event(
                db,
                score_event_id=score_event_id,
                event_type=MetaAndromedaService._external_worker_event_name(event_type),
                runtime_job_id=runtime_job_id,
                receipt_id=receipt_id,
            )
            is not None
        )

    @staticmethod
    def _normalize_external_result_payload(result_payload: dict) -> dict:
        normalized = dict(result_payload)
        model_version = normalized.get("model_version")
        registry_entry = model_registry.get_entry(model_version=model_version)
        normalized.setdefault("status", "completed")
        normalized.setdefault("prediction_mode", "diagnostic_plus_roas")
        normalized.setdefault("feature_manifest_id", registry_entry.feature_manifest_id)
        normalized.setdefault("error_message", None)
        normalized.setdefault("diagnostic_breakdown", {})
        normalized.setdefault("roas_prediction", {})
        normalized.setdefault("risk_tags", [])
        normalized.setdefault("top_positive_drivers", [])
        normalized.setdefault("top_negative_drivers", [])
        normalized.setdefault("explanations", {})
        lineage = dict(normalized.get("lineage") or {})
        lineage.setdefault("feature_manifest_id", registry_entry.feature_manifest_id)
        lineage.setdefault("registry_model_version", registry_entry.model_version)
        lineage.setdefault("registry_provider", registry_entry.provider)
        lineage.setdefault("provider_model", registry_entry.provider_model)
        lineage.setdefault("registry_profile", registry_entry.scoring_profile)
        lineage.setdefault("registry_source", registry_entry.source_of_truth)
        lineage.setdefault("scoring_mode", "external_worker")
        normalized["lineage"] = lineage
        normalized["model_version"] = registry_entry.model_version
        return normalized

    @staticmethod
    def handle_external_worker_callback(db, score_event_id: str, payload: dict) -> dict:
        current = repository.get_review_queue_detail(db, score_event_id)
        queue_host = payload.get("queue_host") or "external_webhook"
        runtime_job_id = payload.get("runtime_job_id") or current.get("runtime_job_id")
        if runtime_job_id and current.get("runtime_job_id") != runtime_job_id:
            if current.get("status") in {"completed", "failed"}:
                return current
            current = repository.assign_runtime_job(db, score_event_id, runtime_job_id)

        event_type = payload["event_type"]
        attempt_count = payload.get("attempt_count") or current.get("attempt_count", 0)
        worker_payload = {
            "worker_id": payload.get("worker_id"),
            "receipt_id": payload.get("receipt_id"),
            "retryable": payload.get("retryable", False),
            "retry_delay_seconds": payload.get("retry_delay_seconds"),
            "callback_metadata": payload.get("callback_metadata") or {},
        }
        if MetaAndromedaService._is_duplicate_external_callback(
            db,
            score_event_id,
            event_type=event_type,
            runtime_job_id=runtime_job_id,
            receipt_id=payload.get("receipt_id"),
        ):
            return repository.get_review_queue_detail(db, score_event_id)

        if event_type == "accepted":
            repository.log_worker_event(
                db,
                score_event_id=score_event_id,
                event_type="external_worker_accepted",
                queue_host=queue_host,
                runtime_job_id=runtime_job_id,
                status=current["status"],
                attempt_count=attempt_count,
                message="external worker accepted dispatch",
                event_payload=worker_payload,
            )
            return repository.get_review_queue_detail(db, score_event_id)

        if event_type == "processing":
            if current["status"] in {"completed", "failed"}:
                return current
            processing = MetaAndromedaService._ensure_external_processing_state(db, score_event_id)
            repository.log_worker_event(
                db,
                score_event_id=score_event_id,
                event_type="external_worker_processing",
                queue_host=queue_host,
                runtime_job_id=runtime_job_id,
                status="processing",
                attempt_count=processing["attempt_count"],
                message="external worker started processing",
                event_payload=worker_payload,
            )
            return processing

        if event_type == "completed":
            if not payload.get("result_payload"):
                raise ValueError("completed callback requires result_payload")
            if current["status"] in {"completed", "failed"}:
                return current
            MetaAndromedaService._ensure_external_processing_state(db, score_event_id)
            normalized_result = MetaAndromedaService._normalize_external_result_payload(payload["result_payload"])
            completed = repository.mark_score_completed(db, score_event_id, normalized_result)
            repository.log_worker_event(
                db,
                score_event_id=score_event_id,
                event_type="external_worker_completed",
                queue_host=queue_host,
                runtime_job_id=runtime_job_id,
                status="completed",
                attempt_count=completed["attempt_count"],
                message="external worker completed scoring",
                event_payload={**worker_payload, "model_version": completed["model_version"]},
            )
            return completed

        if event_type == "failed":
            if current["status"] in {"completed", "failed"}:
                return current
            processing = MetaAndromedaService._ensure_external_processing_state(db, score_event_id)
            error_message = payload.get("error_message") or "external_worker_failed"
            if payload.get("retryable") and processing["attempt_count"] < settings.META_ANDROMEDA_SCORE_MAX_ATTEMPTS:
                queued = repository.requeue_score_event(db, score_event_id, error_message)
                repository.log_worker_event(
                    db,
                    score_event_id=score_event_id,
                    event_type="external_worker_retry_scheduled",
                    queue_host=queue_host,
                    runtime_job_id=runtime_job_id,
                    status="queued",
                    attempt_count=queued["attempt_count"],
                    message=error_message,
                    event_payload=worker_payload,
                )
                return MetaAndromedaService.enqueue_score_event(
                    db,
                    score_event_id=score_event_id,
                    runtime_job_id=queued["runtime_job_id"],
                    delay_seconds=payload.get("retry_delay_seconds")
                    or settings.META_ANDROMEDA_SCORE_RETRY_DELAY_SECONDS,
                    event_type="external_worker_retry_dispatch_requested",
                )

            failed = repository.mark_score_failed(db, score_event_id, error_message)
            repository.log_worker_event(
                db,
                score_event_id=score_event_id,
                event_type="external_worker_failed",
                queue_host=queue_host,
                runtime_job_id=runtime_job_id,
                status="failed",
                attempt_count=failed["attempt_count"],
                message=error_message,
                event_payload=worker_payload,
            )
            repository.create_dead_letter(
                db,
                score_event_id=score_event_id,
                queue_host=queue_host,
                runtime_job_id=runtime_job_id,
                failure_stage="external_worker",
                attempt_count=failed["attempt_count"],
                final_error_message=error_message,
                dead_letter_payload=worker_payload,
            )
            repository.log_worker_event(
                db,
                score_event_id=score_event_id,
                event_type="external_worker_dead_lettered",
                queue_host=queue_host,
                runtime_job_id=runtime_job_id,
                status="failed",
                attempt_count=failed["attempt_count"],
                message=error_message,
                event_payload={"failure_stage": "external_worker", **worker_payload},
            )
            return failed

        raise ValueError(f"Unsupported external worker event_type: {event_type}")

    @staticmethod
    async def process_score_event(score_event_id: str, queue_host: str = "unknown") -> dict:
        async with _score_event_semaphore.acquire():
            db = SessionLocal()
            try:
                current = repository.mark_score_processing(db, score_event_id)
                if current is None:
                    return repository.get_review_queue_detail(db, score_event_id)
                repository.log_worker_event(
                    db,
                    score_event_id=score_event_id,
                    event_type="processing_started",
                    queue_host=queue_host,
                    runtime_job_id=current["runtime_job_id"],
                    status="processing",
                    attempt_count=current["attempt_count"],
                    message="worker started",
                    event_payload={
                        "queue_host": queue_host,
                        "max_concurrency": settings.META_ANDROMEDA_SCORE_MAX_CONCURRENCY,
                    },
                )
            finally:
                db.close()

            try:
                result = await asyncio.wait_for(
                    runtime_adapter.generate_score_result(current),
                    timeout=settings.META_ANDROMEDA_SCORE_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError as exc:
                raise TimeoutError(
                    f"score runtime timed out after {settings.META_ANDROMEDA_SCORE_TIMEOUT_SECONDS:.2f}s"
                ) from exc
            except Exception as exc:
                error_message = str(exc)
                db = SessionLocal()
                try:
                    latest = repository.get_review_queue_detail(db, score_event_id)
                    if latest["attempt_count"] < settings.META_ANDROMEDA_SCORE_MAX_ATTEMPTS:
                        queued = repository.requeue_score_event(db, score_event_id, error_message)
                        repository.log_worker_event(
                            db,
                            score_event_id=score_event_id,
                            event_type="retry_scheduled",
                            queue_host=queue_host,
                            runtime_job_id=queued["runtime_job_id"],
                            status="queued",
                            attempt_count=queued["attempt_count"],
                            message=error_message,
                            event_payload={"retry_delay_seconds": settings.META_ANDROMEDA_SCORE_RETRY_DELAY_SECONDS},
                        )
                        self_dispatch = MetaAndromedaService.enqueue_score_event(
                            db,
                            score_event_id=score_event_id,
                            runtime_job_id=queued["runtime_job_id"],
                            delay_seconds=settings.META_ANDROMEDA_SCORE_RETRY_DELAY_SECONDS,
                            event_type="retry_dispatch_requested",
                        )
                        return self_dispatch

                    failed = repository.mark_score_failed(db, score_event_id, error_message)
                    repository.log_worker_event(
                        db,
                        score_event_id=score_event_id,
                        event_type="failed",
                        queue_host=queue_host,
                        runtime_job_id=failed["runtime_job_id"],
                        status="failed",
                        attempt_count=failed["attempt_count"],
                        message=error_message,
                        event_payload={"queue_host": queue_host},
                    )
                    repository.create_dead_letter(
                        db,
                        score_event_id=score_event_id,
                        queue_host=queue_host,
                        runtime_job_id=failed["runtime_job_id"],
                        failure_stage="runtime",
                        attempt_count=failed["attempt_count"],
                        final_error_message=error_message,
                        dead_letter_payload={
                            "queue_host": queue_host,
                            "attempt_count": failed["attempt_count"],
                            "runtime_job_id": failed["runtime_job_id"],
                        },
                    )
                    repository.log_worker_event(
                        db,
                        score_event_id=score_event_id,
                        event_type="dead_lettered",
                        queue_host=queue_host,
                        runtime_job_id=failed["runtime_job_id"],
                        status="failed",
                        attempt_count=failed["attempt_count"],
                        message=error_message,
                        event_payload={"failure_stage": "runtime"},
                    )
                    return failed
                finally:
                    db.close()

            db = SessionLocal()
            try:
                completed = repository.mark_score_completed(db, score_event_id, result)
                repository.log_worker_event(
                    db,
                    score_event_id=score_event_id,
                    event_type="completed",
                    queue_host=queue_host,
                    runtime_job_id=completed["runtime_job_id"],
                    status="completed",
                    attempt_count=completed["attempt_count"],
                    message="worker completed",
                    event_payload={"queue_host": queue_host, "model_version": completed["model_version"]},
                )
                return completed
            finally:
                db.close()

    @staticmethod
    def _clear_observation_import_status_entries(score_event_ids: set[str]) -> int:
        return clear_import_status_by_score_event_ids(score_event_ids)

    @staticmethod
    def cleanup_stale_score_events(
        db,
        *,
        older_than_minutes: int | None = None,
        include_queued: bool = True,
        purge_worker_events: bool = False,
        purge_dead_letters: bool = False,
        limit: int = 500,
        reason: str = "maintenance_cleanup",
    ) -> dict:
        older_than = older_than_minutes or settings.META_ANDROMEDA_STALE_PROCESSING_MINUTES
        cutoff = datetime.now(UTC) - timedelta(minutes=older_than)
        statuses = ["processing"]
        if include_queued:
            statuses.append("queued")

        rows = (
            db.query(MetaAndromedaScoreEvent)
            .filter(
                MetaAndromedaScoreEvent.status.in_(statuses),
                MetaAndromedaScoreEvent.updated_at < cutoff,
            )
            .order_by(MetaAndromedaScoreEvent.updated_at.asc())
            .limit(limit)
            .all()
        )

        now = datetime.now(UTC)
        cleaned_ids: list[str] = []
        scheduler_job_ids: list[str] = []
        deleted_worker_events = 0
        deleted_dead_letters = 0

        for row in rows:
            cleaned_ids.append(row.id)
            scheduler_job_ids.append(row.runtime_job_id or get_meta_andromeda_score_job_id(row.id))

            if purge_worker_events:
                deleted_worker_events += (
                    db.query(MetaAndromedaWorkerEvent)
                    .filter(MetaAndromedaWorkerEvent.score_event_id == row.id)
                    .delete(synchronize_session=False)
                )
            if purge_dead_letters:
                deleted_dead_letters += (
                    db.query(MetaAndromedaDeadLetter)
                    .filter(MetaAndromedaDeadLetter.score_event_id == row.id)
                    .delete(synchronize_session=False)
                )

            previous_status = row.status
            row.status = "failed"
            row.failed_at = now
            row.updated_at = now
            row.error_message = f"{reason}:{previous_status}:stale_after_{older_than}m"
            db.add(row)

            if not purge_worker_events:
                db.add(
                    MetaAndromedaWorkerEvent(
                        score_event_id=row.id,
                        event_type="maintenance_cancelled",
                        queue_host="maintenance",
                        runtime_job_id=row.runtime_job_id,
                        status="failed",
                        attempt_count=row.attempt_count,
                        message=row.error_message,
                        event_payload={
                            "reason": reason,
                            "previous_status": previous_status,
                            "older_than_minutes": older_than,
                        },
                    )
                )

        db.commit()

        removed_scheduler_jobs = 0
        for job_id in scheduler_job_ids:
            try:
                if scheduler.get_job(job_id):
                    scheduler.remove_job(job_id)
                    removed_scheduler_jobs += 1
            except Exception:
                continue

        cleared_memory_statuses = MetaAndromedaService._clear_observation_import_status_entries(set(cleaned_ids))

        return {
            "cleaned_total": len(cleaned_ids),
            "cleaned_score_event_ids": cleaned_ids,
            "include_statuses": statuses,
            "older_than_minutes": older_than,
            "cutoff_timestamp": cutoff.isoformat(),
            "removed_scheduler_jobs": removed_scheduler_jobs,
            "cleared_memory_statuses": cleared_memory_statuses,
            "deleted_worker_events": deleted_worker_events,
            "deleted_dead_letters": deleted_dead_letters,
            "notes": [
                "Only stale queued/processing score events were terminated.",
                "Completed score history and observed creatives were preserved.",
                "Use include_queued=false for automatic reconciliation of stuck processing items only.",
            ],
        }

    @staticmethod
    def get_score_detail(db, score_event_id: str) -> dict:
        return repository.get_review_queue_detail(db, score_event_id)

    @staticmethod
    def list_feedback(db, score_event_id: str) -> dict:
        return repository.list_feedback(db, score_event_id)

    @staticmethod
    def submit_feedback(
        db,
        score_event_id: str,
        reviewer_id: str,
        decision: str,
        reason_codes: list[str] | None = None,
        comment: str | None = None,
    ) -> dict:
        return repository.submit_feedback(
            db,
            score_event_id=score_event_id,
            reviewer_id=reviewer_id,
            decision=decision,
            reason_codes=reason_codes,
            comment=comment,
        )

    @staticmethod
    def list_feedback_calibration_candidates(db) -> dict:
        candidates = repository.list_feedback_calibration_candidates(db)
        return {"candidates": candidates, "total": len(candidates)}

    @staticmethod
    def analyze_feedback_reason_codes(db) -> dict:
        return repository.analyze_feedback_reason_codes(db)

    @staticmethod
    def perform_release_action(
        db,
        action: str,
        model_version: str,
        actor: str,
        note: str | None = None,
    ) -> dict:
        return repository.perform_release_action(
            db,
            action=action,
            model_version=model_version,
            actor=actor,
            note=note,
        )

    @staticmethod
    def refresh_release_metrics(db, model_version: str) -> dict:
        return repository.refresh_release_metrics(db, model_version)

    @staticmethod
    def list_scoring_profiles(db) -> dict:
        return {"profiles": repository.list_scoring_profiles(db), "total": len(repository.list_scoring_profiles(db))}

    @staticmethod
    def promote_scoring_profile(db, profile_name: str, force: bool = False) -> dict:
        return repository.promote_scoring_profile(db, profile_name, force=force)

    @staticmethod
    async def run_holdout_backtest(db, profile_name: str) -> dict:
        return await repository.run_holdout_backtest(db, profile_name)

    @staticmethod
    def sync_calibration_dataset(
        db,
        window_kind: str,
        excluded_observed_ids: list[str],
    ) -> dict:
        result = repository.sync_calibration_dataset(
            db,
            window_kind=window_kind,
            excluded_observed_ids=excluded_observed_ids,
        )
        # 觸發門檻看的是「有偏差的項目數」（error_item_count），而非 synced_count——
        # synced_count 現在也包含 error=0 的正確配對對照組，用它當門檻會被稀釋
        error_item_count = result.get("error_item_count", 0)
        dataset_id = result.get("dataset_id")
        if error_item_count >= 10 and dataset_id:
            try:
                from core.scheduler import add_meta_andromeda_calibration_job
                base_profile = repository.get_active_base_profile_name(db)
                add_meta_andromeda_calibration_job(dataset_id, base_profile)
            except Exception as exc:
                import logging as _logging
                _logging.getLogger(__name__).warning(
                    "[MetaAndromeda] Failed to enqueue calibration job for dataset %s: %s",
                    dataset_id,
                    exc,
                )
        return result
