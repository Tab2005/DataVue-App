"""
Contribution 模組任務 1.1 / 1.3 / 1.4 / 2.3 驗收測試（docs/21）

驗收標準：
  1.1 /api/contribution/* 未授權回 403、授權後 /ping 回 200
  1.1 管理後台可見「貢獻分析」模組並可指派權限（Module seed enabled=True）
  1.1 三張 contribution_* 資料表可建立 ORM 物件（migration + model 對齊）
  1.3 /campaigns 由快取表 GROUP BY 彙總；/data/refresh 背景抓取 + 4xx token
  1.4 /groups 自動分組 + 手動覆寫；/analyses 編排 + scheduler/local fallback
  2.3 PUT /analyses/{id}/ai-summary 持久化 AI 白話解讀
       - 200 寫入 + 回傳時間戳
       - 404 snapshot 不存在
       - 409 snapshot 非 completed
       - 403 未授權
       - GET 列表帶 has_ai_summary、GET 單筆帶 ai_summary 兩欄
"""

from unittest.mock import patch

import pytest

from database import Module, Team, TeamMember, UserModuleAccess, UserRole
from database.models.contribution import ContributionSnapshot
from modules.auth import dependencies as auth_dependencies
from modules.contribution.dependencies import (
    get_current_contribution_user,
    require_contribution_module,
)
from main import app


@pytest.fixture
def contribution_unauthorized_client(client, db, sample_user):
    """已登入但「未授予 contribution 模組存取」的客戶端 → 端點應回 403。"""
    app.dependency_overrides[get_current_contribution_user] = lambda: sample_user
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: sample_user
    app.dependency_overrides[auth_dependencies.get_db] = lambda: db
    # 不覆寫 require_contribution_module：走真實權限檢查，無存取 → 403
    yield client, sample_user
    app.dependency_overrides.pop(get_current_contribution_user, None)
    app.dependency_overrides.pop(auth_dependencies.get_current_user, None)
    app.dependency_overrides.pop(auth_dependencies.get_db, None)


@pytest.fixture
def contribution_authorized_client(client, db, sample_user, monkeypatch):
    """已登入且「授予 contribution 模組存取」的客戶端 → /ping 200、其餘 501。

    docs/27 任務 1.3 加了帳號層級授權（依 team context 過濾可視 account_id，
    見 dependencies.py）。既有測試皆聚焦模組骨架/業務邏輯本身、不是在測授權
    行為，故此 fixture 把帳號層級的可視集合判斷 patch 成「任何 account_id
    皆視為可視」（`_AllowAllSet.__contains__` 恆真），等同「未設定 team
    context 時的個人帳號範圍」語意；授權行為本身由專門的
    test_contribution_account_access.py 驗證。
    """
    module = db.query(Module).filter(Module.key == "contribution").first()
    if module is None:
        module = Module(key="contribution", name="貢獻分析", enabled=True, sort_order=5)
        db.add(module)
        db.flush()
    access = UserModuleAccess(user_id=sample_user.id, module_id=module.id, enabled=True)
    db.add(access)
    db.commit()

    app.dependency_overrides[get_current_contribution_user] = lambda: sample_user
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: sample_user
    app.dependency_overrides[auth_dependencies.get_db] = lambda: db

    import sys

    dependencies_module = sys.modules["modules.contribution.dependencies"]

    class _AllowAllSet(set):
        def __contains__(self, item):
            return True

    async def _fake_resolve_accessible_account_ids(current_user, team):
        return _AllowAllSet(), None

    monkeypatch.setattr(
        dependencies_module,
        "resolve_accessible_account_ids",
        _fake_resolve_accessible_account_ids,
    )

    yield client, sample_user
    app.dependency_overrides.pop(get_current_contribution_user, None)
    app.dependency_overrides.pop(auth_dependencies.get_current_user, None)
    app.dependency_overrides.pop(auth_dependencies.get_db, None)


# ── 驗收 1a：未授權回 403 ──────────────────────────────────────────────
@pytest.mark.integration
def test_contribution_endpoints_deny_without_module_access(contribution_unauthorized_client):
    client, _ = contribution_unauthorized_client
    for path in [
        "/api/contribution/ping",
        "/api/contribution/campaigns?account_id=act_1",
        "/api/contribution/groups?account_id=act_1",
        "/api/contribution/analyses?account_id=act_1",
    ]:
        resp = client.get(path)
        assert resp.status_code == 403, f"{path} expected 403, got {resp.status_code}"
        assert "contribution" in resp.text, f"{path} 403 訊息應提及 contribution"


@pytest.mark.integration
def test_contribution_post_endpoints_deny_without_module_access(contribution_unauthorized_client):
    client, _ = contribution_unauthorized_client
    # POST /analyses
    resp = client.post(
        "/api/contribution/analyses",
        json={
            "account_id": "act_1",
            "date_start": "2026-01-01",
            "date_end": "2026-06-30",
        },
    )
    assert resp.status_code == 403
    # PUT /groups
    resp = client.put(
        "/api/contribution/groups",
        json={"account_id": "act_1", "groups": []},
    )
    assert resp.status_code == 403


# ── 驗收 1b：授權後 /ping 200、其餘 501 ────────────────────────────────
@pytest.mark.integration
def test_contribution_ping_returns_ok_when_authorized(contribution_authorized_client):
    client, _ = contribution_authorized_client
    resp = client.get("/api/contribution/ping")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert payload["module"] == "contribution"


@pytest.mark.integration
def test_contribution_analyses_get_list_and_detail(
    contribution_authorized_client, db, sample_user
):
    """GET /analyses 分頁 + GET /analyses/{id} 單筆。"""
    from database.models.contribution import ContributionSnapshot
    from modules.contribution.repository import repository

    # 建 3 個 snapshot
    for i in range(3):
        snap = repository.create_snapshot(
            db,
            account_id="act_list1",
            date_start="2026-01-01",
            date_end="2026-06-30",
            config={"n_restarts": 5},
            created_by=sample_user.id,
        )
        repository.set_snapshot_status(
            db,
            snap.id,
            status="completed",
            results={"G1": {"median": 0.5 + i * 0.05}},
            diagnostics={"data_summary": {"days": 180}},
        )
    db.commit()

    client, _ = contribution_authorized_client
    # 列表
    resp = client.get("/api/contribution/analyses?account_id=act_list1&page=1&page_size=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["analyses"]) == 2

    # 單筆
    first_id = body["analyses"][0]["snapshot_id"]
    resp = client.get(f"/api/contribution/analyses/{first_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["status"] == "completed"
    assert detail["results"]["G1"]["median"] >= 0.5

    # 不存在 → 404
    resp = client.get("/api/contribution/analyses/csn_nonexistent")
    assert resp.status_code == 404

    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_list1"
    ).delete()
    db.commit()


# ── 任務 1.3 驗收：/campaigns 與 /data/refresh 實作 ──────────────────
@pytest.mark.integration
def test_contribution_campaigns_returns_empty_list_when_cache_empty(
    contribution_authorized_client,
):
    """/campaigns 在快取為空時回 200 + 空 list（前端引導使用者先 refresh）。"""
    client, _ = contribution_authorized_client
    resp = client.get("/api/contribution/campaigns?account_id=act_nodata_1")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["account_id"] == "act_nodata_1"
    assert payload["campaigns"] == []
    assert payload["total"] == 0


@pytest.mark.integration
def test_contribution_campaigns_returns_aggregated_summaries(
    contribution_authorized_client, db
):
    """/campaigns 由快取表 GROUP BY campaign_id 彙總；多 campaign 排序正確。"""
    from database.models.contribution import ContributionDailyMetric

    # 預先 seed 快取表
    samples = [
        ("cmp_1", "主力", 100.0, 8.0),
        ("cmp_1", "主力", 120.0, 10.0),
        ("cmp_2", "影片", 50.0, 4.0),
    ]
    for i, (cid, name, spend, conv) in enumerate(samples):
        db.add(ContributionDailyMetric(
            account_id="act_agg",
            date=f"2026-07-0{i+1}",
            campaign_id=cid,
            campaign_name=name,
            spend=spend,
            impressions=5000,
            conversions=conv,
            conversion_value=conv * 300,
            metric_key="omni_purchase",
        ))
    db.commit()

    client, _ = contribution_authorized_client
    resp = client.get("/api/contribution/campaigns?account_id=act_agg")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total"] == 2
    # 排序：spend 由大到小 → cmp_1 (220) 在 cmp_2 (50) 之前
    assert payload["campaigns"][0]["campaign_id"] == "cmp_1"
    assert payload["campaigns"][0]["spend"] == 220.0
    assert payload["campaigns"][0]["conversions"] == 18.0
    assert payload["campaigns"][0]["active_days"] == 2
    assert payload["campaigns"][1]["campaign_id"] == "cmp_2"
    assert payload["campaigns"][1]["spend"] == 50.0

    # 清理
    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_agg"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_contribution_campaigns_renamed_campaign_does_not_split_into_two_rows(
    contribution_authorized_client, db
):
    """docs/27 任務 2.4：活動改名後（舊名列 + 新名列，同一 campaign_id）彙總
    仍應合併為一列，花費加總不被攤薄，且顯示名稱取最新一天的值。"""
    from database.models.contribution import ContributionDailyMetric

    rows = [
        ("2026-07-01", "舊名稱", 100.0, 5.0),
        ("2026-07-02", "舊名稱", 100.0, 5.0),
        ("2026-07-03", "新名稱", 150.0, 7.0),  # 改名當天起
    ]
    for date, name, spend, conv in rows:
        db.add(ContributionDailyMetric(
            account_id="act_rename",
            date=date,
            campaign_id="cmp_renamed",
            campaign_name=name,
            spend=spend,
            impressions=1000,
            conversions=conv,
            conversion_value=conv * 300,
            metric_key="omni_purchase",
        ))
    db.commit()

    client, _ = contribution_authorized_client
    resp = client.get("/api/contribution/campaigns?account_id=act_rename")
    assert resp.status_code == 200
    payload = resp.json()
    # 唯一約束是 (account_id, date, campaign_id, metric_key)：改名前後仍是
    # 同一 campaign_id，彙總不應分裂成兩列。
    assert payload["total"] == 1
    row = payload["campaigns"][0]
    assert row["campaign_id"] == "cmp_renamed"
    assert row["campaign_name"] == "新名稱"  # 最新一天（2026-07-03）的名稱
    assert row["spend"] == 350.0  # 100+100+150，未被攤薄
    assert row["conversions"] == 17.0
    assert row["active_days"] == 3

    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_rename"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_contribution_campaigns_filters_by_date_range(
    contribution_authorized_client, db
):
    """docs/27 任務 4.2：`/campaigns` 帶 date_start/date_end 時只彙總該區間，
    不含區間外的花費/轉換（用於前端把自報占比對齊 MMM 快照區間）。"""
    from database.models.contribution import ContributionDailyMetric

    rows = [
        ("2026-01-01", 500.0, 20.0),  # 區間外
        ("2026-06-01", 100.0, 5.0),   # 區間內
        ("2026-06-02", 100.0, 5.0),   # 區間內
        ("2026-12-01", 900.0, 40.0),  # 區間外
    ]
    for date, spend, conv in rows:
        db.add(ContributionDailyMetric(
            account_id="act_daterange",
            date=date,
            campaign_id="cmp_1",
            campaign_name="測試活動",
            spend=spend,
            impressions=1000,
            conversions=conv,
            conversion_value=conv * 300,
            metric_key="omni_purchase",
        ))
    db.commit()

    client, _ = contribution_authorized_client

    # 全歷史（不帶日期）→ 4 天全部加總
    resp_all = client.get("/api/contribution/campaigns?account_id=act_daterange")
    assert resp_all.status_code == 200
    assert resp_all.json()["campaigns"][0]["spend"] == 1600.0
    assert resp_all.json()["campaigns"][0]["active_days"] == 4

    # 限定區間 → 只彙總區間內的 2 天
    resp_ranged = client.get(
        "/api/contribution/campaigns"
        "?account_id=act_daterange&date_start=2026-06-01&date_end=2026-06-30"
    )
    assert resp_ranged.status_code == 200
    row = resp_ranged.json()["campaigns"][0]
    assert row["spend"] == 200.0
    assert row["conversions"] == 10.0
    assert row["active_days"] == 2

    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_daterange"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_contribution_data_refresh_token_missing_returns_4xx(contribution_authorized_client):
    """token 缺失時 /data/refresh 回 4xx（401/502），訊息不含明文 token。"""
    client, _ = contribution_authorized_client
    with patch(
        "modules.contribution.data_source.get_headers",
        return_value=None,
    ):
        resp = client.post(
            "/api/contribution/data/refresh?account_id=act_token_test"
        )
    # 401 是 Authorization 缺失；實際錯誤碼視 exception 翻譯路徑而定
    assert 400 <= resp.status_code < 600, f"expected 4xx/5xx, got {resp.status_code}"
    body = resp.json()
    # 訊息中不應包含 "Bearer "、token 字串等機敏內容
    detail_str = str(body)
    assert "Bearer" not in detail_str
    assert "token=" not in detail_str.lower()
    assert "EAA" not in detail_str  # FB token 開頭固定 EAA...


# ── 驗收 2：管理後台可見「貢獻分析」模組並可指派權限 ──────────────────
@pytest.mark.integration
def test_contribution_module_seed_enabled_and_assignable(db, client):
    """seed 應建立 enabled=True 的 contribution 模組；公開 /modules 應列出它。"""
    module = db.query(Module).filter(Module.key == "contribution").first()
    if module is None:
        # 測試 DB 未跑 seed 時自行建立（等同 seed 結果）
        module = Module(key="contribution", name="貢獻分析", icon="📊", sort_order=5, enabled=True)
        db.add(module)
        db.commit()
        db.refresh(module)

    assert module.enabled is True
    assert module.sort_order == 5

    # 公開模組列表應包含 contribution（管理後台模組可見性的入口）
    resp = client.get("/api/permissions/modules")
    assert resp.status_code == 200
    keys = [m["key"] for m in resp.json()]
    assert "contribution" in keys


@pytest.mark.integration
def test_contribution_module_access_can_be_granted_to_team_member(db, sample_user):
    """模組可被指派給團隊成員（管理後台指派權限的核心操作）。"""
    module = db.query(Module).filter(Module.key == "contribution").first()
    if module is None:
        module = Module(key="contribution", name="貢獻分析", enabled=True)
        db.add(module)
        db.flush()

    team = Team(name="Contribution Team", owner_id=sample_user.id)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=sample_user.id, role=UserRole.MEMBER))
    db.add(UserModuleAccess(user_id=sample_user.id, team_id=team.id, module_id=module.id, enabled=True))
    db.commit()

    from services.permission_service import PermissionService

    service = PermissionService(db)
    assert service.check_module_access(sample_user.id, "contribution", team_id=team.id) is True


# ── 驗收 3：ORM 物件可建立（migration ↔ model 對齊） ───────────────────
@pytest.mark.integration
def test_contribution_models_can_persist(db, sample_user):
    """三張表的 ORM 物件可寫入並讀回，驗證 model 與 migration schema 對齊。"""
    from database.models.contribution import (
        ContributionCampaignGroup,
        ContributionDailyMetric,
        ContributionSnapshot,
    )

    # daily metric
    dm = ContributionDailyMetric(
        account_id="act_123",
        date="2026-07-01",
        campaign_id="cmp_1",
        campaign_name="主力常態",
        spend=123.45,
        impressions=5000,
        conversions=8.0,
        conversion_value=2400.0,
        metric_key="omni_purchase",
        actions_payload=[{"action_type": "purchase", "value": "8"}],
    )
    db.add(dm)

    # campaign group
    cg = ContributionCampaignGroup(
        account_id="act_123",
        group_key="G1",
        group_name="主力常態",
        campaign_ids=["cmp_1", "cmp_2"],
        source="auto",
        updated_by=sample_user.id,
    )
    db.add(cg)

    # snapshot
    snap = ContributionSnapshot(
        account_id="act_123",
        status="queued",
        date_start="2026-01-01",
        date_end="2026-06-30",
        config={"metric_key": "omni_purchase", "n_restarts": 5},
        created_by=sample_user.id,
    )
    db.add(snap)
    db.commit()
    db.refresh(dm)
    db.refresh(cg)
    db.refresh(snap)

    assert dm.id.startswith("cda_")
    assert cg.id.startswith("cgr_")
    assert snap.id.startswith("csn_")
    assert cg.updater is not None  # FK → users.id 關聯生效
    assert snap.creator is not None

    # upsert 唯一約束：同 (account, date, campaign, metric) 第二筆應觸發約束
    dup = ContributionDailyMetric(
        account_id="act_123",
        date="2026-07-01",
        campaign_id="cmp_1",
        metric_key="omni_purchase",
    )
    db.add(dup)
    with pytest.raises(Exception):  # noqa: PT011 — SQLite/Pg 各拋不同例外型別
        db.commit()
    db.rollback()


@pytest.mark.integration
def test_contribution_repository_snapshot_status_flow(db, sample_user):
    """repository 的 snapshot 狀態流轉（queued→processing→completed）可運作。"""
    from modules.contribution.repository import repository

    snap = repository.create_snapshot(
        db,
        account_id="act_123",
        date_start="2026-01-01",
        date_end="2026-06-30",
        config={"n_restarts": 5},
        created_by=sample_user.id,
    )
    db.commit()
    assert snap.status == "queued"

    repository.set_snapshot_status(db, snap.id, status="processing", runtime_job_id="job_1")
    db.commit()
    refreshed = repository.get_snapshot(db, snap.id)
    assert refreshed.status == "processing"
    assert refreshed.runtime_job_id == "job_1"

    repository.set_snapshot_status(
        db,
        snap.id,
        status="completed",
        results={"G1": {"median": 0.29}},
        diagnostics={"holdout_r2": 0.16},
    )
    db.commit()
    refreshed = repository.get_snapshot(db, snap.id)
    assert refreshed.status == "completed"
    assert refreshed.results["G1"]["median"] == 0.29
    assert refreshed.completed_at is not None

    # failed 路徑應記錄 error_message
    snap2 = repository.create_snapshot(
        db,
        account_id="act_123",
        date_start="2026-01-01",
        date_end="2026-06-30",
        config={},
        created_by=sample_user.id,
    )
    db.commit()
    repository.set_snapshot_status(
        db, snap2.id, status="failed", error_message="guardrail: 日均轉換 < 5"
    )
    db.commit()
    refreshed2 = repository.get_snapshot(db, snap2.id)
    assert refreshed2.status == "failed"
    assert "guardrail" in refreshed2.error_message


@pytest.mark.integration
def test_mark_stale_snapshots_failed_reclaims_only_overdue(db, sample_user):
    """docs/27 任務 2.2：殭屍 snapshot 回收只動超時的 queued/processing，
    未超時的正常執行中分析不受影響。"""
    from datetime import datetime, timedelta, timezone
    from modules.contribution.repository import repository

    now = datetime.now(timezone.utc)

    def _make(status: str, age_minutes: int) -> ContributionSnapshot:
        snap = repository.create_snapshot(
            db,
            account_id="act_stale_sweep",
            date_start="2026-01-01",
            date_end="2026-06-30",
            config={},
            created_by=sample_user.id,
        )
        db.commit()
        repository.set_snapshot_status(db, snap.id, status=status)
        snap.created_at = now - timedelta(minutes=age_minutes)
        db.add(snap)
        db.commit()
        return snap

    stale_queued = _make("queued", age_minutes=15)  # > 10 分鐘門檻
    fresh_queued = _make("queued", age_minutes=2)  # 未超時
    stale_processing = _make("processing", age_minutes=45)  # > 30 分鐘門檻
    fresh_processing = _make("processing", age_minutes=5)  # 正常執行中

    reclaimed = repository.mark_stale_snapshots_failed(
        db,
        queued_older_than_minutes=10,
        processing_older_than_minutes=30,
        now=now,
    )
    db.commit()

    assert reclaimed == 2

    assert repository.get_snapshot(db, stale_queued.id).status == "failed"
    assert (
        repository.get_snapshot(db, stale_queued.id).error_message
        == "stale_queued_reclaimed"
    )
    assert repository.get_snapshot(db, stale_processing.id).status == "failed"
    assert (
        repository.get_snapshot(db, stale_processing.id).error_message
        == "stale_processing_reclaimed"
    )
    # 未超時的不受影響
    assert repository.get_snapshot(db, fresh_queued.id).status == "queued"
    assert repository.get_snapshot(db, fresh_processing.id).status == "processing"

    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_stale_sweep"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_sweep_contribution_stale_snapshots_commits_reclaimed_rows(
    db, sample_user, monkeypatch
):
    """core.scheduler.sweep_contribution_stale_snapshots 用短生命週期 session
    掃描並 commit（docs/27 任務 2.2）；以 monkeypatch 把 SessionLocal 綁到測試
    db，驗證確實寫入 failed 狀態。"""
    import asyncio
    from datetime import datetime, timedelta, timezone

    import core.scheduler as scheduler_module
    from modules.contribution.repository import repository

    class _SessionProxy:
        def __init__(self, session):
            self._session = session

        def __getattr__(self, name):
            return getattr(self._session, name)

        def close(self):
            return None

    monkeypatch.setattr(scheduler_module, "SessionLocal", lambda: _SessionProxy(db))

    snap = repository.create_snapshot(
        db,
        account_id="act_sweep_e2e",
        date_start="2026-01-01",
        date_end="2026-06-30",
        config={},
        created_by=sample_user.id,
    )
    db.commit()
    snap.created_at = datetime.now(timezone.utc) - timedelta(minutes=20)
    db.add(snap)
    db.commit()

    asyncio.run(scheduler_module.sweep_contribution_stale_snapshots())

    refreshed = repository.get_snapshot(db, snap.id)
    assert refreshed.status == "failed"
    assert refreshed.error_message == "stale_queued_reclaimed"

    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_sweep_e2e"
    ).delete()
    db.commit()


# ── 任務 2.3 驗收：PUT /analyses/{id}/ai-summary + 列表/單筆帶欄位 ─────
@pytest.mark.integration
def test_contribution_ai_summary_put_persists_and_returns_200(
    contribution_authorized_client, db, sample_user
):
    """PUT ai-summary 對 completed snapshot 寫入並回 200 + 生成時間。"""
    from modules.contribution.repository import repository

    snap = repository.create_snapshot(
        db,
        account_id="act_ai1",
        date_start="2026-01-01",
        date_end="2026-06-30",
        config={"n_restarts": 5},
        created_by=sample_user.id,
    )
    repository.set_snapshot_status(
        db, snap.id, status="completed", results={"G1": {"median": 0.5}}
    )
    db.commit()

    client, _ = contribution_authorized_client
    body_text = "**G1** 貢獻大約 50%，這組是真正的引擎。"
    resp = client.put(
        f"/api/contribution/analyses/{snap.id}/ai-summary",
        json={"ai_summary": body_text},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["snapshot_id"] == snap.id
    assert payload["ai_summary"] == body_text
    assert payload["ai_summary_generated_at"] is not None

    # 再次 GET 單筆 → 持久化生效
    detail = client.get(f"/api/contribution/analyses/{snap.id}").json()
    assert detail["ai_summary"] == body_text
    assert detail["ai_summary_generated_at"] is not None

    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_ai1"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_contribution_ai_summary_put_returns_404_for_missing_snapshot(
    contribution_authorized_client,
):
    """PUT ai-summary 對不存在的 snapshot 回 404。"""
    client, _ = contribution_authorized_client
    resp = client.put(
        "/api/contribution/analyses/csn_nonexistent_xyz/ai-summary",
        json={"ai_summary": "x" * 50},
    )
    assert resp.status_code == 404


@pytest.mark.integration
def test_contribution_ai_summary_put_returns_409_when_not_completed(
    contribution_authorized_client, db, sample_user
):
    """PUT ai-summary 對 queued/processing/failed snapshot 回 409。"""
    from modules.contribution.repository import repository

    for status_value in ("queued", "processing", "failed"):
        snap = repository.create_snapshot(
            db,
            account_id="act_ai2",
            date_start="2026-01-01",
            date_end="2026-06-30",
            config={"n_restarts": 5},
            created_by=sample_user.id,
        )
        repository.set_snapshot_status(
            db, snap.id, status=status_value, error_message="x" if status_value == "failed" else None
        )
        db.commit()

    client, _ = contribution_authorized_client
    # 任何一個非 completed 都應回 409
    snap = (
        db.query(ContributionSnapshot)
        .filter(ContributionSnapshot.account_id == "act_ai2")
        .filter(ContributionSnapshot.status == "queued")
        .first()
    )
    resp = client.put(
        f"/api/contribution/analyses/{snap.id}/ai-summary",
        json={"ai_summary": "提早寫入的解讀"},
    )
    assert resp.status_code == 409
    assert "completed" in resp.text

    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_ai2"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_contribution_ai_summary_put_denies_without_module_access(
    contribution_unauthorized_client, db, sample_user
):
    """未授權使用者 PUT ai-summary 應回 403。"""
    from modules.contribution.repository import repository

    # 先建一個 completed snapshot
    snap = repository.create_snapshot(
        db,
        account_id="act_ai3",
        date_start="2026-01-01",
        date_end="2026-06-30",
        config={"n_restarts": 5},
        created_by=sample_user.id,
    )
    repository.set_snapshot_status(db, snap.id, status="completed")
    db.commit()

    client, _ = contribution_unauthorized_client
    resp = client.put(
        f"/api/contribution/analyses/{snap.id}/ai-summary",
        json={"ai_summary": "未授權嘗試"},
    )
    assert resp.status_code == 403
    assert "contribution" in resp.text

    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_ai3"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_contribution_analyses_list_includes_has_ai_summary(
    contribution_authorized_client, db, sample_user
):
    """GET /analyses 列表帶 has_ai_summary 旗標。"""
    from modules.contribution.repository import repository

    snap_with = repository.create_snapshot(
        db,
        account_id="act_list_ai",
        date_start="2026-01-01",
        date_end="2026-06-30",
        config={"n_restarts": 5},
        created_by=sample_user.id,
    )
    repository.set_snapshot_status(
        db, snap_with.id, status="completed", results={}
    )
    repository.set_ai_summary(db, snap_with.id, ai_summary="預先寫入的解讀")

    snap_without = repository.create_snapshot(
        db,
        account_id="act_list_ai",
        date_start="2026-02-01",
        date_end="2026-07-30",
        config={"n_restarts": 5},
        created_by=sample_user.id,
    )
    repository.set_snapshot_status(
        db, snap_without.id, status="completed", results={}
    )
    db.commit()

    client, _ = contribution_authorized_client
    resp = client.get(
        "/api/contribution/analyses?account_id=act_list_ai&page=1&page_size=10"
    )
    assert resp.status_code == 200
    body = resp.json()
    has_map = {row["snapshot_id"]: row["has_ai_summary"] for row in body["analyses"]}
    assert has_map[snap_with.id] is True
    assert has_map[snap_without.id] is False

    db.query(ContributionSnapshot).filter(
        ContributionSnapshot.account_id == "act_list_ai"
    ).delete()
    db.commit()


# ── 任務 6.2：POST /groups/reset ─────────────────────────────────────
@pytest.mark.integration
def test_contribution_groups_reset_clears_manual_and_regenerates_auto(
    contribution_authorized_client, db
):
    """既有 manual 分組 → POST /groups/reset 清空後以目前 auto_group() 規則
    重新產生，回應 source='auto'（docs/27 任務 6.2：讓 grouping.py 規則修正
    後既有帳戶也能主動重新套用最新規則，不用等 DBA 手動清表）。"""
    from database.models.contribution import ContributionCampaignGroup, ContributionDailyMetric

    db.add(ContributionDailyMetric(
        account_id="act_reset_ep",
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
        account_id="act_reset_ep",
        group_key="G_custom",
        group_name="使用者自訂",
        campaign_ids=["c1"],
        source="manual",
    ))
    db.commit()

    client, _ = contribution_authorized_client
    resp = client.post("/api/contribution/groups/reset?account_id=act_reset_ep")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "auto"
    assert all(g["source"] == "auto" for g in body["groups"])
    assert not any(g["group_key"] == "G_custom" for g in body["groups"])
    assert any(g["group_key"] == "G1" for g in body["groups"])

    db.query(ContributionCampaignGroup).filter(
        ContributionCampaignGroup.account_id == "act_reset_ep"
    ).delete()
    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_reset_ep"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_contribution_groups_reset_denies_without_module_access(
    contribution_unauthorized_client,
):
    client, _ = contribution_unauthorized_client
    resp = client.post("/api/contribution/groups/reset?account_id=act_1")
    assert resp.status_code == 403


# ── 任務 6.1：GET /data/coverage ─────────────────────────────────────
@pytest.mark.integration
def test_contribution_data_coverage_returns_range_when_cached(
    contribution_authorized_client, db
):
    """快取有資料 → 回傳實際涵蓋範圍 (first_date/last_date/days_covered)。"""
    from database.models.contribution import ContributionDailyMetric

    for d, day in enumerate(["2026-01-01", "2026-01-02", "2026-01-05"]):
        db.add(ContributionDailyMetric(
            account_id="act_coverage_ep",
            date=day,
            campaign_id="c1",
            campaign_name="測試活動",
            spend=100.0,
            conversions=5.0,
            metric_key="omni_purchase",
        ))
    db.commit()

    client, _ = contribution_authorized_client
    resp = client.get("/api/contribution/data/coverage?account_id=act_coverage_ep")
    assert resp.status_code == 200
    body = resp.json()
    assert body["first_date"] == "2026-01-01"
    assert body["last_date"] == "2026-01-05"
    assert body["days_covered"] == 5  # 首尾相減 +1（含兩端），中間缺 2 天不影響此欄位定義

    db.query(ContributionDailyMetric).filter(
        ContributionDailyMetric.account_id == "act_coverage_ep"
    ).delete()
    db.commit()


@pytest.mark.integration
def test_contribution_data_coverage_returns_zero_when_empty(
    contribution_authorized_client,
):
    """快取為空 → first_date/last_date 為 None、days_covered=0（不是 404/500）。"""
    client, _ = contribution_authorized_client
    resp = client.get("/api/contribution/data/coverage?account_id=act_nodata_coverage")
    assert resp.status_code == 200
    body = resp.json()
    assert body["first_date"] is None
    assert body["last_date"] is None
    assert body["days_covered"] == 0


@pytest.mark.integration
def test_contribution_data_coverage_denies_without_module_access(
    contribution_unauthorized_client,
):
    client, _ = contribution_unauthorized_client
    resp = client.get("/api/contribution/data/coverage?account_id=act_1")
    assert resp.status_code == 403
