"""
Contribution Module - DB-backed repository（docs/21 任務 1.1 骨架）

第 1 波任務 1.1：僅建立 ORM 存取的最小骨架（snapshot 狀態流轉、daily metrics
upsert、group CRUD 的方法簽名）。實際 upsert / 分組 / 編排邏輯於任務 1.3、1.4
填入；本檔先提供：
  - create_snapshot / get_snapshot / list_snapshots / set_snapshot_status
  - upsert_daily_metrics / list_campaign_summaries
  - get_groups / upsert_groups
並以 stub（raise NotImplementedError）標示本波不實作的部分，讓 router 的 501
路徑有明確的「未實作」邊界，而非散落的空行為。
"""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models.contribution import (
    ContributionCampaignGroup,
    ContributionDailyMetric,
    ContributionSnapshot,
)

logger = logging.getLogger(__name__)


class ContributionRepository:
    """Contribution 模組的 ORM 存取層（單例 repository）。

    本波（1.1）只實作 snapshot 狀態流轉所需的最小方法；其餘為 stub，供任務
    1.3／1.4 填入。所有方法皆不自行 commit，由 service 層控制交易邊界（同
    Meta Andromeda repository 慣例）。"""

    # ── Snapshot CRUD ──────────────────────────────────────────────────
    def create_snapshot(
        self,
        db: Session,
        *,
        account_id: str,
        date_start: str,
        date_end: str,
        config: dict[str, Any],
        created_by: str | None = None,
    ) -> ContributionSnapshot:
        snapshot = ContributionSnapshot(
            account_id=account_id,
            status="queued",
            date_start=date_start,
            date_end=date_end,
            config=config,
            created_by=created_by,
        )
        db.add(snapshot)
        db.flush()
        return snapshot

    def get_snapshot(self, db: Session, snapshot_id: str) -> ContributionSnapshot | None:
        return db.query(ContributionSnapshot).filter(ContributionSnapshot.id == snapshot_id).first()

    def list_snapshots(
        self,
        db: Session,
        *,
        account_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ContributionSnapshot]:
        stmt = (
            select(ContributionSnapshot)
            .where(ContributionSnapshot.account_id == account_id)
            .order_by(ContributionSnapshot.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(db.scalars(stmt).all())

    def set_snapshot_status(
        self,
        db: Session,
        snapshot_id: str,
        *,
        status: str,
        error_message: str | None = None,
        results: dict[str, Any] | None = None,
        diagnostics: dict[str, Any] | None = None,
        runtime_job_id: str | None = None,
    ) -> ContributionSnapshot | None:
        snapshot = self.get_snapshot(db, snapshot_id)
        if snapshot is None:
            return None
        snapshot.status = status
        if error_message is not None:
            snapshot.error_message = error_message
        if results is not None:
            snapshot.results = results
        if diagnostics is not None:
            snapshot.diagnostics = diagnostics
        if runtime_job_id is not None:
            snapshot.runtime_job_id = runtime_job_id
        if status in {"completed", "failed"}:
            snapshot.completed_at = datetime.now(timezone.utc)
        db.add(snapshot)
        db.flush()
        return snapshot

    # ── Daily metrics（任務 1.3 實作 upsert + 彙總） ────────────────────
    def upsert_daily_metrics(
        self,
        db: Session,
        rows: list[dict[str, Any]],
    ) -> int:
        """upsert 活動每日數據；依 (account_id, date, campaign_id, metric_key)
        唯一約束覆寫。任務 1.3 實作。"""
        raise NotImplementedError("upsert_daily_metrics 由任務 1.3 實作")

    def list_campaign_summaries(
        self,
        db: Session,
        *,
        account_id: str,
        metric_key: str = "omni_purchase",
    ) -> list[dict[str, Any]]:
        """由快取表彙總活動近 N 天花費/轉換，供分組 UI。任務 1.3 實作。"""
        raise NotImplementedError("list_campaign_summaries 由任務 1.3 實作")

    # ── Campaign groups（任務 1.4 實作分組讀寫） ────────────────────────
    def get_groups(
        self,
        db: Session,
        *,
        account_id: str,
    ) -> list[ContributionCampaignGroup]:
        """讀取分組；無則回空 list（由 service 觸發自動分組）。任務 1.4 實作。"""
        raise NotImplementedError("get_groups 由任務 1.4 實作")

    def upsert_groups(
        self,
        db: Session,
        *,
        account_id: str,
        groups: list[dict[str, Any]],
        updated_by: str | None = None,
    ) -> list[ContributionCampaignGroup]:
        """整批覆寫分組（前端編輯後提交）。任務 1.4 實作。"""
        raise NotImplementedError("upsert_groups 由任務 1.4 實作")


repository = ContributionRepository()
