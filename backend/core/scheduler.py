"""
APScheduler 核心模組
處理背景自動化報表任務。
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_MISSED
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from core.config import settings
from database import SessionLocal, ReportSchedule, Team, WeeklyReport, User
from services.report_service import generate_report_content

logger = logging.getLogger(__name__)

SCHEDULER_TIMEZONE = "Asia/Taipei"
DEFAULT_MISFIRE_GRACE_TIME = int(
    os.getenv("REPORT_SCHEDULER_MISFIRE_GRACE_TIME", str(24 * 60 * 60))
)
_LOCAL_TIMEZONE = timezone(timedelta(hours=8))
_LISTENERS_REGISTERED = False

# 全域 Scheduler 實例
scheduler = AsyncIOScheduler(timezone=SCHEDULER_TIMEZONE)
META_ANDROMEDA_QUEUE_SWEEP_JOB_ID = "ma_queue_sweeper"
META_ANDROMEDA_REDIS_STREAM_CONSUMER_JOB_ID = "ma_redis_stream_consumer"
META_ANDROMEDA_REDIS_STREAM_RECLAIM_JOB_ID = "ma_redis_stream_reclaim"
META_ANDROMEDA_WEEKLY_CLOSED_LOOP_JOB_ID = "ma_weekly_closed_loop"


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


def resolve_schedule_user(db: Session, schedule: ReportSchedule) -> User | None:
    """解析排程實際執行者。舊版 team schedule 若缺 user_id，回退到 team owner。"""
    if schedule.user_id:
        user = db.query(User).filter(User.id == schedule.user_id).first()
        if user:
            return user

    if schedule.team_id:
        team = db.query(Team).filter(Team.id == schedule.team_id).first()
        if team and team.owner_id:
            owner = db.query(User).filter(User.id == team.owner_id).first()
            if owner:
                logger.warning(
                    "[Scheduler] Schedule %s missing user_id. Falling back to team owner %s.",
                    schedule.id,
                    owner.id,
                )
                schedule.user_id = owner.id
                db.add(schedule)
                return owner

    return None


async def process_scheduled_report(schedule_id: str):
    """
    執行排程任務：
    1. 計算日期區間
    2. 抓取數據與產生內容
    3. 建立 WeeklyReport 記錄
    4. 更新排程資訊（最後執行時間）
    """
    db = SessionLocal()
    try:
        schedule = (
            db.query(ReportSchedule)
            .filter(ReportSchedule.id == schedule_id, ReportSchedule.is_active == True)
            .first()
        )
        if not schedule:
            logger.warning("[Scheduler] Schedule %s not found or inactive.", schedule_id)
            return

        user = resolve_schedule_user(db, schedule)
        if not user:
            logger.error(
                "[Scheduler] User %s not found for schedule %s",
                schedule.user_id,
                schedule.name,
            )
            return

        current_time = _now_local_aware()
        today = current_time.date()
        until_date = today - timedelta(days=1)

        if schedule.frequency == "daily":
            since_date = until_date
        elif schedule.frequency == "weekly":
            days_since_monday = today.weekday()
            last_sunday = today - timedelta(days=days_since_monday + 1)
            since_date = last_sunday - timedelta(days=6)
            until_date = last_sunday
        elif schedule.frequency == "monthly":
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            since_date = last_day_last_month.replace(day=1)
            until_date = last_day_last_month
        else:
            since_date = until_date

        since_str = since_date.strftime("%Y-%m-%d")
        until_str = until_date.strftime("%Y-%m-%d")
        metrics_list = json.loads(schedule.selected_metrics)

        logger.info(
            "[Scheduler] Running %s (%s) for %s ~ %s",
            schedule.name,
            schedule.frequency,
            since_str,
            until_str,
        )

        report_data = await generate_report_content(
            db=db,
            ad_account_id=schedule.ad_account_id,
            since=since_str,
            until=until_str,
            breakdown=schedule.breakdown,
            selected_metrics=metrics_list,
            google_id=user.google_id,
            team_id=schedule.team_id,
            module_type=schedule.module_type or "fb_ads"
        )

        from uuid import uuid4

        new_report = WeeklyReport(
            id=str(uuid4()),
            name=f"[Auto] {schedule.name} ({since_str})",
            module_type=schedule.module_type or "fb_ads",
            ad_account_id=schedule.ad_account_id,
            ad_account_name=schedule.ad_account_name,
            date_since=since_str,
            date_until=until_str,
            date_label=f"Auto Generated ({schedule.frequency})",
            breakdown=schedule.breakdown,
            selected_metrics=schedule.selected_metrics,
            report_data=json.dumps(report_data),
            status="generated",
            user_id=user.id,
            team_id=schedule.team_id,
            share_token=str(uuid4()),
        )
        db.add(new_report)

        schedule.last_run = current_time.replace(tzinfo=None)

        job = scheduler.get_job(get_job_id(schedule.id))
        if job:
            _sync_schedule_next_run(schedule, job.next_run_time)

        db.commit()
        logger.info(
            "[Scheduler] Successfully generated report for %s (Range: %s ~ %s)",
            schedule.name,
            since_str,
            until_str,
        )

        if schedule.is_notify_line and user.line_user_id:
            from core.config import settings
            from services.line_service import send_line_push_message

            report_name = f"{schedule.name} ({since_str})"
            share_url = f"{settings.FRONTEND_URL}/reports/share/{new_report.share_token}"
            message = (
                f"📊 【新報表通知】\n報表名稱：{report_name}\n\n"
                f"系統已自動產生您的週報，點擊下方連結即可查看：\n{share_url}"
            )
            asyncio.create_task(send_line_push_message(user.line_user_id, message))

    except Exception as exc:
        logger.error("[Scheduler] Error processing schedule %s: %s", schedule_id, exc, exc_info=True)
    finally:
        db.close()


async def process_meta_andromeda_score_event(score_event_id: str, queue_host: str = "apscheduler"):
    """Process a queued Meta Andromeda score event."""
    from modules.meta_andromeda.service import MetaAndromedaService

    await MetaAndromedaService.process_score_event(score_event_id, queue_host=queue_host)


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


def add_report_job(
    schedule: ReportSchedule,
    db: Session | None = None,
    persist_next_run: bool = False,
):
    """將排程加入 APScheduler。"""
    if not is_scheduler_enabled():
        logger.info(
            "⏰ [Scheduler] Scheduler disabled. Skipping in-memory job registration for %s.",
            schedule.id,
        )
        if persist_next_run and db is not None:
            _sync_schedule_next_run(schedule, get_next_run_time(schedule))
            db.add(schedule)
        return None

    trigger = _build_trigger(schedule)
    if not trigger:
        return None

    job_id = get_job_id(schedule.id)
    job = scheduler.add_job(
        process_scheduled_report,
        trigger=trigger,
        args=[schedule.id],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=DEFAULT_MISFIRE_GRACE_TIME,
        coalesce=True,
        max_instances=1,
    )

    if persist_next_run and db is not None:
        _sync_schedule_next_run(schedule, job.next_run_time)
        db.add(schedule)

    logger.info(
        "⏰ [Scheduler] Job added/updated: %s (Job_ID: %s, Frequency: %s, Next: %s)",
        schedule.name,
        job_id,
        schedule.frequency,
        job.next_run_time,
    )
    return job


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


def remove_report_job(schedule_id: str):
    """移除排程。"""
    job_id = get_job_id(schedule_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info("⏰ [Scheduler] Job removed: %s", job_id)
    else:
        logger.debug("⏰ [Scheduler] Attempted to remove non-existent job: %s", job_id)


async def start_scheduler() -> dict:
    """啟動 scheduler，載入現有排程並補跑逾期任務。"""
    register_scheduler_listeners()

    if not is_scheduler_enabled():
        logger.info("⏰ [Scheduler] Disabled via ENABLE_REPORT_SCHEDULER=false")
        return get_scheduler_status()

    db = SessionLocal()
    overdue_schedule_ids: list[str] = []
    try:
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
            logger.info("⏰ [Scheduler] AsyncIOScheduler started")
        add_meta_andromeda_queue_sweeper_job()
        add_meta_andromeda_redis_stream_consumer_job()
        add_meta_andromeda_redis_stream_reclaim_job()
        add_meta_andromeda_weekly_closed_loop_job()

        for schedule in active_schedules:
            add_report_job(schedule, db=db, persist_next_run=True)

        from database.models.meta_andromeda import MetaAndromedaScoreEvent

        queued_score_events = (
            db.query(MetaAndromedaScoreEvent)
            .filter(MetaAndromedaScoreEvent.status.in_(["queued", "processing"]))
            .all()
        )
        if settings.META_ANDROMEDA_QUEUE_HOST not in {"redis_stream", "external_webhook"}:
            for score_event in queued_score_events:
                add_meta_andromeda_score_job(score_event.id)

        db.commit()
        logger.info(
            "⏰ [Scheduler] Bootstrapped %s active schedules.",
            len(active_schedules),
        )
        if queued_score_events:
            logger.info(
                "⏰ [MetaAndromeda] Bootstrapped %s queued score events.",
                len(queued_score_events),
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
    else:
        logger.info("⏰ [Scheduler] No overdue schedules found on startup.")

    return get_scheduler_status()


def stop_scheduler() -> None:
    """安全關閉 scheduler。"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("⏰ [Scheduler] Scheduler stopped")
