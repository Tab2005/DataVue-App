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

from database import SessionLocal, ReportSchedule, WeeklyReport, User
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
        return CronTrigger(
            day_of_week=schedule.day_of_week or "0",
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

        user = db.query(User).filter(User.id == schedule.user_id).first()
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
        )

        from uuid import uuid4

        new_report = WeeklyReport(
            id=str(uuid4()),
            name=f"[Auto] {schedule.name} ({since_str})",
            ad_account_id=schedule.ad_account_id,
            ad_account_name=schedule.ad_account_name,
            date_since=since_str,
            date_until=until_str,
            date_label=f"Auto Generated ({schedule.frequency})",
            breakdown=schedule.breakdown,
            selected_metrics=schedule.selected_metrics,
            report_data=json.dumps(report_data),
            status="generated",
            user_id=schedule.user_id,
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

        for schedule in active_schedules:
            add_report_job(schedule, db=db, persist_next_run=True)

        db.commit()
        logger.info(
            "⏰ [Scheduler] Bootstrapped %s active schedules.",
            len(active_schedules),
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
