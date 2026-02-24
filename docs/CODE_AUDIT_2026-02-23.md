# DataVue App — 全專案程式碼架構審查報告

> **審查日期**：2026-02-23  
> **審查者**：GitHub Copilot（Claude Sonnet 4.6）  
> **審查範圍**：後端（FastAPI/Python）、前端（React/Vite）、資料庫、部署設定  
> **審查基礎**：docs/optimization/ 全優化實作完成後的最終狀態驗證

---

## 目錄

1. [整體架構評分](#整體架構評分)
2. [問題發現彙整](#問題發現彙整)
   - [🔴 嚴重問題（Critical）](#嚴重問題-critical)
   - [🟠 高優先問題（High）](#高優先問題-high)
   - [🟡 中優先問題（Medium）](#中優先問題-medium)
   - [🔵 低優先問題（Low）](#低優先問題-low)
3. [後端架構詳細審查](#後端架構詳細審查)
   - [應用程式入口（main.py）](#應用程式入口-mainpy)
   - [資料庫層](#資料庫層)
   - [核心模組（core/）](#核心模組-core)
   - [認證與依賴注入](#認證與依賴注入)
   - [業務模組（modules/）](#業務模組-modules)
   - [服務層（services/）](#服務層-services)
   - [路由層（routers/）](#路由層-routers)
   - [快取架構](#快取架構)
   - [速率限制](#速率限制)
4. [前端架構詳細審查](#前端架構詳細審查)
   - [API 客戶端](#api-客戶端)
   - [Token 管理](#token-管理)
   - [狀態管理（React Query）](#狀態管理-react-query)
   - [型別定義](#型別定義)
5. [資料庫與遷移審查](#資料庫與遷移審查)
6. [安全性審查](#安全性審查)
7. [部署設定審查](#部署設定審查)
8. [優化實作驗收狀況](#優化實作驗收狀況)
9. [必須立即修復事項](#必須立即修復事項)
10. [中期建議事項](#中期建議事項)
11. [架構改進路線圖](#架構改進路線圖)

---

## 整體架構評分

| 面向 | 分數 | 說明 |
|------|------|------|
| 安全性 | 7/10 | TTLCache 修復正確，但 gsc_service 仍有 DEBUG print |
| 程式碼品質 | 7/10 | 核心模組重構成熟，舊服務仍有技術債 |
| 架構清晰度 | 8/10 | 模組化程度大幅提升，database/ 套件設計良好 |
| 可測試性 | 2/10 | **tests/ 目錄完全不存在**，嚴重落後於計畫 |
| 可維護性 | 7/10 | 有橋接層、文件齊全，雙重 get_db 有輕微混亂 |
| 部署就緒度 | 8/10 | Dockerfile、健康端點、Redis 降級設計完整 |
| 前端品質 | 8/10 | React Query 整合良好，型別定義完整 |
| **綜合** | **6.7/10** | 核心優化紮實，但有幾個關鍵遺漏需補齊 |

---

## 問題發現彙整

### 🔴 嚴重問題（Critical）

#### C-1：`backend/tests/` 目錄與 `pytest.ini` 完全不存在

**位置**：`backend/tests/`（不存在）、`backend/pytest.ini`（不存在）  
**影響**：FINAL_OPTIMIZATION_REPORT.md 宣稱已建立 26 個測試案例，但實際磁碟上完全不存在。  
**檢查方法**：
```powershell
Test-Path "backend/tests"    # → False
Test-Path "backend/pytest.ini" # → False
```
`.pytest_cache/` 存在代表某個時間點曾執行 pytest，但找不到任何測試檔案。

**風險**：
- 優化報告的驗收狀態具有誤導性
- 任何重構均無安全網
- 如在 CI/CD 中執行 `pytest tests/`，直接失敗

**必要行動**：建立 `backend/tests/` 完整測試套件（詳見[必須立即修復事項](#必須立即修復事項)）

---

### 🟠 高優先問題（High）

#### H-1：Alembic 遷移腳本使用 SQLite-only 語法（PostgreSQL 不相容）

**位置**：`backend/alembic/versions/20260223_p3_integrations_indexes.py`  
**影響**：在 PostgreSQL 環境執行 `alembic upgrade head` 將立即報錯

**問題語法**（第 69–89 行）：
```sql
-- SQLite 專用函式，PostgreSQL 不支援
lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || ...
json_object('app_id', fb_app_id, ...)   -- SQLite JSON 函式
```

**PostgreSQL 等效寫法**：
```sql
gen_random_uuid()::text    -- PostgreSQL UUID 生成
jsonb_build_object(...)    -- PostgreSQL JSON 構建
```

**風險**：
- 切換至 PostgreSQL 開發環境時，5 個索引/表均無法建立
- 數據遷移失敗，user_integrations 表建立不完整

**必要行動**：
1. 建立新的 migration revision，使用資料庫無關的 Python-level UUID 生成（通過 Alembic `bulk_insert_mappings` 或 migration hook）
2. 或將 SQL 改寫為雙方言相容版本

---

#### H-2：`gsc_service.py` 仍有 18 個 `print()` 呼叫（P4 未完整執行）

**位置**：`backend/gsc_service.py`（第 49、50、64、69、76、80、83、86、90、94、104、123、125、168、174、176、240、314 行）  
**影響**：
- 優化報告聲稱 P4 [3.12] 「18+ 個後端模組完成 print → logger 轉換」，但 gsc_service.py 仍保留大量 DEBUG print 輸出
- 生產環境中 print() 輸出不受日誌等級控制、無時間戳、無模組名稱
- 部分輸出包含敏感資訊（clientId 前綴、Token 狀態）

**典型問題程式碼**：
```python
print(f"DEBUG: Attempting manual token exchange with clientId={client_id[:10]}...")
print(f"DEBUG: Auth Code Length: {len(code)}")
```

**必要行動**：將全部 print() 替換為 `logger.debug()` / `logger.error()`

---

#### H-3：`services/ai/zeabur_client.py` 有 15 個 `print()` 呼叫

**位置**：`backend/services/ai/zeabur_client.py`（第 124、173、174、205、251、261、268-291 行）  
**影響**：AI 服務的生產日誌混雜無格式的 print 輸出，且 production code 與 test script code 混合在同一檔案

**問題**：`if __name__ == "__main__":` 測試區塊中的 print 可接受，但第 124、173、174、205、251 行是業務邏輯中的 print，需轉換。

---

### 🟡 中優先問題（Medium）

#### M-1：`routers/auth.py` 仍直接讀取 `User.fb_access_token`

**位置**：`backend/routers/auth.py`（第 68–85 行）  
**問題**：
```python
# 舊版直接讀取（應改用 integration_service）
target = db.query(User).filter(User.google_id == user_id).first()
if target and hasattr(target, 'fb_access_token') and target.fb_access_token:
    token_exists = len(str(target.fb_access_token)) > 10

if not target or not target.token_expires_at:
    ...
```

雖然 `UserIntegration` 模型與 `integration_service.py` 均已建立，但路由層仍繞過新架構，直接讀取即將廢棄的 User 表欄位。

**影響**：
- UserIntegration 遷移後，此端點的 `token_exists` 判斷將永遠為 False
- 阻礙 User 表 Token 欄位的最終清除

**必要行動**：改用 `integration_service.get_user_integration(db, user.id, "facebook")` 查詢

---

#### M-2：`backend/.gitignore` 規則嚴重不足

**位置**：`backend/.gitignore`  
**內容**（全部 5 條）：
```
venv/
__pycache__/
*.pyc
.env
tokens.json
```

**缺漏的關鍵規則**：

| 缺漏規則 | 風險 |
|---------|------|
| `*.db` / `*.sqlite` | `facebook_dashboard.db` 可能提交至 git |
| `*.log` / `debug_*.log` | `debug_fields.log` 可能提交至 git |
| `*.backup` / `*.bak` / `*.orig` | 備份檔案洩漏 |
| `htmlcov/` | 覆蓋率報告 |
| `*.pyc` 已有，但缺 `*.pyo` / `*.pyd` | |

**說明**：根目錄的 `.gitignore` 已完整包含這些規則，但 `backend/` 子目錄的 `.gitignore` 若獨立使用（如 subtree clone、Docker build context）將無保護。

**必要行動**：更新 `backend/.gitignore` 補齊規則，或刪除 `backend/.gitignore` 並完全依賴根目錄版本。

---

#### M-3：`database_LEGACY.py` 仍位於儲存庫

**位置**：`backend/database_LEGACY.py`（324 行）  
**內容**：原版 `database.py` 的完整複本，包含所有舊版 SQLAlchemy 設定  
**風險**：
- 第三方 import 若意外使用此舊檔案，行為不可預期（有自己的 engine 實例）
- 增加程式碼維護混亂度
- 可能混淆新進開發者

**建議行動**：在確認無任何模組 import `database_LEGACY` 後，刪除此檔案（已驗證：無模組 import 此檔案）

---

#### M-4：`dependencies.py` 含 `logging.basicConfig()` 潛在衝突

**位置**：`backend/dependencies.py`（第 7 行）  
**問題程式碼**：
```python
import logging
logging.basicConfig(level=logging.INFO)  # ← 問題所在
```

**衝突說明**：
- `main.py` 在啟動時呼叫 `core.logging.setup_logging()`，會清空所有 handler 並重建
- 但 `dependencies.py` 的 `basicConfig()` 若先於 `setup_logging()` 被執行，會在根 Logger 上增加一個未格式化的 StreamHandler
- 由於 `dependencies.py` 在 `main.py` 中大約第 175 行才被間接 import，時序上 setup_logging() 應先執行，但此依賴是隱性的，重構時可能改變順序

**建議行動**：移除 `dependencies.py` 中的 `logging.basicConfig()` 呼叫

---

### 🔵 低優先問題（Low）

#### L-1：`get_db()` 重複定義

**位置**：`backend/database/engine.py`（第 81 行）和 `backend/dependencies.py`（第 16 行）  
**說明**：兩個 `get_db()` 產生器功能完全相同（`SessionLocal()` → `yield db` → 關閉），但它們是不同函式，不可替換。若兩地的 `SessionLocal` 不同步，可能產生不一致的行為。  
**建議行動**：所有路由統一使用 `from database import get_db`，廢棄 `dependencies.get_db`

---

#### L-2：`ga4_service.py` 和 `gsc_service.py` 未完成模組化

**位置**：`backend/ga4_service.py`（555 行）、`backend/gsc_service.py`（336 行）  
**說明**：這兩個主服務仍位於 `backend/` 根目錄，而 `modules/ga4/service.py` 和 `modules/gsc/service.py` 只是重新導出橋接層：
```python
# modules/ga4/service.py（全部內容）
from ga4_service import GA4Service
__all__ = ["GA4Service"]
```
這與 `async_services.py` 的橋接層設計一致，屬於正常遷移中間狀態，但長期應完成完整模組化。

---

#### L-3：`ga4_service.py` 仍使用舊版 cache 函式呼叫方式

**位置**：`backend/ga4_service.py`（第 28-29 行）  
**問題**：
```python
from cache import generate_cache_key, get_cached, set_cached, analytics_cache
from redis_cache import get_cached_redis, set_cached_redis
```
向後相容層已在 `cache.py` 中提供這些函式，功能可正常運作，但函式語意已改變（向後相容包裝器），可能帶來困惑。  
**建議行動**：下一版本重構時更新為新 API（`cache_get`/`cache_set`）

---

## 後端架構詳細審查

### 應用程式入口（main.py）

✅ **評分：8/10**

| 項目 | 狀態 | 說明 |
|------|------|------|
| 模組化設計 | ✅ | 目標 200 行以內，實際 282 行（略超但可接受） |
| Lifespan Handler | ✅ | 使用 `@asynccontextmanager`，符合 FastAPI 新版規範 |
| 速率限制掛載 | ✅ | `app.state.limiter = limiter` + `SlowAPIMiddleware` |
| CORS 設定 | ✅ | 正則修正完整，生產環境僅 HTTPS |
| GZip 壓縮 | ✅ | `GZipMiddleware(minimum_size=1000)` |
| 例外處理器 | ✅ | `RateLimitExceeded`、`AppException`、`HTTPException`、`Exception` 全覆蓋 |
| 健康端點 | ✅ | `/health` 含 DB + Redis 狀態，`/api/health` 向後相容 |
| Debug 路由控制 | ✅ | 依 `DEBUG_MODE` 環境變數控制 |
| 啟動任務 | ✅ | `run_startup_tasks()` 封裝於 `core/startup.py` |

**問題**：
- `from datetime import datetime, timezone` 在 `main.py` 底部的 `/health` 端點內容重複了 `lifespan` 頂部的導入，可整理至頂部統一 import。

---

### 資料庫層

✅ **評分：9/10**

#### database/ 套件結構
```
backend/database/
├── __init__.py      ← 公開 API，向後相容匯出
├── base.py          ← DeclarativeBase
├── engine.py        ← 引擎、SessionLocal、get_db、check_db_connection
└── models/
    ├── __init__.py  ← 所有模型匯出
    ├── user.py      ← User, UserRole, UserStatus
    ├── team.py      ← Team, TeamMember, TeamInvite
    ├── view.py      ← SavedView, PageTitle
    ├── permission.py ← Module, Permission, Role...
    └── integration.py ← UserIntegration（新）
```

**設計亮點**：
- 所有模型按職責分檔，每個模型檔案清晰獨立
- `database/__init__.py` 維護完整向後相容匯出，舊版 import 路徑無需改動
- `database/engine.py` 自動判斷 SQLite（開發）/ PostgreSQL（生產）

**UserIntegration 模型設計**：
```python
# 優良設計點：
UniqueConstraint("user_id", "provider", name="uq_user_integration_provider")
Index("ix_user_integrations_lookup", "user_id", "provider")
ForeignKey("users.id", ondelete="CASCADE")  # 級聯刪除
```

**遺留問題**：
- `database_LEGACY.py`（324 行）仍存在，應清除
- `engine.py` 的 `DATABASE_URL` 變數設定後未使用（第 53 行設定但 `get_engine()` 重新讀取環境變數）

---

### 核心模組（core/）

✅ **評分：9/10**

```
backend/core/
├── __init__.py
├── config.py        ← 應用程式設定
├── exceptions.py    ← 自訂例外
├── logging.py       ← 統一日誌設定 ✅
├── security.py      ← Fernet 加密、Google Token 驗證（TTLCache）✅
└── startup.py       ← 啟動任務封裝 ✅
```

#### core/security.py — 詳細審查

```python
# ✅ 正確修復：TTLCache 取代 @lru_cache
_token_cache: TTLCache = TTLCache(maxsize=128, ttl=300)
_token_cache_lock = threading.Lock()

@cached(cache=_token_cache, lock=_token_cache_lock)
def _verify_google_token_raw(token: str) -> dict:
    ...
```

| 特性 | 狀態 |
|------|------|
| P0 安全漏洞（LRU Cache 永不過期）修復 | ✅ |
| Fernet 加密/解密統一入口 | ✅ |
| `verify_google_token()` 公開介面 | ✅ |
| `verify_google_token_and_get_sub()` 精簡介面 | ✅ |
| email_verified 驗證 | ✅ |

**細節提示**：`_get_fernet()` 使用 `@lru_cache()` — 這對靜態 Fernet 實例是可接受的（金鑰不會改變），與 Token 快取問題不同，此處合適。

---

### 認證與依賴注入

⚠️ **評分：7/10**

`dependencies.py` 設計整體合理，但有幾個遺留問題：

```python
# ❌ 問題：logging.basicConfig 不應在此呼叫
logging.basicConfig(level=logging.INFO)

# ⚠️ 重複：此 get_db 與 database/engine.py 中的相同
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**認證流程**（已重構完整）：
```
Bearer Token
  → HTTPBearer（security = HTTPBearer()）
  → verify_google_token_basic()
      → core.security.verify_google_token()（TTLCache）
  → get_current_user()
      → services.user_service.get_or_create_user()
      → sync_super_admin_status()
      → grant_default_module_access()（首次）
```

此設計清晰、職責分明，值得肯定。

---

### 業務模組（modules/）

✅ **評分：8/10**

```
backend/modules/
├── ai_hub/          ← AI 整合
├── auth/            ← Facebook Token 管理
│   ├── service.py   ← TokenManager 類別
│   └── router.py
├── fb_ads/          ← Facebook Ads（P3 重構完成）
│   ├── _base.py
│   ├── accounts_service.py
│   ├── analytics_service.py
│   ├── insights_service.py
│   ├── metrics_registry.py
│   └── trends_service.py
├── ga4/             ← GA4 橋接層（重新匯出 ga4_service.py）
└── gsc/             ← GSC 橋接層（重新匯出 gsc_service.py）
```

**fb_ads 重構**：
- 原 `async_services.py`（834 行）已完整拆分為 6 個專職服務模組
- `async_services.py` 現為橋接層（向後相容），有明確廢棄說明

**ga4 / gsc**：
- 模組存在但只是薄橋接層，實際業務邏輯仍在根目錄的 `ga4_service.py` / `gsc_service.py`
- 這是下一階段的重構目標

---

### 服務層（services/）

⚠️ **評分：7/10**

```
backend/services/
├── facebook_service.py
├── integration_service.py  ← P3 新增 ✅
├── permission_service.py
├── user_service.py         ← P2 重構完成 ✅
└── ai/
    ├── zeabur_client.py    ← ❌ 仍有 print()
    └── intent_classifier.py
```

**integration_service.py — 設計評分：9/10**

提供完整的 CRUD + Token 加解密：

| 函式 | 說明 | 狀態 |
|------|------|------|
| `get_user_integration()` | 取得特定整合 | ✅ |
| `get_all_user_integrations()` | 取得所有整合（無 Token）| ✅ |
| `upsert_user_integration()` | 建立或更新（含加密） | ✅ |
| `delete_user_integration()` | 刪除整合 | ✅ |
| `get_decrypted_access_token()` | 解密 Access Token | ✅ |
| `get_decrypted_refresh_token()` | 解密 Refresh Token | ✅ |

**尚未整合的呼叫點**：路由層仍直接讀取 `user.fb_access_token`（見 M-1）。

---

### 路由層（routers/）

✅ **評分：8/10**

```
backend/routers/
├── admin.py
├── ai.py
├── auth.py          ← ⚠️ token-status 仍讀取舊 User 欄位
├── debug.py
├── facebook.py
├── ga4.py
├── gsc.py
├── invites.py
├── metrics.py       ← P4 新增 ✅
├── permissions.py
├── saved_views.py
├── teams.py
└── users.py
```

**速率限制覆蓋**：
```python
@router.post("/exchange-token")
@limiter.limit("10/minute")   # ✅

@router.get("/token-status")
@limiter.limit("30/minute")   # ✅
```

**metrics.py — METRICS_REGISTRY 設計**：30+ 個 Facebook 指標的 Single Source of Truth 實作，前端可動態取得指標定義，避免前後端重複維護。設計優秀。

---

### 快取架構

✅ **評分：9/10**

```
雙層快取架構：
  L1 — TTLCache（10 秒，本地記憶體，單進程快速複用）
    ↓（L1 miss）
  L2 — Redis（自訂 TTL，共享快取，多進程/多實例）
    ↓（L2 miss）
  後端計算
    ↓
  同時寫入 L1 + L2
```

**設計亮點**：
- Redis 不可用時自動降級至 L1（無需手動切換）
- `cache_delete_pattern()` 使用 SCAN 而非 KEYS（避免 Redis 阻塞）
- 保留全套向後相容函式（`get_account_cache`、`get_insights_cache` 等）
- Redis 連線使用單例模式，避免重複建立連線

**limiter.py**：
- slowapi 使用 Redis 進行分散式速率計數（若 REDIS_URL 設定），否則使用記憶體
- 預設限制 200/minute，特殊端點個別設定

---

### 速率限制

✅ **評分：8/10**

| 端點 | 限制 | 評估 |
|------|------|------|
| `POST /api/auth/exchange-token` | 10/min | 合理（敏感操作） |
| `GET /api/auth/token-status` | 30/min | 合理 |
| 全域預設 | 200/min | 合理 |

**建議**：`GET /api/users/me` 等頻繁呼叫的端點也應考慮設定速率限制。

---

## 前端架構詳細審查

### API 客戶端

✅ **評分：9/10**

`frontend/src/services/apiClient.js`：

| 特性 | 狀態 |
|------|------|
| 統一 fetch 封裝 | ✅ |
| Bearer Token 自動附加 | ✅ |
| X-Team-ID Header 自動附加 | ✅ |
| Token 過期前置檢查 | ✅ |
| AbortController 逾時（30s） | ✅ |
| 重試機制（502/503/504） | ✅ |
| 401 自動跳轉登入 | ✅ |
| ApiError 自訂錯誤類別 | ✅ |
| 請求統計（requestCount, errorCount） | ✅ |

**細節問題**：
- 上傳/串流 API 可能需要特殊處理（目前 body 統一為 JSON.stringify）

---

### Token 管理

✅ **評分：8/10**

`frontend/src/utils/auth.js` + `hooks/useTokenRefresh.js`：

```javascript
// ✅ JWT Payload 解析（不驗證簽名，僅讀取宣告）
parseJwtPayload(token)

// ✅ 過期時間快取至 localStorage（避免每次重複解析）
saveAuthToken(token) → 同步儲存 exp * 1000 至 TOKEN_EXPIRY_KEY

// ✅ 過期檢查（預先 5 分鐘警告）
useTokenRefresh(onExpired) → 每 60 秒定期檢查
```

**TODO 項目**（已記錄於程式碼）：
- 行 45：Google OAuth 靜默刷新（implicit flow）尚未實作，到期時強制重登

---

### 狀態管理（React Query）

✅ **評分：9/10**

`package.json` 確認：
```json
"@tanstack/react-query": "^5.90.21",
"@tanstack/react-query-devtools": "^5.91.3"
```

**hooks/ 結構**：
```
frontend/src/hooks/
├── index.js              ← 統一匯出
├── mutations/            ← Mutation Hooks（增/改/刪）
├── queries/              ← Query Hooks（讀取）
├── useAnalyticsFilters.js
├── useOptimistic.js
├── usePermission.jsx
└── useTokenRefresh.js
```

**優點**：
- Queries 與 Mutations 分目錄管理，職責清晰
- QueryClient 統一設定（staleTime、retry 等）

---

### 型別定義

✅ **評分：8/10**

`frontend/src/types/api.js`：完整定義 11 個 JSDoc 型別：

- `User`、`Team`、`TeamMember`
- `AdAccount`、`InsightMetric`、`Campaign`
- `GSCProperty`、`GA4Property`
- `Permission`、`Module`
- `PaginatedResponse`

設計良好，使用 `@typedef` 確保 VSCode IntelliSense 可正確提示。

---

## 資料庫與遷移審查

### Alembic 遷移版本鏈

```
0001_initial_schema.py
  ↓
20260106_add_permissions_tables.py
  ↓
20260114_add_ga4_columns.py
  ↓
230a10d75894_add_saved_views_table.py
  ↓
fe8441e71f69_add_team_token_expires_at.py
  ↓
20260223_p3_integrations_indexes.py  ← 最新
  ↓              ↑
0303de3f01eb_merge_ga4_and_integrations_heads.py  ← 合併頭部（merge commit）
```

**問題**：
1. `20260223_p3_integrations_indexes.py` 使用 SQLite-only SQL（詳見 H-1）
2. 資料遷移 SQL 依賴舊版 User 表欄位（`fb_access_token` 等）存在，未來移除這些欄位前不可移除此 migration

### 複合索引（已建立）

| 索引名稱 | 資料表 | 欄位 | 查詢優化目標 |
|---------|--------|------|------------|
| `ix_user_integrations_lookup` | `user_integrations` | `(user_id, provider)` | 整合查詢 |
| `ix_user_module_access_composite` | `user_module_access` | `(user_id, team_id, module_id)` | 權限查詢 |
| `ix_team_members_user_id` | `team_members` | `(user_id)` | 團隊反查 |
| `ix_saved_views_user_team` | `saved_views` | `(user_id, team_id)` | 視圖查詢 |

---

## 安全性審查

| 面向 | 狀態 | 說明 |
|------|------|------|
| Google ID Token 驗證 | ✅ | TTLCache(ttl=300)，修復 P0 漏洞 |
| Token 加密存儲 | ✅ | Fernet 對稱加密，統一透過 core/security.py |
| SQL 注入防護 | ✅ | 全程使用 SQLAlchemy ORM |
| CORS 設定 | ✅ | 生產環境僅 HTTPS，正則修正完整 |
| 速率限制 | ✅ | slowapi 10-30/min 重要端點 |
| .gitignore（根目錄） | ✅ | 完整涵蓋 .env、*.db、*.log |
| .gitignore（backend/） | ⚠️ | 只有 5 條規則，需補齊 |
| 非 root 容器執行 | ✅ | Dockerfile 建立 appuser |
| 敏感資訊日誌遮蔽 | ✅ | email 遮蔽、Redis URL 遮蔽 |
| Debug print（生產環境） | ❌ | gsc_service.py、zeabur_client.py 仍有 |
| 第三方 API Key 管理 | ⚠️ | User 表舊欄位尚未移除 |

---

## 部署設定審查

### Dockerfile

✅ **評分：9/10**

```dockerfile
FROM python:3.12-slim          # ✅ P2 升版完成
RUN useradd --system appuser   # ✅ 非 root 執行
HEALTHCHECK --interval=30s ... # ✅ P2 健康檢查整合
CMD ["sh", "-c", "python main.py"]
```

**建議**：CMD 使用 shell form 而非 exec form，在容器訊號處理上可能有差異：
```dockerfile
# 建議改為 exec form（PID 1 直接是 Python 進程）
CMD ["python", "main.py"]
# 或搭配 uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.dev.yml

✅ **評分：8/10**

使用 Docker Compose Profiles 設計：
- 預設模式：僅 Redis
- `--profile postgres`：加入 PostgreSQL 16 + pgAdmin

```yaml
# 啟動完整開發環境
docker compose -f docker-compose.dev.yml --profile postgres up -d
```

### requirements.txt

✅ **評分：9/10**

所有依賴已釘定版本範圍（P1 完成）：
```
fastapi>=0.115.0,<0.116.0
redis>=5.2.0,<6.0.0
cryptography>=44.0.0,<45.0.0
# ...
```

---

## 優化實作驗收狀況

> 基於實際程式碼審查，以下為各優化項目的真實執行狀況

| 優先級 | 項目 | 報告聲稱 | 實際驗證 | 差異說明 |
|--------|------|----------|----------|----------|
| P0 | [3.2] TTLCache 修復 | ✅ | ✅ | 完全正確實作 |
| P0 | [6.1] .env 排除 | ✅ | ✅ | 根目錄 .gitignore 完整 |
| P0 | [6.2] SQLite DB 排除 | ✅ | ⚠️ | 根目錄正確，backend/.gitignore 不完整 |
| P1 | [4.2] Token 過期前端處理 | ✅ | ✅ | useTokenRefresh.js 正確實作 |
| P1 | [4.1] 統一 API Client | ✅ | ✅ | apiClient.js 功能完整 |
| P1 | [3.4] 版本釘定 | ✅ | ✅ | requirements.txt 完整釘定 |
| P1 | [3.5] Redis 雙層快取 | ✅ | ✅ | L1+L2 架構、降級設計完善 |
| P2 | [3.1] Token 驗證統一 | ✅ | ✅ | core/security.py 完整 |
| P2 | [3.3] get_current_user 拆分 | ✅ | ✅ | user_service.py 清晰分離 |
| P2 | [3.11] Depends(get_db) 統一 | ✅ | ⚠️ | 兩個 get_db 定義共存 |
| P2 | [6.4] slowapi 速率限制 | ✅ | ✅ | 正確實作 |
| P2 | [7.1] Python 3.12 升版 | ✅ | ✅ | Dockerfile 已更新 |
| P2 | [7.3] /health 端點 | ✅ | ✅ | DB + Redis 狀態完整 |
| P3 | [3.6] database.py 拆分 | ✅ | ✅ | database/ 套件設計良好 |
| P3 | [3.7] async_services.py 拆分 | ✅ | ✅ | modules/fb_ads/ 完整，橋接層正確 |
| P3 | [5.1] UserIntegration 模型 | ✅ | ✅ | 模型與服務均完整 |
| P3 | [5.1] 路由整合 UserIntegration | 🔜（後續） | ❌ | auth.py 仍讀取舊欄位 |
| P3 | [5.2] 複合索引 | ✅ | ✅ | 4 個索引已定義於遷移腳本 |
| P3 | [5.3] PostgreSQL docker-compose | ✅ | ✅ | profiles 設計完整 |
| P3 | [4.3] React Query | ✅ | ✅ | TanStack v5 已整合 |
| P3 | [4.4] JSDoc 型別 | ✅ | ✅ | 11 個型別定義完整 |
| P3 | [4.7] React 19 相容性 | ✅ | ✅ | @react-oauth/google 0.13.4 |
| P3 | [7.4] pytest 測試框架 | ✅ | ❌ | **tests/ 目錄完全不存在** |
| P4 | [4.5] 備份檔案清理 | ✅ | ✅ | 無 .backup / _orig 檔案 |
| P4 | [3.12] print → logger | ✅ | ⚠️ | gsc_service.py / zeabur_client.py 未完成 |
| P4 | [3.10] CORS 正則修正 | ✅ | ✅ | 正確實作 |
| P4 | [3.8] auth.py 間接層移除 | ✅ | ✅ | modules/auth/service.py 直接引用 |
| P4 | [4.6] Metrics Registry | ✅ | ✅ | routers/metrics.py 完整 |
| Alembic | 遷移腳本 PostgreSQL 相容性 | ✅ | ❌ | randomblob() 為 SQLite-only |

**驗收差異總計**：

- **完全正確**：21 項
- **部分問題**：3 項（⚠️）
- **全部未執行**：3 項（❌）：tests/、auth.py 整合、migration 相容性

---

## 必須立即修復事項

### A. 建立 pytest 測試框架（最高優先）

```bash
mkdir backend/tests
```

**最小可行測試套件**（`backend/tests/conftest.py`）：

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.base import Base
from database import get_db
from main import app

SQLALCHEMY_TEST_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    conn = engine.connect()
    transaction = conn.begin()
    session = TestingSessionLocal(bind=conn)
    yield session
    session.close()
    transaction.rollback()
    conn.close()

@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

---

### B. 修復 Alembic 遷移腳本 PostgreSQL 相容性

在 `20260223_p3_integrations_indexes.py` 的 `upgrade()` 中，以 Python-level bulk insert 取代 SQLite-only SQL：

```python
# 替換原本的 op.execute("""INSERT ... randomblob ...""")

from alembic import op
import sqlalchemy as sa
import uuid

def _migrate_users_to_integrations(conn, provider, token_col, refresh_col=None, 
                                    expiry_col=None, extra_cols=None):
    users = conn.execute(
        sa.text(f"SELECT id, {token_col}{', ' + refresh_col if refresh_col else ''} "
                f"FROM users WHERE {token_col} IS NOT NULL")
    ).fetchall()
    
    for row in users:
        conn.execute(
            sa.text("""
                INSERT INTO user_integrations 
                    (id, user_id, provider, access_token, refresh_token, created_at)
                VALUES (:id, :user_id, :provider, :access_token, :refresh_token, CURRENT_TIMESTAMP)
            """),
            {
                "id": str(uuid.uuid4()),
                "user_id": row[0],
                "provider": provider,
                "access_token": row[1],
                "refresh_token": row[2] if refresh_col else None,
            }
        )
```

---

### C. 修復 gsc_service.py 的 print() 呼叫

將以下 18 個 print 替換為 logger：

```python
import logging
logger = logging.getLogger(__name__)

# 替換：
print(f"DEBUG: ...")  →  logger.debug(f"...")
print(f"ERROR: ...")  →  logger.error(f"...")
print("[GSC] ...")    →  logger.info("[GSC] ...")
```

---

### D. 更新 backend/.gitignore

```gitignore
# === 現有規則 ===
venv/
__pycache__/
*.pyc
.env
tokens.json

# === 新增規則 ===
*.pyo
*.pyd
.env.*
*.db
*.sqlite
*.sqlite3
*.log
debug_*.log
*.backup
*.bak
*.orig
*_orig.*
*_backup.*
.pytest_cache/
htmlcov/
.coverage
dist/
build/
```

---

## 中期建議事項（1-2 週內）

### 1. 完成路由層 integration_service 整合

更新 `routers/auth.py` 的 `get_token_status`：

```python
# 改用 integration_service
from services.integration_service import get_user_integration, get_decrypted_access_token

@router.get("/token-status")
def get_token_status(request: Request, db: Session = Depends(get_db), ...):
    user = db.query(User).filter(User.google_id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # 新版：從 user_integrations 表查詢
    integration = get_user_integration(db, user.id, "facebook")
    token_exists = integration is not None and bool(integration.access_token)
    expires_at = integration.token_expiry if integration else None
    ...
```

### 2. 移除 database_LEGACY.py

```bash
git rm backend/database_LEGACY.py
git commit -m "chore: remove database_LEGACY.py (replaced by database/ package)"
```

### 3. 清理 dependencies.py

```python
# 移除第 7 行
# logging.basicConfig(level=logging.INFO)  ← 刪除

# 移除本地 get_db 定義，改用：
from database import get_db  # ← 使用 database/engine.py 的版本
```

### 4. 提升測試覆蓋率目標

| 階段 | 目標覆蓋率 | 重點模組 |
|------|-----------|---------|
| 第一階段（立即） | 30% | auth、health、permissions 端點 |
| 第二階段（1週） | 50% | cache、teams、users CRUD |
| 第三階段（2週） | 65%+ | Facebook/GSC/GA4 整合（mock httpx） |

---

## 架構改進路線圖

### 短期（本次部署前）

```
1. 建立 backend/tests/ + pytest.ini
2. 修復 20260223_p3_integrations_indexes.py PostgreSQL 相容性
3. gsc_service.py: 18 個 print → logger
4. zeabur_client.py production code: 5 個 print → logger
5. 更新 backend/.gitignore
```

### 中期（1 個月內）

```
6. routers/auth.py 整合 integration_service
7. 移除 database_LEGACY.py
8. 清理 dependencies.py（logging.basicConfig、重複 get_db）
9. ga4_service.py / gsc_service.py 完整模組化至 modules/
10. User 表舊 Token 欄位移除（確認遷移數據後）
```

### 長期（3 個月內）

```
11. CI/CD: pytest tests/ --cov 進入 PR merge 門檻
12. 監控: /health 端點整合至外部監控（UptimeRobot/BetterUptime）
13. 前端 Token 靜默刷新（Google OAuth implicit flow）
14. API 文件自動化（FastAPI /docs 頁面加入認證測試）
15. 完整 TypeScript 遷移（前端 .js → .tsx）
```

---

## 附錄：關鍵檔案清單

| 分類 | 檔案 | 行數 | 狀態 |
|------|------|------|------|
| 入口 | `backend/main.py` | 282 | ✅ 良好 |
| 安全性 | `backend/core/security.py` | 182 | ✅ 優秀 |
| 日誌 | `backend/core/logging.py` | 62 | ✅ 優秀 |
| 啟動 | `backend/core/startup.py` | 297 | ✅ 良好 |
| 快取 | `backend/cache.py` | 245 | ✅ 優秀 |
| Redis | `backend/redis_cache.py` | 115 | ✅ 優秀 |
| 速率限制 | `backend/limiter.py` | 25 | ✅ 簡潔 |
| 依賴注入 | `backend/dependencies.py` | 247 | ⚠️ 需清理 |
| DB 引擎 | `backend/database/engine.py` | 92 | ✅ 良好 |
| DB 初始化 | `backend/database/__init__.py` | 76 | ✅ 優秀 |
| UserIntegration | `backend/database/models/integration.py` | 90 | ✅ 優秀 |
| 整合服務 | `backend/services/integration_service.py` | 250 | ✅ 優秀 |
| 使用者服務 | `backend/services/user_service.py` | 152 | ✅ 良好 |
| GSC 服務 | `backend/gsc_service.py` | 336 | ❌ 需重構 |
| GA4 服務 | `backend/ga4_service.py` | 555 | ⚠️ 需模組化 |
| AI 客戶端 | `backend/services/ai/zeabur_client.py` | — | ⚠️ print 殘留 |
| 認證路由 | `backend/routers/auth.py` | 104 | ⚠️ 需整合新表 |
| 指標路由 | `backend/routers/metrics.py` | 226 | ✅ 優秀 |
| API 客戶端 | `frontend/src/services/apiClient.js` | 183 | ✅ 優秀 |
| Auth 工具 | `frontend/src/utils/auth.js` | 98 | ✅ 良好 |
| 型別定義 | `frontend/src/types/api.js` | 135 | ✅ 優秀 |
| 遷移腳本 | `backend/alembic/versions/20260223_p3_integrations_indexes.py` | 220 | ❌ SQLite-only |
| 遺留代碼 | `backend/database_LEGACY.py` | 324 | ❌ 應刪除 |
| 測試（計畫） | `backend/tests/` | — | ❌ 不存在 |

---

*本報告由 GitHub Copilot 全程序程式碼審查自動生成，涵蓋實際磁碟檔案驗證、程式碼靜態分析及架構一致性審查。*  
*報告日期：2026-02-23 | 版本：1.0.0*
