"""Scheduler engine helpers."""

from ._shared import *  # noqa: F403



def is_scheduler_enabled() -> bool:
    """是否啟用排程器，可透過環境變數關閉。"""
    return os.getenv("ENABLE_REPORT_SCHEDULER", "true").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }



def get_job_id(schedule_id: str) -> str:
    """統一生成 APScheduler Job ID。"""
    return f"report_{schedule_id}"



def get_meta_andromeda_score_job_id(score_event_id: str) -> str:
    """Meta Andromeda score worker job id."""
    return f"ma_score_{score_event_id}"



def get_contribution_analysis_job_id(snapshot_id: str) -> str:
    """Contribution MMM analysis job id."""
    return f"{CONTRIBUTION_ANALYSIS_JOB_PREFIX}_{snapshot_id}"



def _now_local_aware() -> datetime:
    return datetime.now(_LOCAL_TIMEZONE)



def _now_local_naive() -> datetime:
    return _now_local_aware().replace(tzinfo=None)



def _to_local_naive(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(_LOCAL_TIMEZONE).replace(tzinfo=None)



def _parse_time_of_day(raw_value: str | None) -> tuple[int, int]:
    try:
        time_parts = (raw_value or "08:00").split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        return hour, minute
    except (ValueError, IndexError, AttributeError) as exc:
        logger.warning(
            "⏰ [Scheduler] Invalid time_of_day '%s', falling back to 08:00. Error: %s",
            raw_value,
            exc,
        )
        return 8, 0



def _build_trigger(schedule: ReportSchedule) -> CronTrigger | None:
    hour, minute = _parse_time_of_day(schedule.time_of_day)

    if schedule.frequency == "daily":
        return CronTrigger(hour=hour, minute=minute, timezone=SCHEDULER_TIMEZONE)
    if schedule.frequency == "weekly":
        # 前端傳入 0=週日, 1=週一... 6=週六
        # APScheduler 期待 0=週一, 1=週二... 6=週日
        # 轉換公式: (int - 1) % 7
        try:
            raw_day = int(schedule.day_of_week or "1")
            mapped_day = (raw_day - 1) % 7
        except (ValueError, TypeError):
            mapped_day = 0  # 預設週一
            logger.warning(f"⏰ [Scheduler] Invalid day_of_week '{schedule.day_of_week}', fallback to Mon")

        return CronTrigger(
            day_of_week=str(mapped_day),
            hour=hour,
            minute=minute,
            timezone=SCHEDULER_TIMEZONE,
        )
    if schedule.frequency == "monthly":
        return CronTrigger(
            day=schedule.day_of_month or "1",
            hour=hour,
            minute=minute,
            timezone=SCHEDULER_TIMEZONE,
        )

    logger.error(
        "⏰ [Scheduler] Unsupported frequency '%s' for schedule %s",
        schedule.frequency,
        schedule.id,
    )
    return None



def get_next_run_time(
    schedule: ReportSchedule,
    reference_time: datetime | None = None,
) -> datetime | None:
    """計算排程下一次應執行時間（以 Asia/Taipei 的 naive datetime 回傳）。"""
    trigger = _build_trigger(schedule)
    if not trigger:
        return None

    next_fire_time = trigger.get_next_fire_time(
        previous_fire_time=None,
        now=reference_time or _now_local_aware(),
    )
    return _to_local_naive(next_fire_time)



def is_schedule_overdue(
    schedule: ReportSchedule,
    reference_time: datetime | None = None,
) -> bool:
    """判斷此排程是否已經錯過原定執行時間。"""
    if not schedule.is_active or not schedule.next_run:
        return False
    return schedule.next_run <= (reference_time or _now_local_naive())



def _sync_schedule_next_run(schedule: ReportSchedule, next_run_time: datetime | None) -> None:
    schedule.next_run = _to_local_naive(next_run_time)



def _scheduler_event_listener(event) -> None:
    scheduled_run_time = _to_local_naive(getattr(event, "scheduled_run_time", None))

    if event.code == EVENT_JOB_MISSED:
        logger.warning(
            "⏰ [Scheduler] Job missed: %s (scheduled=%s). Instance may have been paused or overloaded.",
            event.job_id,
            scheduled_run_time,
        )
        return

    if getattr(event, "exception", None):
        logger.error(
            "❌ [Scheduler] Job failed: %s (scheduled=%s)\n%s",
            event.job_id,
            scheduled_run_time,
            getattr(event, "traceback", ""),
        )
        return

    logger.info(
        "✅ [Scheduler] Job executed: %s (scheduled=%s)",
        event.job_id,
        scheduled_run_time,
    )



def register_scheduler_listeners() -> None:
    global _LISTENERS_REGISTERED
    if _LISTENERS_REGISTERED:
        return

    scheduler.add_listener(
        _scheduler_event_listener,
        EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED,
    )
    _LISTENERS_REGISTERED = True



def get_scheduler_status() -> dict:
    """提供健康檢查與除錯用的 scheduler 狀態摘要。"""
    return {
        "enabled": is_scheduler_enabled(),
        "running": scheduler.running,
        "job_count": len(scheduler.get_jobs()),
    }



def _resolve_scheduler_role_flags(role: str | None = None) -> tuple[bool, bool]:
    """依 SERVICE_ROLE 決定 start_scheduler() 該註冊哪些 job（docs/24 Wave 2）。

    抽成獨立的純函式方便單元測試，不需要真的驅動一次 start_scheduler()
    （會牽動共用的 AsyncIOScheduler 全域單例與真實 DB session）。

    回傳 (run_report_jobs, run_meta_andromeda_jobs)：
    - all（預設）：兩者皆 True，行為與拆分前完全一致。
    - web：只留週報排程，Meta Andromeda 排程交給 worker process。
    - worker：只留 Meta Andromeda 排程，週報排程留在 web。
    """
    resolved_role = (role or settings.SERVICE_ROLE)
    return resolved_role != "worker", resolved_role != "web"



def remove_report_job(schedule_id: str):
    """移除排程。"""
    job_id = get_job_id(schedule_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info("⏰ [Scheduler] Job removed: %s", job_id)
    else:
        logger.debug("⏰ [Scheduler] Attempted to remove non-existent job: %s", job_id)



async def start_scheduler() -> dict:
    """啟動 scheduler，載入現有排程並補跑逾期任務。

    docs/24 Wave 2：依 `SERVICE_ROLE` 決定要註冊哪些 job——
    - all（預設，單機開發）：週報排程 + Meta Andromeda 排程全部註冊，行為與
      拆分前完全一致。
    - web：只註冊週報排程，不註冊 Meta Andromeda 的 stream consumer/reclaim/
      db queue sweeper/週報閉環（評分/匯入負載交給 worker process）。
    - worker：只註冊 Meta Andromeda 排程，不註冊週報排程（週報留在 web）。
    """
    register_scheduler_listeners()

    if not is_scheduler_enabled():
        logger.info("⏰ [Scheduler] Disabled via ENABLE_REPORT_SCHEDULER=false")
        return get_scheduler_status()

    role = settings.SERVICE_ROLE
    run_report_jobs, run_meta_andromeda_jobs = _resolve_scheduler_role_flags(role)

    db = SessionLocal()
    overdue_schedule_ids: list[str] = []
    active_schedules: list[ReportSchedule] = []
    queued_score_events: list = []
    queued_backtest_runs: list = []
    try:
        if run_report_jobs:
            active_schedules = (
                db.query(ReportSchedule)
                .filter(ReportSchedule.is_active == True)
                .all()
            )
            overdue_schedule_ids = [
                schedule.id for schedule in active_schedules if is_schedule_overdue(schedule)
            ]

        if not scheduler.running:
            scheduler.start()
            logger.info("⏰ [Scheduler] AsyncIOScheduler started (SERVICE_ROLE=%s)", role)

        if run_meta_andromeda_jobs:
            add_meta_andromeda_queue_sweeper_job()
            add_meta_andromeda_redis_stream_consumer_job()
            add_meta_andromeda_redis_stream_reclaim_job()
            add_meta_andromeda_weekly_closed_loop_job()
            add_meta_andromeda_release_metrics_refresh_job()
            # Contribution（MMM）目前與 Meta Andromeda 共用背景負載角色（docs/25
            # Wave 1 規劃將其移入同一 worker），故沿用同一 role flag 註冊殭屍
            # snapshot 回收排程（docs/27 任務 2.2）。開機當下先掃一次（不等
            # 第一個 interval 到），立即回收上次崩潰/重啟留下的殭屍 snapshot。
            add_contribution_stale_sweep_job()
            add_ga4_insights_intraday_job()
            add_ga4_insights_daily_job()
            await sweep_contribution_stale_snapshots()

        if run_report_jobs:
            for schedule in active_schedules:
                add_report_job(schedule, db=db, persist_next_run=True)

        if run_meta_andromeda_jobs:
            from database.models.meta_andromeda import MetaAndromedaBacktestRun, MetaAndromedaScoreEvent

            queued_score_events = (
                db.query(MetaAndromedaScoreEvent)
                .filter(MetaAndromedaScoreEvent.status.in_(["queued", "processing"]))
                .all()
            )
            if settings.META_ANDROMEDA_QUEUE_HOST not in {"redis_stream", "external_webhook"}:
                for score_event in queued_score_events:
                    add_meta_andromeda_score_job(score_event.id)
            queued_backtest_runs = (
                db.query(MetaAndromedaBacktestRun)
                .filter(MetaAndromedaBacktestRun.status.in_(["queued", "running"]))
                .all()
            )
            for run in queued_backtest_runs:
                add_meta_andromeda_backtest_run_job(run.id)

        db.commit()
        if run_report_jobs:
            logger.info(
                "⏰ [Scheduler] Bootstrapped %s active schedules.",
                len(active_schedules),
            )
        if queued_score_events:
            logger.info(
                "⏰ [MetaAndromeda] Bootstrapped %s queued score events.",
                len(queued_score_events),
            )
        if queued_backtest_runs:
            logger.info(
                "⏰ [MetaAndromeda] Bootstrapped %s queued/running backtest runs.",
                len(queued_backtest_runs),
            )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    if overdue_schedule_ids:
        logger.warning(
            "⏰ [Scheduler] Found %s overdue schedules on startup. Running catch-up once for each: %s",
            len(overdue_schedule_ids),
            ", ".join(overdue_schedule_ids),
        )
        for schedule_id in overdue_schedule_ids:
            await process_scheduled_report(schedule_id)
    elif run_report_jobs:
        logger.info("⏰ [Scheduler] No overdue schedules found on startup.")

    return get_scheduler_status()



def stop_scheduler(wait: bool = False) -> None:
    """安全關閉 scheduler。

    `wait=True`（worker process 專用，見 backend/worker_main.py）：等待目前
    正在執行中的 job（例如尚未跑完的評分/匯入）完成才真正關閉，換取比較
    優雅的滾動部署；web process 維持 `wait=False` 的既有行為，不因為評分
    job 拖慢重啟。
    """
    if scheduler.running:
        scheduler.shutdown(wait=wait)
        logger.info("⏰ [Scheduler] Scheduler stopped (wait=%s)", wait)
