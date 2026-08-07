# DataVue App — 架構與程式碼審查報告

> **審查日期**：2026-02-23  
> **審查工具**：GitHub Copilot（Claude Sonnet 4.6）  
> **專案版本**：Backend v2.1.0 / Frontend v1.5.0  
> **審查範圍**：後端（Python/FastAPI）、前端（React/Vite）、資料庫、安全性、部署設定

---

## 目錄

1. [專案概覽](#1-專案概覽)
2. [架構總覽](#2-架構總覽)
3. [後端審查](#3-後端審查)
4. [前端審查](#4-前端審查)
5. [資料庫設計審查](#5-資料庫設計審查)
6. [安全性審查](#6-安全性審查)
7. [部署設定審查](#7-部署設定審查)
8. [優先級矩陣](#8-優先級矩陣)
9. [優化建議具體實作](#9-優化建議具體實作)
10. [總結評分](#10-總結評分)

---

## 1. 專案概覽

DataVue App 是一個多平台分析儀表板，整合了以下資料來源：

- **Facebook Ads**：廣告投放數據、受眾分析、轉換追蹤
- **Google Search Console (GSC)**：搜尋流量、關鍵字排名、點擊率
- **Google Analytics 4 (GA4)**：網站行為數據、電商追蹤
- **AI 分析**：Zeabur AI Hub 或 Google Gemini 提供的智能洞察

技術棧：
| 層級 | 技術 |
|------|------|
| 後端 | FastAPI + SQLAlchemy + Alembic |
| 資料庫 | SQLite（開發）/ PostgreSQL（生產） |
| 快取 | 記憶體 TTLCache + Redis（選配） |
| 前端 | React 19 + Vite 7 + Recharts |
| 認證 | Google OAuth2（ID Token） |
| 部署 | Docker + Zeabur |

---

## 2. 架構總覽

### 2.1 後端模組結構（現狀）

```
backend/
├── main.py              ✅ 保持在 200 行以內（良好實踐）
├── core/
│   ├── config.py        ✅ 集中式設定管理
│   ├── security.py      ✅ Fernet 對稱加密
│   ├── startup.py       ✅ 啟動邏輯分離
│   └── exceptions.py    ⚠️  與根層 exceptions.py 重複命名
├── database.py          ❌ 過重：ORM 引擎 + 所有模型混在單一檔案
├── dependencies.py      ❌ 過重：認證邏輯 + 業務邏輯混合（352 行）
├── async_services.py    ❌ 過重：834 行，Facebook 所有非同步邏輯集中
├── cache.py             ⚠️  僅記憶體快取，不適合多進程環境
├── routers/             ✅ 路由合理分離
└── modules/             ✅ 模組化設計
```

### 2.2 前端模組結構（現狀）

```
frontend/src/
├── App.jsx              ✅ Lazy loading 實作良好
├── pages/               ✅ 頁面分離清楚
├── components/          ⚠️  含 .backup 遺留檔案
├── services/            ❌ 每個 service 重複 fetch 邏輯，無統一 API client
├── hooks/               ✅ 權限 hook 封裝合理
├── constants/           ✅ 指標設定集中管理
└── utils/               ⚠️  auth.js Token 管理缺乏過期處理
```

---

## 3. 後端審查

### 🔴 嚴重問題（Critical）

#### 3.1 Token 驗證邏輯重複（雙重實作）

**位置**：`dependencies.py:36` 以及 `routers/auth.py:19`

**問題**：應用程式有兩個獨立的 Google Token 驗證函式：
- `dependencies.py` 的 `verify_google_token_basic()`
- `routers/auth.py` 的 `verify_google_token()`

兩者邏輯幾乎相同（呼叫 `id_token.verify_oauth2_token`），但返回值不同：前者返回完整 `id_info` dict，後者只返回 `sub`（Google ID）。這造成維護困難與潛在不一致。

**建議**：統一至 `core/security.py` 或 `dependencies.py`，以不同包裝函式提供不同返回格式。

```python
# 建議統一實作於 core/security.py
def verify_google_token(token: str) -> dict:
    """統一的 Google Token 驗證，返回完整 id_info"""
    return id_token.verify_oauth2_token(
        token, google_requests.Request(), settings.GOOGLE_CLIENT_ID, 
        clock_skew_in_seconds=60
    )
```

#### 3.2 LRU Cache 應用於 Token 驗證存在安全漏洞

**位置**：`dependencies.py:30`

```python
@lru_cache(maxsize=128)
def _verify_token_cached(token: str):
    return id_token.verify_oauth2_token(...)
```

**問題**：`lru_cache` 沒有 TTL（存活時間）。Google ID Token 的有效期為 1 小時，但如果 Token 被撤銷（使用者登出、帳號停用），快取中的結果仍會繼續被接受，**直到進程重啟為止**。

**建議**：改用有 TTL 的快取（如 `cachetools.TTLCache`）：

```python
from cachetools import TTLCache, cached
_token_cache = TTLCache(maxsize=128, ttl=300)  # 5 分鐘

@cached(cache=_token_cache)
def _verify_token_cached(token: str):
    return id_token.verify_oauth2_token(...)
```

#### 3.3 `get_current_user` 混合認證與業務邏輯

**位置**：`dependencies.py:56-190`

**問題**：`get_current_user()` 함수 高達 135 行，混合了：
- 使用者認證（應屬認證層）
- 使用者自動註冊（應屬 User Service）
- Super Admin 同步（應屬 Admin Service）
- 模組存取權限授予（應屬 Permission Service）
- 大量 `print(..., file=sys.stderr)` 除錯輸出混混日誌系統

**建議**：拆分為多個函式：
```
authenticate_user()     → 純認證，返回 id_info
get_or_create_user()    → 使用者資料庫邏輯
sync_super_admin()      → 超級管理員同步
grant_default_modules() → 模組授權
```

---

### 🟠 重要問題（High）

#### 3.4 `requirements.txt` 缺乏版本釘定

**位置**：`backend/requirements.txt`

**問題**：所有依賴套件均無版本約束：
```
fastapi        # 應為 fastapi>=0.115.0,<0.116.0
uvicorn        # 應為 uvicorn[standard]>=0.32.0
sqlalchemy     # 應為 sqlalchemy>=2.0.0,<3.0.0
```

**風險**：部署時的套件版本與開發時不同，導致不可預期的錯誤。應使用 `pip freeze > requirements.lock` 或 Poetry 管理精確版本。

#### 3.5 記憶體快取不適合多進程生產環境

**位置**：`cache.py:10-20`

```python
ad_accounts_cache = TTLCache(maxsize=100, ttl=300)
insights_cache = TTLCache(maxsize=500, ttl=120)
```

**問題**：`cachetools.TTLCache` 是進程內記憶體快取。在生產環境使用多個 Uvicorn workers（`--workers 4`）或多個 Docker 副本時，每個進程都有自己的快取，**無法共享**。這導致：
1. 快取命中率大幅降低
2. 對 Facebook API 的請求次數增加（可能超過 rate limit）
3. 不同進程返回不一致的資料

雖然 `redis_cache.py` 已存在，但它尚未整合為主要快取機制。

**建議**：將 Redis 提升為主要快取層，`cachetools` 作為 L1 本地快取（短 TTL）：

```python
def get_insights(key):
    # L1: 本地快取（5 秒）
    local = local_cache.get(key)
    if local:
        return local
    # L2: Redis 快取
    redis_val = get_cached_redis(key)
    if redis_val:
        local_cache[key] = redis_val  # 回填 L1
        return redis_val
    return None
```

#### 3.6 `database.py` 職責過重

**位置**：`backend/database.py`（324 行）

**問題**：單一檔案包含：
- 資料庫連線與引擎建立
- 所有 ORM 模型（User, Team, TeamMember, TeamInvite, SavedView, PageTitle, Module, Permission, Role, RolePermission, UserModuleAccess, UserPermission）
- 資料庫初始化邏輯

**建議**：拆分為：
```
database/
├── __init__.py       # 匯出公共 API
├── engine.py         # 引擎與 Session 設定
├── base.py           # DeclarativeBase
└── models/
    ├── user.py       # User, UserRole, UserStatus
    ├── team.py       # Team, TeamMember, TeamInvite
    ├── view.py       # SavedView, PageTitle
    └── permission.py # Module, Permission, Role, etc.
```

#### 3.7 `async_services.py` 過於龐大

**位置**：`backend/async_services.py`（834 行）

**問題**：所有 Facebook API 非同步邏輯集中在單一 834 行檔案，難以維護、測試與理解。

**建議**：拆分至 `modules/fb_ads/` 下的多個專責服務：
```
modules/fb_ads/
├── accounts_service.py   # Ad Account 查詢
├── insights_service.py   # 廣告洞察數據
├── analytics_service.py  # 完整分析報告
└── trends_service.py     # 趨勢數據
```

---

### 🟡 中等問題（Medium）

#### 3.8 `auth.py` 根層為無必要的間接層

**位置**：`backend/auth.py`

```python
from modules.auth.service import TokenManager as StandardTokenManager
TokenManager = StandardTokenManager
```

**問題**：此檔案僅是 `modules.auth.service.TokenManager` 的別名重新匯出，但增加了一個不必要的匯入路徑。

**建議**：所有使用 `from auth import TokenManager` 的地方，直接改為：
```python
from modules.auth.service import TokenManager
```

#### 3.9 JSON 資料儲存為純字串欄位

**位置**：`database.py:168,190`

```python
visible_ad_account_ids = Column(String, nullable=True)  # Team
metrics = Column(String, nullable=False)                  # SavedView
```

**問題**：JSON 資料（廣告帳號 ID 列表、指標列表）以字串形式儲存，繞過了 ORM 型別檢查，需要在應用層手動 `json.loads()` / `json.dumps()`。

**建議**：PostgreSQL 使用 `JSONB` 型別，SQLite 相容時使用 SQLAlchemy 的 `JSON`：
```python
from sqlalchemy import JSON
metrics = Column(JSON, nullable=False, default=list)
```

#### 3.10 CORS 正則允許 HTTP 協議用於生產域名

**位置**：`main.py:81`

```python
allow_origin_regex = r"https?://.*\.?(tabisme\.com|zeabur\.app|localhost)(:\d+)?$"
```

**問題**：`https?://` 同時允許 `http://` 與 `https://`，生產域名（tabisme.com, zeabur.app）應僅允許 HTTPS。

**建議**：
```python
allow_origin_regex = r"https://.*\.?(tabisme\.com|zeabur\.app)(:\d+)?$|https?://localhost(:\d+)?$"
```

#### 3.11 Session 直接建立而非使用 Dependency

**位置**：`routers/auth.py:67`

```python
session = SessionLocal()
try:
    ...
finally:
    session.close()
```

**問題**：部分路由直接建立 `SessionLocal()` 而非使用 `Depends(get_db)`，雖然有 `finally` 確保關閉，但這繞過了依賴注入系統，使測試更困難。

**建議**：統一使用 `db: Session = Depends(get_db)`。

---

### 🟢 小問題與建議（Low）

#### 3.12 雙重 Exception 模組

`backend/exceptions.py`（根層）與 `backend/core/exceptions.py` 並存，職責有重疊風險。`main.py` 引入根層的 `AppException`，應確認 `core/exceptions.py` 是否為遺留品或有不同用途，並統一為一個來源。

#### 3.13 日誌使用 `print()` 取代 `logger`

**位置**：`dependencies.py`（多處）

```python
print(f"DEBUG: User {user.email}...", file=sys.stderr)
```

這些輸出不會經過標準日誌系統，無法設定日誌層級、格式化或轉至外部日誌服務（如 Datadog、Cloud Logging）。

**建議**：將所有 `print(...)` 替換為 `logger.info(...)` / `logger.debug(...)`。

#### 3.14 `debug_fields.log` 被提交至儲存庫

`backend/debug_fields.log` 似乎是開發除錯中產生的日誌檔案，應加入 `.gitignore`。

---

## 4. 前端審查

### 🔴 嚴重問題（Critical）

#### 4.1 缺乏統一 API Client

**位置**：`frontend/src/services/*.js`

**問題**：每個 service 檔案都獨立實作 `fetch()` 呼叫：

```javascript
// userService.js
const response = await fetch(`${API_URL}/users/`, {
  headers: getAuthHeaders(),
});

// teamService.js（相同模式）
const response = await fetch(`${API_URL}/teams/`, {
  headers: getAuthHeaders(),
});
```

這造成：
1. 錯誤處理邏輯重複
2. 無法統一處理 401（Token 過期重導向至登入頁）
3. 無法添加全局 Request/Response 攔截器（logging, retry, etc.）

**建議**：建立統一的 API client：

```javascript
// src/services/apiClient.js
const apiClient = {
  async request(method, path, options = {}) {
    const response = await fetch(`${API_URL}${path}`, {
      method,
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      ...options,
    });
    if (response.status === 401) {
      // 清除 Token 並重導向登入頁
      localStorage.removeItem('google_token');
      window.location.href = '/login';
      return;
    }
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || `HTTP ${response.status}`);
    }
    return response.json();
  },
  get: (path) => apiClient.request('GET', path),
  post: (path, body) => apiClient.request('POST', path, { body: JSON.stringify(body) }),
  put: (path, body) => apiClient.request('PUT', path, { body: JSON.stringify(body) }),
  delete: (path) => apiClient.request('DELETE', path),
};
```

#### 4.2 Token 過期未處理

**位置**：`frontend/src/utils/auth.js`

**問題**：前端從 localStorage 取得 Google ID Token 並直接附加到請求 headers，但 Google ID Token **有效期僅 1 小時**。目前沒有 Token 過期偵測或重新整理機制，導致使用者在 1 小時後的 API 請求全部返回 401，且前端沒有優雅的處理（直接 throw Error）。

**建議**：
1. 儲存 Token 時同時儲存過期時間（JWT payload 中的 `exp` 欄位）
2. 在發送請求前檢查是否過期，若過期則觸發重新登入流程
3. 使用 `@react-oauth/google` 的 `useGoogleLogin` 的 implicit flow 以支援 Token Refresh

---

### 🟠 重要問題（High）

#### 4.3 缺乏資料請求狀態管理（無 React Query / SWR）

**問題**：所有頁面元件直接在 `useEffect` 中使用 `fetch()`，手動管理 `loading`、`error`、`data` state。這導致：
1. 每次元件重新掛載都重新請求 API（無快取）
2. 相同資料在多個元件中各自請求（例如：多個頁面都需要 user profile）
3. 無法輕易實現樂觀更新（Optimistic Updates）

**建議**：引入 **TanStack Query（React Query）**：
```bash
npm install @tanstack/react-query
```
提供自動快取、背景重新整理、重試等功能，大幅減少手動狀態管理代碼。

#### 4.4 沒有 TypeScript

**問題**：整個前端為純 JavaScript，缺乏靜態型別檢查。API 回應結構在程式碼中沒有型別定義，容易因後端 API 變更而產生難以偵測的 runtime 錯誤。

**建議**：逐步遷移至 TypeScript，至少為關鍵的服務層與 API 回應建立 JSDoc 型別定義：
```javascript
/**
 * @typedef {Object} User
 * @property {string} id
 * @property {string} email
 * @property {boolean} is_super_admin
 * @property {'admin'|'member'|'viewer'} role
 */
```

---

### 🟡 中等問題（Medium）

#### 4.5 遺留備份檔案提交至儲存庫

以下檔案應刪除並加入 `.gitignore`：
- `frontend/src/components/GSCStats.jsx.backup`
- `frontend/src/components/SettingsModal_orig.jsx`

這些是開發過程中的暫存備份，不應進入版本控制。

#### 4.6 `metricsRegistry.js`（前端）與 `METRICS_REGISTRY`（後端）重複定義

**位置**：`frontend/src/constants/metricsRegistry.js` 及 `backend/async_services.py:22-90`

**問題**：相同的指標定義在前後端各維護一份，任何新增指標都需要在兩處同步更新，容易遺漏。

**建議**：考慮在後端提供一個 `GET /api/metrics/registry` 端點，前端動態取得指標定義，避免重複維護。

#### 4.7 React 19 相容性風險

`package.json` 使用 React 19.2.0（最新版），但 `@react-oauth/google` 0.12.2 的官方支援聲明截至 React 18。雖然目前可能正常運作，但應確認無 deprecation warning 並持續關注相容性更新。

---

## 5. 資料庫設計審查

### 5.1 User 模型過度承載職責

**位置**：`database.py：97-152`

User 模型同時存儲：
- 身份認證資訊（google_id, email）
- Facebook 整合 Token（fb_access_token, fb_app_id, fb_app_secret）
- GSC 整合 Token（gsc_access_token, gsc_refresh_token）
- GA4 整合 Token（ga4_access_token, ga4_refresh_token）
- AI 設定（zeabur_api_key, gemini_api_key, ai_provider, ai_model）
- 角色（role, status, is_super_admin）

**建議**：將第三方整合 Token 移至獨立關聯表（如 `UserIntegration`）：
```sql
CREATE TABLE user_integrations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    provider VARCHAR(50),     -- 'facebook', 'gsc', 'ga4'
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP
);
```

### 5.2 缺乏資料庫索引規劃

除了 `unique=True` 和 `index=True` 的欄位外，沒有複合索引。例如：
- `TeamMember(team_id, user_id)` 雖為複合主鍵，但查詢時通常以 `user_id` 為條件
- `UserModuleAccess(user_id, team_id, module_id)` 應建立複合索引

**建議**：添加明確的複合索引：
```python
from sqlalchemy import Index
Index('ix_user_module_access_lookup', 
      UserModuleAccess.user_id, 
      UserModuleAccess.team_id, 
      UserModuleAccess.module_id)
```

### 5.3 SQLite ↔ PostgreSQL 不一致風險

開發使用 SQLite、生產使用 PostgreSQL。兩者在以下方面有差異：
- `CURRENT_TIMESTAMP` 在 SQLite 返回本地時間，PostgreSQL 返回 UTC
- `JSON` / `JSONB` 型別行為不同
- 字串比較大小寫敏感度不同

**建議**：開發環境也改用 PostgreSQL（可使用 Docker Compose）：
```yaml
# docker-compose.dev.yml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: datavue_dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"
```

---

## 6. 安全性審查

### 🔴 嚴重安全問題

#### 6.1 `.env` 文件存在於後端目錄

`backend/.env` 文件在目錄列表中可見。需確認此文件是否已加入 `.gitignore`。若已提交至 Git 歷史，需立即：
1. 撤銷（revoke）所有已洩露的金鑰
2. 使用 `git filter-branch` 或 `BFG Repo Cleaner` 清理 Git 歷史
3. 更新 `.gitignore` 防止再次提交

#### 6.2 `facebook_dashboard.db` SQLite 資料庫提交至儲存庫

`backend/facebook_dashboard.db` 是實際的 SQLite 資料庫文件，可能包含真實使用者資料、加密的 API Token。應立即加入 `.gitignore`。

### 🟠 重要安全問題

#### 6.3 Facebook App Secret 存儲於 User/Team 模型（明文或加密）

`Team.fb_app_id` 和 `User.fb_app_secret` 儲存於資料庫。確認加密功能（Fernet）已正確應用於 App Secret。目前 `TokenManager` 的加密應用情況需要進一步確認。

#### 6.4 無速率限制（Rate Limiting）

FastAPI 應用未配置任何速率限制中間件。惡意使用者可輕易對以下端點進行暴力攻擊：
- `/api/auth/exchange-token`
- `/api/users/`

**建議**：使用 `slowapi`（FastAPI 的速率限制庫）：
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/api/auth/exchange-token")
@limiter.limit("10/minute")
async def exchange_token(...):
    ...
```

#### 6.5 AI API Key 使用者自行輸入未充分驗證

使用者可在 UI 輸入自己的 Zeabur AI Hub 或 Gemini API Key，後端將其加密存儲。需確認：
1. Key 在存儲前已驗證格式
2. Key 在使用時的解密錯誤已妥善處理
3. Key 不會在日誌中被輸出

---

## 7. 部署設定審查

### 7.1 Dockerfile 使用 Python 3.9（已接近 EOL）

**位置**：`backend/Dockerfile:2`

```dockerfile
FROM python:3.9-slim
```

Python 3.9 的安全維護期結束於 **2025-10-05**。應升級至 Python 3.11 或 3.12。

**建議**：
```dockerfile
FROM python:3.12-slim
```

### 7.2 Dockerfile CMD 注釋過多

`backend/Dockerfile` 末尾有大量被注釋掉的 CMD 指令，顯示有多次修改嘗試的歷史。應清理這些注釋，保持 Dockerfile 整潔：

```dockerfile
# 清理後的 CMD
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### 7.3 缺乏健康檢查端點（Health Check）

Dockerfile 和部署設定中未設定 Docker 健康檢查：
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

後端 `main.py` 應提供一個 `/health` 端點供 Load Balancer 和 Zeabur 使用。

### 7.4 缺乏自動化測試（CI/CD）

整個專案無測試目錄（`tests/`），無單元測試、無整合測試。這使得自信地重構或升級依賴極為困難。

**建議**：至少建立以下測試：
```
backend/tests/
├── test_auth.py          # 認證邏輯測試
├── test_permissions.py   # 權限系統測試
├── test_teams.py         # 團隊管理測試
└── conftest.py           # pytest fixtures（測試 DB）
```

---

## 8. 優先級矩陣

| 編號 | 問題 | 嚴重性 | 影響範圍 | 修復難度 | 優先級 |
|------|------|--------|----------|----------|--------|
| 3.2 | LRU Cache 用於 Token 驗證（安全漏洞） | 🔴 Critical | 安全 | 低 | **P0** |
| 6.1 | `.env` 可能提交至 Git | 🔴 Critical | 安全 | 低 | **P0** |
| 6.2 | SQLite DB 文件提交至 Git | 🔴 Critical | 安全/隱私 | 低 | **P0** |
| 4.2 | Token 過期未處理 | 🔴 Critical | UX/安全 | 中 | **P1** |
| 4.1 | 缺乏統一 API Client | 🟠 High | 可維護性 | 中 | **P1** |
| 3.4 | requirements.txt 無版本釘定 | 🟠 High | 穩定性 | 低 | **P1** |
| 3.5 | 記憶體快取不適合生產環境 | 🟠 High | 效能/可靠性 | 中 | **P1** |
| 3.1 | Token 驗證邏輯重複 | 🟠 High | 可維護性 | 低 | **P2** |
| 3.3 | get_current_user 混合邏輯 | 🟠 High | 可維護性 | 中 | **P2** |
| 6.4 | 無速率限制 | 🟠 High | 安全 | 低 | **P2** |
| 7.1 | Python 3.9 即將 EOL | 🟡 Medium | 安全 | 低 | **P2** |
| 3.6 | database.py 過重 | 🟡 Medium | 可維護性 | 高 | **P3** |
| 3.7 | async_services.py 過重 | 🟡 Medium | 可維護性 | 高 | **P3** |
| 5.1 | User 模型職責過多 | 🟡 Medium | 擴充性 | 高 | **P3** |
| 4.3 | 缺乏 React Query | 🟡 Medium | 效能/DX | 中 | **P3** |
| 4.5 | 備份檔案提交至儲存庫 | 🟢 Low | 整潔度 | 低 | **P4** |
| 3.12 | print() 取代 logger | 🟢 Low | 可觀察性 | 低 | **P4** |
| 4.6 | 指標定義重複 | 🟢 Low | 可維護性 | 中 | **P4** |
| 7.4 | 缺乏自動化測試 | 🟡 Medium | 品質 | 高 | **P3** |

---

## 9. 優化建議具體實作

### 9.1 立即可執行（P0/P1，1-2 天）

**步驟 1：修復 .gitignore**

在 `backend/.gitignore` 中確認以下項目存在：
```gitignore
.env
*.db
*.sqlite
debug_*.log
debug_*.log
__pycache__/
venv/
```

**步驟 2：修復 Token 驗證快取（TTL Cache）**

```python
# dependencies.py
from cachetools import TTLCache, cached

_token_cache = TTLCache(maxsize=128, ttl=300)  # 5 分鐘 TTL

@cached(cache=_token_cache)
def _verify_token_cached(token: str):
    return id_token.verify_oauth2_token(
        token, google_requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=60
    )
```

**步驟 3：釘定 requirements.txt 版本**

```bash
cd backend
pip freeze > requirements.lock
```

並更新 `requirements.txt` 使用精確版本。

**步驟 4：刪除遺留備份檔案**

```bash
git rm frontend/src/components/GSCStats.jsx.backup
git rm frontend/src/components/SettingsModal_orig.jsx
```

### 9.2 短期優化（P2，1-2 週）

1. **統一 Token 驗證**：將 `routers/auth.py` 的驗證邏輯替換為呼叫 `dependencies.py` 的函式
2. **添加速率限制**：安裝 `slowapi` 並保護認證端點
3. **升級 Python 版本**：Dockerfile 改為 Python 3.12
4. **添加 `/health` 端點**：供 Docker HEALTHCHECK 使用
5. **統一日誌**：將所有 `print(... file=sys.stderr)` 替換為 `logger.xxx()`

### 9.3 中期優化（P3，1-2 個月）

1. **前端 API Client 統一化**：建立 `src/services/apiClient.js`
2. **處理 Token 過期**：實作前端 Token 有效性檢查
3. **引入 React Query**：替換手動 `useEffect` + `fetch` 模式
4. **拆分 `database.py`**：建立 `database/models/` 套件
5. **拆分 `async_services.py`**：依功能分割至各模組
6. **Redis 作為主要快取**：整合 `redis_cache.py` 至主要快取邏輯
7. **建立測試框架**：pytest + HTTPX TestClient

---

## 10. 總結評分

| 評估維度 | 評分 | 備註 |
|----------|------|------|
| **架構設計** | 7/10 | 模組化方向正確，執行上部分模組仍需細化 |
| **程式碼品質** | 6/10 | 邏輯正確，但部分函式職責不清、缺乏型別 |
| **安全性** | 5/10 | 存在 Token 快取漏洞与潛在的敏感文件洩露風險 |
| **效能** | 6/10 | 有快取機制但不適合多進程；無 DB 索引規劃 |
| **可維護性** | 6/10 | 部分文件過重；缺乏測試；有重複程式碼 |
| **部署設定** | 6/10 | Docker 基本完整，但 Python 版本過舊、缺健康檢查 |
| **前端品質** | 6/10 | 使用現代技術棧，但缺乏統一 API 層與型別系統 |

**整體評分：6.0 / 10**

這是一個功能完整、在正確軌道上的專案。主要強項在於模組化設計方向、權限系統的精細粒度設計，以及整合多個第三方平台的可擴充架構。優化重點應首先聚焦於安全性修復（Token 快取、.gitignore），其次是可維護性改善（統一 API client、拆分大型文件、建立測試）。

---

*本報告由 GitHub Copilot（Claude Sonnet 4.6）於 2026-02-23 自動生成，供開發團隊參考使用。*
