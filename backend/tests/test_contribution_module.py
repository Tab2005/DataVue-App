"""
Contribution 模組任務 1.1 驗收測試（docs/21）

驗收標準：
  1. /api/contribution/* 未授權回 403、授權後 /ping 回 200、其餘端點回 501
  2. 管理後台可見「貢獻分析」模組並可指派權限（Module seed enabled=True）
  3. 三張 contribution_* 資料表可建立 ORM 物件（migration + model 對齊）
"""

import pytest

from database import Module, Team, TeamMember, UserModuleAccess, UserRole
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
def contribution_authorized_client(client, db, sample_user):
    """已登入且「授予 contribution 模組存取」的客戶端 → /ping 200、其餘 501。"""
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
def test_contribution_unimplemented_endpoints_return_501(contribution_authorized_client):
    """授權後，任務 1.1 尚未實作的端點應回 501（非 500、非 404）。"""
    client, _ = contribution_authorized_client

    # GET 類
    for path in [
        "/api/contribution/campaigns?account_id=act_1",
        "/api/contribution/groups?account_id=act_1",
        "/api/contribution/analyses?account_id=act_1",
        "/api/contribution/analyses/csn_dummy",
    ]:
        resp = client.get(path)
        assert resp.status_code == 501, f"GET {path} expected 501, got {resp.status_code}"

    # POST /analyses → 501（注意：端點宣告 status_code=202，但本波主動拋 501）
    resp = client.post(
        "/api/contribution/analyses",
        json={
            "account_id": "act_1",
            "date_start": "2026-01-01",
            "date_end": "2026-06-30",
        },
    )
    assert resp.status_code == 501

    # PUT /groups → 501
    resp = client.put(
        "/api/contribution/groups",
        json={"account_id": "act_1", "groups": []},
    )
    assert resp.status_code == 501

    # POST /data/refresh → 501
    resp = client.post("/api/contribution/data/refresh?account_id=act_1")
    assert resp.status_code == 501


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
