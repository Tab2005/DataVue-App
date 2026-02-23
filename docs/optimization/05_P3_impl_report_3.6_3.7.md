# P3 實作報告：後端重構（3.6 & 3.7）

> **分支**：`dev-saas`  
> **實作日期**：2026-02-23  
> **涵蓋項目**：3.6（拆分 database.py）、3.7（拆分 async_services.py）

---

## 目錄

1. [實作摘要](#實作摘要)
2. [3.6 — 拆分 database.py](#36--拆分-databasepy)
3. [3.7 — 拆分 async_services.py](#37--拆分-async_servicespy)
4. [受影響檔案清單](#受影響檔案清單)
5. [驗收核對表](#驗收核對表)
6. [注意事項與後續建議](#注意事項與後續建議)

---

## 實作摘要

### 已完成
| 項目 | 舊版 | 新版 | 行數變化 |
|------|------|------|----------|
| 3.6 database | `database.py`（324 行，單一檔案） | `database/`（套件，9 個檔案） | 單檔 → 分散 |
| 3.7 async_services | `async_services.py`（834 行） | `modules/fb_ads/`（7 個檔案）| 單檔 → 分散 |

### 向後相容性策略
- **database**：舊版 `database.py` 重命名為 `database_LEGACY.py`；Python imports 自動使用 `database/` 套件（Python 3 以套件優先於同名模組）
- **async_services**：原檔案改為橋接層（44 行），從 `modules.fb_ads` re-export 所有符號，既有呼叫無需修改

---

## 3.6 — 拆分 `database.py`

### 新目錄結構

```
backend/database/
├── __init__.py         ← 公開 API（向後相容匯出）
├── base.py             ← DeclarativeBase = declarative_base()
├── engine.py           ← 引擎、SessionLocal、get_db、check_db_connection
└── models/
    ├── __init__.py     ← 匯出所有模型
    ├── user.py         ← User, UserRole, UserStatus
    ├── team.py         ← Team, TeamMember, TeamInvite
    ├── view.py         ← SavedView, PageTitle
    └── permission.py   ← Module, Permission, Role, RolePermission,
                           UserModuleAccess, UserPermission
```

### 各檔案職責說明

#### `database/base.py`（5 行）
```python
from sqlalchemy.orm import declarative_base
Base = declarative_base()
```
單一職責：提供 SQLAlchemy ORM 基底類別。

#### `database/engine.py`（約 70 行）
- `_normalize_sqlite_url()`：將相對 SQLite 路徑解析為絕對路徑
- `get_engine()`：自動判斷 SQLite（開發）/ PostgreSQL（生產）
- `check_db_connection()`：驗證資料庫連線
- `get_db()`：FastAPI 依賴注入 Generator
- 模組載入時自動驗證連線並記錄日誌

#### `database/models/user.py`（約 68 行）
包含原 `database.py` 中的 `UserRole`、`UserStatus`（Enum）及 `User` 模型。  
**注意**：維持原始 Enum 值（`ADMIN`、`MEMBER`、`VIEWER` 大寫，與現有資料庫記錄相容）。

#### `database/models/team.py`（約 60 行）
包含 `Team`、`TeamMember`、`TeamInvite` 三個模型及其關聯。  
`TeamMember.role` 共用 `UserRole` Enum（從 `database.models.user` 匯入）。

#### `database/models/view.py`（約 40 行）
包含 `SavedView`（指標視圖）、`PageTitle`（GSC 頁面標題快取）。

#### `database/models/permission.py`（約 90 行）
包含完整的權限管理系統模型：
- `Module`：功能模組定義
- `Permission`：細緻權限定義（`模組:功能:動作`）
- `Role` / `RolePermission`：角色與角色-權限關聯
- `UserModuleAccess`：使用者-模組存取
- `UserPermission`：使用者-權限細緻授予/撤銷

#### `database/__init__.py`（約 70 行）
統一匯出所有符號，與原 `database.py` 的公開 API 完全相容：
```python
from database import (
    engine, SessionLocal, get_db, check_db_connection, DATABASE_URL, Base,
    User, UserRole, UserStatus,
    Team, TeamMember, TeamInvite,
    SavedView, PageTitle,
    Module, Permission, Role, RolePermission, UserModuleAccess, UserPermission,
    init_db,
)
```

### Alembic 更新（`alembic/env.py`）
```python
from database import Base, DATABASE_URL as ENV_DATABASE_URL
# 確保所有 ORM 模型已載入至 Base.metadata（autogenerate 必要）
import database.models  # noqa: F401
```
新增 `import database.models` 確保所有模型在 autogenerate 時均被發現。

---

## 3.7 — 拆分 `async_services.py`

### 新目錄結構

```
backend/modules/fb_ads/
├── __init__.py              ← 公開 API + AsyncFacebookService wrapper class
├── _base.py                 ← BASE_URL, TIMEOUT, get_headers()
├── metrics_registry.py      ← METRICS_REGISTRY dict, build_fb_fields()
├── accounts_service.py      ← get_all_ad_accounts()（含快取）
├── insights_service.py      ← get_account_insights()（含前後期並行抓取）
├── analytics_service.py     ← get_custom_report()（動態欄位 + 扁平化處理）
└── trends_service.py        ← get_analytics_trend()（每日時序比較）
```

### 各服務職責說明

#### `modules/fb_ads/_base.py`（20 行）
共用常數（`BASE_URL = "https://graph.facebook.com/v24.0"`、`TIMEOUT = 30.0`）  
及 `get_headers(user_id, team_id, allow_fallback)` ——不變動認證邏輯，直接沿用 `TokenManager`。

#### `modules/fb_ads/metrics_registry.py`（約 170 行）
- `METRICS_REGISTRY`：完整的指標定義字典（100+ 指標）
- `build_fb_fields(custom_fields, level)`：動態建構 FB API 請求欄位字串

#### `modules/fb_ads/accounts_service.py`（約 55 行）
- `get_all_ad_accounts(user_id, team_id, strict_token)`
- 負責查快取 → 呼叫 FB API → 格式化並回寫快取

#### `modules/fb_ads/insights_service.py`（約 90 行）
- `get_account_insights(account_id, user_id, days, team_id, strict_token)`
- 並行取得「本期」與「前期」及「趨勢」三組資料（asyncio.gather）

#### `modules/fb_ads/analytics_service.py`（約 190 行）
- `_process_flat_row(row, level, ad_meta_map)` ← 私有輔助函式（110 行）
- `get_custom_report(account_id, user_id, since, until, level, team_id, custom_fields, strict_token)`
- 包含完整的廣告指標計算邏輯（電商、影音、訊息、Lead、App 等）

#### `modules/fb_ads/trends_service.py`（約 130 行）
- `_process_daily_item(item)` ← 每日數據處理輔助函式
- `get_analytics_trend(account_id, user_id, since, until, prev_since, prev_until, team_id, strict_token)`
- 並行取得本期與前期每日數據，合併為時間序列格式

#### `modules/fb_ads/__init__.py`（約 70 行）
```python
class AsyncFacebookService:
    """向後相容 wrapper —— 所有 staticmethod 委派至對應服務函式"""
    ...
```
直接 wrapper，零邏輯、零資料複製，維持既有 caller 的使用方式不變。

### 橋接層（`async_services.py`，44 行）
```python
"""Deprecated bridge —— 請改用 modules.fb_ads"""
from modules.fb_ads import AsyncFacebookService, METRICS_REGISTRY, build_fb_fields, ...
```
現有 `from async_services import AsyncFacebookService` 呼叫**無需修改**。

---

## 受影響檔案清單

### 新增檔案

| 路徑 | 用途 |
|------|------|
| `backend/database/__init__.py` | database 套件公開 API |
| `backend/database/base.py` | DeclarativeBase |
| `backend/database/engine.py` | 引擎、Session、get_db |
| `backend/database/models/__init__.py` | 模型匯出 |
| `backend/database/models/user.py` | User 相關 |
| `backend/database/models/team.py` | Team 相關 |
| `backend/database/models/view.py` | SavedView, PageTitle |
| `backend/database/models/permission.py` | 權限系統模型 |
| `backend/modules/fb_ads/__init__.py` | FB Ads 模組公開 API |
| `backend/modules/fb_ads/_base.py` | 共用常數 |
| `backend/modules/fb_ads/metrics_registry.py` | 指標定義與動態欄位建構 |
| `backend/modules/fb_ads/accounts_service.py` | 廣告帳號查詢 |
| `backend/modules/fb_ads/insights_service.py` | KPI 洞察 |
| `backend/modules/fb_ads/analytics_service.py` | 自訂報告 |
| `backend/modules/fb_ads/trends_service.py` | 趨勢時序 |

### 修改檔案

| 路徑 | 變更說明 |
|------|----------|
| `backend/async_services.py` | 834 行 → 44 行橋接層（re-export） |
| `backend/alembic/env.py` | 新增 `import database.models` 確保 autogenerate |

### 重命名檔案

| 舊路徑 | 新路徑 | 說明 |
|--------|--------|------|
| `backend/database.py` | `backend/database_LEGACY.py` | 避免與 `database/` 套件衝突，保留作歷史參考 |

---

## 驗收核對表

### 3.6 — database 套件
- [x] `backend/database/` 目錄結構已建立（9 個檔案）
- [x] 所有 ORM 模型已分散至對應模型檔案
- [x] `database/__init__.py` 維持向後相容的匯出 API
- [x] Alembic `env.py` 已更新（新增 `import database.models`）
- [x] 原始 `database.py` 已重命名為 `database_LEGACY.py`
- [ ] `python -c "from database import User, Team, Module"` 執行成功（需在後端環境驗證）

### 3.7 — fb_ads 模組
- [x] `modules/fb_ads/` 目錄已建立（7 個檔案）
- [x] 各服務檔案均不超過 200 行
- [x] `async_services.py` 已更新為橋接層（44 行）
- [x] `AsyncFacebookService` 介面完全向後相容
- [ ] 現有路由功能測試通過（需於後端環境驗證）

---

## 注意事項與後續建議

### 1. Python 版本相容性
- `database/models/user.py` 使用 `str, enum.Enum` 混繼承，需 Python 3.11+（或確保 SQLAlchemy Enum 型別處理正確）
- `database/engine.py` 的 `BASE_DIR` 計算以 `engine.py` 所在的上層目錄（`backend/`）為基準

### 2. `database_LEGACY.py` 後續處理
確認新套件在生產環境穩定運行一段時間後，可執行以下指令移除：
```bash
git rm backend/database_LEGACY.py
git commit -m "chore: remove legacy database.py after successful migration"
```

### 3. 尚未實作項目（本批次不含）
依計畫書，以下項目尚未實作：
- **5.1** — UserIntegration 表（拆分 User Token 至新表）
- **5.2** — 資料庫索引優化（Alembic 遷移）
- **5.3** — 開發環境改用 PostgreSQL（docker-compose.dev.yml）
- **7.4** — pytest 測試框架

### 4. 後端環境驗證步驟
```bash
cd backend

# 驗證 database 套件匯入
python -c "from database import User, Team, Module, get_db; print('DB imports OK')"

# 驗證 fb_ads 模組匯入
python -c "from modules.fb_ads import AsyncFacebookService, METRICS_REGISTRY; print('FB Ads imports OK')"

# 驗證 async_services 橋接層
python -c "from async_services import AsyncFacebookService; print('Bridge OK')"

# 確認無直接依賴舊 database.py 的殘留 import
grep -r "database_LEGACY" backend/ --include="*.py"
```

### 5. 若 alembic autogenerate 未偵測到模型
執行時確保使用新的 env.py（已加入 `import database.models`）：
```bash
cd backend
alembic revision --autogenerate -m "verify_model_detection"
```
若無變更被偵測，表示 Base.metadata 已正確載入所有模型。
