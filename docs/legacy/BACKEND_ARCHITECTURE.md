# DataVue-App - 後端架構文件

## 📖 概述

本文件詳細說明 DataVue-App 後端的架構設計、模組組織、資料流向及最佳實踐。

---

## 🏗️ 整體架構

### 設計原則

1. **模組化 (Modularity)：** 功能模組獨立、可重用
2. **關注點分離 (Separation of Concerns)：** 路由、業務邏輯、資料存取分離
3. **依賴注入 (Dependency Injection)：** 使用 FastAPI Depends 實現權限控制
4. **統一錯誤處理：** 自訂例外類別、統一 JSON 回應格式
5. **可測試性：** 鬆耦合設計、易於單元測試

### 架構層級

```
┌─────────────────────────────────────────────────┐
│              FastAPI Application                │
│                   (main.py)                     │
└─────────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
│   Routers    │ │ Modules  │ │    Core     │
│ (API Layer)  │ │(Business)│ │ (Utilities) │
└───────┬──────┘ └────┬─────┘ └──────┬──────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │     Services & Database     │
        │   (Data Access Layer)       │
        └─────────────────────────────┘
```

---

## 📁 目錄結構詳解

### 1. 核心模組 (`core/`)

**職責：** 提供共用工具、配置、啟動邏輯

```
core/
├── __init__.py
├── config.py           # 環境變數管理、配置載入
├── security.py         # 加密/解密工具 (Fernet)
├── exceptions.py       # 自訂例外類別
└── startup.py          # 應用啟動任務 (DB 初始化、遷移)
```

#### 關鍵功能

- **config.py：** 
  - 環境變數驗證
  - 配置集中管理
  - 支援多環境 (dev/staging/prod)

- **security.py：**
  ```python
  from cryptography.fernet import Fernet
  
  def encrypt_data(data: str) -> str:
      """使用 Fernet 加密敏感資料"""
      pass
  
  def decrypt_data(encrypted: str) -> str:
      """解密資料"""
      pass
  ```

- **exceptions.py：**
  ```python
  class AppException(Exception):
      """基礎例外類別"""
      status_code: int
      error_code: str
      detail: str
  
  class AuthenticationError(AppException):
      status_code = 401
  
  class AuthorizationError(AppException):
      status_code = 403
  ```

- **startup.py：**
  - 環境變數驗證
  - 資料庫連線測試
  - Alembic 遷移自動執行
  - 初始化種子資料 (Modules, Permissions)

### 2. 模組系統 (`modules/`)

**職責：** 獨立、可重用的功能模組

#### 模組結構範例 (`modules/auth/`)

```
auth/
├── __init__.py         # 導出 router, service, dependencies
├── router.py           # FastAPI Router (/api/auth/*)
├── service.py          # TokenManager 業務邏輯
├── dependencies.py     # get_current_user, require_module
├── models.py           # (選用) Pydantic 模型
└── README.md           # 模組文件
```

#### 各模組說明

##### 🔐 Auth Module (`modules/auth/`)

**功能：**
- Google OAuth Token 驗證
- Facebook Token 管理
- 使用者認證依賴注入
- 模組權限檢查

**關鍵依賴：**
```python
# dependencies.py
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """驗證 Google Token，返回當前使用者"""
    pass

def require_module(module_name: str):
    """檢查使用者是否有指定模組權限"""
    def _check(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        if not has_module_access(user, module_name, db):
            raise HTTPException(403, f"No access to {module_name}")
        return True
    return _check
```

##### 🤖 AI Hub Module (`modules/ai_hub/`)

**功能：**
- 多 AI 供應商整合 (Gemini, Zeabur)
- 加密儲存 API Keys
- 串流分析回應
- 意圖分類器

**API 端點：**
- `GET /api/ai/providers` - 列出供應商
- `POST /api/ai/analyze` - 數據分析
- `POST /api/ai/analyze-stream` - SSE 串流
- `GET /api/ai/settings` - 取得設定
- `POST /api/ai/settings` - 儲存設定 (加密)

##### 📊 GSC Module (`modules/gsc/`)

**功能：**
- OAuth2 授權流程
- 網站列表查詢
- Search Analytics API 整合
- 頁面標題抓取與快取
- AI 意圖分析

**資料流：**
```
前端 → OAuth 授權碼 → /api/gsc/authorize → 交換 Refresh Token → 儲存到 User
前端 → 查詢參數 → /api/gsc/analytics → 使用 Refresh Token → GSC API → 返回數據
```

##### 📈 GA4 Module (`modules/ga4/`)

**功能：**
- GA4 Data API 整合
- 帳戶/資源列表
- 流量/行為/內容分析
- 自訂維度與指標

**API 端點：**
- `GET /api/ga4/accounts`
- `GET /api/ga4/properties`
- `GET /api/ga4/analytics`

### 3. 路由層 (`routers/`)

**職責：** API 端點定義、參數驗證、回應格式化

#### 路由分類

| 檔案 | 路徑前綴 | 功能 |
|------|----------|------|
| `users.py` | `/api/users` | 使用者 CRUD |
| `teams.py` | `/api/teams` | 團隊管理 |
| `invites.py` | `/api/invites` | 邀請系統 |
| `admin.py` | `/api/admin` | 超級管理員 |
| `permissions.py` | `/api/permissions` | 權限管理 |
| `facebook.py` | `/api/ad-accounts`, `/api/dashboard-data` | Facebook Ads |
| `gsc.py` | `/api/gsc` | GSC (轉發到 module) |
| `ga4.py` | `/api/ga4` | GA4 (轉發到 module) |
| `ai.py` | `/api/ai` | AI (轉發到 module) |
| `saved_views.py` | `/api/saved-views` | 儲存視圖 |
| `debug.py` | `/api/debug` | 開發除錯 |

#### 路由最佳實踐

```python
from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_current_user, require_module

router = APIRouter(prefix="/api/example", tags=["example"])

@router.get("/data")
def get_data(
    user: User = Depends(get_current_user),  # 認證
    _: bool = Depends(require_module("example")),  # 模組權限
    db: Session = Depends(get_db)  # 資料庫連線
):
    """取得範例資料"""
    # 業務邏輯
    return {"data": []}
```

### 4. 服務層 (`services/`, 各 `*_service.py`)

**職責：** 外部 API 整合、複雜業務邏輯

#### 範例：`gsc_service.py`

```python
class GSCService:
    @staticmethod
    def list_sites(user: User) -> tuple[list, str | None]:
        """列出使用者的 GSC 網站"""
        if not user.gsc_refresh_token:
            return [], "No GSC token"
        
        # 使用 Refresh Token 建立 Credentials
        credentials = build_credentials(user.gsc_refresh_token)
        service = build('searchconsole', 'v1', credentials=credentials)
        
        try:
            result = service.sites().list().execute()
            sites = result.get('siteEntry', [])
            return sites, None
        except Exception as e:
            return [], str(e)
```

### 5. 資料存取層 (`database.py`)

**職責：** ORM 模型定義、資料庫連線管理

#### 關鍵模型

```python
from sqlalchemy import Column, String, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    google_id = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.MEMBER)
    is_super_admin = Column(Boolean, default=False)
    
    # OAuth Tokens
    fb_access_token = Column(String, nullable=True)
    gsc_refresh_token = Column(String, nullable=True)
    ga4_refresh_token = Column(String, nullable=True)
    
    # Relationships
    teams = relationship("TeamMember", back_populates="user")
    module_access = relationship("UserModuleAccess", back_populates="user")

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    owner_id = Column(String, ForeignKey("users.id"))
    fb_access_token = Column(String, nullable=True)
    
    members = relationship("TeamMember", back_populates="team")
```

---

## 🔄 資料流範例

### 1. 使用者登入流程

```
┌─────────┐     Google Token      ┌─────────┐
│ Frontend│ ───────────────────> │ Backend │
└─────────┘                       └────┬────┘
                                       │
                                       │ 1. verify_google_token()
                                       │    (驗證 ID Token)
                                       │
                                       ▼
                                  ┌─────────┐
                                  │ Google  │
                                  │  Auth   │
                                  └────┬────┘
                                       │
                                       │ 2. 返回 google_id
                                       │
                                       ▼
                                  ┌─────────┐
                                  │Database │
                                  │(查詢/建立│
                                  │  User)  │
                                  └────┬────┘
                                       │
                                       │ 3. 返回 User 物件
                                       │
┌─────────┐     User Data        ┌────▼────┐
│ Frontend│ <─────────────────── │ Backend │
└─────────┘                       └─────────┘
```

### 2. GSC 數據查詢流程

```
1. 前端發送請求
   GET /api/gsc/analytics?site_url=...&start_date=...

2. Router 驗證權限
   - get_current_user (驗證 Token)
   - require_module("gsc") (檢查模組權限)

3. GSCService 處理業務邏輯
   - 從 User 取得 gsc_refresh_token
   - 使用 Refresh Token 建立 Credentials
   - 呼叫 Google Search Console API
   
4. 回應數據
   - 格式化 API 回應
   - 返回 JSON 給前端
```

### 3. AI 分析串流流程

```
1. 前端發送 POST /api/ai/analyze-stream
   {
     "data": {...},
     "context": "分析這些數據的趨勢",
     "provider": "gemini"
   }

2. Backend 處理
   - 驗證使用者
   - 從加密儲存取得 API Key
   - 呼叫 AI Service (Gemini/Zeabur)
   
3. SSE 串流回應
   - 逐步返回 AI 生成的內容
   - 前端即時顯示
   
   data: {"chunk": "根據數據分析..."}
   data: {"chunk": "發現以下趨勢..."}
   data: {"done": true}
```

---

## 🔐 權限控制機制

### 三層權限體系

#### 1. 模組權限 (Module Access)

```python
# 檢查使用者是否有 GSC 模組權限
@router.get("/api/gsc/analytics")
def gsc_analytics(_: bool = Depends(require_module("gsc"))):
    pass
```

**實作邏輯：**
```python
def require_module(module_name: str):
    def _check(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        # 超級管理員自動通過
        if user.is_super_admin:
            return True
        
        # 查詢 user_module_access
        access = db.query(UserModuleAccess).filter(
            UserModuleAccess.user_id == user.id,
            UserModuleAccess.module_id == module_name
        ).first()
        
        if not access:
            raise HTTPException(403, f"No access to {module_name}")
        
        return True
    return _check
```

#### 2. 角色權限 (Role-based)

```python
# 管理員才能執行
def admin_endpoint(admin: User = Depends(get_admin_user)):
    pass

# 實作
def get_admin_user(user: User = Depends(get_current_user)):
    if user.role not in [UserRole.ADMIN, UserRole.OWNER] and not user.is_super_admin:
        raise HTTPException(403, "Admin access required")
    return user
```

#### 3. 細粒度權限 (Permission-based)

```python
# 檢查特定權限
def require_permission(permission_name: str):
    def _check(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        if user.is_super_admin:
            return True
        
        has_perm = db.query(UserPermission).join(Permission).filter(
            UserPermission.user_id == user.id,
            Permission.name == permission_name
        ).first()
        
        if not has_perm:
            raise HTTPException(403, f"Missing permission: {permission_name}")
        
        return True
    return _check
```

---

## 🛡️ 安全性設計

### 1. Token 儲存

- **Google ID Token：** 前端儲存，每次請求帶入 `Authorization: Bearer <token>`
- **Facebook Long-lived Token：** 加密儲存於資料庫 (可選)
- **AI API Keys：** 使用 Fernet 加密儲存

```python
from core.security import encrypt_data, decrypt_data

# 儲存時加密
user.encrypted_api_key = encrypt_data(api_key)

# 使用時解密
api_key = decrypt_data(user.encrypted_api_key)
```

### 2. CORS 設定

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境應限制來源
    allow_credentials=False,  # Token-based auth 不需要 cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. 輸入驗證

- **Pydantic Models：** 自動驗證請求資料
- **SQL Injection：** 使用 SQLAlchemy ORM
- **XSS：** 前端 React 自動跳脫

---

## 🔧 中介軟體與攔截器

### 例外處理器

```python
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "detail": exc.detail
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled exception: {exc}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

### 生命週期管理

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用啟動/關閉時執行"""
    print("🚀 Application starting...")
    # 啟動任務：初始化快取、連線池等
    yield
    # 關閉任務：釋放資源
    print("👋 Application shutting down...")

app = FastAPI(lifespan=lifespan)
```

---

## 📊 效能優化

### 1. 批次請求

```python
# Facebook Ads 批次請求
@router.post("/api/analytics/batch")
def batch_analytics(requests: List[AnalyticsRequest]):
    """一次處理多個分析請求"""
    results = []
    for req in requests:
        result = fetch_analytics(req)
        results.append(result)
    return results
```

### 2. 快取機制

```python
# GSC 頁面標題快取
def get_page_title(url: str, team_id: str, db: Session) -> str:
    # 先查快取
    cached = db.query(PageTitle).filter(
        PageTitle.url == url,
        PageTitle.team_id == team_id
    ).first()
    
    if cached:
        return cached.title
    
    # 未快取則抓取
    title = fetch_title_from_web(url)
    
    # 儲存快取
    page_title = PageTitle(url=url, title=title, team_id=team_id)
    db.add(page_title)
    db.commit()
    
    return title
```

### 3. 連線池管理

```python
# SQLAlchemy 連線池配置
engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # 連線池大小
    max_overflow=20,       # 超出池大小的額外連線
    pool_pre_ping=True     # 連線前測試有效性
)
```

---

## 🧪 測試策略

### 單元測試範例

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_auth_required():
    response = client.get("/api/users/me")
    assert response.status_code == 401  # 未授權

def test_module_permission():
    # Mock 已認證使用者但無 GSC 模組權限
    response = client.get("/api/gsc/analytics", headers={
        "Authorization": "Bearer fake_token"
    })
    assert response.status_code == 403  # 無權限
```

---

## 📝 最佳實踐

### 1. 程式碼組織

✅ **DO：**
- 按功能模組分離程式碼
- 使用依賴注入減少耦合
- 保持檔案小於 300 行

❌ **DON'T：**
- 在 `main.py` 寫太多業務邏輯
- 直接在 Router 寫資料庫查詢
- 硬編碼配置資訊

### 2. 錯誤處理

✅ **DO：**
```python
try:
    result = external_api_call()
except ExternalAPIError as e:
    raise AppException(
        status_code=502,
        error_code="EXTERNAL_API_ERROR",
        detail=f"Failed to fetch data: {e}"
    )
```

❌ **DON'T：**
```python
try:
    result = external_api_call()
except:
    pass  # 吞掉錯誤
```

### 3. 資料庫操作

✅ **DO：**
```python
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user
```

❌ **DON'T：**
```python
# 不要在函式內建立新 Session
def get_user(user_id: str):
    db = SessionLocal()  # ❌ 不會自動關閉
    return db.query(User).filter(User.id == user_id).first()
```

---

## 🔄 遷移與維護

### Alembic 遷移流程

```bash
# 1. 修改 database.py 的模型

# 2. 自動生成遷移檔
alembic revision --autogenerate -m "Add new field to User"

# 3. 檢查生成的遷移檔
# 編輯 alembic/versions/xxxx_add_new_field_to_user.py

# 4. 執行遷移
alembic upgrade head

# 5. (如需回退)
alembic downgrade -1
```

### 版本管理

- **API 版本化：** 使用路徑前綴 `/api/v1/`, `/api/v2/`
- **向後兼容：** 新欄位使用 `nullable=True`
- **棄用通知：** 在 response 加入 `deprecated: true` 標記

---

## 📚 參考資源

- [FastAPI 官方文件](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文件](https://docs.sqlalchemy.org/)
- [Alembic 文件](https://alembic.sqlalchemy.org/)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)

---

**文件版本：** 2.0  
**最後更新：** 2026-01-15
