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

from database import SessionLocal, WeeklyReport, User
from dependencies import get_current_user, require_module

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
        "user_id": report.user_id,
        "team_id": report.team_id,
        "created_at": report.created_at.isoformat() if report.created_at else "",
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
    }

# ---- Endpoints ----

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
        .filter(WeeklyReport.user_id == current_user.id)\
        .order_by(WeeklyReport.created_at.desc()).all()
    for r in personal:
        reports_map[r.id] = _serialize(r)
        
    # 團隊
    if team_id:
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
        user_id=current_user.id if not payload.team_id else None,
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
    report = db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # 1. 解析指標與日期
    try:
        metrics_list = json.loads(report.selected_metrics)
        custom_fields = ",".join(metrics_list) if isinstance(metrics_list, list) else None
    except:
        metrics_list = ["spend", "impressions", "ctr", "cpc"]
        custom_fields = ",".join(metrics_list)

    # 推算前一期日期 (Comparison Period)
    since_dt = datetime.strptime(report.date_since, '%Y-%m-%d')
    until_dt = datetime.strptime(report.date_until, '%Y-%m-%d')
    duration = (until_dt - since_dt).days + 1
    prev_until = (since_dt - timedelta(days=1)).strftime('%Y-%m-%d')
    prev_since = (since_dt - timedelta(days=duration)).strftime('%Y-%m-%d')

    # 2. 抓取資料
    from modules.fb_ads.analytics_service import get_custom_report
    from modules.fb_ads.trends_service import get_analytics_trend

    # 抓取明細 (及時段總計)
    current_rows = await get_custom_report(
        account_id=report.ad_account_id,
        since=report.date_since,
        until=report.date_until,
        user_id=current_user.google_id,
        level=report.breakdown or "campaign",
        custom_fields=custom_fields
    )

    # 抓取趨勢 (含對比)
    trend_data = await get_analytics_trend(
        account_id=report.ad_account_id,
        user_id=current_user.google_id,
        since=report.date_since,
        until=report.date_until,
        prev_since=prev_since,
        prev_until=prev_until
    )

    if current_rows is None:
        raise HTTPException(status_code=502, detail="Failed to fetch FB data")

    # 3. 數據彙整 (Aggregation)
    def _sum_metrics(rows):
        s = {
            "spend": 0.0, "impressions": 0, "clicks": 0, "link_clicks": 0, "reach": 0,
            "purchases": 0, "purchase_value": 0.0, "add_to_cart": 0, "view_content": 0
        }
        for row in rows:
            for k in s.keys():
                s[k] += float(row.get(k, 0))
        
        # 計算比率指標
        s["ctr"] = (s["link_clicks"] / s["impressions"] * 100) if s["impressions"] > 0 else 0
        s["cpc"] = s["spend"] / s["clicks"] if s["clicks"] > 0 else 0
        s["cpm"] = (s["spend"] / s["impressions"] * 1000) if s["impressions"] > 0 else 0
        s["roas"] = s["purchase_value"] / s["spend"] if s["spend"] > 0 else 0
        s["cpa"] = s["spend"] / s["purchases"] if s["purchases"] > 0 else 0
        return s

    summary = _sum_metrics(current_rows)
    
    # 從趨勢資料中提取前期總計
    prev_summary = {}
    if trend_data:
        p_rows = []
        for d in trend_data:
            # 建立虛擬 row 來複用 _sum_metrics 
            p_rows.append({k.replace("_prev", ""): v for k, v in d.items() if "_prev" in k})
        prev_summary = _sum_metrics(p_rows)

    # 4. 結構化存檔
    structured_data = {
        "summary": summary,
        "prev_summary": prev_summary,
        "trends": trend_data or [],
        "table_data": current_rows
    }

    report.report_data = json.dumps(structured_data)
    report.status = "generated"
    report.updated_at = datetime.now(timezone.utc)
    db.commit()

    return _serialize(report)
