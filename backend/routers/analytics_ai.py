"""成效分析頁「AI 廣告分析」快照 + 分享連結端點（docs/58）。

跟 GA4 轉換洞察不同，這裡沒有「每次 GET 報表就自動 upsert 快照」的機制
（成效分析表格是即時運算，隨篩選/排序/勾選指標變動，沒有天然的 upsert
key）。改成使用者點「開始 AI 解讀」時，前端把當下組好的 payload 送來
建立一筆新快照，AI 解讀完成後存回同一筆快照；每次重新解讀都是一筆全新
快照，分享連結一旦產生就永久凍結在分享當下的內容。
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import Team, TeamMember, User, get_db
from dependencies import get_current_user, require_module, require_permission
from modules.fb_ads.analytics_ai_repository import analytics_ai_repository

router = APIRouter(prefix="/api/analytics-ai", tags=["analytics_ai"])

require_fb_ads_module = require_module("fb_ads")
require_analytics_view = require_permission("fb_ads:analytics:view")


def _ensure_team_membership(db, user: User, team_id: Optional[str]) -> None:
    if not team_id or user.is_super_admin:
        return
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this team")


class SnapshotCreatePayload(BaseModel):
    account_id: str
    team_id: Optional[str] = None
    level: str
    date_since: str
    date_until: str
    payload: Dict[str, Any]


class AiSummaryPayload(BaseModel):
    ai_summary: str


def _serialize(row) -> dict:
    return {
        "snapshot_id": row.id,
        "account_id": row.account_id,
        "level": row.level,
        "date_since": row.date_since,
        "date_until": row.date_until,
        "payload": row.payload,
        "ai_summary": row.ai_summary,
        "ai_summary_generated_at": row.ai_summary_generated_at,
        "created_at": row.created_at,
    }


def _serialize_shared(row) -> dict:
    """公開分享端點專用序列化：不回傳 team_id/created_by 等內部資訊。"""
    return {
        "account_id": row.account_id,
        "level": row.level,
        "date_since": row.date_since,
        "date_until": row.date_until,
        "payload": row.payload,
        "ai_summary": row.ai_summary,
        "ai_summary_generated_at": row.ai_summary_generated_at,
    }


@router.post("/snapshots", dependencies=[Depends(require_fb_ads_module), Depends(require_analytics_view)])
def create_snapshot(
    body: SnapshotCreatePayload,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    _ensure_team_membership(db, user, body.team_id)
    row = analytics_ai_repository.create_snapshot(
        db,
        account_id=body.account_id,
        team_id=body.team_id,
        level=body.level,
        date_since=body.date_since,
        date_until=body.date_until,
        payload=body.payload,
        created_by=user.id,
    )
    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.put("/snapshots/{snapshot_id}/ai-summary", dependencies=[Depends(require_fb_ads_module), Depends(require_analytics_view)])
def save_ai_summary(
    snapshot_id: str,
    body: AiSummaryPayload,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    row = analytics_ai_repository.update_ai_summary(db, snapshot_id=snapshot_id, ai_summary=body.ai_summary)
    if not row:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    db.commit()
    db.refresh(row)
    return _serialize(row)


@router.post("/snapshots/{snapshot_id}/share", dependencies=[Depends(require_fb_ads_module), Depends(require_analytics_view)])
def create_share_link(
    snapshot_id: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    row = analytics_ai_repository.get_or_create_share_token(db, snapshot_id=snapshot_id)
    if not row:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    db.commit()
    db.refresh(row)
    return {"snapshot_id": row.id, "share_token": row.share_token}


@router.get("/share/{token}")
def get_shared_snapshot(token: str, db=Depends(get_db)):
    """公開分享端點：無需登入即可取得快照數據與 AI 解讀。"""
    row = analytics_ai_repository.get_snapshot_by_share_token(db, token)
    if not row:
        raise HTTPException(status_code=404, detail="Shared snapshot not found")
    return _serialize_shared(row)
