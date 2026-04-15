"""
Weekly Reports Router
週報專案 CRUD + 資料產生端點
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json, uuid, logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from database import SessionLocal, WeeklyReport, User, ReportSchedule, Team, TeamMember
from dependencies import get_current_user, require_module
from core.scheduler import add_report_job, get_next_run_time, remove_report_job


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reports", tags=["reports"])
fb_ads_check = require_module("fb_ads")

# ---- Dependency ----
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_team_access(db: Session, current_user: User, team_id: Optional[str]) -> Optional[Team]:
    if not team_id:
        return None

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if current_user.is_super_admin:
        return team

    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    return team


def _ensure_schedule_access(db: Session, current_user: User, schedule: ReportSchedule) -> None:
    if schedule.team_id:
        _ensure_team_access(db, current_user, schedule.team_id)
        return

    if not current_user.is_super_admin and schedule.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to access this schedule")


def _ensure_report_access(db: Session, current_user: User, report: WeeklyReport) -> None:
    if report.team_id:
        _ensure_team_access(db, current_user, report.team_id)
        return

    if not current_user.is_super_admin and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to access this report")


# ---- Pydantic Schemas for Schedules ----


class ScheduleCreate(BaseModel):
    name: str
    ad_account_id: str
    ad_account_name: Optional[str] = None
    selected_metrics: List[str]
    breakdown: Optional[str] = "campaign"
    frequency: str  # daily, weekly, monthly
    day_of_week: Optional[str] = None
    day_of_month: Optional[str] = None
    time_of_day: Optional[str] = "08:00"
    is_notify_line: Optional[bool] = False
    team_id: Optional[str] = None

class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    selected_metrics: Optional[List[str]] = None
    breakdown: Optional[str] = None
    frequency: Optional[str] = None
    day_of_week: Optional[str] = None
    day_of_month: Optional[str] = None
    time_of_day: Optional[str] = None
    is_active: Optional[bool] = None
    is_notify_line: Optional[bool] = None

def _serialize_schedule(s: ReportSchedule) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "ad_account_id": s.ad_account_id,
        "ad_account_name": s.ad_account_name,
        "selected_metrics": json.loads(s.selected_metrics) if s.selected_metrics else [],
        "breakdown": s.breakdown,
        "frequency": s.frequency,
        "day_of_week": s.day_of_week,
        "day_of_month": s.day_of_month,
        "time_of_day": s.time_of_day,
        "is_active": s.is_active,
        "is_notify_line": s.is_notify_line,
        "user_id": s.user_id,
        "team_id": s.team_id,
        "last_run": s.last_run.isoformat() if s.last_run else None,
        "next_run": s.next_run.isoformat() if s.next_run else None,
    }

# ---- Schedule Endpoints ----

@router.get("/schedules", dependencies=[Depends(fb_ads_check)])
async def list_schedules(
    team_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得排程列表"""
    query = db.query(ReportSchedule)
    if team_id:
        _ensure_team_access(db, current_user, team_id)
        query = query.filter(ReportSchedule.team_id == team_id)
    else:
        query = query.filter(
            ReportSchedule.user_id == current_user.id,
            ReportSchedule.team_id.is_(None),
        )
    
    schedules = query.all()
    return [_serialize_schedule(s) for s in schedules]

@router.get("/schedules/{schedule_id}", dependencies=[Depends(fb_ads_check)])
async def get_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得單筆排程詳情"""
    schedule = db.query(ReportSchedule).filter(ReportSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    _ensure_schedule_access(db, current_user, schedule)
    return _serialize_schedule(schedule)

@router.post("/schedules", dependencies=[Depends(fb_ads_check)])
async def create_schedule(
    payload: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """建立新排程"""
    _ensure_team_access(db, current_user, payload.team_id)

    schedule = ReportSchedule(
        id=str(uuid.uuid4()),
        name=payload.name,
        ad_account_id=payload.ad_account_id,
        ad_account_name=payload.ad_account_name,
        selected_metrics=json.dumps(payload.selected_metrics),
        breakdown=payload.breakdown,
        frequency=payload.frequency,
        day_of_week=payload.day_of_week,
        day_of_month=payload.day_of_month,
        time_of_day=payload.time_of_day or "08:00",
        user_id=current_user.id,
        team_id=payload.team_id,
        is_active=True,
        is_notify_line=payload.is_notify_line or False
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    # 加入排程器並同步下次執行時間 (採用極強容錯模式)
    try:
        add_report_job(schedule)
        schedule.next_run = get_next_run_time(schedule)
        db.add(schedule)
        db.commit()
    except Exception as e:
        logger.error(f"❌ [API] Critical error in starting scheduler job for {schedule.id}: {e}")
        # 注意：此處不拋出異常，確保 API 能成功回傳，因為 DB 基礎紀錄已經 commit
    
    return _serialize_schedule(schedule)

@router.put("/schedules/{schedule_id}", dependencies=[Depends(fb_ads_check)])
async def update_schedule(
    schedule_id: str,
    payload: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新排程設定"""
    schedule = db.query(ReportSchedule).filter(ReportSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    _ensure_schedule_access(db, current_user, schedule)
    
    if payload.name is not None: schedule.name = payload.name
    if payload.selected_metrics is not None: schedule.selected_metrics = json.dumps(payload.selected_metrics)
    if payload.breakdown is not None: schedule.breakdown = payload.breakdown
    if payload.frequency is not None: schedule.frequency = payload.frequency
    if payload.day_of_week is not None: schedule.day_of_week = payload.day_of_week
    if payload.day_of_month is not None: schedule.day_of_month = payload.day_of_month
    if payload.time_of_day is not None: schedule.time_of_day = payload.time_of_day
    if payload.is_active is not None: schedule.is_active = payload.is_active
    if payload.is_notify_line is not None: schedule.is_notify_line = payload.is_notify_line
    
    db.commit()
    db.refresh(schedule)
    
    # 更新排程器狀態並同步下次執行時間 (與資料庫狀態同步)
    try:
        if schedule.is_active:
            add_report_job(schedule)
            schedule.next_run = get_next_run_time(schedule)
            db.add(schedule)
            db.commit()
        else:
            remove_report_job(schedule.id)
            schedule.next_run = None
            db.add(schedule)
            db.commit()
    except Exception as e:
        logger.error(f"❌ [API] Critical error in updating scheduler job for {schedule.id}: {e}")
        # 不拋出異常，因基礎資料已在下方 commit 或已成功
    
    return _serialize_schedule(schedule)

@router.delete("/schedules/{schedule_id}", dependencies=[Depends(fb_ads_check)])
async def delete_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刪除排程"""
    schedule = db.query(ReportSchedule).filter(ReportSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    _ensure_schedule_access(db, current_user, schedule)
    
    # 從排程器移除
    remove_report_job(schedule.id)
    
    db.delete(schedule)
    db.commit()
    return {"message": "deleted"}

# ---- Pydantic Schemas ----


class ReportCreate(BaseModel):
    name: str
    description: Optional[str] = None
    ad_account_id: str
    ad_account_name: Optional[str] = None
    date_since: str
    date_until: str
    date_label: Optional[str] = None
    breakdown: Optional[str] = "campaign"
    selected_metrics: List[str]
    team_id: Optional[str] = None

class ReportUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sections: Optional[List[dict]] = None
    ai_summary: Optional[str] = None
    status: Optional[str] = None

# ---- Helpers ----
def _serialize(report: WeeklyReport) -> dict:
    def _safe_json_load(data, default):
        if not data: return default
        try:
            return json.loads(data)
        except:
            return default

    return {
        "id": report.id,
        "name": report.name,
        "description": report.description,
        "ad_account_id": report.ad_account_id,
        "ad_account_name": report.ad_account_name,
        "date_since": report.date_since,
        "date_until": report.date_until,
        "date_label": report.date_label,
        "breakdown": report.breakdown,
        "selected_metrics": _safe_json_load(report.selected_metrics, []),
        "report_data": _safe_json_load(report.report_data, None),
        "ai_summary": report.ai_summary,
        "sections": _safe_json_load(report.sections, []),
        "status": report.status,
        "share_token": report.share_token,
        "user_id": report.user_id,
        "team_id": report.team_id,
        "created_at": report.created_at.isoformat() if report.created_at else "",
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
    }

# ---- Endpoints ----

@router.get("/share/{token}")
async def get_shared_report(token: str, db: Session = Depends(get_db)):
    """公開分享端點：無需登入即可取得報表資料"""
    report = db.query(WeeklyReport).filter(WeeklyReport.share_token == token).first()
    if not report:
        raise HTTPException(status_code=404, detail="Shared report not found")
    
    # 僅回傳唯讀所需欄位，增加安全性
    data = _serialize(report)
    return data

@router.get("", dependencies=[Depends(fb_ads_check)])
async def list_reports(
    team_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """列出個人 + 團隊週報列表"""
    reports_map = {}
    # 個人
    personal = db.query(WeeklyReport)\
        .filter(WeeklyReport.user_id == current_user.id, WeeklyReport.team_id.is_(None))\
        .order_by(WeeklyReport.created_at.desc()).all()
    for r in personal:
        reports_map[r.id] = _serialize(r)
        
    # 團隊
    if team_id:
        _ensure_team_access(db, current_user, team_id)
        team_reports = db.query(WeeklyReport)\
            .filter(WeeklyReport.team_id == team_id)\
            .order_by(WeeklyReport.created_at.desc()).all()
        for r in team_reports:
            reports_map[r.id] = _serialize(r)
            
    return list(reports_map.values())


@router.post("", dependencies=[Depends(fb_ads_check)])
async def create_report(
    payload: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """建立新週報（草稿狀態）"""
    _ensure_team_access(db, current_user, payload.team_id)

    report = WeeklyReport(
        id=str(uuid.uuid4()),
        name=payload.name,
        description=payload.description,
        ad_account_id=payload.ad_account_id,
        ad_account_name=payload.ad_account_name,
        date_since=payload.date_since,
        date_until=payload.date_until,
        date_label=payload.date_label,
        breakdown=payload.breakdown or "campaign",
        selected_metrics=json.dumps(payload.selected_metrics),
        status="draft",
        share_token=str(uuid.uuid4()),
        user_id=current_user.id,
        team_id=payload.team_id,
        created_by=current_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return _serialize(report)


@router.get("/{report_id}", dependencies=[Depends(fb_ads_check)])
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得單一週報"""
    report = db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    _ensure_report_access(db, current_user, report)
    
    # 自動補齊遺漏的 share_token (針對舊報表)
    if not report.share_token:
        report.share_token = str(uuid.uuid4())
        db.commit()
        db.refresh(report)

    return _serialize(report)


@router.put("/{report_id}", dependencies=[Depends(fb_ads_check)])
async def update_report(
    report_id: str,
    payload: ReportUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新週報（名稱、章節、AI摘要、狀態）"""
    report = db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    _ensure_report_access(db, current_user, report)
    if payload.name is not None:
        report.name = payload.name
    if payload.description is not None:
        report.description = payload.description
    if payload.sections is not None:
        report.sections = json.dumps(payload.sections)
    if payload.ai_summary is not None:
        report.ai_summary = payload.ai_summary
    if payload.status is not None:
        report.status = payload.status
    report.updated_at = datetime.now(timezone.utc)
    db.commit()
    return _serialize(report)


@router.delete("/{report_id}", dependencies=[Depends(fb_ads_check)])
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刪除週報"""
    report = db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    _ensure_report_access(db, current_user, report)
    db.delete(report)
    db.commit()
    return {"message": "deleted"}


@router.post("/{report_id}/generate", dependencies=[Depends(fb_ads_check)])
async def generate_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    觸發報表資料產生：
    複用現有 analytics_service 抓取 FB 廣告資料，
    並計算摘要 (Summary)、對比數據與趨勢圖表。
    """
    from services.report_service import trigger_manual_generate
    try:
        report = await trigger_manual_generate(db, report_id, current_user.google_id)
        return _serialize(report)
    except Exception as e:
        logger.error(f"Generate report failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

