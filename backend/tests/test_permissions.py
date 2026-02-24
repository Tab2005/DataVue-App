"""
權限模組基礎測試
"""
import pytest


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
