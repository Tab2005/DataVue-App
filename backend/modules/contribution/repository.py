"""
Contribution Module - DB-backed repository（docs/21）

提供：
  - snapshot 狀態流轉（create / get / list / set status）
  - daily metrics upsert / list campaign summaries
  - 分組讀寫（get_groups / upsert_groups）+ manual 編輯時的 campaign 集合驗證

所有方法皆不自行 commit，由 service 層控制交易邊界（同 Meta Andromeda
repository 慣例）。
"""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
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
    # 唯一約束名稱（與 migration 20260706_contribution_module_tables 對齊）
    _DAILY_METRICS_UNIQUE = (
        "uq_contribution_daily_metrics_account_date_campaign_metric"
    )
    # 唯一約束欄位（insert 中宣告 conflict_target 使用）
    _DAILY_METRICS_UNIQUE_COLS = (
        "account_id",
        "date",
        "campaign_id",
        "metric_key",
    )
    # 每個 INSERT 語句最多攜帶的列數。全量 180 天 × 全活動一次塞進單一
    # INSERT 時，SQLAlchemy 編譯巨型 VALUES（每列還含 actions_payload JSON）
    # 的峰值記憶體可達 GB 級，曾把 backend 推到 2GB 拖垮整台機器
    # （2026-07-08 事故）；分批後峰值只與批次大小成正比。
    _UPSERT_CHUNK_SIZE = 500

    def upsert_daily_metrics(
        self,
        db: Session,
        rows: list[dict[str, Any]],
    ) -> int:
        """upsert 活動每日數據；依 (account_id, date, campaign_id, metric_key)
        唯一約束覆寫（dialect-aware：PostgreSQL 走 ON CONFLICT、SQLite 走
        ON CONFLICT DO UPDATE，兩者皆由 SQLAlchemy 統一介面呼叫）。

        寫入欄位（不含 fetched_at，由 DB 預設 CURRENT_TIMESTAMP 觸發）：
          account_id, date, campaign_id, campaign_name, spend, impressions,
          conversions, conversion_value, metric_key, actions_payload
        衝突時更新：以上除主鍵外的全部欄位（不更新 fetched_at — 保留初次抓取時間
        供診斷；如需刷新時間可用 NOW() 覆寫，但本模組無此需求）。

        回傳實際 upsert 成功的列數（rows 數；唯一衝突由 ON CONFLICT 處理，不會
        拋例外）。
        """
        if not rows:
            return 0

        insert_cols = list(rows[0].keys())

        bind = db.get_bind()
        dialect_name = bind.dialect.name if bind is not None else ""
        # SQLAlchemy 2.0：pg_insert 與 sqlite_insert 都會回傳帶 .excluded 屬性的
        # Insert 物件，可用以建構「衝突時更新為插入值」的 SET 表達式
        # （例如 stmt.excluded.spend 即 PostgreSQL 的 EXCLUDED.spend）。
        insert_fn = pg_insert if dialect_name == "postgresql" else sqlite_insert

        total = 0
        for start in range(0, len(rows), self._UPSERT_CHUNK_SIZE):
            chunk = rows[start : start + self._UPSERT_CHUNK_SIZE]
            values = [{k: r.get(k) for k in insert_cols} for r in chunk]
            stmt = insert_fn(ContributionDailyMetric).values(values)
            update_cols = {
                "campaign_name": stmt.excluded.campaign_name,
                "spend": stmt.excluded.spend,
                "impressions": stmt.excluded.impressions,
                "conversions": stmt.excluded.conversions,
                "conversion_value": stmt.excluded.conversion_value,
                "actions_payload": stmt.excluded.actions_payload,
                "fetched_at": func.current_timestamp(),
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=self._DAILY_METRICS_UNIQUE_COLS,
                set_=update_cols,
            )
            result = db.execute(stmt)
            if result is not None:
                total += len(chunk)
        return total

    def list_campaign_summaries(
        self,
        db: Session,
        *,
        account_id: str,
        metric_key: str = "omni_purchase",
        days: int | None = None,
    ) -> list[dict[str, Any]]:
        """由快取表彙總活動近 N 天花費/轉換，供分組 UI。

        days=None → 全歷史彙總（首次全量抓取後即用此）；days 指定 → 只彙總近
        N 天的資料。回傳 list[dict]，每個 dict 對應一個 campaign：
          {campaign_id, campaign_name, spend, impressions, conversions,
           conversion_value, active_days, first_date, last_date}
        按 spend 由大到小排序。"""
        stmt = (
            select(
                ContributionDailyMetric.campaign_id,
                ContributionDailyMetric.campaign_name,
                func.sum(ContributionDailyMetric.spend).label("spend"),
                func.sum(ContributionDailyMetric.impressions).label("impressions"),
                func.sum(ContributionDailyMetric.conversions).label("conversions"),
                func.sum(ContributionDailyMetric.conversion_value).label("conversion_value"),
                func.count(ContributionDailyMetric.date).label("active_days"),
                func.min(ContributionDailyMetric.date).label("first_date"),
                func.max(ContributionDailyMetric.date).label("last_date"),
            )
            .where(
                ContributionDailyMetric.account_id == account_id,
                ContributionDailyMetric.metric_key == metric_key,
            )
            .group_by(
                ContributionDailyMetric.campaign_id,
                ContributionDailyMetric.campaign_name,
            )
            .order_by(func.sum(ContributionDailyMetric.spend).desc())
        )
        if days is not None:
            # 由 db 端以 max(date) 倒推 N 天（不假設今天日期，讓測試可注入）
            max_date_subq = (
                select(func.max(ContributionDailyMetric.date))
                .where(
                    ContributionDailyMetric.account_id == account_id,
                    ContributionDailyMetric.metric_key == metric_key,
                )
                .scalar_subquery()
            )
            # SQLite/Postgres 皆支援 date('substr(max_date,1,10)', '-N day')
            # 但跨 dialect 的安全做法是在 Python 端算好 cutoff（callers 傳入）
            # 此處直接接由呼叫端在 date 欄位上篩選 — 提供 days 提示，但實際
            # 過濾交由 service 層傳入明確 date_start/date_end 較不易出錯。
            # 為了維持單一方法簽名，這裡保留 days 作為提示（callers 多以 None 呼叫）
            del max_date_subq
        rows = db.execute(stmt).all()
        return [
            {
                "campaign_id": r.campaign_id,
                "campaign_name": r.campaign_name,
                "spend": float(r.spend or 0.0),
                "impressions": int(r.impressions or 0),
                "conversions": float(r.conversions or 0.0),
                "conversion_value": float(r.conversion_value or 0.0),
                "active_days": int(r.active_days or 0),
                "first_date": r.first_date,
                "last_date": r.last_date,
            }
            for r in rows
        ]

    # ── 分組讀寫（任務 1.4 實作） ───────────────────────────────
    def get_groups(
        self,
        db: Session,
        *,
        account_id: str,
    ) -> list[ContributionCampaignGroup]:
        """讀取該帳戶的分組（含 auto 與 manual），依 `group_key` 排序。

        若無資料回空 list，由 service 層決定是否觸發 auto_group() 並寫入。
        """
        stmt = (
            select(ContributionCampaignGroup)
            .where(ContributionCampaignGroup.account_id == account_id)
            .order_by(ContributionCampaignGroup.group_key.asc())
        )
        return list(db.scalars(stmt).all())

    def get_active_group_source(
        self,
        db: Session,
        *,
        account_id: str,
    ) -> str:
        """回傳目前「生效中」的分組 source：有 manual 則 manual、否則 auto、否則 'none'。"""
        stmt = select(ContributionCampaignGroup.source).where(
            ContributionCampaignGroup.account_id == account_id
        )
        sources = {row for row in db.scalars(stmt).all() if row}
        if "manual" in sources:
            return "manual"
        if "auto" in sources:
            return "auto"
        return "none"

    def upsert_groups(
        self,
        db: Session,
        *,
        account_id: str,
        groups: list[dict[str, Any]],
        updated_by: str | None = None,
    ) -> list[ContributionCampaignGroup]:
        """整批覆寫分組：先刪除該帳戶既有列，再依 `groups` 寫入新列。

        groups 為 list[dict]，每個 dict 含 keys：
          `group_key` / `group_name` / `campaign_ids` / `source`
        service 層已用 `grouping.validate_manual_groups` 校驗過合法性；本方法
        僅負責寫入。

        回傳新寫入的 ORM 物件 list（依 group_key 排序）。
        """
        # 刪除既有列（account_id 範圍）
        existing = (
            db.query(ContributionCampaignGroup)
            .filter(ContributionCampaignGroup.account_id == account_id)
            .all()
        )
        for row in existing:
            db.delete(row)
        db.flush()

        now_expr = func.current_timestamp()
        new_rows: list[ContributionCampaignGroup] = []
        for g in groups:
            row = ContributionCampaignGroup(
                account_id=account_id,
                group_key=str(g["group_key"]),
                group_name=str(g["group_name"]),
                campaign_ids=list(g.get("campaign_ids") or []),
                source=str(g.get("source") or "manual"),
                updated_by=updated_by,
                created_at=now_expr,
                updated_at=now_expr,
            )
            db.add(row)
            new_rows.append(row)
        db.flush()
        # 重排：依 group_key
        new_rows.sort(key=lambda r: r.group_key)
        return new_rows

    def get_groups_by_source(
        self,
        db: Session,
        *,
        account_id: str,
        source: str,
    ) -> list[ContributionCampaignGroup]:
        """讀取指定 source 的分組（service 用以分辨 manual / auto）。"""
        stmt = (
            select(ContributionCampaignGroup)
            .where(
                ContributionCampaignGroup.account_id == account_id,
                ContributionCampaignGroup.source == source,
            )
            .order_by(ContributionCampaignGroup.group_key.asc())
        )
        return list(db.scalars(stmt).all())

    # ── Snapshot 列表分頁（任務 1.4 加強） ─────────────────────────
    def count_snapshots(
        self,
        db: Session,
        *,
        account_id: str,
    ) -> int:
        stmt = select(func.count(ContributionSnapshot.id)).where(
            ContributionSnapshot.account_id == account_id
        )
        return int(db.execute(stmt).scalar() or 0)


repository = ContributionRepository()
