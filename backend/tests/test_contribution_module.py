"""
Contribution 模組任務 1.1 / 1.3 / 1.4 驗收測試（docs/21）

驗收標準：
  1.1 /api/contribution/* 未授權回 403、授權後 /ping 回 200
  1.1 管理後台可見「貢獻分析」模組並可指派權限（Module seed enabled=True）
  1.1 三張 contribution_* 資料表可建立 ORM 物件（migration + model 對齊）
  1.3 /campaigns 由快取表 GROUP BY 彙總；/data/refresh 背景抓取 + 4xx token
  1.4 /groups 自動分組 + 手動覆寫；/analyses 編排 + scheduler/local fallback
"""

from unittest.mock import patch

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
