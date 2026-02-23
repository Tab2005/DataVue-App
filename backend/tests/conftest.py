"""
pytest Fixtures — DataVue Backend 測試套件

提供測試資料庫、測試客戶端、假使用者等核心 Fixtures。

用法：
    cd backend
    pytest tests/ -v
    pytest tests/ -v --cov=. --cov-report=html
"""

import os
import pytest
from unittest.mock import patch, MagicMock

# ── 設定測試環境變數（必須在 import app 之前）──────────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_datavue.db")
os.environ.setdefault("ENCRYPTION_KEY", "")          # 測試時無加密
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("REDIS_URL", "")               # 測試時不用 Redis
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DEBUG", "true")

# ── SQLAlchemy 測試引擎 ────────────────────────────────────────────────────
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite:///./test_datavue.db"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """Session 開始時建表，結束時清除（沙箱式測試 DB）。"""
    # Patch startup tasks 避免 DB 連線失敗時阻擋測試
    with patch("core.startup.run_startup_tasks", return_value=True):
        from database import Base
        Base.metadata.create_all(bind=engine)
        yield
        Base.metadata.drop_all(bind=engine)
        
    # 確保所有連線已關閉（Windows 檔案鎖定必要）
    engine.dispose()

    # 清除測試資料庫檔案
    import pathlib
    import time
    db_file = pathlib.Path("test_datavue.db")
    if db_file.exists():
        try:
            # 稍微等待確保檔案釋放
            time.sleep(0.1)
            db_file.unlink()
        except PermissionError:
            pass # 如果還是鎖住，交給作業系統或下次測試處理


@pytest.fixture
def db():
    """
    每個測試使用獨立 Session，結束後回滾（隔離副作用）。
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    """
    FastAPI TestClient，覆寫 get_db 依賴為測試 Session。
    """
    from fastapi.testclient import TestClient

    with patch("core.startup.run_startup_tasks", return_value=True):
        from main import app
        from database.engine import get_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ── 使用者 Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def test_user(db):
    """建立一般測試使用者（VIEWER 角色）。"""
    from database.models.user import User, UserRole, UserStatus

    user = User(
        id="test-user-uuid-0001",
        google_id="google-sub-viewer-001",
        email="viewer@test.example.com",
        name="Test Viewer",
        role=UserRole.VIEWER,
        status=UserStatus.ACTIVE,
        is_super_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db):
    """建立 ADMIN 測試使用者。"""
    from database.models.user import User, UserRole, UserStatus

    user = User(
        id="test-admin-uuid-0002",
        google_id="google-sub-admin-002",
        email="admin@test.example.com",
        name="Test Admin",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_super_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def super_admin_user(db):
    """建立 Super Admin 測試使用者。"""
    from database.models.user import User, UserRole, UserStatus

    user = User(
        id="test-superadmin-uuid-0003",
        google_id="google-sub-superadmin-003",
        email="superadmin@test.example.com",
        name="Super Admin",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_super_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Google Token Mock Fixtures ─────────────────────────────────────────────

@pytest.fixture
def mock_google_token_viewer(test_user):
    """Mock Google Token 驗證 → 回傳 test_user 身分。"""
    with patch("core.security._verify_google_token_raw") as mock:
        mock.return_value = {
            "sub": test_user.google_id,
            "email": test_user.email,
            "name": test_user.name,
            "picture": "https://example.com/avatar.jpg",
            "email_verified": True,
        }
        yield mock


@pytest.fixture
def mock_google_token_admin(admin_user):
    """Mock Google Token 驗證 → 回傳 admin_user 身分。"""
    with patch("core.security._verify_google_token_raw") as mock:
        mock.return_value = {
            "sub": admin_user.google_id,
            "email": admin_user.email,
            "name": admin_user.name,
            "picture": "https://example.com/admin_avatar.jpg",
            "email_verified": True,
        }
        yield mock


@pytest.fixture
def mock_google_token_super_admin(super_admin_user):
    """Mock Google Token 驗證 → 回傳 super_admin_user 身分。"""
    with patch("core.security._verify_google_token_raw") as mock:
        mock.return_value = {
            "sub": super_admin_user.google_id,
            "email": super_admin_user.email,
            "name": super_admin_user.name,
            "picture": "https://example.com/sa_avatar.jpg",
            "email_verified": True,
        }
        yield mock


@pytest.fixture
def viewer_auth_headers():
    """帶有偽造 Google Token 的請求 headers（Viewer）。"""
    return {"Authorization": "Bearer fake-viewer-token"}


@pytest.fixture
def admin_auth_headers():
    """帶有偽造 Google Token 的請求 headers（Admin）。"""
    return {"Authorization": "Bearer fake-admin-token"}


@pytest.fixture
def super_admin_auth_headers():
    """帶有偽造 Google Token 的請求 headers（Super Admin）。"""
    return {"Authorization": "Bearer fake-superadmin-token"}
