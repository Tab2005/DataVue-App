"""Scheduler report jobs helpers."""

from ._shared import *  # noqa: F403



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
