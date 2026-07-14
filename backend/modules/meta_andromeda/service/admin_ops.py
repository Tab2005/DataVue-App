"""AdminOpsServiceMixin for Meta Andromeda service."""

from ._shared import *  # noqa: F403


class AdminOpsServiceMixin:

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
        internal_worker_auth_configured = bool(
            settings.META_ANDROMEDA_INTERNAL_WORKER_SHARED_SECRET
            or settings.META_ANDROMEDA_INTERNAL_WORKER_TOKEN
        )

        if storage_backend == "filesystem":
            if settings.SERVICE_ROLE == "web":
                storage_check = {
                    "backend": "filesystem",
                    "mode": "worker_remote",
                    "local_root_required": False,
                    "internal_worker_base_url": settings.META_ANDROMEDA_INTERNAL_WORKER_BASE_URL,
                }
                checks["internal_asset_worker"] = {
                    "required": True,
                    "base_url": settings.META_ANDROMEDA_INTERNAL_WORKER_BASE_URL,
                    "auth_configured": internal_worker_auth_configured,
                    "service_role": settings.SERVICE_ROLE,
                }
                if not settings.META_ANDROMEDA_INTERNAL_WORKER_BASE_URL or not internal_worker_auth_configured:
                    status = "degraded" if status == "healthy" else status
                    notes.append("filesystem storage on web role requires internal worker base URL and auth to be configured.")
            else:
                storage_root = Path(settings.META_ANDROMEDA_STORAGE_ROOT)
                probe_dir = storage_root if storage_root.exists() else storage_root.parent
                writable = probe_dir.exists() and probe_dir.is_dir()
                storage_check = {
                    "backend": "filesystem",
                    "root": str(storage_root),
                    "probe_dir": str(probe_dir),
                    "writable_probe_present": writable,
                    "local_root_required": True,
                    "mode": "local_holder" if settings.SERVICE_ROLE == "all" else "worker_holder",
                }
                checks["internal_asset_worker"] = {
                    "required": settings.SERVICE_ROLE == "worker",
                    "base_url": settings.META_ANDROMEDA_INTERNAL_WORKER_BASE_URL,
                    "auth_configured": internal_worker_auth_configured,
                    "service_role": settings.SERVICE_ROLE,
                }
                if not writable:
                    status = "degraded" if status == "healthy" else status
                    notes.append("filesystem storage root is not present yet; upload path has not been validated on this host.")
                if settings.SERVICE_ROLE == "worker" and not internal_worker_auth_configured:
                    status = "degraded" if status == "healthy" else status
                    notes.append("worker role serving filesystem assets requires internal worker auth to be configured.")
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
        force: bool = False,
    ) -> dict:
        return repository.perform_release_action(
            db,
            action=action,
            model_version=model_version,
            actor=actor,
            note=note,
            force=force,
        )


    @staticmethod
    def create_release_candidate(
        db,
        *,
        model_version: str,
        provider: str,
        provider_model: str,
        scoring_profile: str | None,
        actor: str,
        note: str | None = None,
    ) -> dict:
        return repository.create_release_candidate(
            db,
            model_version=model_version,
            provider=provider,
            provider_model=provider_model,
            scoring_profile=scoring_profile,
            actor=actor,
            note=note,
        )



    @staticmethod
    def create_backtest_run(
        db,
        *,
        provider_model: str,
        sample_limit: int | None = None,
        note: str | None = None,
    ) -> dict:
        from fastapi import HTTPException, status
        from ..model_catalog import validate_candidate_model

        validation = validate_candidate_model(provider_model)
        if not validation.get("ok"):
            issues = validation.get("issues") or ["Candidate model failed validation."]
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "Candidate model is not usable for backtest.", "validation": validation, "issues": issues},
            )
        run = repository.create_backtest_run(
            db,
            provider_model=provider_model,
            sample_limit=sample_limit,
            note=note,
        )
        try:
            from core.scheduler import add_meta_andromeda_backtest_run_job
            add_meta_andromeda_backtest_run_job(run["run_id"])
        except Exception as exc:
            logger.warning("[MetaAndromeda] Failed to enqueue backtest run %s: %s", run["run_id"], exc)
        return run


    @staticmethod
    def list_backtest_runs(db, limit: int = 20) -> dict:
        return repository.list_backtest_runs(db, limit=limit)


    @staticmethod
    def get_backtest_run(db, run_id: str) -> dict:
        return repository.get_backtest_run(db, run_id)


    @staticmethod
    def _build_backtest_score_payload(observed: MetaAndromedaObservedCreative, run: dict) -> dict:
        snapshot = observed.performance_snapshot or {}
        return {
            "asset_uri": observed.asset_uri,
            "asset_type": observed.media_type or "image",
            "asset_id": observed.asset_id,
            "request_mode": "analytics_backtest",
            "objective": observed.objective or "unknown",
            "placement_family": observed.placement_family or "unknown",
            "market": observed.market or "unknown",
            "headline": snapshot.get("headline") or snapshot.get("ad_name") or observed.ad_name or "",
            "primary_text": snapshot.get("primary_text") or snapshot.get("body") or "",
            "cta": snapshot.get("cta") or snapshot.get("call_to_action") or "",
            "request_context": {
                "origin": "backtest",
                "is_backtest": True,
                "scoring_purpose": "backtest",
                "backtest_run_id": run["run_id"],
                "backtest_provider_model": run["provider_model"],
                "observed_creative_id": observed.id,
            },
        }


    @staticmethod
    async def run_backtest_run(run_id: str) -> dict:
        db = SessionLocal()
        try:
            run = repository.get_backtest_run(db, run_id)
            if run["status"] not in ("queued", "running"):
                return run

            query = (
                db.query(MetaAndromedaObservedCreative)
                .filter(MetaAndromedaObservedCreative.asset_uri.isnot(None))
                .order_by(MetaAndromedaObservedCreative.imported_at.desc())
            )
            observed_rows = [
                row for row in query.all()
                if (row.media_type or "image") in ("image", "video")
                and float((row.performance_snapshot or {}).get("spend", 0) or 0) > 0
            ]
            if run.get("sample_limit"):
                observed_rows = observed_rows[: int(run["sample_limit"])]

            now = datetime.now(UTC)
            repository.update_backtest_run(
                db,
                run_id,
                status="running",
                total_count=len(observed_rows),
                started_at=now,
                error_message=None,
            )
            success_count = 0
            failed_count = 0
            processed_count = 0
            sleep_seconds = float(getattr(settings, "META_ANDROMEDA_BACKTEST_INTERVAL_SECONDS", 2) or 2)

            for observed in observed_rows:
                created = None
                try:
                    existing = [
                        row for row in db.query(MetaAndromedaScoreEvent).all()
                        if row.status == "completed"
                        and (row.lineage or {}).get("scoring_purpose") == "backtest"
                        and (row.lineage or {}).get("backtest_run_id") == run_id
                        and (row.request_context or {}).get("observed_creative_id") == observed.id
                    ]
                    if existing:
                        success_count += 1
                        continue

                    payload = MetaAndromedaService._build_backtest_score_payload(observed, run)
                    score_payload = runtime_adapter.build_score_submission(payload)
                    score_payload["request_context"] = payload["request_context"]
                    created = repository.create_score_event(db, score_payload)
                    repository.mark_score_processing(db, created["score_event_id"])
                    current = repository.get_review_queue_detail(db, created["score_event_id"])
                    result_payload = await asyncio.to_thread(runtime_adapter.generate_score_result, current)
                    lineage = dict(result_payload.get("lineage") or {})
                    lineage.update({
                        "scoring_purpose": "backtest",
                        "backtest_run_id": run_id,
                        "backtest_provider_model": run["provider_model"],
                    })
                    result_payload["lineage"] = lineage
                    repository.mark_score_completed(db, created["score_event_id"], result_payload)
                    success_count += 1
                except Exception as exc:
                    failed_count += 1
                    if created:
                        repository.mark_score_failed(db, created["score_event_id"], str(exc))
                    logger.warning("[MetaAndromeda] Backtest run %s failed item %s: %s", run_id, getattr(observed, "id", None), exc)
                finally:
                    processed_count += 1
                    repository.update_backtest_run(
                        db,
                        run_id,
                        processed_count=processed_count,
                        success_count=success_count,
                        failed_count=failed_count,
                    )
                    if sleep_seconds > 0:
                        await asyncio.sleep(sleep_seconds)

            return repository.complete_backtest_run_metrics(db, run_id)
        except Exception as exc:
            try:
                repository.update_backtest_run(
                    db,
                    run_id,
                    status="failed",
                    error_message=str(exc),
                    completed_at=datetime.now(UTC),
                )
            except Exception:
                logger.exception("[MetaAndromeda] Failed to mark backtest run failed: %s", run_id)
            raise
        finally:
            db.close()


    @staticmethod
    def refresh_release_metrics(db, model_version: str) -> dict:
        return repository.refresh_release_metrics(db, model_version)


    @staticmethod
    def list_release_metric_pairs(db, model_version: str, *, sort: str = "mismatch", limit: int = 50) -> dict:
        return repository.list_release_metric_pairs(db, model_version, sort=sort, limit=limit)


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
