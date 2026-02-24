# P1 優化實作記錄

> **分支**：`dev-saas`  
> **完成日期**：2026-02-23  
> **涵蓋項目**：4.1、4.2、3.4、3.5  
> **總修改檔案**：11 個

---

## 目錄

1. [4.1 — 統一 Frontend API Client](#41--統一-frontend-api-client)
2. [4.2 — Frontend Token 過期偵測](#42--frontend-token-過期偵測)
3. [3.4 — 釘定 requirements.txt 套件版本](#34--釘定-requirementstxt-套件版本)
4. [3.5 — Redis 雙層快取架構](#35--redis-雙層快取架構)
5. [驗收清單](#驗收清單)
6. [後續注意事項](#後續注意事項)

---

## 4.1 — 統一 Frontend API Client

### 新增 / 修改的檔案

| 檔案 | 操作 | 說明 |
|------|------|------|
| `frontend/src/services/apiClient.js` | **新增** | 統一 API 請求封裝 |
| `frontend/src/services/userService.js` | **重構** | 改用 apiClient |
| `frontend/src/services/adminService.js` | **重構** | 改用 apiClient |
| `frontend/src/services/teamService.js` | **重構** | 改用 apiClient |
| `frontend/src/services/aiService.js` | **重構** | testConnection 改用 apiClient；串流端點保留原生 fetch |

### apiClient.js 核心功能

```
apiClient
├── get(path, options)
├── post(path, body, options)
├── put(path, body, options)
├── patch(path, body, options)
├── delete(path, options)
└── getStats()                 → { requestCount, errorCount }
```

**關鍵特性**：

- **401 自動導向登入頁**：清除 Token → 儲存 `redirectAfterLogin` → 跳轉 `/login`
- **502/503/504 自動重試**：最多 2 次，延遲遞增（1s、2s）
- **逾時控制**：預設 30 秒，超時拋出 `ApiError`
- **`X-Team-ID` header 維持**：自動從 `localStorage.selected_team_id` 注入，與舊行為一致
- **`skipAuth` 選項**：公開端點（如 checkInvite）可跳過認證 header
- **`ApiError` 自訂例外**：附帶 `statusCode` 與 `path` 屬性，供 Error Boundary 辨識

### aiService 串流端點說明

`analyzeDataStream` 需要直接操作 `ReadableStream`（SSE），無法透過通用 apiClient 封裝，故保留原生 `fetch`，但已將 `localStorage.getItem('google_token')` 改為使用 `getAuthToken()` 函式，確保與 Token 儲存鍵名一致。

---

## 4.2 — Frontend Token 過期偵測

### 新增 / 修改的檔案

| 檔案 | 操作 | 說明 |
|------|------|------|
| `frontend/src/utils/auth.js` | **重構** | 新增 JWT 解析、過期時間儲存、剩餘時間查詢 |
| `frontend/src/hooks/useTokenRefresh.js` | **新增** | Token 過期自動監控 Hook |
| `frontend/src/hooks/index.js` | **更新** | 匯出 `useTokenRefresh` |
| `frontend/src/App.jsx` | **重構** | 整合 Token 監控，抽出 `AppInner` 元件 |

### auth.js 新增功能

| 函式 | 說明 |
|------|------|
| `parseJwtPayload(token)` | 解碼 JWT Payload（Base64url，不驗簽） |
| `saveAuthToken(token)` | 儲存 Token 並同步寫入 `google_token_expiry`（毫秒） |
| `isTokenExpired(token?)` | 比對 `Date.now()` 與過期時間戳，true = 已過期 |
| `getTokenRemainingTime()` | 回傳剩餘毫秒，`-1` = 無法確認，`≤0` = 已過期 |
| `clearAuthToken()` | 同步清除 Token、過期時間、`redirectAfterLogin` |

> **注意**：`saveAuthToken()` 為新增函式。現有登入流程（`Login.jsx`）若直接寫 `localStorage.setItem('google_token', ...)` 需改為呼叫 `saveAuthToken()` 以確保過期時間被一同記錄。

### App.jsx 架構調整

重構前後的元件結構：

```
重構前：
App()
  └── <Router><Routes>...</Routes></Router>

重構後：
App()
  └── <Router>
        └── AppInner()      ← useTokenRefresh + useEffect 初始檢查
              └── <Routes>...</Routes>
```

`AppInner` 必須在 `<Router>` 內部，才能使用 `useNavigate`。

### Token 監控流程

```
App 掛載
  ├─ useEffect：立即檢查 isTokenExpired()
  │    └─ 若已過期 → handleTokenExpired()
  └─ useTokenRefresh：每 60 秒定期檢查
       ├─ 剩餘 ≤ 0      → handleTokenExpired()
       └─ 剩餘 ≤ 5 min  → console.info 警告（可擴充為 Toast）

handleTokenExpired()
  ├─ clearAuthToken()
  ├─ alert('您的登入已過期，請重新登入')
  └─ navigate('/login')
```

---

## 3.4 — 釘定 requirements.txt 套件版本

### 新增 / 修改的檔案

| 檔案 | 操作 | 說明 |
|------|------|------|
| `backend/requirements.txt` | **重構** | 所有套件加入版本範圍約束 |
| `backend/requirements-dev.txt` | **新增** | 開發/測試工具分離 |

### 版本策略

採用**寬鬆約束**（`>=min,<nextMajor`），比 `pip freeze` 的精確版本更具彈性，但仍避免引入破壞性升級：

```
fastapi>=0.115.0,<0.116.0
sqlalchemy>=2.0.0,<3.0.0
pydantic>=2.10.0,<3.0.0
redis>=5.2.0,<6.0.0
...
```

### requirements-dev.txt

```
-r requirements.txt
pytest>=8.3.0,<9.0.0
pytest-asyncio>=0.24.0,<1.0.0
pytest-cov>=6.0.0,<7.0.0
black>=24.0.0,<25.0.0
ruff>=0.8.0,<1.0.0
mypy>=1.14.0,<2.0.0
```

### 後續建議

生產部署前執行：

```powershell
cd backend
pip install -r requirements.txt
pip freeze > requirements.lock   # 精確版本鎖定
```

CI/CD 部署時使用 `requirements.lock` 確保環境一致性。

---

## 3.5 — Redis 雙層快取架構

### 新增 / 修改的檔案

| 檔案 | 操作 | 說明 |
|------|------|------|
| `backend/cache.py` | **重構** | 雙層快取架構（L1 + L2 Redis） |
| `backend/redis_cache.py` | **重構** | 強化連線穩健性、單例模式、URL 遮蔽 |
| `docker-compose.dev.yml` | **新增** | 本地開發 Redis 服務 |

### 雙層快取架構

```
┌─────────────────────────────────────────┐
│               請求進入                    │
└──────────────────┬──────────────────────┘
                   │
          ┌────────▼────────┐
          │   L1：TTLCache   │  maxsize=500, TTL=10s
          │   (本地記憶體)    │  thread-safe（Lock）
          └────────┬────────┘
              未命中│
          ┌────────▼────────┐
          │   L2：Redis      │  TTL=依資料類型（120-300s）
          │   (共享快取)      │  multi-process 共享
          └────────┬────────┘
              未命中│
          ┌────────▼────────┐
          │   原始資料來源   │  Facebook API / DB
          └─────────────────┘
                   │ 寫入時
         L2 Redis ← │ → L1 TTLCache 回填
```

**各層特性**：

| | L1（TTLCache） | L2（Redis） |
|--|--|--|
| 範圍 | 單一進程 | 所有進程共享 |
| TTL | 固定 10 秒 | 依資料類型（120-300s） |
| 不可用時 | 不會失敗 | 自動降級至 L1 only |
| 序列化 | 不需要 | JSON |

### redis_cache.py 改進項目

1. **單例模式**：`_redis_available` 旗標，連線失敗後快速失敗（避免重複嘗試）
2. **連線超時**：`socket_connect_timeout=3s`，避免拖慢請求
3. **URL 遮蔽**：日誌中密碼以 `***` 取代
4. **`reset_redis_client()`**：測試時可重置連線狀態
5. **`retry_on_timeout=True`**：短暫網路不穩時自動重試

### 向後相容性

現有程式碼中所有 `get_cached(cache_obj, key)` / `set_cached(cache_obj, key, value)` 呼叫 **無需修改**，函式簽名不變，底層已自動路由至雙層快取。

TTL 從傳入的 `cache_obj.ttl` 自動讀取，保持原有快取時間設定。

### docker-compose.dev.yml

```yaml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck: redis-cli ping
```

本地開發設定 `REDIS_URL=redis://redis:6379/0` 即可啟用 L2 快取；不設定則自動使用 L1 only，不影響開發。

---

## 驗收清單

### 4.1 統一 Frontend API Client

- [x] `src/services/apiClient.js` 已建立並包含統一的 fetch 邏輯
- [x] `userService.js`、`adminService.js`、`teamService.js` 已改用 apiClient
- [x] `aiService.js` 的 `testConnection` 改用 apiClient
- [x] 401 回應會自動清除 Token 並重導向至登入頁
- [x] 網路錯誤（連線失敗、逾時）拋出 `ApiError` 附帶錯誤訊息
- [x] 502/503/504 有自動重試邏輯（最多 2 次）
- [ ] **待確認**：Login.jsx 中的 `localStorage.setItem('google_token', ...)` 改為 `saveAuthToken()`

### 4.2 Frontend Token 過期偵測

- [x] `src/utils/auth.js` 的 `saveAuthToken()` 已建立並同時儲存過期時間
- [x] `isTokenExpired()` 函式已實作並在 apiClient 中調用
- [x] `useTokenRefresh` hook 已建立並在 App.jsx 中啟用
- [x] Token 過期後會顯示提示並自動導向登入頁
- [x] 登入後 `sessionStorage.redirectAfterLogin` 會被設定（供登入後返回）
- [ ] **待確認**：Login.jsx 登入成功後讀取 `redirectAfterLogin` 並導向原頁

### 3.4 釘定套件版本

- [x] `requirements.txt` 所有套件都有版本範圍約束
- [x] `requirements-dev.txt` 已建立（測試與開發工具分離）
- [ ] **待執行**：`pip freeze > requirements.lock`（需在生產環境執行）
- [ ] **待確認**：Dockerfile 確認使用 `requirements.txt`

### 3.5 Redis 雙層快取

- [x] `cache.py` 已實作雙層快取（L1 本地 10s + L2 Redis，依原始 TTL）
- [x] `redis_cache.py` 有防護性連線處理（Redis 不可用時自動降級）
- [x] 快取鍵有前綴以避免不同功能間的衝突
- [x] `docker-compose.dev.yml` 已包含 Redis 服務（redis:7-alpine，256MB 限制）
- [x] 本地開發時不設定 `REDIS_URL` 也能正常運作（降級至 L1）
- [ ] **待測試**：部署後監控 Facebook API 請求量是否降低

---

## 後續注意事項

### 必要的跟進項目

1. **Login.jsx**：將 `localStorage.setItem('google_token', token)` 改為 `saveAuthToken(token)`，否則 Token 過期時間不會被記錄，`isTokenExpired()` 無法正常運作。

2. **登入後跳轉**：在 Login.jsx 登入成功後加入以下邏輯：
   ```js
   const redirect = sessionStorage.getItem('redirectAfterLogin');
   if (redirect) {
     sessionStorage.removeItem('redirectAfterLogin');
     navigate(redirect);
   } else {
     navigate('/');
   }
   ```

3. **requirements.lock 生成**：在生產環境執行 `pip freeze > requirements.lock` 並提交到版本控制。

4. **Zeabur 部署 Redis**：在 Zeabur Dashboard 新增 Redis 服務，環境變數 `REDIS_URL` 會自動注入。

### 已知限制

- `aiService.analyzeDataStream` 保留原生 `fetch`，Token 過期不會自動導回登入頁（串流中斷時例外處理由呼叫端負責）。
- `useTokenRefresh` 目前僅顯示 `alert()`，建議更換為 Toast 通知元件（如 react-hot-toast）以提升 UX。
- Redis 單例狀態在連線失敗後不會自動重試（需呼叫 `reset_redis_client()` 重置），適合定期重啟或健康檢查機制觸發重連。
