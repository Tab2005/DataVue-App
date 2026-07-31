"""GA4 insights persistence helpers."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import desc

from database.models.ga4_insights import (
    GA4AnomalyEvent,
    GA4AnomalyRule,
    GA4ChannelGroupRule,
    GA4InsightsSnapshot,
    GA4ItemCategoryRule,
    GA4KpiTarget,
    GA4LandingPageRule,
)


class GA4InsightsRepository:
    def upsert_snapshot(self, db, *, property_id: str, kind: str, date: str, payload: dict, fetched_by: str | None):
        row = (
            db.query(GA4InsightsSnapshot)
            .filter(
                GA4InsightsSnapshot.property_id == property_id,
                GA4InsightsSnapshot.kind == kind,
                GA4InsightsSnapshot.date == date,
            )
            .first()
        )
        if row:
            row.payload = payload
            row.fetched_by = fetched_by
            row.fetched_at = datetime.utcnow()
            row.ai_summary = None
            row.ai_summary_generated_at = None
            db.add(row)
            return row

        row = GA4InsightsSnapshot(
            property_id=property_id,
            kind=kind,
            date=date,
            payload=payload,
            fetched_by=fetched_by,
        )
        db.add(row)
        db.flush()
        return row

    def get_latest_snapshot(self, db, *, property_id: str, kind: str, date: str | None = None):
        query = db.query(GA4InsightsSnapshot).filter(
            GA4InsightsSnapshot.property_id == property_id,
            GA4InsightsSnapshot.kind == kind,
        )
        if date:
            query = query.filter(GA4InsightsSnapshot.date == date)
        return query.order_by(desc(GA4InsightsSnapshot.fetched_at)).first()

    def get_snapshot_by_id(self, db, snapshot_id: str):
        return db.query(GA4InsightsSnapshot).filter(GA4InsightsSnapshot.id == snapshot_id).first()

    def user_has_fetched_property(self, db, *, user_id: str, property_id: str) -> bool:
        """這個使用者是否曾經親自抓過這個 property 的快照（docs/60 授權檢查用）。

        快照列只會在 `GA4Service.get_analytics` 成功回傳後才寫入（見
        `insights/landing_pages.py` 等各查詢的 `if error: raise` 前置），
        而 GA4 憑證是 per-user OAuth（`user.ga4_access_token`），所以
        「有一筆 fetched_by == 我的快照」等同「我自己的 Google 帳號讀得到
        這個 property」——可以直接當授權判斷的快取，不必每次都打 Admin API。
        """
        row = (
            db.query(GA4InsightsSnapshot.id)
            .filter(
                GA4InsightsSnapshot.property_id == property_id,
                GA4InsightsSnapshot.fetched_by == user_id,
            )
            .first()
        )
        return row is not None

    def update_ai_summary(self, db, *, snapshot_id: str, ai_summary: str):
        row = self.get_snapshot_by_id(db, snapshot_id)
        if not row:
            return None
        row.ai_summary = ai_summary
        row.ai_summary_generated_at = datetime.utcnow()
        db.add(row)
        return row

    # ─── docs/39：快照分享連結 ─────────────────────────────────────────
    def get_or_create_share_token(self, db, *, snapshot_id: str):
        row = self.get_snapshot_by_id(db, snapshot_id)
        if not row:
            return None
        if not row.share_token:
            row.share_token = uuid.uuid4().hex
            db.add(row)
            db.flush()
        return row

    def get_snapshot_by_share_token(self, db, token: str):
        return db.query(GA4InsightsSnapshot).filter(GA4InsightsSnapshot.share_token == token).first()

    def create_rule(self, db, **payload):
        row = GA4AnomalyRule(**payload)
        db.add(row)
        db.flush()
        return row

    def list_rules(self, db, *, created_by: str | None = None, property_id: str | None = None):
        query = db.query(GA4AnomalyRule)
        if created_by:
            query = query.filter(GA4AnomalyRule.created_by == created_by)
        if property_id:
            query = query.filter(GA4AnomalyRule.property_id == property_id)
        return query.order_by(desc(GA4AnomalyRule.updated_at), desc(GA4AnomalyRule.created_at)).all()

    def get_rule(self, db, rule_id: str):
        return db.query(GA4AnomalyRule).filter(GA4AnomalyRule.id == rule_id).first()

    def delete_rule(self, db, rule_id: str) -> bool:
        row = self.get_rule(db, rule_id)
        if not row:
            return False
        db.query(GA4AnomalyEvent).filter(GA4AnomalyEvent.rule_id == rule_id).delete()
        db.delete(row)
        return True

    def list_enabled_rules(self, db, *, frequency: str):
        return (
            db.query(GA4AnomalyRule)
            .filter(
                GA4AnomalyRule.is_enabled == True,
                GA4AnomalyRule.check_frequency == frequency,
            )
            .all()
        )

    def create_event(self, db, **payload):
        row = GA4AnomalyEvent(**payload)
        db.add(row)
        db.flush()
        return row

    def get_event(self, db, event_id: str):
        return db.query(GA4AnomalyEvent).filter(GA4AnomalyEvent.id == event_id).first()

    def list_events(self, db, *, property_id: str | None = None, created_by: str | None = None, page: int = 1, page_size: int = 20):
        query = db.query(GA4AnomalyEvent).join(GA4AnomalyRule, GA4AnomalyRule.id == GA4AnomalyEvent.rule_id)
        if property_id:
            query = query.filter(GA4AnomalyRule.property_id == property_id)
        if created_by:
            query = query.filter(GA4AnomalyRule.created_by == created_by)
        total = query.count()
        # 未讀總數不受分頁影響，讓前端的「N 則未讀告警」提示可以獨立於目前顯示的分頁。
        unacknowledged_total = query.filter(GA4AnomalyEvent.acknowledged_at.is_(None)).count()
        rows = (
            query.order_by(desc(GA4AnomalyEvent.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return rows, total, unacknowledged_total

    def acknowledge_event(self, db, *, event_id: str, user_id: str):
        row = self.get_event(db, event_id)
        if not row:
            return None
        row.acknowledged_by = user_id
        row.acknowledged_at = datetime.utcnow()
        db.add(row)
        return row

    # ─── 第 3 波：KPI 目標（property × 指標 × 月/季） ──────────────────
    def upsert_kpi_target(
        self, db, *, property_id: str, metric_key: str, period_type: str,
        period_key: str, target_value: float, created_by: str,
    ):
        row = (
            db.query(GA4KpiTarget)
            .filter(
                GA4KpiTarget.property_id == property_id,
                GA4KpiTarget.metric_key == metric_key,
                GA4KpiTarget.period_type == period_type,
                GA4KpiTarget.period_key == period_key,
            )
            .first()
        )
        if row:
            row.target_value = target_value
            row.updated_at = datetime.utcnow()
            db.add(row)
            return row

        row = GA4KpiTarget(
            property_id=property_id,
            metric_key=metric_key,
            period_type=period_type,
            period_key=period_key,
            target_value=target_value,
            created_by=created_by,
        )
        db.add(row)
        db.flush()
        return row

    def list_kpi_targets(self, db, *, property_id: str):
        return (
            db.query(GA4KpiTarget)
            .filter(GA4KpiTarget.property_id == property_id)
            .order_by(desc(GA4KpiTarget.period_key))
            .all()
        )

    def get_kpi_target(self, db, target_id: str):
        return db.query(GA4KpiTarget).filter(GA4KpiTarget.id == target_id).first()

    def delete_kpi_target(self, db, target_id: str) -> bool:
        row = self.get_kpi_target(db, target_id)
        if not row:
            return False
        db.delete(row)
        return True

    # ─── 第 5 波：到達頁分類規則 ────────────────────────────────────────
    def create_landing_page_rule(self, db, **payload):
        row = GA4LandingPageRule(**payload)
        db.add(row)
        db.flush()
        return row

    def list_landing_page_rules(self, db, *, property_id: str):
        return (
            db.query(GA4LandingPageRule)
            .filter(GA4LandingPageRule.property_id == property_id)
            .order_by(GA4LandingPageRule.priority.asc())
            .all()
        )

    def get_landing_page_rule(self, db, rule_id: str):
        return db.query(GA4LandingPageRule).filter(GA4LandingPageRule.id == rule_id).first()

    def delete_landing_page_rule(self, db, rule_id: str) -> bool:
        row = self.get_landing_page_rule(db, rule_id)
        if not row:
            return False
        db.delete(row)
        return True

    # ─── 第 7 波：商品分類補充規則 ──────────────────────────────────────
    def create_item_category_rule(self, db, **payload):
        row = GA4ItemCategoryRule(**payload)
        db.add(row)
        db.flush()
        return row

    def list_item_category_rules(self, db, *, property_id: str):
        return (
            db.query(GA4ItemCategoryRule)
            .filter(GA4ItemCategoryRule.property_id == property_id)
            .order_by(GA4ItemCategoryRule.priority.asc())
            .all()
        )

    def get_item_category_rule(self, db, rule_id: str):
        return db.query(GA4ItemCategoryRule).filter(GA4ItemCategoryRule.id == rule_id).first()

    def delete_item_category_rule(self, db, rule_id: str) -> bool:
        row = self.get_item_category_rule(db, rule_id)
        if not row:
            return False
        db.delete(row)
        return True

    # ─── docs/44：渠道值自訂分組規則 ──────────────────────────────────
    def create_channel_group_rule(self, db, **payload):
        row = GA4ChannelGroupRule(**payload)
        db.add(row)
        db.flush()
        return row

    def list_channel_group_rules(self, db, *, property_id: str, channel_dimension: str | None = None):
        query = db.query(GA4ChannelGroupRule).filter(GA4ChannelGroupRule.property_id == property_id)
        if channel_dimension:
            query = query.filter(GA4ChannelGroupRule.channel_dimension == channel_dimension)
        return query.order_by(GA4ChannelGroupRule.priority.asc()).all()

    def get_channel_group_rule(self, db, rule_id: str):
        return db.query(GA4ChannelGroupRule).filter(GA4ChannelGroupRule.id == rule_id).first()

    def delete_channel_group_rule(self, db, rule_id: str) -> bool:
        row = self.get_channel_group_rule(db, rule_id)
        if not row:
            return False
        db.delete(row)
        return True

    def get_recent_event_for_rule(self, db, *, rule_id: str, cooldown_hours: int):
        threshold = datetime.utcnow() - timedelta(hours=max(cooldown_hours, 0))
        return (
            db.query(GA4AnomalyEvent)
            .filter(
                GA4AnomalyEvent.rule_id == rule_id,
                GA4AnomalyEvent.created_at >= threshold,
            )
            .order_by(desc(GA4AnomalyEvent.created_at))
            .first()
        )


repository = GA4InsightsRepository()



