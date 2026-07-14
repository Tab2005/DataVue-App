"""Scheduler meta andromeda jobs helpers."""

from ._shared import *  # noqa: F403



async def process_meta_andromeda_score_event(score_event_id: str, queue_host: str = "apscheduler"):
    """Process a queued Meta Andromeda score event."""
    from modules.meta_andromeda.service import MetaAndromedaService

    await MetaAndromedaService.process_score_event(score_event_id, queue_host=queue_host)



async def process_meta_andromeda_observation_import(
    payload: dict, user_id: str, team_id: str | None = None
) -> None:
    """Process a queued Meta Andromeda observation-import job (docs/24 Wave 2).

    入口由 `add_meta_andromeda_observation_import_job()` 註冊，該 job 本身由
    Redis stream 上收到 `kind=observation_import` 訊息時派發（見
    modules.meta_andromeda.queue_host._schedule_observation_import_message）。
    """
    from modules.meta_andromeda.service import MetaAndromedaService

    await MetaAndromedaService.run_observed_facebook_ad_import_job(
        payload, user_id=user_id, team_id=team_id
    )




async def process_meta_andromeda_backtest_run(run_id: str) -> None:
    """Process a queued Meta Andromeda backtest run (docs/32 Wave 2)."""
    from modules.meta_andromeda.service import MetaAndromedaService

    await MetaAndromedaService.run_backtest_run(run_id)



def get_meta_andromeda_backtest_job_id(run_id: str) -> str:
    return f"{META_ANDROMEDA_BACKTEST_JOB_PREFIX}_{run_id}"



def add_meta_andromeda_backtest_run_job(run_id: str, delay_seconds: float = 1):
    if not is_scheduler_enabled() or not scheduler.running:
        logger.info("⏰ [MetaAndromeda] Scheduler unavailable. Skipping backtest job registration for %s.", run_id)
        return None
    run_at = datetime.now(_LOCAL_TIMEZONE) + timedelta(seconds=delay_seconds)
    job_id = get_meta_andromeda_backtest_job_id(run_id)
    job = scheduler.add_job(
        process_meta_andromeda_backtest_run,
        trigger="date",
        run_date=run_at,
        args=[run_id],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=DEFAULT_MISFIRE_GRACE_TIME,
        coalesce=True,
        max_instances=1,
    )
    logger.info("⏰ [MetaAndromeda] Backtest run job added: %s", job_id)
    return job



async def sweep_meta_andromeda_queue() -> None:
    """Sweep queued Meta Andromeda records for database-backed queue hosting."""
    from database.models.meta_andromeda import MetaAndromedaScoreEvent
    from modules.meta_andromeda.service import MetaAndromedaService

    db = SessionLocal()
    try:
        cleanup_summary = MetaAndromedaService.cleanup_stale_score_events(
            db,
            older_than_minutes=settings.META_ANDROMEDA_STALE_PROCESSING_MINUTES,
            include_queued=False,
            purge_worker_events=False,
            purge_dead_letters=False,
            limit=200,
            reason="automatic_stale_processing_reconcile",
        )
        if cleanup_summary.get("cleaned_total"):
            logger.warning(
                "⏰ [MetaAndromeda] Reconciled %s stale processing score event(s) before queue sweep.",
                cleanup_summary["cleaned_total"],
            )

        queued_score_events = (
            db.query(MetaAndromedaScoreEvent)
            .filter(MetaAndromedaScoreEvent.status == "queued")
            .order_by(MetaAndromedaScoreEvent.created_at.asc())
            .limit(50)
            .all()
        )
        for score_event in queued_score_events:
            job_id = get_meta_andromeda_score_job_id(score_event.id)
            if scheduler.get_job(job_id):
                continue
            add_meta_andromeda_score_job(
                score_event.id,
                delay_seconds=0,
                queue_host="database_queue",
            )
        if queued_score_events:
            logger.info(
                "⏰ [MetaAndromeda] Sweeper inspected %s queued score events.",
                len(queued_score_events),
            )
    finally:
        db.close()



async def consume_meta_andromeda_redis_stream() -> None:
    """Consume broker-style Redis stream entries and ack them after scheduling."""
    from modules.meta_andromeda.queue_host import queue_host_adapter

    summary = queue_host_adapter.consume_redis_stream_batch()
    if summary.get("consumed_count"):
        logger.info(
            "⏰ [MetaAndromeda] Redis stream consumer handled %s message(s).",
            summary["consumed_count"],
        )



async def reclaim_meta_andromeda_redis_stream_pending() -> None:
    """Reclaim stale Redis-stream pending entries and reschedule them."""
    from modules.meta_andromeda.queue_host import queue_host_adapter

    summary = queue_host_adapter.reclaim_redis_stream_pending()
    if summary.get("claimed_count"):
        logger.info(
            "⏰ [MetaAndromeda] Redis stream reclaim handled %s stale message(s).",
            summary["claimed_count"],
        )



def add_meta_andromeda_score_job(score_event_id: str, delay_seconds: float = 1, queue_host: str = "apscheduler"):
    """Enqueue an immediate Meta Andromeda score job on the shared scheduler."""
    if not is_scheduler_enabled() or not scheduler.running:
        logger.info(
            "⏰ [MetaAndromeda] Scheduler unavailable. Skipping score job registration for %s.",
            score_event_id,
        )
        return None
    run_at = datetime.now(_LOCAL_TIMEZONE) + timedelta(seconds=delay_seconds)
    job_id = get_meta_andromeda_score_job_id(score_event_id)
    job = scheduler.add_job(
        process_meta_andromeda_score_event,
        trigger="date",
        run_date=run_at,
        args=[score_event_id, queue_host],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=DEFAULT_MISFIRE_GRACE_TIME,
        coalesce=True,
        max_instances=1,
    )
    logger.info("⏰ [MetaAndromeda] Score job added: %s for %s (delay=%ss)", job_id, score_event_id, delay_seconds)
    return job



def add_meta_andromeda_observation_import_job(
    payload: dict, *, user_id: str, team_id: str | None = None, delay_seconds: float = 0
):
    """Enqueue an immediate Meta Andromeda observation-import job on the shared
    scheduler (docs/24 Wave 2；worker process 消費 Redis stream 時呼叫)。

    與 `add_meta_andromeda_score_job` 不同，觀測匯入沒有預先建立的 DB row 可
    當 job id 去重鍵，所以 job id 加上短亂數尾碼，允許同一 ad_id/window 短時間
    內的並發匯入各自成一個 job（不會被 `replace_existing` 互相蓋掉）。
    """
    if not is_scheduler_enabled() or not scheduler.running:
        logger.info(
            "⏰ [MetaAndromeda] Scheduler unavailable. Skipping observation import job registration for ad_id=%s.",
            payload.get("ad_id"),
        )
        return None

    from uuid import uuid4

    from modules.meta_andromeda.service import MetaAndromedaService

    observed_creative_id = MetaAndromedaService.build_observed_creative_id(
        payload["ad_id"], payload["observation_window_kind"]
    )
    run_at = datetime.now(_LOCAL_TIMEZONE) + timedelta(seconds=delay_seconds)
    job_id = f"ma_obs_import_{observed_creative_id}_{uuid4().hex[:8]}"
    job = scheduler.add_job(
        process_meta_andromeda_observation_import,
        trigger="date",
        run_date=run_at,
        args=[payload, user_id, team_id],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=DEFAULT_MISFIRE_GRACE_TIME,
        coalesce=True,
        max_instances=1,
    )
    logger.info(
        "⏰ [MetaAndromeda] Observation import job added: %s for %s (delay=%ss)",
        job_id,
        observed_creative_id,
        delay_seconds,
    )
    return job


async def run_meta_andromeda_calibration_pipeline(dataset_id: str, base_profile_name: str) -> None:
    """Run the prompt calibration pipeline for a completed calibration dataset."""
    from modules.meta_andromeda.calibration_pipeline import generate_calibrated_profile
    from database import SessionLocal
    db = SessionLocal()
    try:
        new_profile = generate_calibrated_profile(db, dataset_id, base_profile_name)
        if new_profile:
            logger.info(
                "⏰ [MetaAndromeda] Calibration pipeline completed. New profile: %s",
                new_profile,
            )
        else:
            logger.info(
                "⏰ [MetaAndromeda] Calibration pipeline skipped for dataset %s (insufficient samples).",
                dataset_id,
            )
    except Exception as exc:
        logger.error(
            "⏰ [MetaAndromeda] Calibration pipeline failed for dataset %s: %s",
            dataset_id,
            exc,
        )
    finally:
        db.close()



def add_meta_andromeda_calibration_job(dataset_id: str, base_profile_name: str):
    """Enqueue a one-off prompt calibration job for the given calibration dataset."""
    if not is_scheduler_enabled() or not scheduler.running:
        logger.info(
            "⏰ [MetaAndromeda] Scheduler unavailable. Skipping calibration job for dataset %s.",
            dataset_id,
        )
        return None
    run_at = datetime.now(_LOCAL_TIMEZONE) + timedelta(seconds=5)
    job_id = f"ma_cal_{dataset_id}"
    job = scheduler.add_job(
        run_meta_andromeda_calibration_pipeline,
        trigger="date",
        run_date=run_at,
        args=[dataset_id, base_profile_name],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=DEFAULT_MISFIRE_GRACE_TIME,
        coalesce=True,
        max_instances=1,
    )
    logger.info(
        "⏰ [MetaAndromeda] Calibration job enqueued: %s for dataset %s (base=%s).",
        job_id,
        dataset_id,
        base_profile_name,
    )
    return job



def add_meta_andromeda_queue_sweeper_job():
    """Register periodic queue sweep for database-backed queue host."""
    job = scheduler.add_job(
        sweep_meta_andromeda_queue,
        trigger="interval",
        seconds=settings.META_ANDROMEDA_QUEUE_SWEEP_INTERVAL_SECONDS,
        id=META_ANDROMEDA_QUEUE_SWEEP_JOB_ID,
        replace_existing=True,
        misfire_grace_time=DEFAULT_MISFIRE_GRACE_TIME,
        coalesce=True,
        max_instances=1,
    )
    logger.info(
        "⏰ [MetaAndromeda] Queue sweeper registered (interval=%ss).",
        settings.META_ANDROMEDA_QUEUE_SWEEP_INTERVAL_SECONDS,
    )
    return job



def add_meta_andromeda_redis_stream_consumer_job():
    """Register periodic Redis-stream consumer for worker-style queue hosting."""
    job = scheduler.add_job(
        consume_meta_andromeda_redis_stream,
        trigger="interval",
        seconds=settings.META_ANDROMEDA_QUEUE_SWEEP_INTERVAL_SECONDS,
        id=META_ANDROMEDA_REDIS_STREAM_CONSUMER_JOB_ID,
        replace_existing=True,
        misfire_grace_time=DEFAULT_MISFIRE_GRACE_TIME,
        coalesce=True,
        max_instances=1,
    )
    logger.info(
        "⏰ [MetaAndromeda] Redis stream consumer registered (interval=%ss).",
        settings.META_ANDROMEDA_QUEUE_SWEEP_INTERVAL_SECONDS,
    )
    return job



def add_meta_andromeda_redis_stream_reclaim_job():
    """Register periodic reclaim pass for stale Redis-stream pending entries."""
    job = scheduler.add_job(
        reclaim_meta_andromeda_redis_stream_pending,
        trigger="interval",
        seconds=settings.META_ANDROMEDA_QUEUE_SWEEP_INTERVAL_SECONDS,
        id=META_ANDROMEDA_REDIS_STREAM_RECLAIM_JOB_ID,
        replace_existing=True,
        misfire_grace_time=DEFAULT_MISFIRE_GRACE_TIME,
        coalesce=True,
        max_instances=1,
    )
    logger.info(
        "⏰ [MetaAndromeda] Redis stream reclaim registered (interval=%ss, idle=%sms).",
        settings.META_ANDROMEDA_QUEUE_SWEEP_INTERVAL_SECONDS,
        settings.META_ANDROMEDA_REDIS_STREAM_RECLAIM_IDLE_MS,
    )
    return job



async def refresh_meta_andromeda_release_metrics() -> None:
    """Daily refresh for current production release metrics (docs/32 Wave 3)."""
    from modules.meta_andromeda.service import MetaAndromedaService

    db = SessionLocal()
    try:
        overview = MetaAndromedaService.get_release_overview(db)
        model_version = (overview.get("current_production") or {}).get("model_version")
        if not model_version:
            logger.info("⏰ [MetaAndromeda] Release metrics refresh skipped: no current production model.")
            return

        result = MetaAndromedaService.refresh_release_metrics(db, model_version)
        status = result.get("status")
        if status == "computed":
            logger.info(
                "⏰ [MetaAndromeda] Release metrics refreshed for %s (sample_count=%s, accuracy=%s, mae=%s).",
                model_version,
                result.get("sample_count"),
                result.get("pairwise_ranking_accuracy"),
                result.get("mean_band_error"),
            )
        elif status == "insufficient_data":
            logger.info(
                "⏰ [MetaAndromeda] Release metrics refresh found insufficient data for %s (sample_count=%s).",
                model_version,
                result.get("sample_count", 0),
            )
        else:
            logger.info(
                "⏰ [MetaAndromeda] Release metrics refresh finished for %s (status=%s).",
                model_version,
                status,
            )
    except Exception as exc:
        logger.warning("⏰ [MetaAndromeda] Release metrics refresh failed: %s", exc, exc_info=True)
    finally:
        db.close()



def add_meta_andromeda_release_metrics_refresh_job():
    """Register daily refresh for current production release metrics (UTC 02:00)."""
    job = scheduler.add_job(
        refresh_meta_andromeda_release_metrics,
        trigger=CronTrigger(hour=2, minute=0, timezone="UTC"),
        id=META_ANDROMEDA_RELEASE_METRICS_REFRESH_JOB_ID,
        replace_existing=True,
        misfire_grace_time=DEFAULT_MISFIRE_GRACE_TIME,
        coalesce=True,
        max_instances=1,
    )
    logger.info("⏰ [MetaAndromeda] Release metrics refresh job registered (02:00 UTC daily).")
    return job


async def run_meta_andromeda_weekly_closed_loop() -> None:
    """Per docs/20 P2-6: for every account with observed creatives, weekly
    auto-run drift report -> (if any account unhealthy) calibration dataset
    sync -> calibration pipeline (already auto-triggered by sync when
    error_item_count >= 10, see service.sync_calibration_dataset). The
    resulting profile still needs a human to hit promote — this job doesn't
    change any live scoring behavior on its own, it just removes "someone has
    to remember to click the button" from the cadence.
    """
    from modules.meta_andromeda.repository import repository

    db = SessionLocal()
    try:
        accounts = repository.list_observed_accounts(db)
        logger.info("⏰ [MetaAndromeda] Weekly closed-loop run starting for %d account(s).", len(accounts))

        any_unhealthy = False
        for account in accounts:
            account_id = account.get("account_id")
            if not account_id:
                continue
            try:
                report = repository.create_drift_report(
                    db,
                    window_kind="last_7d",
                    triggered_by="weekly_auto_scheduler",
                    account_id=account_id,
                )
                drift_status = report.get("drift_status")
                logger.info(
                    "⏰ [MetaAndromeda] Weekly drift report for account %s: status=%s",
                    account_id, drift_status,
                )
                if drift_status in ("warning", "drifted"):
                    any_unhealthy = True
            except Exception as exc:
                logger.warning(
                    "⏰ [MetaAndromeda] Weekly drift report failed for account %s: %s", account_id, exc
                )

        if not any_unhealthy:
            logger.info("⏰ [MetaAndromeda] Weekly closed-loop: all accounts healthy, skipping calibration sync.")
            return

        try:
            # sync_calibration_dataset 目前不支援 account 篩選（見 docs/20 已知限制），
            # 全帳戶都不健康時每週跑一次全域同步即可，不必每個帳戶各跑一次
            sync_result = repository.sync_calibration_dataset(
                db, window_kind="last_7d", excluded_observed_ids=[]
            )
            error_item_count = sync_result.get("error_item_count", 0)
            dataset_id = sync_result.get("dataset_id")
            logger.info(
                "⏰ [MetaAndromeda] Weekly calibration sync: %d error items in dataset %s",
                error_item_count, dataset_id,
            )
            if error_item_count >= 10 and dataset_id:
                base_profile = repository.get_active_base_profile_name(db)
                add_meta_andromeda_calibration_job(dataset_id, base_profile)
        except Exception as exc:
            logger.warning("⏰ [MetaAndromeda] Weekly calibration sync failed: %s", exc)
    finally:
        db.close()



def add_meta_andromeda_weekly_closed_loop_job():
    """Register the weekly per-account drift -> calibration closed-loop job (P2-6)."""
    if not settings.META_ANDROMEDA_WEEKLY_LOOP_ENABLED:
        logger.info("⏰ [MetaAndromeda] Weekly closed-loop disabled via META_ANDROMEDA_WEEKLY_LOOP_ENABLED=false.")
        return None
    job = scheduler.add_job(
        run_meta_andromeda_weekly_closed_loop,
        trigger=CronTrigger(
            day_of_week=settings.META_ANDROMEDA_WEEKLY_LOOP_DAY_OF_WEEK,
            hour=settings.META_ANDROMEDA_WEEKLY_LOOP_HOUR,
            minute=0,
            timezone=SCHEDULER_TIMEZONE,
        ),
        id=META_ANDROMEDA_WEEKLY_CLOSED_LOOP_JOB_ID,
        replace_existing=True,
        misfire_grace_time=DEFAULT_MISFIRE_GRACE_TIME,
        coalesce=True,
        max_instances=1,
    )
    logger.info(
        "⏰ [MetaAndromeda] Weekly closed-loop job registered (day_of_week=%s, hour=%s %s).",
        settings.META_ANDROMEDA_WEEKLY_LOOP_DAY_OF_WEEK,
        settings.META_ANDROMEDA_WEEKLY_LOOP_HOUR,
        SCHEDULER_TIMEZONE,
    )
    return job
