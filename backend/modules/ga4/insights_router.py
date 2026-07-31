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
    require_ga4_resource_access_or_404,
    verify_ga4_property_access_or_403,
)
from .insights_service import LANDING_PAGE_KEY_EVENT_PATTERN, GA4InsightsService

router = APIRouter()


class RulePayload(BaseModel):
    property_id: str = Field(..., min_length=1)
    metric_key: str = Field(..., min_length=1)
    # docs/52：只有 metric_key=="conversions" 時才有意義，None＝全部關鍵事件
    # （現況）。格式沿用到達頁既有的關鍵事件白名單（LANDING_PAGE_KEY_EVENT_PATTERN）。
    key_event: str | None = None
    sensitivity: str = "medium"
    check_frequency: str = "hourly"
    is_enabled: bool = True
    notify_line: bool = True
    notify_email: bool = False
    cooldown_hours: int = 6

    @field_validator("key_event")
    @classmethod
    def _validate_key_event(cls, value: str | None, info):
        if value is None:
            return value
        if not LANDING_PAGE_KEY_EVENT_PATTERN.match(value):
            raise ValueError(f"Invalid key_event: {value}")
        if info.data.get("metric_key") != "conversions":
            raise ValueError("key_event is only supported when metric_key is 'conversions'")
        return value


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


# 第 5 波：到達頁分類規則（enum 用 Literal，非法值 422，同第 4 波前例）。
LandingPageCategory = Literal["product", "article", "functional", "other"]
LandingPageMatchType = Literal["prefix", "contains"]


class LandingPageRulePayload(BaseModel):
    # PUT 走「有 id 就更新、沒有就新增」的 upsert 語意（同 KPI 目標頁籤的
    # 表單模式，但規則沒有天然的複合唯一鍵可比對，改用 id 判斷）。
    id: str | None = None
    property_id: str = Field(..., min_length=1)
    category: LandingPageCategory
    match_type: LandingPageMatchType
    pattern: str = Field(..., min_length=1, max_length=200)
    priority: int = Field(0, ge=0)


# 第 7 波：商品分類補充規則。分類是自由文字（比照商店既有分類命名，不像
# 到達頁固定 4 類），只有 match_type 用 Literal 驗證。
ItemCategoryMatchType = Literal["prefix", "contains"]


class ItemCategoryRulePayload(BaseModel):
    id: str | None = None
    property_id: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=50)
    match_type: ItemCategoryMatchType
    pattern: str = Field(..., min_length=1, max_length=200)
    priority: int = Field(0, ge=0)


# docs/44：渠道值自訂分組規則。group_label 是自由文字（比照商品分類，不像
# 到達頁固定 4 類），match_type 比到達頁/商品規則多一個 exact——自訂分組
# 常見情境是先精確排除幾個已知例外值，不像分類規則通常用 prefix/contains
# 就夠。channel_dimension 沿用渠道對照既有的白名單，規則綁定單一維度
# （docs/43 定案，不跨維度共用）。
ChannelGroupMatchType = Literal["exact", "prefix", "contains"]


class ChannelGroupRulePayload(BaseModel):
    id: str | None = None
    property_id: str = Field(..., min_length=1)
    channel_dimension: ChannelDimension
    group_label: str = Field(..., min_length=1, max_length=100)
    match_type: ChannelGroupMatchType
    pattern: str = Field(..., min_length=1, max_length=200)
    priority: int = Field(0, ge=0)


def _verify_rule_not_moved_across_properties(
    db, *, user, resource: str, rule_id: str, property_id: str,
):
    """規則類 PUT（upsert-by-id）的既有列檢查（docs/60）。

    兩件事一起做：
    1. 既有列的 property 必須對呼叫者可存取，否則回 404（與「規則不存在」
       同訊息，見 `require_ga4_resource_access_or_404`）。
    2. 既有列的 property 必須與請求帶的 property_id 相同。原本的 upsert 會
       直接覆寫 `row.property_id`，等於允許把一條規則搬到另一個 property
       底下——即使兩邊都有權限，這也不是「更新規則」該有的語意，一律視為
       錯誤（docs/59 P0-3）。
    """
    row = require_ga4_resource_access_or_404(db, user=user, resource=resource, resource_id=rule_id)
    if row.property_id != property_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot move an existing rule to a different property",
        )
    return row


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
    key_event: str | None = Query(None, pattern=r"^[A-Za-z0-9_]{1,40}$"),
    # docs/42+44：到達頁渠道篩選。channel_value（單一精確值）與 channel_group
    # （docs/43 自訂分組）互斥，是否成對/互斥提供由 service 層驗證
    # （ValueError 統一在下面轉成 400），這裡只負責型別/白名單/長度層級的
    # 基本驗證。
    channel_dimension: ChannelDimension | None = Query(None),
    channel_value: str | None = Query(None, max_length=100),
    channel_group: str | None = Query(None, max_length=100),
    compare: bool = Query(False),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    try:
        snapshot = GA4InsightsService.get_landing_pages(
            db, user=user, property_id=property_id, days=days, key_event=key_event,
            channel_dimension=channel_dimension, channel_value=channel_value,
            channel_group=channel_group, compare=compare,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(snapshot)
    return serialize_snapshot(snapshot)


# ─── 第 5 波：到達頁分類規則（docs/22 5 節，追加） ──────────────────
@router.get("/landing-page-rules")
def list_landing_page_rules(
    property_id: str = Query(...),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    verify_ga4_property_access_or_403(db, user=user, property_id=property_id)
    rows = GA4InsightsService.list_landing_page_rules(db, property_id=property_id)
    return {"rules": [serialize_landing_page_rule(row) for row in rows]}


@router.put("/landing-page-rules")
def upsert_landing_page_rule(
    payload: LandingPageRulePayload,
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_manage_alerts),
    db=Depends(get_db),
):
    verify_ga4_property_access_or_403(db, user=user, property_id=payload.property_id)
    if payload.id:
        _verify_rule_not_moved_across_properties(
            db, user=user, resource="landing_page_rule",
            rule_id=payload.id, property_id=payload.property_id,
        )
    row = GA4InsightsService.upsert_landing_page_rule(
        db,
        rule_id=payload.id,
        user_id=user.id,
        property_id=payload.property_id,
        category=payload.category,
        match_type=payload.match_type,
        pattern=payload.pattern,
        priority=payload.priority,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Landing page rule not found")
    db.commit()
    db.refresh(row)
    return serialize_landing_page_rule(row)


@router.delete("/landing-page-rules/{rule_id}")
def delete_landing_page_rule(
    rule_id: str,
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_manage_alerts),
    db=Depends(get_db),
):
    require_ga4_resource_access_or_404(db, user=user, resource="landing_page_rule", resource_id=rule_id)
    deleted = GA4InsightsService.delete_landing_page_rule(db, rule_id=rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Landing page rule not found")
    db.commit()
    return {"status": "deleted", "rule_id": rule_id}


# ─── docs/44：渠道值自訂分組規則 ────────────────────────────────────
@router.get("/channel-group-rules")
def list_channel_group_rules(
    property_id: str = Query(...),
    channel_dimension: ChannelDimension | None = Query(None),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    verify_ga4_property_access_or_403(db, user=user, property_id=property_id)
    rows = GA4InsightsService.list_channel_group_rules(
        db, property_id=property_id, channel_dimension=channel_dimension
    )
    return {"rules": [serialize_channel_group_rule(row) for row in rows]}


@router.put("/channel-group-rules")
def upsert_channel_group_rule(
    payload: ChannelGroupRulePayload,
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_manage_alerts),
    db=Depends(get_db),
):
    verify_ga4_property_access_or_403(db, user=user, property_id=payload.property_id)
    if payload.id:
        _verify_rule_not_moved_across_properties(
            db, user=user, resource="channel_group_rule",
            rule_id=payload.id, property_id=payload.property_id,
        )
    try:
        row = GA4InsightsService.upsert_channel_group_rule(
            db,
            rule_id=payload.id,
            user_id=user.id,
            property_id=payload.property_id,
            channel_dimension=payload.channel_dimension,
            group_label=payload.group_label,
            match_type=payload.match_type,
            pattern=payload.pattern,
            priority=payload.priority,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not row:
        raise HTTPException(status_code=404, detail="Channel group rule not found")
    db.commit()
    db.refresh(row)
    return serialize_channel_group_rule(row)


@router.delete("/channel-group-rules/{rule_id}")
def delete_channel_group_rule(
    rule_id: str,
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_manage_alerts),
    db=Depends(get_db),
):
    require_ga4_resource_access_or_404(db, user=user, resource="channel_group_rule", resource_id=rule_id)
    deleted = GA4InsightsService.delete_channel_group_rule(db, rule_id=rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Channel group rule not found")
    db.commit()
    return {"status": "deleted", "rule_id": rule_id}


@router.get("/channel-groups")
def list_channel_groups(
    property_id: str = Query(...),
    channel_dimension: ChannelDimension = Query(...),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    """依 group_label 去重列出某維度底下已定義的分組，供前端「自訂分組」
    下拉選單使用（docs/43：新增規則後自動出現在下拉裡，不用另外維護選單）。"""
    verify_ga4_property_access_or_403(db, user=user, property_id=property_id)
    groups = GA4InsightsService.list_channel_groups(
        db, property_id=property_id, channel_dimension=channel_dimension
    )
    return {"groups": groups}


@router.get("/items")
def get_items(
    property_id: str = Query(...),
    days: int = Query(7, ge=1, le=90),
    # docs/45：商品渠道篩選，比照到達頁（42+44），channel_value/channel_group
    # 互斥的驗證在 service 層做（ValueError 統一轉 400）。
    channel_dimension: ChannelDimension | None = Query(None),
    channel_value: str | None = Query(None, max_length=100),
    channel_group: str | None = Query(None, max_length=100),
    compare: bool = Query(False),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    try:
        snapshot = GA4InsightsService.get_items(
            db, user=user, property_id=property_id, days=days,
            channel_dimension=channel_dimension, channel_value=channel_value,
            channel_group=channel_group, compare=compare,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(snapshot)
    return serialize_snapshot(snapshot)


# ─── docs/47：商品頁面與商品轉換率交叉對照 ──────────────────────────
@router.get("/item-landing-cross")
def get_item_landing_cross(
    property_id: str = Query(...),
    days: int = Query(7, ge=1, le=90),
    compare: bool = Query(False),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    try:
        snapshot = GA4InsightsService.get_item_landing_cross(db, user=user, property_id=property_id, days=days, compare=compare)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(snapshot)
    return serialize_snapshot(snapshot)


# ─── 第 7 波：商品分類補充規則（docs/22 5 節，追加） ────────────────
@router.get("/item-category-rules")
def list_item_category_rules(
    property_id: str = Query(...),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    verify_ga4_property_access_or_403(db, user=user, property_id=property_id)
    rows = GA4InsightsService.list_item_category_rules(db, property_id=property_id)
    return {"rules": [serialize_item_category_rule(row) for row in rows]}


@router.put("/item-category-rules")
def upsert_item_category_rule(
    payload: ItemCategoryRulePayload,
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_manage_alerts),
    db=Depends(get_db),
):
    verify_ga4_property_access_or_403(db, user=user, property_id=payload.property_id)
    if payload.id:
        _verify_rule_not_moved_across_properties(
            db, user=user, resource="item_category_rule",
            rule_id=payload.id, property_id=payload.property_id,
        )
    row = GA4InsightsService.upsert_item_category_rule(
        db,
        rule_id=payload.id,
        user_id=user.id,
        property_id=payload.property_id,
        category=payload.category,
        match_type=payload.match_type,
        pattern=payload.pattern,
        priority=payload.priority,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Item category rule not found")
    db.commit()
    db.refresh(row)
    return serialize_item_category_rule(row)


@router.delete("/item-category-rules/{rule_id}")
def delete_item_category_rule(
    rule_id: str,
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_manage_alerts),
    db=Depends(get_db),
):
    require_ga4_resource_access_or_404(db, user=user, resource="item_category_rule", resource_id=rule_id)
    deleted = GA4InsightsService.delete_item_category_rule(db, rule_id=rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item category rule not found")
    db.commit()
    return {"status": "deleted", "rule_id": rule_id}


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
    require_ga4_resource_access_or_404(db, user=user, resource="snapshot", resource_id=snapshot_id)
    row = GA4InsightsService.save_ai_summary(db, snapshot_id=snapshot_id, ai_summary=payload.ai_summary)
    if not row:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    db.commit()
    db.refresh(row)
    return serialize_snapshot(row)


# ─── docs/39：快照分享連結 ───────────────────────────────────────────
@router.post("/snapshots/{snapshot_id}/share")
def create_snapshot_share_link(
    snapshot_id: str,
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    require_ga4_resource_access_or_404(db, user=user, resource="snapshot", resource_id=snapshot_id)
    row = GA4InsightsService.create_share_link(db, snapshot_id=snapshot_id)
    if not row:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    db.commit()
    db.refresh(row)
    return {"snapshot_id": row.id, "share_token": row.share_token}


@router.get("/share/{token}")
def get_shared_snapshot(token: str, db=Depends(get_db)):
    """公開分享端點：無需登入即可取得快照數據與 AI 解讀。"""
    row = GA4InsightsService.get_snapshot_by_share_token(db, token)
    if not row:
        raise HTTPException(status_code=404, detail="Shared snapshot not found")
    return serialize_shared_snapshot(row)


# ─── 第 3 波：KPI 目標追蹤（選配，docs/22 5 節） ───────────────────────
@router.get("/kpi-targets")
def list_kpi_targets(
    property_id: str = Query(...),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    verify_ga4_property_access_or_403(db, user=user, property_id=property_id)
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
    verify_ga4_property_access_or_403(db, user=user, property_id=payload.property_id)
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
    require_ga4_resource_access_or_404(db, user=user, resource="kpi_target", resource_id=target_id)
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


# docs/52：告警規則「轉換」的關鍵事件下拉選單來源，近 7 天、使用者開表單時
# 才呼叫一次，不進排程，跟規則本身的 check_frequency 無關。
@router.get("/anomaly-rules/available-key-events")
def list_anomaly_rule_available_key_events(
    property_id: str = Query(...),
    user=Depends(get_current_user),
    _module: bool = Depends(require_ga4_module),
    _perm: bool = Depends(require_ga4_insights_view),
    db=Depends(get_db),
):
    try:
        events = GA4InsightsService.list_available_key_events(db, user=user, property_id=property_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"events": events}


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
    rows, total, unacknowledged_total = GA4InsightsService.list_events(
        db,
        user_id=user.id,
        property_id=property_id,
        page=page,
        page_size=page_size,
    )
    return {
        "events": [serialize_event(row) for row in rows],
        "total": total,
        "unacknowledged_total": unacknowledged_total,
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


def serialize_landing_page_rule(row):
    return {
        "id": row.id,
        "property_id": row.property_id,
        "category": row.category,
        "match_type": row.match_type,
        "pattern": row.pattern,
        "priority": row.priority,
        "created_by": row.created_by,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def serialize_item_category_rule(row):
    return {
        "id": row.id,
        "property_id": row.property_id,
        "category": row.category,
        "match_type": row.match_type,
        "pattern": row.pattern,
        "priority": row.priority,
        "created_by": row.created_by,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def serialize_channel_group_rule(row):
    return {
        "id": row.id,
        "property_id": row.property_id,
        "channel_dimension": row.channel_dimension,
        "group_label": row.group_label,
        "match_type": row.match_type,
        "pattern": row.pattern,
        "priority": row.priority,
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


def serialize_shared_snapshot(row):
    """公開分享端點專用序列化：不回傳 fetched_by 等內部使用者資訊。
    docs/47 追加：property_id 改回傳（比照 docs/39 原計劃），讓分享連結能顯示
    是哪個 GA4 屬性的資料——這個值本來就存在快照列上，不用額外查 GA4 API。"""
    return {
        "property_id": row.property_id,
        "kind": row.kind,
        "date": row.date,
        "payload": row.payload,
        "ai_summary": row.ai_summary,
        "ai_summary_generated_at": row.ai_summary_generated_at,
    }


def serialize_rule(row):
    return {
        "id": row.id,
        "property_id": row.property_id,
        "metric_key": row.metric_key,
        "key_event": row.key_event,
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
        "key_event": row.rule.key_event if row.rule else None,
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
