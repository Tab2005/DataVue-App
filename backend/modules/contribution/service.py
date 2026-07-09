"""
Contribution Module - 業務編排層（docs/21 §3.4 / 任務 1.4）

負責：
  - get_or_create_groups: 讀取或自動產生該帳戶分組
  - update_groups: 套用使用者手動分組（覆寫既有 auto/manual）
  - list_groups / get_groups_summary: 對外讀取
  - create_analysis: 接收分析請求，建 snapshot + 排程背景任務
  - process_analysis: 背景任務主體（組裝資料 + 跑引擎 + 寫結果）
  - list_snapshots / get_snapshot: 對外讀取分析
  - run_analysis_sync: 同步呼叫（測試與本地 fallback 共用）

所有方法不發 HTTP、不直接 FastAPI Depends；router 層做型別轉換。
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.scheduler import (
    add_contribution_analysis_job,
    is_scheduler_enabled,
    scheduler,
)
from database import SessionLocal
from database.models.contribution import (
    ContributionCampaignGroup,
    ContributionDailyMetric,
    ContributionSnapshot,
)
from . import grouping
from .engine import GuardrailViolation, run_analysis
from .repository import repository

logger = logging.getLogger(__name__)


# ── 例外 ──────────────────────────────────────────────────────────────
class ContributionServiceError(Exception):
    """Service 層錯誤基類；service 內不直接拋 HTTPException，由 router 翻譯。"""


class GuardrailRejected(ContributionServiceError):
    """Guardrail 預檢不通過；detail 為人類可讀原因清單。"""

    def __init__(self, violations: list[str]):
        self.violations = violations
        super().__init__("; ".join(violations))


class GroupValidationRejected(ContributionServiceError):
    """手動分組驗證失敗。"""

    def __init__(self, errors: list[str], missing: list[str] | None = None):
        self.errors = errors
        self.missing = missing or []
        super().__init__("; ".join(errors))


class SnapshotNotFound(ContributionServiceError):
    pass


class SnapshotNotCompleted(ContributionServiceError):
    """嘗試寫入 AI 摘要但 snapshot 尚未 completed（前端應在生成前輪詢至 completed）。"""


# ── 分組（get / create / update） ──────────────────────────────────────
def get_or_create_groups(
    db: Session,
    *,
    account_id: str,
    updated_by: str | None = None,
) -> list[ContributionCampaignGroup]:
    """取得該帳戶分組：
      - 有 manual → 回傳 manual
      - 僅有 auto → 回傳 auto
      - 完全無 → 觸發 auto_group() 並寫入後回傳
    """
    manual = repository.get_groups_by_source(db, account_id=account_id, source="manual")
    if manual:
        return manual
    auto = repository.get_groups_by_source(db, account_id=account_id, source="auto")
    if auto:
        return auto

    # 全無 → 用 auto_group() 產生並寫入
    summaries = repository.list_campaign_summaries(
        db, account_id=account_id, metric_key="omni_purchase"
    )
    if not summaries:
        # 該帳戶完全無活動資料：不要建立空 G_other 桶（前端需先 /data/refresh）
        return []
    auto_groups = grouping.auto_group(summaries)
    if not auto_groups:
        return []
    rows = repository.upsert_groups(
        db,
        account_id=account_id,
        groups=auto_groups,
        updated_by=updated_by,
    )
    db.commit()
    return rows


def list_groups(
    db: Session,
    *,
    account_id: str,
) -> list[ContributionCampaignGroup]:
    return repository.get_groups(db, account_id=account_id)


def update_groups(
    db: Session,
    *,
    account_id: str,
    groups_payload: list[dict[str, Any]],
    updated_by: str | None,
) -> list[ContributionCampaignGroup]:
    """套用手動分組：先以現有活動清單驗證 submitted payload，再覆寫。

    規則（grouping.validate_manual_groups）：
      - group_key 不可重複、不可空
      - 全部活動 ID 必須屬於該帳戶、不可丟失
    """
    summaries = repository.list_campaign_summaries(
        db, account_id=account_id, metric_key="omni_purchase"
    )
    existing_ids = {str(c["campaign_id"]) for c in summaries}
    errors, _missing = grouping.validate_manual_groups(existing_ids, groups_payload)
    if errors:
        raise GroupValidationRejected(errors)

    # 強制 source=manual（拒絕將 auto payload 寫入）
    normalized = [
        {**g, "source": "manual"}
        for g in groups_payload
    ]
    rows = repository.upsert_groups(
        db,
        account_id=account_id,
        groups=normalized,
        updated_by=updated_by,
    )
    db.commit()
    return rows


# ── 分析編排 ───────────────────────────────────────────────────────────
def prepare_analysis(
    db: Session,
    *,
    account_id: str,
    date_start: str,
    date_end: str,
    metric_key: str = "omni_purchase",
    n_restarts: int | None = None,
    holdout_days: int | None = None,
    marginal_step: float | None = None,
    created_by: str | None = None,
) -> ContributionSnapshot:
    """同步段：guardrail 預檢 + 建 snapshot（status=queued）。**不做 dispatch**。

    刻意與 dispatch 分離（docs/27 任務 1.2）：本函式全程為同步 DB + numpy
    運算，FastAPI 端點應以 `asyncio.to_thread(prepare_analysis, ...)` 呼叫，
    完成後回到 event loop 再呼叫 `_dispatch_analysis(snapshot.id)`——舊版
    `create_analysis` 把這整段（含 `_assemble_arrays` 撈最多 180 天全活動
    資料 + `check_guardrails` 的 numpy 運算）直接跑在 `async def` 端點的
    event loop 執行緒上，等同 router.py 檔頭自述要避免的模式：一次慢查詢
    或大量資料組裝就會把整個 backend（含 `/health`）擠到無回應。
    """
    # 1. 預檢：是否有資料、組別、guardrail
    groups = get_or_create_groups(db, account_id=account_id, updated_by=created_by)
    if not groups:
        raise GuardrailRejected(["該帳戶尚無活動資料，請先呼叫 /data/refresh 抓取資料"])

    # 2. 預檢 guardrail（在背景任務之前發現問題可回 4xx）
    spend_by_group, y, weekdays, precheck_messages = _assemble_arrays(
        db,
        account_id=account_id,
        date_start=date_start,
        date_end=date_end,
        metric_key=metric_key,
        groups=groups,
    )
    if y is None or len(y) == 0:
        raise GuardrailRejected(
            [f"分析區間 {date_start} ~ {date_end} 無資料（請先 /data/refresh）"]
        )

    # 直接以 engine.check_guardrails 同步預檢，避免背景任務才發現問題
    from .engine import check_guardrails, resolve_config
    cfg = resolve_config(
        {
            "n_restarts": int(n_restarts) if n_restarts else 5,
            "holdout_days": int(holdout_days) if holdout_days else 45,
        }
    )
    violations = check_guardrails(spend_by_group, y, cfg)
    if violations:
        raise GuardrailRejected(violations)

    # 3. 建 snapshot（status=queued）
    config = {
        "metric_key": metric_key,
        "n_restarts": n_restarts or 5,
        "holdout_days": holdout_days or 45,
        "marginal_step": marginal_step,
        "group_snapshot": [_group_to_dict(g) for g in groups],
    }
    snapshot = repository.create_snapshot(
        db,
        account_id=account_id,
        date_start=date_start,
        date_end=date_end,
        config=config,
        created_by=created_by,
    )
    db.commit()
    db.refresh(snapshot)
    return snapshot


def create_analysis(
    db: Session,
    *,
    account_id: str,
    date_start: str,
    date_end: str,
    metric_key: str = "omni_purchase",
    n_restarts: int | None = None,
    holdout_days: int | None = None,
    marginal_step: float | None = None,
    created_by: str | None = None,
) -> tuple[ContributionSnapshot, str, str]:
    """相容包裝：同步 `prepare_analysis` + `_dispatch_analysis`（測試 / CLI
    直呼叫用；FastAPI 端點改為 `await asyncio.to_thread(prepare_analysis, ...)`
    後再於 event loop 呼叫 `_dispatch_analysis`，兩段分離見 router.py）。

    回傳 (snapshot, queue_host, dispatch_mode)。
      queue_host ∈ {'apscheduler', 'local_async', 'unavailable'}
      dispatch_mode 為 router 用以決定 202 訊息的提示詞。
    """
    snapshot = prepare_analysis(
        db,
        account_id=account_id,
        date_start=date_start,
        date_end=date_end,
        metric_key=metric_key,
        n_restarts=n_restarts,
        holdout_days=holdout_days,
        marginal_step=marginal_step,
        created_by=created_by,
    )
    queue_host, dispatch_mode = _dispatch_analysis(snapshot.id)
    return snapshot, queue_host, dispatch_mode


def _dispatch_analysis(snapshot_id: str) -> tuple[str, str]:
    """決定背景任務執行位置，回傳 (queue_host, dispatch_mode)。

    規則（簡化為兩層，docs/21 §3.4）：
      1. scheduler 啟用且 running → add_contribution_analysis_job（apscheduler）
      2. 否則 → asyncio task（local_async），有 running loop 時 create_task，
         沒有時用 asyncio.run() 阻塞跑（適用於測試與 CLI 直呼叫）
      3. asyncio 不可用（理論上不該發生）→ unavailable
    """
    if is_scheduler_enabled() and scheduler.running:
        job = add_contribution_analysis_job(snapshot_id)
        if job is not None:
            return "apscheduler", "scheduler_job"

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:

        async def _run() -> None:
            await process_analysis(snapshot_id)

        loop.create_task(_run())
        return "local_async", "in_process_task"

    # 同步上下文（測試 / CLI）：以 asyncio.run 阻塞跑完
    try:

        async def _run() -> None:
            await process_analysis(snapshot_id)

        asyncio.run(_run())
        return "local_async", "in_process_blocking"
    except Exception as exc:
        logger.warning(
            "[Contribution] _dispatch_analysis: asyncio.run failed for %s: %s",
            snapshot_id,
            exc,
        )
        return "unavailable", "none"


# ── 背景任務主體 ───────────────────────────────────────────────────────
async def process_analysis(snapshot_id: str) -> None:
    """背景任務：組裝資料 → 跑引擎 → 寫結果。

    寫失敗規則（依 docs/21 §3.4 驗收：分析失敗時 snapshot 可見 error_message）：
      - guardrail 拒絕 → status=failed，error_message 列出 violations
      - 引擎例外 / 組裝例外 → status=failed，error_message 含類型與訊息
      - 成功 → status=completed，results 與 diagnostics 寫入
    """
    db = SessionLocal()
    try:
        snapshot = repository.get_snapshot(db, snapshot_id)
        if snapshot is None:
            logger.error(
                "[Contribution] process_analysis: snapshot %s not found", snapshot_id
            )
            return
        repository.set_snapshot_status(db, snapshot_id, status="processing")
        db.commit()

        groups_payload: list[dict[str, Any]] = list(
            (snapshot.config or {}).get("group_snapshot") or []
        )
        metric_key = (snapshot.config or {}).get("metric_key", "omni_purchase")
        n_restarts = (snapshot.config or {}).get("n_restarts", 5)
        holdout_days = (snapshot.config or {}).get("holdout_days", 45)
        marginal_step = (snapshot.config or {}).get("marginal_step")

        # 由 snapshot config 還原分組：將 group_snapshot 視為已存在的 groups
        # 結構，每個 group 需有 group_key / group_name / campaign_ids。
        groups = _restore_groups(groups_payload)
        if not groups:
            raise GroupValidationRejected(
                ["snapshot.config.group_snapshot 為空或格式錯誤"]
            )

        # 同步呼叫 run_analysis（純函數，無 I/O）；包進 to_thread 釋放 event loop
        config_overrides: dict[str, Any] = {
            "n_restarts": int(n_restarts),
            "holdout_days": int(holdout_days),
        }
        if marginal_step is not None:
            config_overrides["marginal_step"] = float(marginal_step)

        try:
            spend_by_group, y, weekdays, _ = _assemble_arrays(
                db,
                account_id=snapshot.account_id,
                date_start=snapshot.date_start,
                date_end=snapshot.date_end,
                metric_key=metric_key,
                groups=groups,
            )
        except Exception as exc:
            raise ContributionServiceError(
                f"組裝分析資料失敗：{type(exc).__name__}: {exc}"
            ) from exc

        if y is None or len(y) == 0:
            raise GuardrailRejected(
                [f"分析區間 {snapshot.date_start} ~ {snapshot.date_end} 無資料"]
            )

        try:
            outcome = await asyncio.to_thread(
                run_analysis, spend_by_group, y, weekdays, config_overrides
            )
        except GuardrailViolation as exc:
            raise GuardrailRejected(list(exc.violations)) from exc
        except Exception as exc:
            raise ContributionServiceError(
                f"引擎執行失敗：{type(exc).__name__}: {exc}"
            ) from exc

        repository.set_snapshot_status(
            db,
            snapshot_id,
            status="completed",
            results=outcome["results"],
            diagnostics=outcome["diagnostics"],
        )
        db.commit()
        logger.info(
            "[Contribution] snapshot %s completed (account=%s, %s..%s)",
            snapshot_id,
            snapshot.account_id,
            snapshot.date_start,
            snapshot.date_end,
        )
    except (GuardrailRejected, GroupValidationRejected) as exc:
        _mark_failed(db, snapshot_id, exc)
    except ContributionServiceError as exc:
        _mark_failed(db, snapshot_id, exc)
    except Exception as exc:  # 保險：背景任務不要把錯誤吞掉
        logger.exception("[Contribution] process_analysis %s crashed", snapshot_id)
        try:
            _mark_failed(
                db,
                snapshot_id,
                ContributionServiceError(
                    f"未預期錯誤：{type(exc).__name__}: {exc}"
                ),
            )
        except Exception:
            db.rollback()
    finally:
        db.close()


def _mark_failed(db: Session, snapshot_id: str, exc: Exception) -> None:
    try:
        repository.set_snapshot_status(
            db, snapshot_id, status="failed", error_message=str(exc)
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "[Contribution] failed to mark snapshot %s as failed", snapshot_id
        )


# ── 對外讀取（list / detail） ─────────────────────────────────────────
def list_snapshots(
    db: Session,
    *,
    account_id: str,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ContributionSnapshot], int]:
    total = repository.count_snapshots(db, account_id=account_id)
    items = repository.list_snapshots(
        db, account_id=account_id, limit=page_size, offset=(page - 1) * page_size
    )
    return items, total


def get_snapshot(db: Session, snapshot_id: str) -> ContributionSnapshot:
    snap = repository.get_snapshot(db, snapshot_id)
    if snap is None:
        raise SnapshotNotFound(snapshot_id)
    return snap


def save_ai_summary(
    db: Session,
    *,
    snapshot_id: str,
    ai_summary: str,
) -> ContributionSnapshot:
    """寫入 AI 白話解讀到 snapshot。

    規則：
      - snapshot 不存在 → 拋 SnapshotNotFound（router 翻 404）
      - snapshot.status != 'completed' → 拋 SnapshotNotCompleted
        （router 翻 409，避免前端把尚未分析的結果配上 AI 解讀）
      - 寫入成功回傳刷新後的 ORM 物件（含 ai_summary_generated_at）
    """
    snap = repository.get_snapshot(db, snapshot_id)
    if snap is None:
        raise SnapshotNotFound(snapshot_id)
    if snap.status != "completed":
        raise SnapshotNotCompleted(
            f"snapshot {snapshot_id} 狀態為 {snap.status}，僅 completed 可寫入 AI 解讀"
        )
    updated = repository.set_ai_summary(db, snapshot_id, ai_summary=ai_summary)
    if updated is None:  # 競態：get 完到 set 之間被刪除
        raise SnapshotNotFound(snapshot_id)
    db.commit()
    db.refresh(updated)
    return updated


# ── 內部：組裝 spend_by_group / y / weekdays ──────────────────────────
def _assemble_arrays(
    db: Session,
    *,
    account_id: str,
    date_start: str,
    date_end: str,
    metric_key: str,
    groups: list[ContributionCampaignGroup] | list[dict[str, Any]],
) -> tuple[dict[str, np.ndarray], np.ndarray | None, np.ndarray, list[str]]:
    """由 daily metrics 快取組裝模型輸入。

    規則：
      - 從 date_start 到 date_end 逐日（含兩端）
      - y 為每日 conversions 加總（不分組）
      - spend_by_group 為每組每日花費（缺值補 0）
      - 任何活動若未在 groups 中 → 不計入 spend_by_group，但會貢獻到 y（保持總和）
    """
    start = date.fromisoformat(date_start)
    end = date.fromisoformat(date_end)
    if end < start:
        end = start
    days = (end - start).days + 1
    if days <= 0:
        return {}, None, np.array([]), ["分析區間無效"]

    # 拉資料
    stmt = (
        select(
            ContributionDailyMetric.date,
            ContributionDailyMetric.campaign_id,
            ContributionDailyMetric.spend,
            ContributionDailyMetric.conversions,
        )
        .where(
            ContributionDailyMetric.account_id == account_id,
            ContributionDailyMetric.metric_key == metric_key,
            ContributionDailyMetric.date >= date_start,
            ContributionDailyMetric.date <= date_end,
        )
    )
    rows = db.execute(stmt).all()

    # campaign_id → group_key 對映
    cid_to_group: dict[str, str] = {}
    for g in groups:
        cids = g.campaign_ids if hasattr(g, "campaign_ids") else g.get("campaign_ids", [])
        gk = g.group_key if hasattr(g, "group_key") else g.get("group_key")
        for cid in cids:
            cid_to_group[str(cid)] = str(gk)

    # 初始化
    date_axis = [(start + timedelta(days=i)).isoformat() for i in range(days)]
    date_index = {d: i for i, d in enumerate(date_axis)}
    group_keys: list[str] = []
    for g in groups:
        gk = g.group_key if hasattr(g, "group_key") else g.get("group_key")
        if gk and gk not in group_keys:
            group_keys.append(str(gk))
    spend_by_group = {gk: np.zeros(days) for gk in group_keys}
    y = np.zeros(days)

    for r in rows:
        idx = date_index.get(r.date)
        if idx is None:
            continue
        y[idx] += float(r.conversions or 0.0)
        gk = cid_to_group.get(str(r.campaign_id))
        if gk and gk in spend_by_group:
            spend_by_group[gk][idx] += float(r.spend or 0.0)

    weekdays = np.array([date.fromisoformat(d).weekday() for d in date_axis])
    return spend_by_group, y, weekdays, []


def _group_to_dict(g: ContributionCampaignGroup) -> dict[str, Any]:
    return {
        "group_key": g.group_key,
        "group_name": g.group_name,
        "campaign_ids": list(g.campaign_ids or []),
        "source": g.source,
    }


def _restore_groups(payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """由 snapshot.config.group_snapshot 還原為與 list[ContributionCampaignGroup]
    屬性相容的 dict 結構，供 _assemble_arrays 使用。"""
    out: list[dict[str, Any]] = []
    for g in payload:
        if not isinstance(g, dict):
            continue
        if not g.get("group_key") or not g.get("campaign_ids"):
            continue
        out.append(
            {
                "group_key": g["group_key"],
                "group_name": g.get("group_name") or g["group_key"],
                "campaign_ids": list(g["campaign_ids"]),
                "source": g.get("source", "auto"),
            }
        )
    return out


# ── 對外：分析同步執行（測試 / fallback） ──────────────────────────────
def run_analysis_sync(
    db: Session,
    *,
    snapshot_id: str,
) -> None:
    """同步版本的 process_analysis（測試用；正式背景任務走 async 入口）。"""
    asyncio.run(process_analysis(snapshot_id))


__all__ = [
    "ContributionServiceError",
    "GuardrailRejected",
    "GroupValidationRejected",
    "SnapshotNotFound",
    "SnapshotNotCompleted",
    "get_or_create_groups",
    "list_groups",
    "update_groups",
    "prepare_analysis",
    "create_analysis",
    "process_analysis",
    "list_snapshots",
    "get_snapshot",
    "save_ai_summary",
    "run_analysis_sync",
]
