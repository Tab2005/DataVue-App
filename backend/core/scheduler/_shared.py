"""Shared scheduler dependencies and singleton."""

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
META_ANDROMEDA_RELEASE_METRICS_REFRESH_JOB_ID = "ma_release_metrics_refresh"
META_ANDROMEDA_BACKTEST_JOB_PREFIX = "ma_backtest"
CONTRIBUTION_ANALYSIS_JOB_PREFIX = "ca_analysis"
CONTRIBUTION_STALE_SWEEP_JOB_ID = "ca_stale_sweeper"
GA4_INSIGHTS_INTRADAY_JOB_ID = "ga4_insights_intraday"
GA4_INSIGHTS_DAILY_JOB_ID = "ga4_insights_daily"

__all__ = [name for name in globals() if not name.startswith("__")]
