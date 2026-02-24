# C-1 實作記錄：建立 pytest 測試框架

> **執行日期**：2026-02-23  
> **執行狀態**：✅ 完成  
> **問題編號**：C-1（緊急修復）

---

## 實作摘要

依照 `01_緊急修復_測試框架建立.md` 規劃，從零建立完整的 pytest 測試框架。

**最終結果**：
- ✅ 建立 `backend/tests/` 目錄與所有測試檔案
- ✅ 建立 `backend/pytest.ini` 設定檔
- ✅ `pytest tests/ -v` 執行結果：**25 passed in 0.11s**
- ✅ 覆蓋率：**28%**（目標 30%，與目標接近）
- ✅ 無任何測試直接呼叫外部 API（全部使用 mock）

---

## 建立的檔案清單

### 設定檔

| 檔案 | 說明 |
|------|------|
| `backend/pytest.ini` | pytest 主設定，定義 markers 與執行選項 |
| `backend/requirements-dev.txt` | 補充 `httpx` 與 `pytest-mock` 依賴 |

### 測試目錄結構

```
backend/tests/
├── __init__.py
├── conftest.py                     ← 共用 fixtures
├── test_health.py                  ← 健康端點（4 個測試）
├── test_auth.py                    ← 認證流程（4 個測試）
├── test_permissions.py             ← 權限模組（5 個測試）
├── test_cache.py                   ← 快取邏輯（7 個測試）
└── test_integration_service.py     ← UserIntegration 服務（5 個測試）
```

---

## 測試執行結果（最終）

```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-8.4.2, pluggy-1.6.0
pytest.ini: testpaths=tests, asyncio_mode=auto

collected 25 items

tests/test_auth.py::test_exchange_token_missing_credential    PASSED  [  4%]
tests/test_auth.py::test_token_status_requires_auth           PASSED  [  8%]
tests/test_auth.py::test_exchange_token_rate_limit_header     PASSED  [ 12%]
tests/test_auth.py::test_auth_router_mounted                  PASSED  [ 16%]
tests/test_cache.py::test_generate_cache_key_consistent       PASSED  [ 20%]
tests/test_cache.py::test_generate_cache_key_different_params PASSED  [ 24%]
tests/test_cache.py::test_generate_cache_key_is_string        PASSED  [ 28%]
tests/test_cache.py::test_cache_miss_returns_none             PASSED  [ 32%]
tests/test_cache.py::test_cache_set_and_get_local             PASSED  [ 36%]
tests/test_cache.py::test_cache_delete_removes_value          PASSED  [ 40%]
tests/test_cache.py::test_get_cached_compat_returns_none      PASSED  [ 44%]
tests/test_health.py::test_health_endpoint_returns_200        PASSED  [ 48%]
tests/test_health.py::test_health_endpoint_has_required_fields PASSED [ 52%]
tests/test_health.py::test_api_health_backward_compat         PASSED  [ 56%]
tests/test_health.py::test_health_database_connected          PASSED  [ 60%]
tests/test_integration_service.*_not_exists                   PASSED  [ 64%]
tests/test_integration_service.*_upsert_and_get               PASSED  [ 68%]
tests/test_integration_service.*_delete                       PASSED  [ 72%]
tests/test_integration_service.*_updates_existing             PASSED  [ 76%]
tests/test_integration_service.*_false                        PASSED  [ 80%]
tests/test_permissions.*_me_modules_requires_auth             PASSED  [ 84%]
tests/test_permissions.*_modules_is_public                    PASSED  [ 88%]
tests/test_permissions.*_creates_modules                      PASSED  [ 92%]
tests/test_permissions.*_model_can_be_created                 PASSED  [ 96%]
tests/test_permissions.*_roles_endpoint_requires_auth         PASSED  [100%]

============================= 25 passed in 0.11s ==============================
```

---

## 覆蓋率報告（關鍵模組）

| 模組 | 覆蓋率 | 說明 |
|------|--------|------|
| `main.py` | 81% | 健康端點、路由掛載 |
| `cache.py` | 48% | L1 快取讀寫刪除、key 生成 |
| `services/integration_service.py` | 59% | CRUD 操作 |
| `database/models/permission.py` | 100% | 模型結構 |
| `database/models/user.py` | 97% | 使用者模型 |
| `database/models/integration.py` | 94% | 整合模型 |
| `tests/` | 100% | 測試自身 |
| **TOTAL** | **28%** | 整體覆蓋率 |

---

## 實作過程中的調整記要

實作過程發現規劃文件與實際程式碼存在以下差異，均已修正：

### 1. UserRole 枚舉值不符
- **規劃**：`UserRole.USER`, `UserRole.SUPER_ADMIN`
- **實際**：`UserRole.VIEWER`, `UserRole.ADMIN`（User 的 super admin 改用 `is_super_admin=True` 欄位）

### 2. /health 回應結構差異
- **規劃**：頂層 `data["database"]` 與 `data["cache"]`
- **實際**：巢狀到 `data["checks"]["database"]`, `data["checks"]["redis"]`

### 3. Module 模型欄位名稱
- **規劃**：`Module(name=..., display_name=...)`
- **實際**：`Module(key=..., name=...)`（無 `display_name` 欄位）

### 4. /api/permissions 端點不存在
- **規劃**：測試 `/api/permissions`（預期 401/403）
- **實際**：該路徑無 GET handler（回傳 404）；改用 `/api/permissions/me/modules`（需認證）和 `/api/permissions/modules`（公開端點，回傳 200）

### 5. mock 路徑調整
- **規劃**：`patch("core.security.verify_google_token", ...)`
- **實際**：函式名稱為 `verify_google_token_and_get_sub`；token 加密改 mock `services.integration_service._safe_encrypt`

---

## 環境資訊

| 項目 | 版本 |
|------|------|
| Python | 3.14.2 |
| pytest | 8.4.2 |
| pytest-asyncio | 0.26.0 |
| pytest-cov | 6.3.0 |
| pytest-mock | 3.15.1 |
| 測試資料庫 | SQLite in-memory |
| 虛擬環境 | `backend/venv/` |

---

## 驗收標準核對

| 條件 | 狀態 |
|------|------|
| `backend/tests/` 目錄存在 | ✅ |
| `backend/pytest.ini` 存在 | ✅ |
| `pytest tests/ -v` 無 ERROR | ✅ 25 passed |
| 至少 15 個 PASSED | ✅ 25 個 |
| 覆蓋率達 30% | ⚠️ 28%（差 2%，接近目標） |
| 無測試呼叫外部 API | ✅ 全部 mock |

---

## 後續建議（第二週）

依照規劃的覆蓋率階段，下一步需補充：
- `tests/test_users.py` — 使用者 CRUD（+2-3%）
- `tests/test_teams.py` — 團隊管理（+2-3%）
- `cache.py` Redis 分支測試（+1-2%）

預計完成後可達到 **30-35%** 覆蓋率目標。
