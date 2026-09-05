"""
FB Ads 模組帳號層級授權測試

背景：`dashboard-data` / `analytics-data` / `analytics-trend` 這三個端點過去
直接把 query string 傳入的 account_id 拿去打 Facebook API，完全沒有比對
`team.visible_ad_account_ids` 白名單（只有 `/ad-accounts` 清單端點有做過濾）。
非 owner 的團隊成員只要知道/猜到白名單外的 act_id，仍能用團隊 token 讀到完整
廣告成效資料，等同繞過團隊隔離。

本檔驗證新增的 `_ensure_account_access`（沿用與 contribution/ga4 模組相同的
`resolve_accessible_account_ids` 判斷邏輯）：帳號不在可視範圍內回 403，在範圍
內則放行並回 200。
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

import dependencies as root_dependencies
from database import Module, Team, TeamMember, UserModuleAccess, UserRole
from modules.fb_ads import AsyncFacebookService, accounts_service
from modules.fb_ads import router as fb_ads_router
from main import app


@pytest.fixture
def fb_ads_client_with_module_access(client, db, sample_user):
    """已登入且有 fb_ads 模組權限，但**不 patch 帳號授權層**——用於實際驗證
    授權通過/拒絕的行為。"""
    module = db.query(Module).filter(Module.key == "fb_ads").first()
    if module is None:
        module = Module(key="fb_ads", name="廣告管理", enabled=True, sort_order=1)
        db.add(module)
        db.flush()
    access = UserModuleAccess(user_id=sample_user.id, module_id=module.id, enabled=True)
    db.add(access)
    db.commit()

    app.dependency_overrides[fb_ads_router.verify_google_token] = lambda: sample_user.google_id
    app.dependency_overrides[root_dependencies.get_current_user] = lambda: sample_user
    app.dependency_overrides[root_dependencies.get_db] = lambda: db
    yield client, sample_user
    app.dependency_overrides.pop(fb_ads_router.verify_google_token, None)
    app.dependency_overrides.pop(root_dependencies.get_current_user, None)
    app.dependency_overrides.pop(root_dependencies.get_db, None)
    app.dependency_overrides.pop(root_dependencies.get_current_team, None)


def _override_team(team):
    app.dependency_overrides[root_dependencies.get_current_team] = lambda: team


def _make_team(db, user, *, owner_id: str, visible_ad_account_ids: str | None):
    team = Team(name="Test Team", owner_id=owner_id, visible_ad_account_ids=visible_ad_account_ids)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=user.id, role=UserRole.VIEWER))
    db.commit()
    return team


def _cleanup_team(db, team):
    db.query(TeamMember).filter(TeamMember.team_id == team.id).delete()
    db.query(Team).filter(Team.id == team.id).delete()
    db.commit()


ENDPOINTS = [
    ("/api/dashboard-data", {"account_id": "{account_id}", "days": 7}),
    (
        "/api/analytics-data",
        {"account_id": "{account_id}", "since": "2026-01-01", "until": "2026-01-31"},
    ),
    (
        "/api/analytics-trend",
        {"account_id": "{account_id}", "since": "2026-01-01", "until": "2026-01-31"},
    ),
]


def _request(client, path: str, params: dict, account_id: str):
    query = {k: (v.format(account_id=account_id) if isinstance(v, str) else v) for k, v in params.items()}
    return client.get(path, params=query)


@pytest.mark.integration
@pytest.mark.parametrize("path,params", ENDPOINTS)
def test_denies_owner_account_outside_meta_scope(
    fb_ads_client_with_module_access, db, sample_user, path, params
):
    """owner（無 team header，個人範圍）：查詢自己 FB token 看不到的 account_id → 403。"""
    client, user = fb_ads_client_with_module_access
    _override_team(None)
    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_mine"}], None)),
    ):
        resp = _request(client, path, params, "act_not_mine")
    assert resp.status_code == 403
    assert "act_not_mine" in resp.text


@pytest.mark.integration
@pytest.mark.parametrize("path,params", ENDPOINTS)
def test_allows_owner_account_inside_meta_scope(
    fb_ads_client_with_module_access, db, sample_user, path, params
):
    """owner：查詢自己 FB token 看得到的 account_id → 200（下游 FB API 呼叫另行 mock）。"""
    client, user = fb_ads_client_with_module_access
    _override_team(None)
    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_mine"}], None)),
    ), patch.object(
        AsyncFacebookService, "get_account_insights", new=AsyncMock(return_value={"kpi": {}}),
    ), patch.object(
        AsyncFacebookService, "get_custom_report", new=AsyncMock(return_value={"rows": []}),
    ), patch.object(
        AsyncFacebookService, "get_analytics_trend", new=AsyncMock(return_value=[]),
    ):
        resp = _request(client, path, params, "act_mine")
    assert resp.status_code == 200


@pytest.mark.integration
@pytest.mark.parametrize("path,params", ENDPOINTS)
def test_denies_non_owner_account_outside_whitelist(
    fb_ads_client_with_module_access, db, sample_user, path, params
):
    """非 owner + team 白名單：team token 看得到、但不在白名單內的帳號 → 403
    （這是原本的漏洞：修復前這裡會回 200 並洩漏白名單外的廣告成效資料）。"""
    client, user = fb_ads_client_with_module_access
    team = _make_team(
        db, user, owner_id="someone_else", visible_ad_account_ids=json.dumps(["act_whitelisted"])
    )
    _override_team(team)

    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_whitelisted"}, {"id": "act_not_whitelisted"}], None)),
    ):
        resp = _request(client, path, params, "act_not_whitelisted")
    assert resp.status_code == 403

    _cleanup_team(db, team)


@pytest.mark.integration
@pytest.mark.parametrize("path,params", ENDPOINTS)
def test_allows_non_owner_account_inside_whitelist(
    fb_ads_client_with_module_access, db, sample_user, path, params
):
    """非 owner + team 白名單：白名單內的帳號 → 200。"""
    client, user = fb_ads_client_with_module_access
    team = _make_team(
        db, user, owner_id="someone_else", visible_ad_account_ids=json.dumps(["act_whitelisted"])
    )
    _override_team(team)

    with patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": "act_whitelisted"}, {"id": "act_not_whitelisted"}], None)),
    ), patch.object(
        AsyncFacebookService, "get_account_insights", new=AsyncMock(return_value={"kpi": {}}),
    ), patch.object(
        AsyncFacebookService, "get_custom_report", new=AsyncMock(return_value={"rows": []}),
    ), patch.object(
        AsyncFacebookService, "get_analytics_trend", new=AsyncMock(return_value=[]),
    ):
        resp = _request(client, path, params, "act_whitelisted")
    assert resp.status_code == 200

    _cleanup_team(db, team)
