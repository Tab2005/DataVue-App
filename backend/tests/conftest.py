"""
共用測試 Fixtures

使用 SQLite in-memory 作為測試資料庫，確保：
1. 每個測試函式使用獨立的 DB transaction（測試後自動 rollback）
2. 不干擾本地開發的 SQLite 檔案
3. 不需要 PostgreSQL 連線即可執行所有單元測試
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from database.base import Base
from database import get_db
from main import app

# ─── 測試資料庫設定 ────────────────────────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ─── Session-level Fixtures ───────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """建立所有資料表（整個測試 session 共用）"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ─── Function-level Fixtures ──────────────────────────────────────
@pytest.fixture
def db():
    """
    提供一個在測試後自動 rollback 的 DB session。
    保證每個測試函式之間互相隔離。
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
    提供 FastAPI TestClient，並覆寫 get_db 依賴。
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass  # rollback 由 db fixture 負責

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_verify_google_token():
    """
    Mock Google Token 驗證，避免實際呼叫 Google API。
    回傳一個標準的已驗證 payload。
    """
    mock_payload = {
        "sub": "google_test_user_123",
        "email": "test@example.com",
        "email_verified": True,
        "name": "Test User",
        "picture": "https://example.com/photo.jpg",
    }
    with patch("core.security.verify_google_token_and_get_sub", return_value="google_test_user_123"):
        yield mock_payload


@pytest.fixture
def mock_redis():
    """Mock Redis 連線，讓快取測試不依賴真實 Redis 服務"""
    with patch("cache._get_redis") as mock:
        mock_client = MagicMock()
        mock_client.get.return_value = None  # 預設快取 miss
        mock_client.setex.return_value = True
        mock_client.delete.return_value = 1
        mock.return_value = mock_client
        yield mock_client


# ─── 測試資料 Factories ──────────────────────────────────────────
@pytest.fixture
def sample_user(db):
    """建立一個測試用 User 實例"""
    from database.models.user import User, UserRole, UserStatus

    user = User(
        google_id="google_test_user_123",
        email="test@example.com",
        name="Test User",
        role=UserRole.VIEWER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_admin_user(db):
    """建立一個測試用管理員 User 實例"""
    from database.models.user import User, UserRole, UserStatus

    user = User(
        google_id="google_admin_user_456",
        email="admin@example.com",
        name="Admin User",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_super_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
