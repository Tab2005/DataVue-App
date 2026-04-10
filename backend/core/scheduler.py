# backend/core/scheduler.py
"""
APScheduler 核心模組
處理背景自動化報表任務。
"""

import logging
import json
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from database import SessionLocal, ReportSchedule, WeeklyReport, User
from services.report_service import generate_report_content

logger = logging.getLogger(__name__)

# 全域 Scheduler 實例
scheduler = AsyncIOScheduler(timezone="Asia/Taipei")

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass # 手動關閉

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
        schedule = db.query(ReportSchedule).filter(ReportSchedule.id == schedule_id, ReportSchedule.is_active == True).first()
        if not schedule:
            logger.warning(f"[Scheduler] Schedule {schedule_id} not found or inactive.")
            return

        # 取得使用者 Google ID (TokenManager 需要)
        user = db.query(User).filter(User.id == schedule.user_id).first()
        if not user:
            logger.error(f"[Scheduler] User {schedule.user_id} not found for schedule {schedule.name}")
            return

        # 1. 計算日期區間 (基於 Asia/Taipei)
        # 由於是自動產生，通常是在凌晨執行，所以取「昨日」作為基準
        t_now = datetime.now(timezone(timedelta(hours=8)))
        today = t_now.date()
        until_date = today - timedelta(days=1)
        
        if schedule.frequency == 'daily':
            since_date = until_date
        elif schedule.frequency == 'weekly':
            # 優化為「上個完整週」：上週一到上週日
            # weekday() 0=Mon, 6=Sun
            days_since_monday = today.weekday()
            last_sunday = today - timedelta(days=days_since_monday + 1)
            since_date = last_sunday - timedelta(days=6)
            until_date = last_sunday
        elif schedule.frequency == 'monthly':
            # 上個月的第一天到最後一天
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            since_date = last_day_last_month.replace(day=1)
            until_date = last_day_last_month
        else:
            since_date = until_date # 預設

        since_str = since_date.strftime('%Y-%m-%d')
        until_str = until_date.strftime('%Y-%m-%d')
        
        # 2. 準備報表參數
        metrics_list = json.loads(schedule.selected_metrics)
        
        logger.info(f"[Scheduler] Running {schedule.name} ({schedule.frequency}) for {since_str} ~ {until_str}")

        # 3. 呼叫核心產生邏輯
        report_data = await generate_report_content(
            db=db,
            ad_account_id=schedule.ad_account_id,
            since=since_str,
            until=until_str,
            breakdown=schedule.breakdown,
            selected_metrics=metrics_list,
            google_id=user.google_id
        )

        # 4. 建立新的 WeeklyReport 記錄
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
            share_token=str(uuid4())
        )
        db.add(new_report)
        
        schedule.last_run = t_now.replace(tzinfo=None) # 移除時區資訊存入 DB (保持一致性)
        
        # 嘗試取得下次執行時間
        job = scheduler.get_job(f"report_{schedule.id}")
        if job and job.next_run_time:
            schedule.next_run = job.next_run_time.replace(tzinfo=None)

        db.commit()
        logger.info(f"[Scheduler] Successfully generated report for {schedule.name} (Range: {since_str} ~ {until_str})")

        # 5. 發送 LINE 通知 (如果有開啟且用戶已綁定)
        if schedule.is_notify_line and user.line_user_id:
            from services.line_service import send_line_push_message
            from core.config import settings
            
            report_name = f"{schedule.name} ({since_str})"
            share_url = f"{settings.FRONTEND_URL}/reports/share/{new_report.share_token}"
            
            message = f"📊 【新報表通知】\n報表名稱：{report_name}\n\n系統已自動產生您的週報，點擊下方連結即可查看：\n{share_url}"
            
            # 使用 BackgroundTasks 或直接 await (在 APScheduler thread 中 OK)
            import asyncio
            asyncio.create_task(send_line_push_message(user.line_user_id, message))

    except Exception as e:
        logger.error(f"[Scheduler] Error processing schedule {schedule_id}: {e}", exc_info=True)
    finally:
        db.close()

def add_report_job(schedule: ReportSchedule):

    """
    將排程加入 APScheduler
    """
    trigger = None
    # 支援 HH:MM 或 HH:MM:SS 格式
    time_parts = schedule.time_of_day.split(':')
    h = int(time_parts[0])
    m = int(time_parts[1])

    if schedule.frequency == 'daily':
        trigger = CronTrigger(hour=h, minute=m)
    elif schedule.frequency == 'weekly':
        trigger = CronTrigger(day_of_week=schedule.day_of_week or '0', hour=h, minute=m)
    elif schedule.frequency == 'monthly':
        trigger = CronTrigger(day=schedule.day_of_month or '1', hour=h, minute=m)

    if trigger:
        job = scheduler.add_job(
            process_scheduled_report,
            trigger=trigger,
            args=[schedule.id],
            id=f"report_{schedule.id}",
            replace_existing=True,
            misfire_grace_time=3600 # 錯過一小時內允許補執行
        )
        
        # 同步 next_run 到資料庫供 UI 顯示 (加上 try-except 防止干擾主流程)
        if job and job.next_run_time:
            try:
                from database import SessionLocal
                db_sync = SessionLocal()
                db_sync.query(ReportSchedule).filter(ReportSchedule.id == schedule.id).update({
                    "next_run": job.next_run_time.replace(tzinfo=None)
                })
                db_sync.commit()
                db_sync.close()
            except Exception as sync_err:
                logger.warning(f"⏰ [Scheduler] Failed to sync next_run for {schedule.id}: {sync_err}")
                    
        logger.info(f"⏰ Added job: {schedule.name} (ID: {schedule.id}, Frequency: {schedule.frequency}, Next: {job.next_run_time})")
        return job

    return None

def remove_report_job(schedule_id: str):
    """
    移除排程
    """
    job_id = f"report_{schedule_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"⏰ Removed job: {job_id}")
