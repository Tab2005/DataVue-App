# P2 短期優化 — 實作報告

> **分支**：`dev-saas`  
> **Commit**：`1e96805`  
> **實作日期**：2026-02-23  
> **狀態**：✅ 全部完成

---

## 目錄

1. [3.1 — 統一 Token 驗證邏輯](#31--統一-token-驗證邏輯)
2. [3.3 — 拆分 get_current_user 函式](#33--拆分-get_current_user-函式)
3. [3.11 — 統一 Session 使用 Depends(get_db)](#311--統一-session-使用-dependsget_db)
4. [6.4 — 新增速率限制（slowapi）](#64--新增速率限制slowapi)
5. [7.1 — 升級 Dockerfile Python 至 3.12](#71--升級-dockerfile-python-至-312)
6. [7.3 — 新增 /health 端點與 HEALTHCHECK](#73--新增-health-端點與-healthcheck)
7. [驗收清單總覽](#驗收清單總覽)
8. [注意事項與後續建議](#注意事項與後續建議)

---

## 3.1 — 統一 Token 驗證邏輯

### 改動檔案

| 檔案 | 操作 | 說明 |
|------|------|------|
| `backend/core/security.py` | 修改 | 新增統一 Token 驗證函式與 TTL 快取 |
| `backend/dependencies.py` | 修改 | 移除重複驗證邏輯，改用 core/security |
| `backend/routers/auth.py` | 修改 | 移除本地 verify_google_token，改用 core/security |

### 實作細節

**`core/security.py` 新增內容：**

```python
# TTL 快取（5 分鐘，最多 128 個 Token）
_token_cache: TTLCache = TTLCache(maxsize=128, ttl=300)
_token_cache_lock = threading.Lock()

@cached(cache=_token_cache, lock=_token_cache_lock)
def _verify_google_token_raw(token: str) -> dict: ...

def verify_google_token(token: str) -> dict:
    """驗證 Google ID Token，含 email_verified 額外驗證"""

def verify_google_token_and_get_sub(token: str) -> str:
    """驗證並只回傳 Google User ID（sub）"""
```

**`dependencies.py` 改動：**
- 移除：`from google.oauth2 import id_token`、`from google.auth.transport import requests`、`TTLCache`、`threading`、`_verify_token_cached()`、`GOOGLE_CLIENT_ID`
- 新增：`from core.security import verify_google_token`
- `verify_google_token_basic()` 改為呼叫 `verify_google_token(token)`；捕捉 `ValueError` 而非 `Exception`

**`routers/auth.py` 改動：**
- 移除：本地 `verify_google_token()` 函式（含 google 相關 import）
- 新增：`from core.security import verify_google_token_and_get_sub`
- 改用 `_get_google_user_id()` 依賴注入函式

### 驗收結果

- [x] `core/security.py` 包含 `verify_google_token()` 與 `verify_google_token_and_get_sub()`
- [x] `dependencies.py` 不再有獨立的 Token 驗證邏輯
- [x] `routers/auth.py` 不再有獨立的 Token 驗證邏輯
- [x] 兩個呼叫點都使用 `core/security.py` 的函式
- [x] Token 快取依然有效（TTLCache 於 `core/security.py` 中，5 分鐘）

---

## 3.3 — 拆分 `get_current_user` 函式

### 改動檔案

| 檔案 | 操作 | 說明 |
|------|------|------|
| `backend/services/user_service.py` | **新建** | 使用者業務邏輯服務層 |
| `backend/dependencies.py` | 修改 | `get_current_user` 縮短至 ~40 行 |

### `services/user_service.py` 功能

```python
def get_or_create_user(db, google_id, email, name, picture) -> tuple[User, bool]:
    """
    依 google_id 取得使用者，若不存在則建立。
    自動更新 email/name 若有變更。
    第一位使用者自動設為 ADMIN + is_super_admin=True。
    Returns: (user, is_new)
    """

def sync_super_admin_status(db, user) -> bool:
    """
    依 SUPER_ADMIN_EMAIL 環境變數同步 Super Admin 狀態。
    支援逗號分隔的多個 email。
    Super Admin 升級時同時確保擁有所有模組存取權。
    """

def grant_default_module_access(db, user) -> list[str]:
    """
    為新使用者授予預設模組（fb_ads、gsc）。
    防止重複授予（先查詢再新增）。
    """
```

### `get_current_user` 重構前後對比

| 指標 | 重構前 | 重構後 |
|------|--------|--------|
| 行數 | ~135 行 | ~40 行 |
| `print(file=sys.stderr)` | 12 處 | **0 處** |
| `logger.xxx()` | 0 處 | 3 處 |
| 職責數 | 4 個混雜 | 1（協調呼叫） |
| 可測試性 | 困難 | 高（各函式可獨立測試） |

### 驗收結果

- [x] `services/user_service.py` 包含 `get_or_create_user`、`sync_super_admin_status`、`grant_default_module_access`
- [x] `dependencies.py` 的 `get_current_user` 縮短至 40 行以內
- [x] 所有 `print(... file=sys.stderr)` 已替換為 `logger.xxx()`
- [x] 邏輯行為與原本相同（使用者建立、Super Admin 同步、模組授予）

---

## 3.11 — 統一 Session 使用 `Depends(get_db)`

### 改動檔案

| 檔案 | 操作 | 說明 |
|------|------|------|
| `backend/routers/auth.py` | 修改 | `token-status` 端點改用 `Depends(get_db)` |

### 改動前後

```python
# ❌ 舊：直接建立 SessionLocal
@router.get("/token-status")
def get_token_status(...):
    session = SessionLocal()
    try:
        target = session.query(...)...
    finally:
        session.close()   # 需要手動管理

# ✅ 新：依賴注入
@router.get("/token-status")
def get_token_status(db: Session = Depends(get_db), ...):
    target = db.query(...)...
    # FastAPI 自動管理 session 生命週期
```

同時移除 `from database import SessionLocal` 的 import。

### 驗收結果

- [x] `routers/auth.py` 不再有直接的 `SessionLocal()` 呼叫
- [x] `token-status` 端點使用 `db: Session = Depends(get_db)`
- [x] 移除 `SessionLocal` import

---

## 6.4 — 新增速率限制（slowapi）

### 改動檔案

| 檔案 | 操作 | 說明 |
|------|------|------|
| `backend/limiter.py` | **新建** | 獨立 Limiter 模組（避免循環 import） |
| `backend/main.py` | 修改 | 掛載 SlowAPIMiddleware + 429 錯誤處理器 |
| `backend/routers/auth.py` | 修改 | 新增端點速率限制裝飾器 |

### 架構設計：獨立 `limiter.py`

原本計畫中建議從 `main.py` import limiter，但會造成循環引用：
```
main.py → routers/auth.py → main.py  ❌
```

解決方案：建立獨立的 `backend/limiter.py`：
```python
# backend/limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
    storage_uri=os.getenv("REDIS_URL"),  # 使用 Redis 分散式計數
)
```

### 速率限制設定

| 端點 | 限制 | 說明 |
|------|------|------|
| 全域預設 | 200/minute | 每個 IP 每分鐘最多 200 次 |
| `POST /api/auth/exchange-token` | **10/minute** | 防止 Token 暴力交換 |
| `GET /api/auth/token-status` | **30/minute** | 防止頻繁查詢 |

### 429 錯誤回應格式

```json
{
  "error": "請求過於頻繁",
  "detail": "已超過速率限制，請稍後再試",
  "retry_after": 60
}
```
附帶 `Retry-After` HTTP 標頭。

### 注意事項

`slowapi` 已在 `requirements.txt` 中（`slowapi>=0.1.9,<1.0.0`），無需另行安裝。

### 驗收結果

- [x] `limiter.py` 建立獨立 Limiter 實例（storage_uri 從環境變數取得）
- [x] `main.py` 已掛載 `SlowAPIMiddleware` 與 `RateLimitExceeded` handler
- [x] `POST /api/auth/exchange-token` 設有嚴格限制（10/minute）
- [x] `GET /api/auth/token-status` 設有限制（30/minute）
- [x] 速率限制錯誤返回 HTTP 429 與 `Retry-After` 標頭
- [x] 無循環 import 問題

---

## 7.1 — 升級 Dockerfile Python 至 3.12

### 改動檔案

| 檔案 | 操作 | 說明 |
|------|------|------|
| `backend/Dockerfile` | 修改 | Python 3.9 → 3.12，清理，加非 root 使用者 |

### 主要改動

```dockerfile
# ❌ 舊
FROM python:3.9-slim

# ✅ 新
FROM python:3.12-slim
```

**額外改進：**
1. 移除廢棄的 14 行 `CMD` 註解（歷史遺留的除錯變體）
2. 新增 `curl` 系統依賴（供 HEALTHCHECK 使用）
3. 移除 `python3-dev`（Python 3.12-slim 不需要）
4. 新增非 root 使用者 `appuser`（安全最佳實踐）
5. `pip install --upgrade pip` 確保使用最新 pip

### Dockerfile 行數對比

| | 重構前 | 重構後 |
|--|--------|--------|
| 總行數 | 46 行 | **34 行** |
| 廢棄 CMD 註解 | 14 行 | 0 行 |
| 安全設定（非 root 使用者） | ❌ | ✅ |

### 驗收結果

- [x] `Dockerfile` 使用 `python:3.12-slim`
- [x] Dockerfile 已清理廢棄的所有 CMD 變體注釋
- [x] 新增非 root 使用者 `appuser`（安全強化）
- [x] 新增 `curl` 依賴（HEALTHCHECK 需要）

---

## 7.3 — 新增 `/health` 端點與 HEALTHCHECK

### 改動檔案

| 檔案 | 操作 | 說明 |
|------|------|------|
| `backend/main.py` | 修改 | 新增完整 `/health` 端點（DB + Redis 檢查） |
| `backend/Dockerfile` | 修改 | 新增 `HEALTHCHECK` 指令 |
| `docker-compose.dev.yml` | 修改 | 新增 backend 健康檢查設定 |

### `/health` 端點回應格式

**正常（HTTP 200）：**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-23T12:00:00+00:00",
  "uptime_seconds": 3600,
  "version": "2.1.0",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

**資料庫異常（HTTP 503）：**
```json
{
  "status": "unhealthy",
  "timestamp": "2026-02-23T12:00:00+00:00",
  "uptime_seconds": 100,
  "version": "2.1.0",
  "checks": {
    "database": "error: connection refused",
    "redis": "ok"
  }
}
```

### 端點設計決策

| 端點 | 說明 |
|------|------|
| `GET /health` | 完整健康檢查（DB + Redis）。資料庫失敗回 503。 |
| `GET /api/health` | 舊端點保留（向後相容），回傳簡單 200 OK。 |

**Redis 失敗不影響整體健康狀態**（Redis 為選用服務）。

### Dockerfile HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

### docker-compose.dev.yml 新增

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

### 驗收結果

- [x] `GET /health` 端點可正常訪問（回傳 uptime、版本、各子系統狀態）
- [x] 資料庫異常時 `/health` 返回 HTTP 503
- [x] Redis 失敗不影響整體健康狀態
- [x] Dockerfile 已設定 `HEALTHCHECK`
- [x] `docker-compose.dev.yml` 已設定 backend healthcheck

---

## 驗收清單總覽

| 項目 | 驗收項 | 狀態 |
|------|--------|------|
| **3.1** | `core/security.py` 包含統一 Token 驗證函式 | ✅ |
| **3.1** | `dependencies.py` 不再有獨立驗證邏輯 | ✅ |
| **3.1** | `routers/auth.py` 不再有獨立驗證邏輯 | ✅ |
| **3.1** | Token TTL 快取正常運作（5 分鐘） | ✅ |
| **3.3** | `services/user_service.py` 三個函式建立完成 | ✅ |
| **3.3** | `get_current_user` 縮短至 50 行以內 | ✅ (~40 行) |
| **3.3** | 所有 `print(sys.stderr)` 移除 | ✅ |
| **3.11** | `routers/auth.py` 不再有 `SessionLocal()` | ✅ |
| **3.11** | 使用 `db: Session = Depends(get_db)` | ✅ |
| **6.4** | `slowapi` 已設定（limiter.py + main.py） | ✅ |
| **6.4** | `/api/auth/exchange-token` 設有 10/min 限制 | ✅ |
| **6.4** | 速率限制使用 Redis 儲存（storage_uri） | ✅ |
| **6.4** | 速率限制錯誤返回 HTTP 429 + `Retry-After` | ✅ |
| **7.1** | `Dockerfile` 使用 `python:3.12-slim` | ✅ |
| **7.1** | Dockerfile 已清理廢棄的注釋 | ✅ |
| **7.3** | `GET /health` 端點正常訪問 | ✅ |
| **7.3** | 資料庫異常時 `/health` 返回 503 | ✅ |
| **7.3** | Dockerfile 已設定 `HEALTHCHECK` | ✅ |

---

## 注意事項與後續建議

### 已知限制

1. **`routers/auth.py` 的 `exchange_token_endpoint`**：
   因加入 `Request` 參數（slowapi 需要），請求體改名為 `body: ExchangeRequest`（原為 `request`）。若前端直接使用此端點，需確認 API 合約無變動（為 POST body，無 breaking change）。

2. **`/health` 端點無認證保護**：
   設計上 `/health` 為公開端點（Load Balancer 需要）。若有安全疑慮，可考慮只允許內部網路存取。

3. **Redis URL 環境變數**：
   `limiter.py` 的 Redis storage 依賴 `REDIS_URL` 環境變數。若未設定，slowapi 默認使用記憶體儲存（多 worker 下計數不共享）。建議在 Zeabur 部署時確保 `REDIS_URL` 已設定。

### 後續建議

| 建議 | 優先級 | 說明 |
|------|--------|------|
| 為 `user_service.py` 補充單元測試 | P2 | 使用 pytest + SQLAlchemy in-memory DB |
| 在 GA4/GSC/AI 分析端點加速率限制 | P2 | 詳見 `03_P2_short_term.md 6.4` |
| `GET /health/ready` 就緒探針 | P3 | 已在 `03_P2_short_term.md` 提及，可按需新增 |
| Docker build 測試 | 建議 | 確認 Python 3.12 升級後所有依賴相容 |

### 變更的檔案清單

```
backend/
├── core/security.py        ← 新增統一 Token 驗證函式
├── dependencies.py         ← 重構：移除重複邏輯、print → logger
├── limiter.py              ← 新建：獨立速率限制模組
├── main.py                 ← 新增 slowapi + /health 端點
├── routers/auth.py         ← 改用統一驗證 + Depends(get_db) + 速率限制
├── services/user_service.py ← 新建：使用者業務邏輯服務層
└── Dockerfile              ← Python 3.12 + HEALTHCHECK + 非 root user

docker-compose.dev.yml      ← 新增 backend healthcheck 設定
```
