"""
Contribution 模組帳號層級授權測試（docs/27 任務 1.3）

背景：contribution 讀寫本地快取表（daily metrics / groups / snapshots），
不像 fb_ads 有「用自己 token 打 Meta API」的隱性授權門檻——審查發現任何有
`contribution` 模組權限的使用者原本可用任意 account_id 讀到其他團隊帳號的
快取資料。本檔驗證新增的授權層：

  1. `resolve_accessible_account_ids`（純函數層）：owner / 非 owner 白名單 /
     錯誤傳遞 / 白名單格式異常 的可視集合計算邏輯。
  2. Router 層：帳號類端點（campaigns / groups / analyses 列表）未授權回
     403；snapshot 類端點（analyses 單筆 / ai-summary）未授權回 404（與
     「不存在」同訊息，避免洩漏 snapshot 是否存在）。
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from database import Module, Team, TeamMember, UserModuleAccess, UserRole
from database.models.contribution import ContributionSnapshot
from modules.auth import dependencies as auth_dependencies
from modules.contribution.dependencies import get_current_contribution_user
from modules.fb_ads import accounts_service
from main import app


# ── 1. resolve_accessible_account_ids（純函數層，不經 HTTP） ───────────
class _FakeUser:
    def __init__(self, user_id: str, google_id: str):
        self.id = user_id
        self.google_id = google_id


class _FakeTeam:
    def __init__(self, owner_id: str, visible_ad_account_ids: str | None = None, team_id: str = "team_1"):
        self.id = team_id
        self.owner_id = owner_id
        self.visible_ad_account_ids = visible_ad_account_ids


@pytest.mark.asyncio
async def test_resolve_accessible_ids_no_team_returns_unfiltered_meta_accounts():
    """無 team context（個人範圍）：回傳使用者自己 FB token 可見的全部帳號，不受白名單限制。"""
    user = _FakeUser("u1", "g1")
    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_1"}, {"id": "act_2"}], None)),
    ):
        ids, error = await accounts_service.resolve_accessible_account_ids(user, None)
    assert error is None
    assert "act_1" in ids and "act_2" in ids
    assert "1" in ids  # 純數字型式也應涵蓋


@pytest.mark.asyncio
async def test_resolve_accessible_ids_owner_unfiltered_by_whitelist():
    """team owner：即使 team 設有白名單，owner 仍見自己 FB token 下的全部帳號（同 /api/ad-accounts 規則）。"""
    user = _FakeUser("owner_1", "g_owner")
    team = _FakeTeam(owner_id="owner_1", visible_ad_account_ids=json.dumps(["act_whitelisted"]))
    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_whitelisted"}, {"id": "act_not_whitelisted"}], None)),
    ):
        ids, error = await accounts_service.resolve_accessible_account_ids(user, team)
    assert error is None
    assert "act_whitelisted" in ids
    assert "act_not_whitelisted" in ids  # owner 不受白名單過濾


@pytest.mark.asyncio
async def test_resolve_accessible_ids_non_owner_filtered_by_whitelist():
    """非 owner：可視集合 = team token 可見帳號 ∩ 白名單。"""
    user = _FakeUser("member_1", "g_member")
    team = _FakeTeam(owner_id="owner_1", visible_ad_account_ids=json.dumps(["act_whitelisted"]))
    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_whitelisted"}, {"id": "act_not_whitelisted"}], None)),
    ):
        ids, error = await accounts_service.resolve_accessible_account_ids(user, team)
    assert error is None
    assert "act_whitelisted" in ids
    assert "act_not_whitelisted" not in ids


@pytest.mark.asyncio
async def test_resolve_accessible_ids_non_owner_no_whitelist_means_no_restriction_beyond_meta():
    """非 owner 但 team 未設定白名單：僅受 team token 可見範圍限制，不額外過濾。"""
    user = _FakeUser("member_1", "g_member")
    team = _FakeTeam(owner_id="owner_1", visible_ad_account_ids=None)
    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_visible"}], None)),
    ):
        ids, error = await accounts_service.resolve_accessible_account_ids(user, team)
    assert error is None
    assert "act_visible" in ids


@pytest.mark.asyncio
async def test_resolve_accessible_ids_propagates_error_as_empty_set():
    """get_all_ad_accounts 回錯誤時，回傳空集合 + error（呼叫端應保守拒絕）。"""
    user = _FakeUser("u1", "g1")
    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([], "No access token found for this user.")),
    ):
        ids, error = await accounts_service.resolve_accessible_account_ids(user, None)
    assert error is not None
    assert ids == set()


@pytest.mark.asyncio
async def test_resolve_accessible_ids_malformed_whitelist_returns_empty_set():
    """team.visible_ad_account_ids 格式異常（非 JSON list）：保守回空集合，不放行。"""
    user = _FakeUser("member_1", "g_member")
    team = _FakeTeam(owner_id="owner_1", visible_ad_account_ids="not-json")
    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_1"}], None)),
    ):
        ids, error = await accounts_service.resolve_accessible_account_ids(user, team)
    assert ids == set()


# ── 2. Router 層：帳號類端點 403 / snapshot 類端點 404 ─────────────────
@pytest.fixture
def contribution_client_with_module_access(client, db, sample_user):
    """已登入且有 contribution 模組權限，但**不 patch 帳號授權層**——用於
    實際驗證授權通過/拒絕的行為（有別於 test_contribution_module.py 的
    `contribution_authorized_client`，那個 fixture 為了聚焦其他業務邏輯而
    把帳號授權層 patch 為全放行）。
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
    yield client, sample_user
    app.dependency_overrides.pop(get_current_contribution_user, None)
    app.dependency_overrides.pop(auth_dependencies.get_current_user, None)
    app.dependency_overrides.pop(auth_dependencies.get_db, None)
    app.dependency_overrides.pop(auth_dependencies.get_current_team, None)


def _override_team(team):
    app.dependency_overrides[auth_dependencies.get_current_team] = lambda: team


@pytest.mark.integration
def test_campaigns_denies_account_outside_owner_meta_scope(
    contribution_client_with_module_access, db, sample_user
):
    """owner（無 team header，個人範圍）：查詢自己 FB token 看不到的 account_id → 403。"""
    client, user = contribution_client_with_module_access
    _override_team(None)
    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_mine"}], None)),
    ):
        resp = client.get("/api/contribution/campaigns?account_id=act_not_mine")
    assert resp.status_code == 403
    assert "act_not_mine" in resp.text


@pytest.mark.integration
def test_campaigns_allows_account_inside_owner_meta_scope(
    contribution_client_with_module_access, db, sample_user
):
    """owner：查詢自己 FB token 看得到的 account_id → 200。"""
    client, user = contribution_client_with_module_access
    _override_team(None)
    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_mine"}], None)),
    ):
        resp = client.get("/api/contribution/campaigns?account_id=act_mine")
    assert resp.status_code == 200


@pytest.mark.integration
def test_campaigns_denies_non_owner_account_outside_whitelist(
    contribution_client_with_module_access, db, sample_user
):
    """非 owner + team 白名單：team token 看得到、但不在白名單內的帳號 → 403。"""
    client, user = contribution_client_with_module_access
    team = Team(
        name="Other Owner Team",
        owner_id="someone_else",
        visible_ad_account_ids=json.dumps(["act_whitelisted"]),
    )
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=user.id, role=UserRole.VIEWER))
    db.commit()
    _override_team(team)

    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_whitelisted"}, {"id": "act_not_whitelisted"}], None)),
    ):
        resp = client.get("/api/contribution/campaigns?account_id=act_not_whitelisted")
    assert resp.status_code == 403

    db.query(TeamMember).filter(TeamMember.team_id == team.id).delete()
    db.query(Team).filter(Team.id == team.id).delete()
    db.commit()


@pytest.mark.integration
def test_campaigns_allows_non_owner_account_inside_whitelist(
    contribution_client_with_module_access, db, sample_user
):
    """非 owner + team 白名單：白名單內的帳號 → 200。"""
    client, user = contribution_client_with_module_access
    team = Team(
        name="Other Owner Team 2",
        owner_id="someone_else",
        visible_ad_account_ids=json.dumps(["act_whitelisted"]),
    )
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=user.id, role=UserRole.VIEWER))
    db.commit()
    _override_team(team)

    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_whitelisted"}, {"id": "act_not_whitelisted"}], None)),
    ):
        resp = client.get("/api/contribution/campaigns?account_id=act_whitelisted")
    assert resp.status_code == 200

    db.query(TeamMember).filter(TeamMember.team_id == team.id).delete()
    db.query(Team).filter(Team.id == team.id).delete()
    db.commit()


@pytest.mark.integration
def test_groups_get_and_put_deny_unauthorized_account(
    contribution_client_with_module_access, db, sample_user
):
    """GET /groups 與 PUT /groups 皆需通過帳號授權（不只 campaigns）。"""
    client, user = contribution_client_with_module_access
    _override_team(None)
    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_mine"}], None)),
    ):
        resp = client.get("/api/contribution/groups?account_id=act_not_mine")
        assert resp.status_code == 403

        resp = client.put(
            "/api/contribution/groups",
            json={"account_id": "act_not_mine", "groups": []},
        )
        assert resp.status_code == 403


@pytest.mark.integration
def test_analyses_list_denies_unauthorized_account(
    contribution_client_with_module_access, db, sample_user
):
    client, user = contribution_client_with_module_access
    _override_team(None)
    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_mine"}], None)),
    ):
        resp = client.get("/api/contribution/analyses?account_id=act_not_mine")
    assert resp.status_code == 403


@pytest.mark.integration
def test_analysis_detail_denies_unauthorized_account_with_404_not_403(
    contribution_client_with_module_access, db, sample_user
):
    """GET /analyses/{id}：帳號未授權時回 404（與 snapshot 不存在同訊息），
    不可回 403（避免探測者用狀態碼差異判斷 snapshot_id 是否存在）。"""
    client, user = contribution_client_with_module_access
    _override_team(None)

    snap = ContributionSnapshot(
        account_id="act_not_mine",
        status="completed",
        date_start="2026-01-01",
        date_end="2026-06-30",
        config={},
        results={"groups": {}, "base_share": {}, "r2": {}, "seeds": []},
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)

    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_mine"}], None)),
    ):
        resp = client.get(f"/api/contribution/analyses/{snap.id}")
    assert resp.status_code == 404
    assert "不存在" in resp.text
    # 對照組：真的不存在的 snapshot 也應回同樣的 404 訊息（無法從回應分辨兩種情況）
    # 注意：main.py 的全域 HTTPException handler 把回應改寫為 {"error": ...}
    # （非 FastAPI 預設的 {"detail": ...}），故讀 "error" 欄位。
    resp_missing = client.get("/api/contribution/analyses/csn_truly_missing")
    assert resp_missing.status_code == 404, resp_missing.text
    assert resp_missing.json()["error"] == resp.json()["error"].replace(snap.id, "csn_truly_missing")

    db.query(ContributionSnapshot).filter(ContributionSnapshot.id == snap.id).delete()
    db.commit()


@pytest.mark.integration
def test_analysis_detail_allows_authorized_account(
    contribution_client_with_module_access, db, sample_user
):
    client, user = contribution_client_with_module_access
    _override_team(None)

    snap = ContributionSnapshot(
        account_id="act_mine",
        status="completed",
        date_start="2026-01-01",
        date_end="2026-06-30",
        config={},
        results={"groups": {}, "base_share": {}, "r2": {}, "seeds": []},
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)

    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_mine"}], None)),
    ):
        resp = client.get(f"/api/contribution/analyses/{snap.id}")
    assert resp.status_code == 200

    db.query(ContributionSnapshot).filter(ContributionSnapshot.id == snap.id).delete()
    db.commit()


@pytest.mark.integration
def test_ai_summary_put_denies_unauthorized_account_with_404(
    contribution_client_with_module_access, db, sample_user
):
    client, user = contribution_client_with_module_access
    _override_team(None)

    snap = ContributionSnapshot(
        account_id="act_not_mine",
        status="completed",
        date_start="2026-01-01",
        date_end="2026-06-30",
        config={},
        results={"groups": {}, "base_share": {}, "r2": {}, "seeds": []},
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)

    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_mine"}], None)),
    ):
        resp = client.put(
            f"/api/contribution/analyses/{snap.id}/ai-summary",
            json={"ai_summary": "測試內容"},
        )
    assert resp.status_code == 404

    db.query(ContributionSnapshot).filter(ContributionSnapshot.id == snap.id).delete()
    db.commit()
