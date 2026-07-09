"""
Contribution 模組任務 1.4 service 編排測試（docs/21 §3.4）

驗收：
  - get_or_create_groups：manual 優先 → auto fallback → 觸發 auto_group
  - update_groups：非法 payload 拋 GroupValidationRejected；合法寫 source=manual
  - create_analysis：guardrail 預檢 + 建 snapshot + 排程（apscheduler/local_async）
  - process_analysis：背景任務主體；成功 → status=completed；失敗 → status=failed
  - list_snapshots / get_snapshot 對外讀取
  - scheduler 不可用時 _dispatch_analysis 退回 local_async
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import patch

import pytest

from database.models.contribution import (
    ContributionCampaignGroup,
    ContributionDailyMetric,
    ContributionSnapshot,
)
from modules.contribution import service as service_module
from modules.contribution import service
from modules.contribution.repository import repository


class _SessionProxy:
    """將測試 db session 偽裝成 SessionLocal() — 沿用既有 test_meta_andromeda_module 慣例。"""

    def __init__(self, session):
        self._session = session

    def __getattr__(self, name):
        return getattr(self._session, name)

    def close(self):
        return None


@pytest.fixture
def patched_session(monkeypatch):
    """將 service 模組的 SessionLocal 替換成回傳測試 db 的 factory。
    背景任務與 service 內部 SessionLocal() 都會用同一個測試 session。"""
    # 由 service.process_analysis 用 monkeypatch 綁進去
    return monkeypatch


# ── get_or_create_groups ────────────────────────────────────────────
@pytest.mark.integration
def test_get_or_create_groups_triggers_auto_when_empty(db, sample_user):
    """無資料：回 G_other 空組（不是觸發 auto_group，auto_group 在有活動時才跑）。"""
    out = service.get_or_create_groups(
        db, account_id="act_empty", updated_by=sample_user.id
    )
    assert out == []  # 沒快取 → 不會有 manual / auto 列

    # 預先 seed 一個活動 → 第二次呼叫會觸發 auto
    db.add(ContributionDailyMetric(
        account_id="act_one",
        date="2026-06-01",
        campaign_id="c1",
        campaign_name="OB 主力常態 A",
        spend=1000.0,
        impressions=10000,
        conversions=50.0,
        conversion_value=15000.0,
        metric_key="omni_purchase",
    ))
    db.commit()
    out = service.get_or_create_groups(
        db, account_id="act_one", updated_by=sample_user.id
    )
    assert any(g.group_key == "G1" for g in out)
    assert all(g.source == "auto" for g in out)
    # 清理
    db.query(ContributionCampaignGroup).filter(
        ContributionCampaignGroup.account_id == "act_one"
    ).delete()
    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_one"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_get_or_create_groups_returns_manual_over_auto(db, sample_user):
    """手動分組存在時優先回傳手動分組。"""
    # 既有 auto
    db.add(ContributionCampaignGroup(
        account_id="act_prio",
        group_key="G1",
        group_name="auto 主力",
        campaign_ids=["c1"],
        source="auto",
    ))
    db.add(ContributionCampaignGroup(
        account_id="act_prio",
        group_key="G1",
        group_name="manual 主力",
        campaign_ids=["c1", "c2"],
        source="manual",
    ))
    db.commit()

    out = service.get_or_create_groups(
        db, account_id="act_prio", updated_by=sample_user.id
    )
    assert all(g.source == "manual" for g in out)
    assert next(g for g in out if g.group_key == "G1").group_name == "manual 主力"

    db.query(ContributionCampaignGroup).filter(
        ContributionCampaignGroup.account_id == "act_prio"
    ).delete()
    db.commit()


# ── update_groups ──────────────────────────────────────────────────
@pytest.mark.integration
def test_update_groups_rejects_invalid_payload(db, sample_user):
    """活動不屬於該帳戶 → 拋 GroupValidationRejected。"""
    db.add(ContributionDailyMetric(
        account_id="act_u1",
        date="2026-06-01",
        campaign_id="c1",
        campaign_name="x",
        spend=100.0,
        conversions=4.0,
        metric_key="omni_purchase",
    ))
    db.commit()
    with pytest.raises(service.GroupValidationRejected) as exc_info:
        service.update_groups(
            db,
            account_id="act_u1",
            groups_payload=[
                {"group_key": "G1", "group_name": "X", "campaign_ids": ["c1", "c_unknown"]},
            ],
            updated_by=sample_user.id,
        )
    assert any("c_unknown" in e for e in exc_info.value.errors)

    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_u1"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_update_groups_writes_manual_source(db, sample_user):
    """合法 payload 寫入後 source=manual。"""
    for cid in ("c1", "c2"):
        db.add(ContributionDailyMetric(
            account_id="act_u2",
            date="2026-06-01",
            campaign_id=cid,
            campaign_name=f"n_{cid}",
            spend=100.0,
            conversions=4.0,
            metric_key="omni_purchase",
        ))
    db.commit()
    rows = service.update_groups(
        db,
        account_id="act_u2",
        groups_payload=[
            {"group_key": "G1", "group_name": "X", "campaign_ids": ["c1", "c2"]},
        ],
        updated_by=sample_user.id,
    )
    assert all(r.source == "manual" for r in rows)

    db.query(ContributionCampaignGroup).filter(
        ContributionCampaignGroup.account_id == "act_u2"
    ).delete()
    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_u2"
    ).delete()
    db.commit()


# ── create_analysis + process_analysis（端到端） ────────────────────
def _seed_180_days(db, account_id: str = "act_svc1") -> None:
    """Seed 180 天資料：每天 spend / conversions 帶隨機變化（避免 holdout
    期間全常數導致 R²=None）。"""
    import random

    rng = random.Random(42)
    for cid in ("c1", "c2"):
        for d in range(180):
            month = (d // 30) + 1
            day = (d % 30) + 1
            if month > 6:
                break
            # base 100/50 spend、15/7 conv，±20% 隨機
            base_spend = 100.0 if cid == "c1" else 50.0
            base_conv = 15.0 if cid == "c1" else 7.0
            spend = base_spend * rng.uniform(0.8, 1.2)
            conv = base_conv * rng.uniform(0.8, 1.2)
            db.add(ContributionDailyMetric(
                account_id=account_id,
                date=f"2026-{month:02d}-{day:02d}",
                campaign_id=cid,
                campaign_name=f"camp_{cid}",
                spend=spend,
                impressions=5000,
                conversions=conv,
                conversion_value=conv * 300,
                metric_key="omni_purchase",
            ))
    db.commit()


@pytest.mark.integration
def test_create_analysis_creates_snapshot_and_dispatches(
    db, sample_user, monkeypatch
):
    """create_analysis 建 snapshot 並透過本地 fallback 派發任務。

    端到端「跑到 completed」由 test_process_analysis_runs_to_completion 驗證
    —— 本測試只驗證 create_analysis 本身（建 snapshot、guardrail 預檢、dispatch）。
    """
    _seed_180_days(db, "act_svc1")
    # 把 dispatch 改為 no-op，避免背景任務搶同一個 session 的 transaction
    # （測試環境下 asyncio.run 與 fixture transaction 共享 connection 容易出問題）
    monkeypatch.setattr(service_module, "_dispatch_analysis", lambda _id: ("local_async", "noop"))
    monkeypatch.setattr(
        service_module, "SessionLocal", lambda: _SessionProxy(db)
    )

    snap, queue_host, mode = service.create_analysis(
        db,
        account_id="act_svc1",
        date_start="2026-01-01",
        date_end="2026-06-30",
        n_restarts=2,
        holdout_days=30,
        created_by=sample_user.id,
    )
    db.commit()
    assert queue_host == "local_async"
    assert snap.status == "queued"
    assert snap.id.startswith("csn_")
    # 從 DB 重讀
    final = repository.get_snapshot(db, snap.id)
    assert final is not None
    assert final.status == "queued"

    # 清理
    db.query(ContributionCampaignGroup).filter(
        ContributionCampaignGroup.account_id == "act_svc1"
    ).delete()
    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_svc1"
    ).delete()
    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_svc1"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_create_analysis_endpoint_offloads_to_thread_then_dispatches(
    db, sample_user, monkeypatch
):
    """docs/27 任務 1.2 回歸：POST /analyses 端點的同步段（prepare_analysis：
    guardrail 預檢 + `_assemble_arrays` + 建 snapshot）透過 `asyncio.to_thread`
    執行，執行緒完成回到 event loop 後才呼叫 `_dispatch_analysis`。

    直接 `asyncio.run()` 呼叫 router coroutine（略過 TestClient/lifespan，
    docs/21 任務 1.4 附註過 HTTP e2e 在 TestClient lifespan 累積下會 OOM），
    驗證 wiring 正確：回傳型別正確、dispatch 只在 snapshot 建立後才被呼叫恰
    一次、且傳入的 snapshot_id 與回傳值一致。
    """
    # 注意：`modules/contribution/__init__.py` 執行 `from .router import router`
    # 後，套件屬性 `modules.contribution.router` 被同名的 APIRouter 實例
    # 覆蓋——連 `import modules.contribution.router as x` 這種寫法都是靠
    # 屬性鏈存取（等同 `x = modules.contribution.router`），一樣會撈到被覆蓋
    # 後的 APIRouter 而非子模組。唯一可靠做法是直接從 sys.modules 取子模組。
    import sys

    import modules.contribution.router  # noqa: F401 確保子模組已載入
    from modules.contribution.router import create_analysis_endpoint
    from modules.contribution.schemas import AnalysisCreateRequest

    router_module = sys.modules["modules.contribution.router"]

    _seed_180_days(db, "act_ep1")

    dispatch_calls: list[str] = []

    def _fake_dispatch(snapshot_id: str):
        dispatch_calls.append(snapshot_id)
        return ("local_async", "noop")

    # router.py 是 `from .service import _dispatch_analysis`（值傳入時已綁定），
    # 故需 patch router 模組自己的名稱，patch service_module 上的同名屬性
    # 不會影響 router 已綁定的參照。
    monkeypatch.setattr(router_module, "_dispatch_analysis", _fake_dispatch)

    # docs/27 任務 1.3 帳號授權：直接呼叫 coroutine 略過 FastAPI DI，故
    # `team` 參數不會被 Depends(get_current_team) 解析，需明確傳入 None
    # （等同無 X-Team-ID header 的個人帳號範圍）；並 patch 帳號可視性判斷
    # 為全放行，因為本測試驗證的是 to_thread + dispatch 的 wiring，不是
    # 授權行為本身（授權行為由 test_contribution_account_access.py 驗證）。
    async def _fake_ensure_account_access(account_id, *, team, user):
        return None

    monkeypatch.setattr(
        router_module, "ensure_account_access", _fake_ensure_account_access
    )

    body = AnalysisCreateRequest(
        account_id="act_ep1",
        date_start="2026-01-01",
        date_end="2026-06-30",
        n_restarts=2,
        holdout_days=30,
    )
    result = asyncio.run(
        create_analysis_endpoint(
            body, user=sample_user, _access=True, team=None, db=db
        )
    )

    assert result.status == "queued"
    assert result.queue_host == "local_async"
    assert result.snapshot_id.startswith("csn_")
    assert dispatch_calls == [result.snapshot_id]

    final = repository.get_snapshot(db, result.snapshot_id)
    assert final is not None
    assert final.status == "queued"

    # 清理
    db.query(ContributionCampaignGroup).filter(
        ContributionCampaignGroup.account_id == "act_ep1"
    ).delete()
    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_ep1"
    ).delete()
    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_ep1"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_process_analysis_runs_to_completion(db, sample_user, monkeypatch):
    """process_analysis 從 queued 跑到 completed（單獨測試避免 transaction 共享問題）。"""
    _seed_180_days(db, "act_pa1")
    monkeypatch.setattr(
        service_module, "SessionLocal", lambda: _SessionProxy(db)
    )

    # 預先建 snapshot（模擬 create_analysis 已建立）
    snap = repository.create_snapshot(
        db,
        account_id="act_pa1",
        date_start="2026-01-01",
        date_end="2026-06-30",
        config={
            "metric_key": "omni_purchase",
            "n_restarts": 2,
            "holdout_days": 30,
            "group_snapshot": [
                {
                    "group_key": "G_other",
                    "group_name": "其他",
                    "campaign_ids": ["c1", "c2"],
                    "source": "auto",
                }
            ],
        },
        created_by=sample_user.id,
    )
    db.commit()

    # 用 asyncio.run 觸發 process_analysis
    asyncio.run(service.process_analysis(snap.id))

    # db.expire_all 確保從 DB 重新查詢（不靠 identity map 殘留）
    db.expire_all()
    final = repository.get_snapshot(db, snap.id)
    assert final is not None, f"snapshot {snap.id} not found"
    status = final.status
    if status == "failed":
        pytest.fail(f"process_analysis failed unexpectedly: {final.error_message}")
    assert status in {"completed", "failed"}
    assert final.results is not None
    assert "groups" in final.results
    assert "r2" in final.results
    assert "collinearity_warnings" in final.diagnostics

    # 清理
    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_pa1"
    ).delete()
    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_pa1"
    ).delete()
    db.commit()


# ── 未分組花費診斷警告（docs/27 任務 5.3） ──────────────────────────
def test_merge_ungrouped_spend_diagnostics_adds_warning_above_threshold():
    """純函數層：占比超過門檻時附加 data_quality_warnings 條目。"""
    diagnostics = {"data_summary": {"days": 180}, "collinearity_warnings": []}
    merged = service._merge_ungrouped_spend_diagnostics(
        diagnostics, {"ungrouped_spend_share": 0.12}
    )
    assert merged["data_summary"]["ungrouped_spend_share"] == 0.12
    assert merged["data_summary"]["days"] == 180  # 既有欄位不受影響
    assert len(merged["data_quality_warnings"]) == 1
    warning = merged["data_quality_warnings"][0]
    assert warning["type"] == "ungrouped_spend"
    assert warning["share"] == 0.12
    assert "未分組" in warning["message"]
    assert "基線" in warning["message"]


def test_merge_ungrouped_spend_diagnostics_no_warning_below_threshold():
    """占比未超過門檻（5%）時不附加警告，但仍寫入 data_summary 供顯示。"""
    diagnostics = {"data_summary": {}}
    merged = service._merge_ungrouped_spend_diagnostics(
        diagnostics, {"ungrouped_spend_share": 0.02}
    )
    assert merged["data_summary"]["ungrouped_spend_share"] == 0.02
    assert merged["data_quality_warnings"] == []


@pytest.mark.integration
def test_process_analysis_flags_ungrouped_spend_above_threshold(db, sample_user, monkeypatch):
    """合成測試：3 活動其中 1 個（c3）不在任何組 → ungrouped_spend_share 正確
    算出、且因占比 > 5% 而在 diagnostics 附加警告（docs/27 任務 5.3）。"""
    _seed_180_days(db, "act_ungrouped")
    # c3：日均花費 30（c1=100、c2=50，c3 占比 30/180=16.7% > 5% 門檻），
    # 刻意不出現在下方 snapshot 的 group_snapshot 中（保持未分組）。
    for d in range(180):
        month = (d // 30) + 1
        day = (d % 30) + 1
        if month > 6:
            break
        db.add(ContributionDailyMetric(
            account_id="act_ungrouped",
            date=f"2026-{month:02d}-{day:02d}",
            campaign_id="c3",
            campaign_name="camp_c3_ungrouped",
            spend=30.0,
            impressions=2000,
            conversions=3.0,
            conversion_value=900.0,
            metric_key="omni_purchase",
        ))
    db.commit()

    monkeypatch.setattr(service_module, "SessionLocal", lambda: _SessionProxy(db))

    snap = repository.create_snapshot(
        db,
        account_id="act_ungrouped",
        date_start="2026-01-01",
        date_end="2026-06-30",
        config={
            "metric_key": "omni_purchase",
            "n_restarts": 2,
            "holdout_days": 30,
            "group_snapshot": [
                {
                    "group_key": "G_other",
                    "group_name": "其他",
                    "campaign_ids": ["c1", "c2"],  # c3 刻意不分組
                    "source": "auto",
                }
            ],
        },
        created_by=sample_user.id,
    )
    db.commit()

    asyncio.run(service.process_analysis(snap.id))

    db.expire_all()
    final = repository.get_snapshot(db, snap.id)
    assert final.status == "completed", final.error_message
    share = final.diagnostics["data_summary"]["ungrouped_spend_share"]
    assert 0.10 < share < 0.25  # 約 16.7%，留合理誤差範圍
    warnings = final.diagnostics["data_quality_warnings"]
    assert len(warnings) == 1
    assert warnings[0]["type"] == "ungrouped_spend"

    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_ungrouped"
    ).delete()
    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_ungrouped"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_process_analysis_no_ungrouped_spend_warning_when_fully_grouped(db, sample_user, monkeypatch):
    """全部活動皆已分組 → ungrouped_spend_share 應為 0，無警告。"""
    _seed_180_days(db, "act_fully_grouped")
    monkeypatch.setattr(service_module, "SessionLocal", lambda: _SessionProxy(db))

    snap = repository.create_snapshot(
        db,
        account_id="act_fully_grouped",
        date_start="2026-01-01",
        date_end="2026-06-30",
        config={
            "metric_key": "omni_purchase",
            "n_restarts": 2,
            "holdout_days": 30,
            "group_snapshot": [
                {
                    "group_key": "G_other",
                    "group_name": "其他",
                    "campaign_ids": ["c1", "c2"],
                    "source": "auto",
                }
            ],
        },
        created_by=sample_user.id,
    )
    db.commit()

    asyncio.run(service.process_analysis(snap.id))

    db.expire_all()
    final = repository.get_snapshot(db, snap.id)
    assert final.status == "completed", final.error_message
    assert final.diagnostics["data_summary"]["ungrouped_spend_share"] == 0.0
    assert final.diagnostics["data_quality_warnings"] == []

    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_fully_grouped"
    ).delete()
    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_fully_grouped"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_create_analysis_rejects_guardrail_violation(db, sample_user):
    """天數 < 90：guardrail 拒絕 → 422 訊息。"""
    # 只有 30 天
    for d in range(30):
        db.add(ContributionDailyMetric(
            account_id="act_short",
            date=f"2026-06-{d + 1:02d}",  # 6-01..6-30 唯一 30 天
            campaign_id="c1",
            campaign_name="OB 主力 A",
            spend=100.0,
            conversions=10.0,
            metric_key="omni_purchase",
        ))
    db.commit()
    with pytest.raises(service.GuardrailRejected) as exc_info:
        service.create_analysis(
            db,
            account_id="act_short",
            date_start="2026-06-01",
            date_end="2026-06-30",
            created_by=sample_user.id,
        )
    assert any("資料天數" in v for v in exc_info.value.violations)

    db.query(ContributionCampaignGroup).filter(
        ContributionCampaignGroup.account_id == "act_short"
    ).delete()
    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_short"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_create_analysis_rejects_no_data(db, sample_user):
    """該帳戶無 daily metric → GuardrailRejected。"""
    with pytest.raises(service.GuardrailRejected) as exc_info:
        service.create_analysis(
            db,
            account_id="act_nothing",
            date_start="2026-01-01",
            date_end="2026-06-30",
            created_by=sample_user.id,
        )
    assert any("尚無活動資料" in v for v in exc_info.value.violations)


# ── 資料涵蓋範圍 clamp（docs/27 任務 6.1） ───────────────────────────
def test_clamp_to_coverage_no_coverage_returns_original_range():
    """帳戶完全無快取（coverage=None）→ 原樣回傳，交由既有「無資料」guardrail 攔截。"""
    start, end, note = service._clamp_to_coverage("2026-01-01", "2026-06-30", None)
    assert (start, end) == ("2026-01-01", "2026-06-30")
    assert note is None


def test_clamp_to_coverage_within_range_no_adjustment():
    """請求區間完全落在實際快取範圍內 → 不調整、note=None。"""
    start, end, note = service._clamp_to_coverage(
        "2026-02-01", "2026-05-01", ("2026-01-01", "2026-06-30")
    )
    assert (start, end) == ("2026-02-01", "2026-05-01")
    assert note is None


def test_clamp_to_coverage_start_earlier_than_actual_clamps_and_notes():
    """要求 365 天但實際只快取 180 天 → 起始日 clamp 到實際快取起點，並附說明。"""
    start, end, note = service._clamp_to_coverage(
        "2025-07-01", "2026-06-30", ("2026-01-01", "2026-06-30")
    )
    assert (start, end) == ("2026-01-01", "2026-06-30")
    assert note is not None
    assert "2025-07-01" in note and "2026-01-01" in note


def test_clamp_to_coverage_end_later_than_actual_clamps_and_notes():
    """要求結束日晚於實際快取最後一天（尚未補抓）→ 結束日 clamp。"""
    start, end, note = service._clamp_to_coverage(
        "2026-01-01", "2026-07-09", ("2026-01-01", "2026-06-30")
    )
    assert (start, end) == ("2026-01-01", "2026-06-30")
    assert note is not None


def test_append_coverage_warning_adds_entry_and_preserves_existing():
    """純函數層：附加 coverage_adjustment 警告，不動既有 data_quality_warnings。"""
    diagnostics = {"data_quality_warnings": [{"type": "ungrouped_spend", "share": 0.1}]}
    merged = service._append_coverage_warning(diagnostics, "要求區間已自動調整")
    assert len(merged["data_quality_warnings"]) == 2
    assert merged["data_quality_warnings"][0]["type"] == "ungrouped_spend"
    assert merged["data_quality_warnings"][1] == {
        "type": "coverage_adjustment",
        "message": "要求區間已自動調整",
    }


@pytest.mark.integration
def test_prepare_analysis_clamps_request_beyond_cached_coverage(db, sample_user):
    """端到端：請求區間早於實際快取起點（模擬選了 365 天但只快取 180 天），
    prepare_analysis 應把 snapshot 的實際區間 clamp 到快取範圍，並在
    config.coverage_note 留下調整說明——而不是讓 _assemble_arrays 把缺口
    日子填成假的 spend=0/y=0 直接進模型（docs/27 任務 6.1）。"""
    _seed_180_days(db, "act_coverage")
    # 請求區間往前多要 180 天（早於實際快取的 2026-01-01）
    snapshot = service.prepare_analysis(
        db,
        account_id="act_coverage",
        date_start="2025-07-05",
        date_end="2026-06-30",
        n_restarts=2,
        holdout_days=30,
        created_by=sample_user.id,
    )
    db.commit()
    assert snapshot.date_start == "2026-01-01"
    assert snapshot.date_end == "2026-06-30"
    assert snapshot.config.get("coverage_note") is not None
    assert "2025-07-05" in snapshot.config["coverage_note"]

    db.query(ContributionCampaignGroup).filter(
        ContributionCampaignGroup.account_id == "act_coverage"
    ).delete()
    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_coverage"
    ).delete()
    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_coverage"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_prepare_analysis_no_coverage_note_when_within_range(db, sample_user):
    """請求區間完全落在實際快取範圍內 → config.coverage_note 為 None（不誤報調整）。"""
    _seed_180_days(db, "act_coverage_ok")
    snapshot = service.prepare_analysis(
        db,
        account_id="act_coverage_ok",
        date_start="2026-01-01",
        date_end="2026-06-30",
        n_restarts=2,
        holdout_days=30,
        created_by=sample_user.id,
    )
    db.commit()
    assert snapshot.config.get("coverage_note") is None

    db.query(ContributionCampaignGroup).filter(
        ContributionCampaignGroup.account_id == "act_coverage_ok"
    ).delete()
    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_coverage_ok"
    ).delete()
    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_coverage_ok"
    ).delete()
    db.commit()


# ── 重設為自動分組（docs/27 任務 6.2） ───────────────────────────────
@pytest.mark.integration
def test_reset_groups_clears_manual_and_regenerates_auto(db, sample_user):
    """既有 manual 分組 → reset_groups 清空後重新以目前 auto_group() 規則
    產生（測試驗證清空與重生兩件事，不驗證 grouping.py 規則本身，規則
    正確性由 test_contribution_grouping.py 把關）。"""
    db.add(ContributionDailyMetric(
        account_id="act_reset",
        date="2026-06-01",
        campaign_id="c1",
        campaign_name="OB 主力常態 A",
        spend=1000.0,
        impressions=10000,
        conversions=50.0,
        conversion_value=15000.0,
        metric_key="omni_purchase",
    ))
    db.add(ContributionCampaignGroup(
        account_id="act_reset",
        group_key="G_custom",
        group_name="使用者自訂",
        campaign_ids=["c1"],
        source="manual",
    ))
    db.commit()

    out = service.reset_groups(db, account_id="act_reset", updated_by=sample_user.id)
    assert all(g.source == "auto" for g in out)
    assert not any(g.group_key == "G_custom" for g in out)
    assert any(g.group_key == "G1" for g in out)

    db.query(ContributionCampaignGroup).filter(
        ContributionCampaignGroup.account_id == "act_reset"
    ).delete()
    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_reset"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_reset_groups_no_campaigns_returns_empty(db, sample_user):
    """帳戶完全無活動資料 → reset_groups 清空後回空 list（不建空 G_other）。"""
    db.add(ContributionCampaignGroup(
        account_id="act_reset_empty",
        group_key="G_stale",
        group_name="舊分組",
        campaign_ids=["ghost"],
        source="auto",
    ))
    db.commit()

    out = service.reset_groups(db, account_id="act_reset_empty", updated_by=sample_user.id)
    assert out == []

    db.query(ContributionCampaignGroup).filter(
        ContributionCampaignGroup.account_id == "act_reset_empty"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_process_analysis_marks_failed_on_invalid_config(db, sample_user, monkeypatch):
    """手動塞入壞 config → 背景任務寫 status=failed + error_message。"""
    _seed_180_days(db, "act_fail")
    monkeypatch.setattr(
        service_module, "SessionLocal", lambda: _SessionProxy(db)
    )
    snap = repository.create_snapshot(
        db,
        account_id="act_fail",
        date_start="2026-01-01",
        date_end="2026-06-30",
        config={
            "metric_key": "omni_purchase",
            "n_restarts": 2,
            "holdout_days": 30,
            "group_snapshot": [],  # 空 → 觸發 GroupValidationRejected
        },
        created_by=sample_user.id,
    )
    db.commit()

    asyncio.run(service.process_analysis(snap.id))

    final = repository.get_snapshot(db, snap.id)
    assert final.status == "failed"
    assert "group_snapshot" in (final.error_message or "")

    db.query(ContributionCampaignGroup).filter(
        ContributionCampaignGroup.account_id == "act_fail"
    ).delete()
    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_fail"
    ).delete()
    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_fail"
    ).delete()
    db.commit()


# ── dispatch fallback ───────────────────────────────────────────────
@pytest.mark.unit
def test_dispatch_analysis_falls_back_to_local_async(monkeypatch):
    """scheduler 不可用時退回 local_async。"""
    monkeypatch.setattr(
        "modules.contribution.service.is_scheduler_enabled", lambda: False
    )
    monkeypatch.setattr(
        "modules.contribution.service.scheduler", type("S", (), {"running": False})()
    )

    # 跑在 event loop 中可建立 task
    async def _run():
        return service._dispatch_analysis("csn_dummy")

    queue_host, mode = asyncio.run(_run())
    assert queue_host == "local_async"
    assert mode == "in_process_task"


@pytest.mark.unit
def test_dispatch_analysis_keeps_strong_reference_until_task_completes(monkeypatch):
    """docs/27 任務 2.1 回歸：`loop.create_task(...)` 的回傳值必須被模組層級的
    `_background_tasks` 強引用，直到 task 完成才移除——否則長達數十秒的分析
    task 在中途可能被 GC 回收（CPython 文件明確警告未被引用的 task 有此風險）。
    """
    monkeypatch.setattr(
        "modules.contribution.service.is_scheduler_enabled", lambda: False
    )
    monkeypatch.setattr(
        "modules.contribution.service.scheduler", type("S", (), {"running": False})()
    )

    async def _run():
        started = asyncio.Event()
        finished = asyncio.Event()

        async def _fake_process_analysis(snapshot_id):
            started.set()
            await asyncio.sleep(0.05)
            finished.set()

        monkeypatch.setattr(
            service_module, "process_analysis", _fake_process_analysis
        )

        queue_host, mode = service._dispatch_analysis("csn_gc_test")
        assert queue_host == "local_async"
        assert mode == "in_process_task"
        # dispatch 完成當下，task 應已在強引用集合中（尚未執行完）
        assert len(service._background_tasks) == 1

        await started.wait()
        await finished.wait()
        # 讓 event loop 跑一次 done_callback
        await asyncio.sleep(0)
        assert len(service._background_tasks) == 0

    asyncio.run(_run())


# ── list / get snapshot ────────────────────────────────────────────
@pytest.mark.integration
def test_list_snapshots_pagination(db, sample_user):
    for i in range(5):
        snap = repository.create_snapshot(
            db,
            account_id="act_list",
            date_start="2026-01-01",
            date_end="2026-06-30",
            config={"n_restarts": 5},
            created_by=sample_user.id,
        )
        repository.set_snapshot_status(db, snap.id, status="completed")
    db.commit()

    page1, total = service.list_snapshots(db, account_id="act_list", page=1, page_size=2)
    page3, _ = service.list_snapshots(db, account_id="act_list", page=3, page_size=2)
    assert total == 5
    assert len(page1) == 2
    assert len(page3) == 1

    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_list"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_get_snapshot_raises_not_found(db):
    with pytest.raises(service.SnapshotNotFound):
        service.get_snapshot(db, "csn_nonexistent_xyz")
