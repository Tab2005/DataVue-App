# P3：後端重構（長期，1-2 個月）

> **優先級**：🔵 P3 — 長期重構，需充分計畫  
> **預估工時**：3-5 週  
> **涵蓋項目**：3.6、3.7、5.1、5.2、5.3、7.4

---

## 目錄

1. [3.6 — 拆分 database.py 至 database/ 套件](#36--拆分-databasepy-至-database-套件)
2. [3.7 — 拆分 async_services.py 至模組](#37--拆分-async_servicespy-至模組)
3. [5.1 — 拆分 User 整合 Token 至 UserIntegration 表](#51--拆分-user-整合-token-至-userintegration-表)
4. [5.2 — 資料庫索引優化](#52--資料庫索引優化)
5. [5.3 — 開發環境改用 PostgreSQL](#53--開發環境改用-postgresql)
6. [7.4 — 建立 pytest 測試框架](#74--建立-pytest-測試框架)

---

## 3.6 — 拆分 `database.py` 至 `database/` 套件

### 問題說明

`backend/database.py`（324 行）包含資料庫連線設定、所有 ORM 模型、初始化邏輯，職責過重。

### 目標結構

```
backend/database/
├── __init__.py         # 公開 API：匯出所有模型與 get_db
├── engine.py           # 引擎、Session Factory
├── base.py             # DeclarativeBase
└── models/
    ├── __init__.py     # 匯出所有模型
    ├── user.py         # User
    ├── team.py         # Team, TeamMember, TeamInvite
    ├── view.py         # SavedView, PageTitle
    └── permission.py   # Module, Permission, Role, UserModuleAccess, etc.
```

### 實作步驟

**步驟 1：建立 `database/base.py`**

```python
# backend/database/base.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

**步驟 2：建立 `database/engine.py`**

```python
# backend/database/engine.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from core.config import settings

# 同步引擎（用於 Alembic 遷移和直接 Session）
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG,
)

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI 依賴：提供資料庫 Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**步驟 3：建立 `database/models/user.py`**

```python
# backend/database/models/user.py

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from database.base import Base


class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    admin = "admin"
    member = "member"
    viewer = "viewer"


class UserStatus(str, enum.Enum):
    active = "active"
    disabled = "disabled"
    pending = "pending"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    google_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    
    # 角色與狀態
    role = Column(Enum(UserRole), default=UserRole.member, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.active, nullable=False)
    is_super_admin = Column(Boolean, default=False, nullable=False)
    
    # 時間戳記
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User {self.email}>"
```

**步驟 4：建立 `database/models/team.py`**

```python
# backend/database/models/team.py

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
import uuid

from database.base import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # 廣告帳號設定（改用 JSON 型別）
    fb_app_id = Column(String, nullable=True)
    fb_app_secret = Column(String, nullable=True)  # Fernet 加密
    visible_ad_account_ids = Column(JSON, nullable=True, default=list)  # 原為 String
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    members = relationship("TeamMember", back_populates="team", lazy="select")
    invites = relationship("TeamInvite", back_populates="team", lazy="select")


class TeamMember(Base):
    __tablename__ = "team_members"

    team_id = Column(String, ForeignKey("teams.id"), primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True, index=True)
    role = Column(String, default="member", nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 關聯
    team = relationship("Team", back_populates="members")


class TeamInvite(Base):
    __tablename__ = "team_invites"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String, ForeignKey("teams.id"), nullable=False, index=True)
    email = Column(String, nullable=False)
    role = Column(String, default="member", nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 關聯
    team = relationship("Team", back_populates="invites")
```

**步驟 5：建立 `database/models/permission.py`**

```python
# backend/database/models/permission.py

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import relationship
import uuid

from database.base import Base


class Module(Base):
    __tablename__ = "modules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserModuleAccess(Base):
    __tablename__ = "user_module_access"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    team_id = Column(String, ForeignKey("teams.id"), nullable=True)
    module_id = Column(String, ForeignKey("modules.id"), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)
    granted_by = Column(String, ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "team_id", "module_id", name="uq_user_module_access"),
        # 複合索引（查詢時常用 user_id + team_id 過濾）
        Index("ix_user_module_access_lookup", "user_id", "team_id", "module_id"),
    )
```

**步驟 6：建立 `database/__init__.py`（統一匯出）**

```python
# backend/database/__init__.py
"""
資料庫套件的公開 API。
從此處匯入所有模型和資料庫工具，以維持向後相容性。
"""

from database.engine import engine, SessionLocal, get_db
from database.base import Base
from database.models.user import User, UserRole, UserStatus
from database.models.team import Team, TeamMember, TeamInvite
from database.models.view import SavedView, PageTitle
from database.models.permission import (
    Module, Permission, Role, RolePermission,
    UserModuleAccess, UserPermission,
)

__all__ = [
    # 引擎
    "engine", "SessionLocal", "get_db", "Base",
    # 模型
    "User", "UserRole", "UserStatus",
    "Team", "TeamMember", "TeamInvite",
    "SavedView", "PageTitle",
    "Module", "Permission", "Role", "RolePermission",
    "UserModuleAccess", "UserPermission",
]
```

**步驟 7：遷移策略（漸進式）**

```bash
# 1. 建立新的 database/ 目錄結構（不刪除舊 database.py）
# 2. 讓新 database/__init__.py 匯出相同的公開 API
# 3. 執行測試確認所有匯入正常
# 4. 刪除舊的 database.py

# 確認沒有直接 import database 的地方被漏改
grep -r "from database import" backend/
grep -r "import database" backend/
```

### 驗收標準

- [ ] `backend/database/` 目錄結構已建立
- [ ] 所有 ORM 模型已分散至對應的模型文件
- [ ] `database/__init__.py` 維持向後相容的匯出 API
- [ ] Alembic 遷移設定已更新（`env.py` 引用新的 Base）
- [ ] `python -c "from database import User, Team, Module"` 執行成功
- [ ] 所有現有測試（若有）通過

---

## 3.7 — 拆分 `async_services.py` 至模組

### 問題說明

`backend/async_services.py`（834 行）包含所有 Facebook API 非同步邏輯，難以維護與測試。

### 目標結構

```
backend/modules/fb_ads/
├── __init__.py
├── accounts_service.py   # Ad Account 查詢
├── insights_service.py   # 廣告洞察數據
├── analytics_service.py  # 完整分析報告
└── trends_service.py     # 趨勢數據
```

### 實作步驟

**步驟 1：分析現有函式並分類**

```python
# 在 async_services.py 中辨識各類函式：

# accounts_service：
# - get_ad_accounts()
# - get_user_ad_accounts()

# insights_service：
# - get_campaign_insights()
# - get_adset_insights()
# - get_ad_insights()
# - get_insights_with_date_range()

# analytics_service：
# - get_full_analytics_report()
# - get_account_performance()

# trends_service：
# - get_performance_trends()
# - compare_periods()
```

**步驟 2：建立 `modules/fb_ads/accounts_service.py`**

```python
# backend/modules/fb_ads/accounts_service.py

import logging
from typing import Optional
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.user import User as FbUser

from cache import cache_get, cache_set

logger = logging.getLogger(__name__)


async def get_ad_accounts(
    access_token: str,
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
) -> list[dict]:
    """
    取得使用者的所有廣告帳號。
    
    Args:
        access_token: Facebook User Access Token
        app_id: 可選，自訂 App ID
        app_secret: 可選，自訂 App Secret
        
    Returns:
        廣告帳號資訊列表
    """
    cache_key = f"fb_accounts:{hash(access_token)}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    try:
        FacebookAdsApi.init(
            app_id=app_id,
            app_secret=app_secret,
            access_token=access_token,
        )

        me = FbUser(fbid="me")
        accounts = me.get_ad_accounts(fields=[
            "id", "name", "account_status", "currency",
            "timezone_name", "business",
        ])

        result = [account.export_all_data() for account in accounts]
        cache_set(cache_key, result, ttl=300)
        return result

    except Exception as e:
        logger.error(f"[FbAds] 取得廣告帳號失敗: {e}")
        raise
```

**步驟 3：建立統一匯出**

```python
# backend/modules/fb_ads/__init__.py

from modules.fb_ads.accounts_service import get_ad_accounts
from modules.fb_ads.insights_service import get_campaign_insights, get_insights_with_date_range
from modules.fb_ads.analytics_service import get_full_analytics_report
from modules.fb_ads.trends_service import get_performance_trends, compare_periods

__all__ = [
    "get_ad_accounts",
    "get_campaign_insights",
    "get_insights_with_date_range",
    "get_full_analytics_report",
    "get_performance_trends",
    "compare_periods",
]
```

**步驟 4：在 `async_services.py` 添加 Deprecation 警告**

```python
# backend/async_services.py（轉為向後相容橋接層）

"""
⚠️ 此模組已棄用，正在逐步遷移至 modules/fb_ads/。
請直接使用 modules.fb_ads 的對應函式。
"""

import warnings
from modules.fb_ads import (
    get_ad_accounts as _get_ad_accounts,
    get_campaign_insights as _get_campaign_insights,
    # ... 其他函式
)

def get_ad_accounts(*args, **kwargs):
    warnings.warn(
        "async_services.get_ad_accounts 已棄用，請使用 modules.fb_ads.accounts_service",
        DeprecationWarning, stacklevel=2
    )
    return _get_ad_accounts(*args, **kwargs)
```

### 驗收標準

- [ ] `modules/fb_ads/` 目錄已建立並包含四個服務文件
- [ ] 每個服務文件不超過 200 行
- [ ] `async_services.py` 已更新為橋接層（向後相容）
- [ ] 所有相關路由的功能測試通過

---

## 5.1 — 拆分 User 整合 Token 至 UserIntegration 表

### 問題說明

`User` 模型同時存儲 Facebook、GSC、GA4 的 Token 和 AI 設定，職責過多。

### 遷移計畫

**步驟 1：建立新的 Alembic 遷移**

```bash
cd backend
alembic revision --autogenerate -m "add_user_integrations_table"
```

**步驟 2：撰寫遷移腳本**

```python
# backend/alembic/versions/xxxx_add_user_integrations_table.py

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'user_integrations',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expiry', sa.DateTime(), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),  # app_id, app_secret 等
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    
    op.create_index(
        'ix_user_integrations_lookup',
        'user_integrations',
        ['user_id', 'provider'],
        unique=True
    )
    
    # 將現有 User 表中的 Token 資料遷移至新表
    op.execute("""
        INSERT INTO user_integrations (id, user_id, provider, access_token, refresh_token, created_at)
        SELECT 
            hex(randomblob(16)), id, 'facebook', fb_access_token, NULL, datetime('now')
        FROM users 
        WHERE fb_access_token IS NOT NULL
    """)
    
    # 注意：遷移後不要立即刪除舊欄位，先保留一段時間確認資料正確


def downgrade():
    op.drop_index('ix_user_integrations_lookup', table_name='user_integrations')
    op.drop_table('user_integrations')
```

**步驟 3：建立 `database/models/integration.py`**

```python
# backend/database/models/integration.py

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text, UniqueConstraint, Index
import uuid

from database.base import Base


class UserIntegration(Base):
    """使用者第三方服務整合 Token 儲存"""
    __tablename__ = "user_integrations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # 服務提供者：'facebook', 'gsc', 'ga4', 'ai_zeabur', 'ai_gemini'
    provider = Column(String(50), nullable=False)
    
    # Token（Fernet 加密儲存）
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    
    # 額外設定（provider-specific，如 fb_app_id, default_account_id 等）
    extra_data = Column(JSON, nullable=True, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_integration"),
        Index("ix_user_integrations_lookup", "user_id", "provider"),
    )

    def __repr__(self):
        return f"<UserIntegration user={self.user_id} provider={self.provider}>"
```

**步驟 4：建立 `services/integration_service.py`**

```python
# backend/services/integration_service.py

from sqlalchemy.orm import Session
from database.models.integration import UserIntegration
from modules.auth.service import TokenManager


def get_user_integration(db: Session, user_id: str, provider: str) -> UserIntegration | None:
    return db.query(UserIntegration).filter(
        UserIntegration.user_id == user_id,
        UserIntegration.provider == provider,
    ).first()


def upsert_user_integration(
    db: Session,
    user_id: str,
    provider: str,
    access_token: str | None = None,
    refresh_token: str | None = None,
    extra_data: dict | None = None,
) -> UserIntegration:
    """建立或更新使用者整合設定"""
    integration = get_user_integration(db, user_id, provider)
    
    # 加密 Token
    encrypted_access = TokenManager.encrypt(access_token) if access_token else None
    encrypted_refresh = TokenManager.encrypt(refresh_token) if refresh_token else None
    
    if integration:
        if encrypted_access is not None:
            integration.access_token = encrypted_access
        if encrypted_refresh is not None:
            integration.refresh_token = encrypted_refresh
        if extra_data is not None:
            integration.extra_data = {**(integration.extra_data or {}), **extra_data}
    else:
        integration = UserIntegration(
            user_id=user_id,
            provider=provider,
            access_token=encrypted_access,
            refresh_token=encrypted_refresh,
            extra_data=extra_data or {},
        )
        db.add(integration)
    
    db.commit()
    db.refresh(integration)
    return integration


def get_decrypted_token(integration: UserIntegration) -> str | None:
    """取得解密後的 Access Token"""
    if not integration or not integration.access_token:
        return None
    return TokenManager.decrypt(integration.access_token)
```

### 驗收標準

- [ ] `user_integrations` 表已建立並遷移現有 Token 資料
- [ ] `UserIntegration` 模型已建立
- [ ] `integration_service.py` 提供 CRUD 操作
- [ ] 現有存取 `user.fb_access_token` 的程式碼已更新為使用 `integration_service`
- [ ] 舊 User 欄位（經過一段時間確認後）已透過 Alembic 移除

---

## 5.2 — 資料庫索引優化

### 實作步驟

**新增 Alembic 遷移添加複合索引**

```python
# backend/alembic/versions/xxxx_add_composite_indexes.py

from alembic import op

def upgrade():
    # UserModuleAccess 複合索引
    op.create_index(
        'ix_user_module_access_lookup',
        'user_module_access',
        ['user_id', 'team_id', 'module_id']
    )
    
    # TeamMember 以 user_id 查詢索引
    op.create_index(
        'ix_team_members_user_id',
        'team_members',
        ['user_id']
    )
    
    # SavedView 複合索引（使用者的所有 View）
    op.create_index(
        'ix_saved_views_user_team',
        'saved_views',
        ['user_id', 'team_id']
    )

def downgrade():
    op.drop_index('ix_user_module_access_lookup', table_name='user_module_access')
    op.drop_index('ix_team_members_user_id', table_name='team_members')
    op.drop_index('ix_saved_views_user_team', table_name='saved_views')
```

---

## 5.3 — 開發環境改用 PostgreSQL

### 實作步驟

**建立 `docker-compose.dev.yml`**

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://dev:dev@db:5432/datavue_dev
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: datavue_dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev -d datavue_dev"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host

volumes:
  pg_data:
```

---

## 7.4 — 建立 pytest 測試框架

### 目標結構

```
backend/tests/
├── conftest.py              # Fixtures（測試 DB、Mock 使用者）
├── test_auth.py             # 認證測試
├── test_permissions.py      # 權限系統測試
├── test_teams.py            # 團隊管理測試
├── test_cache.py            # 快取邏輯測試
└── integration/
    ├── test_facebook_api.py # Facebook API 整合測試
    └── test_gsc_api.py      # GSC API 整合測試
```

### 核心 Fixtures

```python
# backend/tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, patch

from main import app
from database import Base, get_db
from database.models.user import User, UserRole

# 使用記憶體 SQLite 作為測試資料庫
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """建立測試資料庫表格"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """每個測試使用獨立的資料庫 Session（事務回滾）"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    """FastAPI TestClient，使用測試資料庫"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db) -> User:
    """建立測試使用者"""
    user = User(
        id="test-user-id",
        google_id="google-123",
        email="test@example.com",
        name="Test User",
        role=UserRole.member,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def super_admin_user(db) -> User:
    """建立 Super Admin 測試使用者"""
    user = User(
        id="admin-user-id",
        google_id="google-admin",
        email="admin@example.com",
        name="Admin User",
        role=UserRole.super_admin,
        is_super_admin=True,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def mock_google_token():
    """Mock Google Token 驗證（避免真實 API 呼叫）"""
    with patch("core.security._verify_google_token_raw") as mock:
        mock.return_value = {
            "sub": "google-123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg",
            "email_verified": True,
        }
        yield mock
```

### 測試範例

```python
# backend/tests/test_auth.py

import pytest
from fastapi import status


def test_exchange_token_success(client, db, mock_google_token):
    """正常 Token 交換流程"""
    response = client.post(
        "/api/auth/exchange-token",
        json={"token": "valid-google-token"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"


def test_exchange_token_invalid(client):
    """無效 Token 應返回 401"""
    with patch("core.security._verify_google_token_raw", side_effect=ValueError("Invalid token")):
        response = client.post(
            "/api/auth/exchange-token",
            json={"token": "invalid-token"}
        )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_endpoint_without_token(client):
    """無 Token 存取受保護端點"""
    response = client.get("/api/users/me")
    assert response.status_code == status.HTTP_403_FORBIDDEN


# backend/tests/test_permissions.py

def test_regular_user_cannot_access_admin(client, test_user, mock_google_token):
    """一般使用者不可存取管理員 API"""
    headers = {"Authorization": "Bearer valid-token"}
    response = client.get("/api/admin/users", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_super_admin_can_access_admin(client, super_admin_user, db):
    """Super Admin 可存取管理員 API"""
    with patch("core.security._verify_google_token_raw") as mock:
        mock.return_value = {
            "sub": super_admin_user.google_id,
            "email": super_admin_user.email,
            "name": super_admin_user.name,
            "email_verified": True,
        }
        headers = {"Authorization": "Bearer admin-token"}
        response = client.get("/api/admin/users", headers=headers)
    assert response.status_code == status.HTTP_200_OK
```

**安裝測試依賴**

```bash
pip install pytest pytest-asyncio pytest-cov httpx

# 執行測試
cd backend
pytest tests/ -v --cov=. --cov-report=html
```

### 驗收標準

- [ ] `backend/tests/conftest.py` 已建立並包含核心 fixtures
- [ ] `test_auth.py`、`test_permissions.py`、`test_teams.py` 已建立
- [ ] 所有測試通過（`pytest tests/ -v`）
- [ ] 測試覆蓋率 > 60%（關鍵路徑）
- [ ] CI/CD pipeline（若有）已整合 pytest
