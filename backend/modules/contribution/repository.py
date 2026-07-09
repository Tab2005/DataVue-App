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
from datetime import datetime, timedelta, timezone
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

        寫入欄位（首次 INSERT 不含 fetched_at，由 DB 預設 CURRENT_TIMESTAMP 觸發）：
          account_id, date, campaign_id, campaign_name, spend, impressions,
          conversions, conversion_value, metric_key, actions_payload
        衝突時更新：以上除主鍵外的全部欄位，並以 `func.current_timestamp()`
        刷新 `fetched_at`（docs/27 任務 5.2 修正：`fetched_at` 語義為「最後一次
        抓取時間」，每次重抓/補資料皆會更新，並非保留初次抓取時間）。

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
        date_start: str | None = None,
        date_end: str | None = None,
    ) -> list[dict[str, Any]]:
        """由快取表彙總活動花費/轉換，供分組 UI 與自報占比計算。

        `date_start`/`date_end` 皆為 None → 全歷史彙總（首次全量抓取後即用
        此，分組編輯器與「快取活動數」提示走這個模式）；兩者皆提供 →
        只彙總該區間內的資料（`WHERE date BETWEEN`，前端用於把自報占比對齊
        MMM 分析的快照區間，docs/27 任務 4.2——取代原本永遠是死碼的 `days`
        參數，改為呼叫端直接傳明確日期界線，不易出錯）。回傳 list[dict]，
        每個 dict 對應一個 campaign：
          {campaign_id, campaign_name, spend, impressions, conversions,
           conversion_value, active_days, first_date, last_date}
        按 spend 由大到小排序。

        只 `GROUP BY campaign_id`（不含 campaign_name，docs/27 任務 2.4）：
        活動改名後，增量抓取只覆寫最近 3 天（現為「補缺口」視窗，見任務 1.1）
        的 campaign_name，較舊的歷史列仍保留改名前的舊名快照——若沿用舊版
        `GROUP BY (campaign_id, campaign_name)`，同一 campaign_id 因為出現
        過兩種名稱字串會被拆成兩列，花費占比因此被攤薄，且 `auto_group` 會
        把同一 campaign_id append 兩次（可能同時分進兩個組，`update_groups`
        的合法性驗證會報「活動同時出現在多個組別中」）。campaign_name 改在
        Python 端用「該 campaign_id 最新一天」的名稱回填——`(account_id,
        date, campaign_id, metric_key)` 是資料表的唯一約束，故「campaign_id
        對應到某個 max(date)」查回原表必為恰一列，不需要 DISTINCT（若有指定
        日期區間，「最新一天」也限縮在該區間內，與彙總口徑一致）。
        """
        base_filters = [
            ContributionDailyMetric.account_id == account_id,
            ContributionDailyMetric.metric_key == metric_key,
        ]
        if date_start is not None:
            base_filters.append(ContributionDailyMetric.date >= date_start)
        if date_end is not None:
            base_filters.append(ContributionDailyMetric.date <= date_end)
        base_filters = tuple(base_filters)

        stmt = (
            select(
                ContributionDailyMetric.campaign_id,
                func.sum(ContributionDailyMetric.spend).label("spend"),
                func.sum(ContributionDailyMetric.impressions).label("impressions"),
                func.sum(ContributionDailyMetric.conversions).label("conversions"),
                func.sum(ContributionDailyMetric.conversion_value).label("conversion_value"),
                func.count(ContributionDailyMetric.date).label("active_days"),
                func.min(ContributionDailyMetric.date).label("first_date"),
                func.max(ContributionDailyMetric.date).label("last_date"),
            )
            .where(*base_filters)
            .group_by(ContributionDailyMetric.campaign_id)
            .order_by(func.sum(ContributionDailyMetric.spend).desc())
        )
        rows = db.execute(stmt).all()
        if not rows:
            return []

        # 各 campaign_id 最新一天的 campaign_name（見上方 docstring 的唯一約束說明）
        max_date_per_campaign = (
            select(
                ContributionDailyMetric.campaign_id.label("campaign_id"),
                func.max(ContributionDailyMetric.date).label("max_date"),
            )
            .where(*base_filters)
            .group_by(ContributionDailyMetric.campaign_id)
            .subquery()
        )
        name_rows = db.execute(
            select(
                ContributionDailyMetric.campaign_id,
                ContributionDailyMetric.campaign_name,
            ).join(
                max_date_per_campaign,
                (ContributionDailyMetric.campaign_id == max_date_per_campaign.c.campaign_id)
                & (ContributionDailyMetric.date == max_date_per_campaign.c.max_date),
            ).where(*base_filters)
        ).all()
        name_by_campaign = {r.campaign_id: r.campaign_name for r in name_rows}

        return [
            {
                "campaign_id": r.campaign_id,
                "campaign_name": name_by_campaign.get(r.campaign_id),
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

    def delete_groups(
        self,
        db: Session,
        *,
        account_id: str,
    ) -> int:
        """刪除該帳戶所有分組列（manual + auto），供「重設為自動分組」使用
        （docs/27 任務 6.2）：`get_or_create_groups` 只在完全無分組時才會跑
        `auto_group()`，grouping.py 規則修正後既有帳戶不會自動受益，需要
        先清空既有列才能重新觸發。回傳刪除筆數；呼叫端負責 commit。
        """
        existing = (
            db.query(ContributionCampaignGroup)
            .filter(ContributionCampaignGroup.account_id == account_id)
            .all()
        )
        for row in existing:
            db.delete(row)
        db.flush()
        return len(existing)

    # ── 資料涵蓋範圍（docs/27 任務 6.1） ──────────────────────────
    def get_data_coverage(
        self,
        db: Session,
        *,
        account_id: str,
        metric_key: str = "omni_purchase",
    ) -> tuple[str, str] | None:
        """查詢該帳戶指定 metric_key 目前快取的 (first_date, last_date)；
        無資料回 None。

        供兩處使用：`data_source._resolve_fetch_window` 的增量抓取起點
        判斷（原本各自 inline 一份相同查詢，此處收斂為單一實作）；以及
        `service.prepare_analysis` 判斷請求分析區間是否超出實際快取範圍
        ——超出的部分若放給 `_assemble_arrays` 逐日組裝，缺口日子會被填成
        spend=0/conversions=0 的假資料直接進模型，稀釋 guardrail 檢查並偏
        誤迴歸估計。
        """
        stmt = select(
            func.min(ContributionDailyMetric.date),
            func.max(ContributionDailyMetric.date),
        ).where(
            ContributionDailyMetric.account_id == account_id,
            ContributionDailyMetric.metric_key == metric_key,
        )
        row = db.execute(stmt).first()
        if row is None or row[0] is None or row[1] is None:
            return None
        return (row[0], row[1])

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

    # ── 殭屍 snapshot 回收（docs/27 任務 2.2） ─────────────────────
    def mark_stale_snapshots_failed(
        self,
        db: Session,
        *,
        queued_older_than_minutes: int = 10,
        processing_older_than_minutes: int = 30,
        now: datetime | None = None,
    ) -> int:
        """把超時卡在 queued/processing 的 snapshot 標為 failed。

        apscheduler 為 in-memory date-trigger：server 在 job 執行前重啟、或
        scheduler 與 local async fallback 皆不可用（503 路徑，snapshot 已建
        但從未真正排程）都會留下永久卡住的 snapshot，前端輪詢會無限轉圈。

        - queued 超過 `queued_older_than_minutes`（依 `created_at` 計算）：
          代表從未被成功排程（fallback 全部失敗、或 job 尚未觸發前 server
          已重啟），標 failed + `stale_queued_reclaimed`。
        - processing 超過 `processing_older_than_minutes`（依 `created_at`
          計算——`process_analysis` 轉 processing 後未再更新任何時間戳可用，
          用建立時間近似「已執行多久」，門檻已含跑完分析的安全餘裕）：
          代表背景任務執行中途被中斷（server 重啟/程序被殺），標 failed +
          `stale_processing_reclaimed`。
        - 執行中的正常分析（未超過門檻）不受影響。

        回傳被回收的筆數。呼叫端負責 commit。
        """
        now = now or datetime.now(timezone.utc)
        queued_cutoff = now - timedelta(minutes=queued_older_than_minutes)
        processing_cutoff = now - timedelta(minutes=processing_older_than_minutes)

        reclaimed = 0
        stale_queued = (
            db.query(ContributionSnapshot)
            .filter(
                ContributionSnapshot.status == "queued",
                ContributionSnapshot.created_at < queued_cutoff,
            )
            .all()
        )
        for snap in stale_queued:
            snap.status = "failed"
            snap.error_message = "stale_queued_reclaimed"
            snap.completed_at = now
            db.add(snap)
            reclaimed += 1

        stale_processing = (
            db.query(ContributionSnapshot)
            .filter(
                ContributionSnapshot.status == "processing",
                ContributionSnapshot.created_at < processing_cutoff,
            )
            .all()
        )
        for snap in stale_processing:
            snap.status = "failed"
            snap.error_message = "stale_processing_reclaimed"
            snap.completed_at = now
            db.add(snap)
            reclaimed += 1

        if reclaimed:
            db.flush()
        return reclaimed

    # ── AI 白話解讀（任務 2.3 追加） ──────────────────────────────
    def set_ai_summary(
        self,
        db: Session,
        snapshot_id: str,
        *,
        ai_summary: str,
    ) -> ContributionSnapshot | None:
        """寫入 AI 白話解讀（含生成時間）；snapshot 不存在回 None。

        寫入時同時設置 ai_summary 與 ai_summary_generated_at，呼叫端應
        先確認 snapshot.status == 'completed'（service 層把關）。"""
        snapshot = self.get_snapshot(db, snapshot_id)
        if snapshot is None:
            return None
        snapshot.ai_summary = ai_summary
        snapshot.ai_summary_generated_at = datetime.now(timezone.utc)
        db.add(snapshot)
        db.flush()
        return snapshot


repository = ContributionRepository()
