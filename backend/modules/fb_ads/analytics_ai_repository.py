"""Persistence helpers for the 成效分析 AI insight snapshot (docs/58)."""

from __future__ import annotations

import uuid
from datetime import datetime

from database.models.fb_ads import FbAdsAnalyticsAiSnapshot


class AnalyticsAiRepository:
    def create_snapshot(
        self, db, *, account_id: str, team_id: str | None, level: str,
        date_since: str, date_until: str, payload: dict, created_by: str,
    ):
        row = FbAdsAnalyticsAiSnapshot(
            account_id=account_id,
            team_id=team_id,
            level=level,
            date_since=date_since,
            date_until=date_until,
            payload=payload,
            created_by=created_by,
        )
        db.add(row)
        db.flush()
        return row

    def get_snapshot_by_id(self, db, snapshot_id: str):
        return db.query(FbAdsAnalyticsAiSnapshot).filter(FbAdsAnalyticsAiSnapshot.id == snapshot_id).first()

    def update_ai_summary(self, db, *, snapshot_id: str, ai_summary: str):
        row = self.get_snapshot_by_id(db, snapshot_id)
        if not row:
            return None
        row.ai_summary = ai_summary
        row.ai_summary_generated_at = datetime.utcnow()
        db.add(row)
        return row

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
        return db.query(FbAdsAnalyticsAiSnapshot).filter(FbAdsAnalyticsAiSnapshot.share_token == token).first()


analytics_ai_repository = AnalyticsAiRepository()
