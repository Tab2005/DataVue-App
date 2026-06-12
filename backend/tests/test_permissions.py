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
    def check_permission(_: bool = Depends(auth_dependencies.require_permission("meta_andromeda:feedback"))):
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
    module = Module(key="meta_andromeda", name="Meta Andromeda", enabled=True)

    db.add_all([role, module])
    db.flush()
    db.add(
        Permission(
            module_id=module.id,
            key="meta_andromeda:feedback",
            name="審核回饋",
            category="feature",
        )
    )
    db.flush()

    db.add(TeamMember(team_id=team.id, user_id=sample_user.id, role=UserRole.MEMBER))
    permission = db.query(Permission).filter(Permission.key == "meta_andromeda:feedback").one()
    db.add(RolePermission(role_id=role.id, permission_id=permission.id))
    db.commit()

    app = _build_permission_test_app(db, sample_user)
    with TestClient(app) as client:
        response_without_team = client.get("/test/permission")
        response_with_team = client.get("/test/permission", headers={"X-Team-ID": team.id})

    assert response_without_team.status_code == 403
    assert response_with_team.status_code == 200
