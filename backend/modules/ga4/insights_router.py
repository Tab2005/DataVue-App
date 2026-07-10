"""GA4 insights API endpoints."""

from __future__ import annotations

import re
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

from database import get_db

from .dependencies import (
    get_current_user,
    require_ga4_insights_manage_alerts,
    require_ga4_insights_view,
    require_ga4_module,
)
from .insights_service import GA4InsightsService

router = APIRouter()


class RulePayload(BaseModel):
    property_id: str = Field(..., min_length=1)
    metric_key: str = Field(..., min_length=1)
    sensitivity: str = "medium"
    check_frequency: str = "hourly"
    is_enabled: bool = True
    notify_line: bool = True
    notify_email: bool = False
    cooldown_hours: int = 6


class EventAckPayload(BaseModel):
    acknowledged: bool = True


class PropertyIdPayload(BaseModel):
    property_id: str = Field(..., min_length=1)


class AiSummaryPayload(BaseModel):
    ai_summary: str = Field(..., min_length=1)


_MONTH_KEY_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_QUARTER_KEY_RE = re.compile(r"^\d{4}-Q[1-4]$")


class KpiTargetPayload(BaseModel):
    property_id: str = Field(..., min_length=1)
    metric_key: str = Field(..., min_length=1)
    period_type: str = Field(..., pattern="^(month|quarter)$")
    period_key: str = Field(..., min_length=1)
    target_value: float = Field(..., gt=0)

    @field_validator("period_key")
    @classmethod
    def _validate_period_key(cls, value: str, info):
        period_type = info.data.get("period_type")
        if period_type == "month" and not _MONTH_KEY_RE.match(value):
            raise ValueError("period_key must look like YYYY-MM when period_type is 'month'")
        if period_type == "quarter" and not _QUARTER_KEY_RE.match(value):
            raise ValueError("period_key must look like YYYY-Qn when period_type is 'quarter'")
        return value


# 第 4 波：渠道對照維度切換白名單（非白名單值 FastAPI/pydantic 自動回 422）。
ChannelDimension = Literal["default_channel_group", "source_medium", "source", "medium", "campaign"]


# ─── 第 2 波：當日儀表板／Realtime／渠道／到達頁／商品（docs/22 3.5 節） ───
@router.get("/dashboard")
def get_dashboard(
    property_id: str = Query(...),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    try:
        snapshot = GA4InsightsService.get_dashboard(db, user=user, property_id=property_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(snapshot)
    return serialize_snapshot(snapshot)


@router.post("/dashboard/refresh")
def refresh_dashboard(
    payload: PropertyIdPayload,
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    try:
        snapshot, refreshed = GA4InsightsService.refresh_dashboard(db, user=user, property_id=payload.property_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(snapshot)
    return {**serialize_snapshot(snapshot), "refreshed": refreshed}


@router.get("/realtime")
def get_realtime(
    property_id: str = Query(...),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    try:
        return GA4InsightsService.get_realtime(user=user, property_id=property_id, db=db)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/channels")
def get_channels(
    property_id: str = Query(...),
    days: int = Query(7, ge=1, le=90),
    dimension: ChannelDimension = Query("default_channel_group"),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    try:
        snapshot = GA4InsightsService.get_channels(
            db, user=user, property_id=property_id, days=days, dimension=dimension
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(snapshot)
    return serialize_snapshot(snapshot)


@router.get("/landing-pages")
def get_landing_pages(
    property_id: str = Query(...),
    days: int = Query(7, ge=1, le=90),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    try:
        snapshot = GA4InsightsService.get_landing_pages(db, user=user, property_id=property_id, days=days)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(snapshot)
    return serialize_snapshot(snapshot)


@router.get("/items")
def get_items(
    property_id: str = Query(...),
    days: int = Query(7, ge=1, le=90),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    try:
        snapshot = GA4InsightsService.get_items(db, user=user, property_id=property_id, days=days)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(snapshot)
    return serialize_snapshot(snapshot)


# ─── 第 2 波任務 2.4：AI 白話解讀持久化 ─────────────────────────────
@router.put("/snapshots/{snapshot_id}/ai-summary")
def save_ai_summary(
    snapshot_id: str,
    payload: AiSummaryPayload,
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    row = GA4InsightsService.save_ai_summary(db, snapshot_id=snapshot_id, ai_summary=payload.ai_summary)
    if not row:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    db.commit()
    db.refresh(row)
    return serialize_snapshot(row)


# ─── 第 3 波：KPI 目標追蹤（選配，docs/22 5 節） ───────────────────────
@router.get("/kpi-targets")
def list_kpi_targets(
    property_id: str = Query(...),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    targets = GA4InsightsService.get_kpi_targets_with_pacing(db, user=user, property_id=property_id)
    return {"targets": targets}


@router.put("/kpi-targets")
def upsert_kpi_target(
    payload: KpiTargetPayload,
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_manage_alerts),
    db=Depends(get_db),
):
    row = GA4InsightsService.upsert_kpi_target(
        db,
        user_id=user.id,
        property_id=payload.property_id,
        metric_key=payload.metric_key,
        period_type=payload.period_type,
        period_key=payload.period_key,
        target_value=payload.target_value,
    )
    db.commit()
    db.refresh(row)
    return serialize_kpi_target(row)


@router.delete("/kpi-targets/{target_id}")
def delete_kpi_target(
    target_id: str,
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_manage_alerts),
    db=Depends(get_db),
):
    deleted = GA4InsightsService.delete_kpi_target(db, target_id=target_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="KPI target not found")
    db.commit()
    return {"status": "deleted", "target_id": target_id}


@router.get("/anomaly-rules")
def list_anomaly_rules(
    property_id: str | None = Query(None),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    rows = GA4InsightsService.list_rules(db, user_id=user.id, property_id=property_id)
    return {"rules": [serialize_rule(row) for row in rows]}


@router.post("/anomaly-rules", status_code=status.HTTP_201_CREATED)
def create_anomaly_rule(
    payload: RulePayload,
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_manage_alerts),
    db=Depends(get_db),
):
    row = GA4InsightsService.create_rule(db, user_id=user.id, payload=payload.model_dump())
    db.commit()
    db.refresh(row)
    return serialize_rule(row)


@router.put("/anomaly-rules/{rule_id}")
def update_anomaly_rule(
    rule_id: str,
    payload: RulePayload,
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_manage_alerts),
    db=Depends(get_db),
):
    row = GA4InsightsService.update_rule(db, rule_id=rule_id, user_id=user.id, payload=payload.model_dump())
    if not row:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.commit()
    db.refresh(row)
    return serialize_rule(row)


@router.delete("/anomaly-rules/{rule_id}")
def delete_anomaly_rule(
    rule_id: str,
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_manage_alerts),
    db=Depends(get_db),
):
    deleted = GA4InsightsService.delete_rule(db, rule_id=rule_id, user_id=user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.commit()
    return {"status": "deleted", "rule_id": rule_id}


@router.get("/anomaly-events")
def list_anomaly_events(
    property_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    rows, total = GA4InsightsService.list_events(
        db,
        user_id=user.id,
        property_id=property_id,
        page=page,
        page_size=page_size,
    )
    return {
        "events": [serialize_event(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/anomaly-events/{event_id}/ack")
def acknowledge_event(
    event_id: str,
    _payload: EventAckPayload,
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    row = GA4InsightsService.acknowledge_event(db, event_id=event_id, user_id=user.id)
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    db.commit()
    db.refresh(row)
    return serialize_event(row)


def serialize_kpi_target(row):
    return {
        "id": row.id,
        "property_id": row.property_id,
        "metric_key": row.metric_key,
        "period_type": row.period_type,
        "period_key": row.period_key,
        "target_value": row.target_value,
        "created_by": row.created_by,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def serialize_snapshot(row):
    return {
        "snapshot_id": row.id,
        "property_id": row.property_id,
        "kind": row.kind,
        "date": row.date,
        "payload": row.payload,
        "ai_summary": row.ai_summary,
        "ai_summary_generated_at": row.ai_summary_generated_at,
        "fetched_at": row.fetched_at,
    }


def serialize_rule(row):
    return {
        "id": row.id,
        "property_id": row.property_id,
        "metric_key": row.metric_key,
        "sensitivity": row.sensitivity,
        "check_frequency": row.check_frequency,
        "is_enabled": row.is_enabled,
        "notify_line": row.notify_line,
        "notify_email": row.notify_email,
        "cooldown_hours": row.cooldown_hours,
        "created_by": row.created_by,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def serialize_event(row):
    return {
        "id": row.id,
        "rule_id": row.rule_id,
        "property_id": row.rule.property_id if row.rule else None,
        "metric_key": row.rule.metric_key if row.rule else None,
        "severity": row.severity,
        "direction": row.direction,
        "observed_value": row.observed_value,
        "expected_low": row.expected_low,
        "expected_high": row.expected_high,
        "message": row.message,
        "notified_channels": row.notified_channels or {},
        "acknowledged_by": row.acknowledged_by,
        "acknowledged_at": row.acknowledged_at,
        "created_at": row.created_at,
    }
