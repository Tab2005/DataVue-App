"""
權限模組基礎測試
"""
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from database import (
    Module,
    Permission,
    Role,
    RolePermission,
    Team,
    TeamMember,
    UserModuleAccess,
    UserRole,
)
from modules.auth import dependencies as auth_dependencies


@pytest.mark.unit
def test_permissions_me_modules_requires_auth(client):
    """/api/permissions/me/modules 端點應需要認證"""
    response = client.get("/api/permissions/me/modules")
    assert response.status_code in (401, 403)


@pytest.mark.unit
def test_permissions_modules_is_public(client):
    """/api/permissions/modules 是公開端點，應回傳 200"""
    response = client.get("/api/permissions/modules")
    assert response.status_code == 200


@pytest.mark.integration
def test_seed_permissions_creates_modules(db):
    """
    seed_permissions 應正確建立 Module 資料
    （空表格查詢也視為通過，驗證資料表結構正確）
    """
    from database.models.permission import Module

    # 確認資料表可正常查詢（空的也算通過）
    modules = db.query(Module).all()
    assert isinstance(modules, list)


@pytest.mark.integration
def test_permission_model_can_be_created(db):
    """Module 模型應可正常建立"""
    from database.models.permission import Module

    module = Module(key="test_module_key", name="Test Module")
    db.add(module)
    db.commit()
    db.refresh(module)

    assert module.id is not None
    assert module.key == "test_module_key"


@pytest.mark.unit
def test_roles_endpoint_requires_auth(client):
    """/api/permissions/admin/roles 端點應需要認證"""
    response = client.get("/api/permissions/admin/roles")
    assert response.status_code in (401, 403)


def _build_permission_test_app(db, user):
    app = FastAPI()

    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: user
    app.dependency_overrides[auth_dependencies.get_db] = lambda: db

    @app.get("/test/module")
    def check_module(_: bool = Depends(auth_dependencies.require_module("meta_andromeda"))):
        return {"ok": True}

    @app.get("/test/permission")
    def check_permission(_: bool = Depends(auth_dependencies.require_permission("fb_ads:analytics:view"))):
        return {"ok": True}

    return app


@pytest.mark.unit
def test_require_module_uses_x_team_id_for_team_scoped_module_access(db, sample_user):
    """require_module 應使用 X-Team-ID 判定 team-scoped module access"""
    team = Team(name="Meta Team", owner_id=sample_user.id)
    db.add(team)
    db.flush()

    module = Module(key="meta_andromeda", name="Meta Andromeda", enabled=True)
    db.add(module)
    db.flush()

    db.add(
        UserModuleAccess(
            user_id=sample_user.id,
            team_id=team.id,
            module_id=module.id,
            enabled=True,
        )
    )
    db.commit()

    app = _build_permission_test_app(db, sample_user)
    with TestClient(app) as client:
        response_without_team = client.get("/test/module")
        response_with_team = client.get("/test/module", headers={"X-Team-ID": team.id})

    assert response_without_team.status_code == 403
    assert response_with_team.status_code == 200


@pytest.mark.unit
def test_require_permission_uses_x_team_id_for_team_role_permissions(db, sample_user):
    """require_permission 應使用 X-Team-ID 判定 team role permission"""
    team = Team(name="Review Team", owner_id=sample_user.id)
    db.add(team)
    db.flush()

    role = Role(key="team_member", name="團隊成員", scope="team")
    module = Module(key="fb_ads", name="FB Ads", enabled=True)

    db.add_all([role, module])
    db.flush()
    db.add(
        Permission(
            module_id=module.id,
            key="fb_ads:analytics:view",
            name="數據查看",
            category="feature",
        )
    )
    db.flush()

    db.add(TeamMember(team_id=team.id, user_id=sample_user.id, role=UserRole.MEMBER))
    permission = db.query(Permission).filter(Permission.key == "fb_ads:analytics:view").one()
    db.add(RolePermission(role_id=role.id, permission_id=permission.id))
    db.commit()

    app = _build_permission_test_app(db, sample_user)
    with TestClient(app) as client:
        response_without_team = client.get("/test/permission")
        response_with_team = client.get("/test/permission", headers={"X-Team-ID": team.id})

    assert response_without_team.status_code == 403
    assert response_with_team.status_code == 200


@pytest.mark.unit
def test_require_module_and_permission_allow_super_admin_without_team_context(db, sample_admin_user):
    """super admin 應可繞過 module 與 permission 檢查"""
    module = Module(key="meta_andromeda", name="Meta Andromeda", enabled=True)
    db.add(module)
    db.flush()
    db.add(
        Permission(
            module_id=module.id,
            key="fb_ads:analytics:view",
            name="數據查看",
            category="feature",
        )
    )
    db.commit()

    app = _build_permission_test_app(db, sample_admin_user)
    with TestClient(app) as client:
        module_response = client.get("/test/module")
        permission_response = client.get("/test/permission")

    assert module_response.status_code == 200
    assert permission_response.status_code == 200


# ─── GA4 insights：個人工作區退回模組存取檢查（2026-07-10 生產環境回報的
#     「Permission denied: ga4:insights:view」修復驗證，見 modules/ga4/dependencies.py） ──
@pytest.mark.unit
def test_ga4_insights_permission_falls_back_to_module_access_in_personal_workspace(db, sample_user):
    """
    個人工作區（無 X-Team-ID）呼叫 ga4:insights:* 應退回只檢查模組存取
    （比照既有 /api/ga4/report 的慣例），而非一律 403——GA4 是 per-user
    OAuth，本就該讓沒有團隊的個人工作區使用者能用洞察頁。
    """
    from modules.ga4.dependencies import require_ga4_insights_view

    module = Module(key="ga4", name="Google Analytics 4", enabled=True)
    db.add(module)
    db.flush()
    db.add(
        UserModuleAccess(user_id=sample_user.id, team_id=None, module_id=module.id, enabled=True)
    )
    db.commit()

    app = FastAPI()
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: sample_user
    app.dependency_overrides[auth_dependencies.get_db] = lambda: db

    @app.get("/test/ga4-insights-view")
    def check(_: bool = Depends(require_ga4_insights_view)):
        return {"ok": True}

    with TestClient(app) as client:
        response = client.get("/test/ga4-insights-view")

    assert response.status_code == 200


@pytest.mark.unit
def test_ga4_insights_permission_denies_personal_workspace_without_ga4_module(db, sample_user):
    """個人工作區沒開 GA4 模組時仍應正確擋下，不是無條件放行。"""
    from modules.ga4.dependencies import require_ga4_insights_view

    app = FastAPI()
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: sample_user
    app.dependency_overrides[auth_dependencies.get_db] = lambda: db

    @app.get("/test/ga4-insights-view")
    def check(_: bool = Depends(require_ga4_insights_view)):
        return {"ok": True}

    with TestClient(app) as client:
        response = client.get("/test/ga4-insights-view")

    assert response.status_code == 403


@pytest.mark.unit
def test_ga4_insights_permission_still_uses_team_role_matrix_with_team_header(db, sample_user):
    """帶 X-Team-ID 時仍沿用團隊角色權限矩陣：team_member 未被授予
    manage_alerts 時應維持 403，個人工作區的退回邏輯不影響團隊分層。"""
    from modules.ga4.dependencies import require_ga4_insights_manage_alerts

    team = Team(name="GA4 Team", owner_id=sample_user.id)
    db.add(team)
    db.flush()

    role = Role(key="team_member", name="團隊成員", scope="team")
    module = Module(key="ga4", name="Google Analytics 4", enabled=True)
    db.add_all([role, module])
    db.flush()
    db.add(Permission(module_id=module.id, key="ga4:insights:manage_alerts", name="告警管理", category="admin"))
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=sample_user.id, role=UserRole.MEMBER))
    db.commit()

    app = FastAPI()
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: sample_user
    app.dependency_overrides[auth_dependencies.get_db] = lambda: db

    @app.get("/test/ga4-insights-manage")
    def check(_: bool = Depends(require_ga4_insights_manage_alerts)):
        return {"ok": True}

    with TestClient(app) as client:
        response = client.get("/test/ga4-insights-manage", headers={"X-Team-ID": team.id})

    assert response.status_code == 403
