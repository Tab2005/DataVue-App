"""Scheduler contribution jobs helpers."""

from ._shared import *  # noqa: F403


async def process_contribution_analysis(snapshot_id: str) -> None:
    """Process a queued Contribution MMM analysis snapshot.

    入口由 `add_contribution_analysis_job()` 註冊；service 層若 scheduler 不可用
    會改走 local async fallback（in-process task），不走此函式。
    """
    from modules.contribution.service import process_analysis

    await process_analysis(snapshot_id)



async def sweep_contribution_stale_snapshots() -> None:
    """定期回收永久卡在 queued/processing 的 contribution snapshot（docs/27 任務 2.2）。

    apscheduler 為 in-memory date-trigger：server 在 job 執行前重啟、或
    scheduler／local async fallback 皆不可用（503 路徑，snapshot 已建但從未
    真正排程）都會留下永久卡住的 snapshot，前端輪詢會無限轉圈。
    """
    from modules.contribution.repository import repository as contribution_repository

    db = SessionLocal()
    try:
        reclaimed = contribution_repository.mark_stale_snapshots_failed(
            db,
            queued_older_than_minutes=settings.CONTRIBUTION_STALE_QUEUED_MINUTES,
            processing_older_than_minutes=settings.CONTRIBUTION_STALE_PROCESSING_MINUTES,
        )
        db.commit()
        if reclaimed:
            logger.warning(
                "⏰ [Contribution] Reclaimed %s stale snapshot(s) (queued>%smin / processing>%smin).",
                reclaimed,
                settings.CONTRIBUTION_STALE_QUEUED_MINUTES,
                settings.CONTRIBUTION_STALE_PROCESSING_MINUTES,
            )
    except Exception:
        db.rollback()
        logger.exception("⏰ [Contribution] sweep_contribution_stale_snapshots failed")
    finally:
        db.close()



def add_contribution_analysis_job(snapshot_id: str, delay_seconds: float = 1):
    """Enqueue a one-off Contribution MMM analysis job on the shared scheduler.

    Scheduler 不可用時回 None（呼叫端應改走 local async fallback，見
    modules.contribution.service._dispatch_analysis）。
    """
    if not is_scheduler_enabled() or not scheduler.running:
        logger.info(
            "⏰ [Contribution] Scheduler unavailable. Caller should use local async fallback for %s.",
            snapshot_id,
        )
        return None
    run_at = datetime.now(_LOCAL_TIMEZONE) + timedelta(seconds=delay_seconds)
    job_id = get_contribution_analysis_job_id(snapshot_id)
    job = scheduler.add_job(
        process_contribution_analysis,
        trigger="date",
        run_date=run_at,
        args=[snapshot_id],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=DEFAULT_MISFIRE_GRACE_TIME,
        coalesce=True,
        max_instances=1,
    )
    logger.info(
        "⏰ [Contribution] Analysis job added: %s for snapshot %s (delay=%ss)",
        job_id,
        snapshot_id,
        delay_seconds,
    )
    return job



def add_contribution_stale_sweep_job():
    """Register periodic sweep for stale contribution snapshots（docs/27 任務 2.2）。"""
    job = scheduler.add_job(
        sweep_contribution_stale_snapshots,
        trigger="interval",
        seconds=settings.CONTRIBUTION_STALE_SWEEP_INTERVAL_SECONDS,
        id=CONTRIBUTION_STALE_SWEEP_JOB_ID,
        replace_existing=True,
        misfire_grace_time=DEFAULT_MISFIRE_GRACE_TIME,
        coalesce=True,
        max_instances=1,
    )
    logger.info(
        "⏰ [Contribution] Stale snapshot sweeper registered (interval=%ss).",
        settings.CONTRIBUTION_STALE_SWEEP_INTERVAL_SECONDS,
    )
    return job
