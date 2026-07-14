"""Scheduler ga4 jobs helpers."""

from ._shared import *  # noqa: F403



async def run_ga4_insights_intraday_job() -> None:
    from modules.ga4.insights_service import GA4InsightsService
    from modules.ga4.repository import repository as ga4_repository

    db = SessionLocal()
    try:
        rules = ga4_repository.list_enabled_rules(db, frequency="hourly")
        for rule in rules:
            try:
                await GA4InsightsService.evaluate_rule(db, rule, now_local=_now_local_naive())
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("⏰ [GA4Insights] intraday rule failed: %s", rule.id)
    finally:
        db.close()



def add_ga4_insights_intraday_job():
    job = scheduler.add_job(
        run_ga4_insights_intraday_job,
        trigger=CronTrigger(minute=10, timezone=SCHEDULER_TIMEZONE),
        id=GA4_INSIGHTS_INTRADAY_JOB_ID,
        replace_existing=True,
        misfire_grace_time=DEFAULT_MISFIRE_GRACE_TIME,
        coalesce=True,
        max_instances=1,
    )
    logger.info("⏰ [GA4Insights] Intraday anomaly job registered.")
    return job



async def run_ga4_insights_daily_job() -> None:
    from modules.ga4.insights_service import GA4InsightsService
    from modules.ga4.repository import repository as ga4_repository

    db = SessionLocal()
    try:
        rules = ga4_repository.list_enabled_rules(db, frequency="daily")
        for rule in rules:
            try:
                await GA4InsightsService.evaluate_rule(db, rule, now_local=_now_local_naive())
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("⏰ [GA4Insights] daily rule failed: %s", rule.id)
    finally:
        db.close()



def add_ga4_insights_daily_job():
    job = scheduler.add_job(
        run_ga4_insights_daily_job,
        trigger=CronTrigger(hour=9, minute=0, timezone=SCHEDULER_TIMEZONE),
        id=GA4_INSIGHTS_DAILY_JOB_ID,
        replace_existing=True,
        misfire_grace_time=DEFAULT_MISFIRE_GRACE_TIME,
        coalesce=True,
        max_instances=1,
    )
    logger.info("⏰ [GA4Insights] Daily anomaly job registered.")
    return job
