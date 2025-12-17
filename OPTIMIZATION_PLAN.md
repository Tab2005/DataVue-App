# Facebook Dashboard - 專案優化建議報告

> **分析日期**: 2025-12-17
> **分析模型**: Claude (Anthropic)

---

## 📊 優化優先級總覽

| 優先級 | 類別 | 影響 | 工作量 |
|--------|------|------|--------|
| 🔴 高 | 效能優化 | 高 | 中 |
| 🔴 高 | 安全性強化 | 高 | 低 |
| 🟡 中 | 程式碼架構 | 中 | 高 |
| 🟡 中 | 使用者體驗 | 中 | 中 |
| 🟢 低 | 可維護性 | 中 | 低 |

---

## 🔴 高優先級優化

### 1. 後端效能優化

#### 1.1 API 快取機制 (Redis/Memory Cache) ✅ 已完成 (2025-12-17)
**問題**: 每次請求都直接呼叫 Facebook Graph API，造成延遲和 API 配額消耗。

**現況** (`services.py`):
```python
# 每次都發送新請求
response = requests.get(url, headers=headers, params=params, timeout=10)
```

**建議**:
- 實作 Redis 或記憶體快取層
- 快取廣告帳號列表 (TTL: 5分鐘)
- 快取報表數據 (TTL: 1-5分鐘，依據使用者設定)

```python
# 建議架構
from functools import lru_cache
import redis

class CacheService:
    def get_or_fetch(self, key, fetch_fn, ttl=300):
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)
        data = fetch_fn()
        self.redis.setex(key, ttl, json.dumps(data))
        return data
```

---

#### 1.2 非同步 API 呼叫 ✅ 已完成 (2025-12-17)
**問題**: `services.py` 使用同步 `requests` 庫，阻塞事件迴圈。

**現況**:
```python
cur_res = requests.get(url, headers=headers, params=current_params).json()
# ... 接著又發另一個請求
prev_res = requests.get(url, headers=headers, params=prev_params).json()
```

**建議**:
- 改用 `httpx.AsyncClient` 實現非同步請求
- 使用 `asyncio.gather()` 並行抓取 Current 和 Previous 數據

```python
import httpx

async def get_account_insights(self, account_id, user_id, days=7):
    async with httpx.AsyncClient() as client:
        cur_task = client.get(url, params=current_params)
        prev_task = client.get(url, params=prev_params)
        cur_res, prev_res = await asyncio.gather(cur_task, prev_task)
```

**預估效益**: API 響應時間減少 30-50%

---

#### 1.3 Facebook API 批次請求
**問題**: 多個獨立 API 呼叫可以合併為批次請求。

**建議**:
- 使用 Facebook Batch API 減少網路往返
- 特別適用於 `get_custom_report` 中同時抓取 insights 和 ads 資料

---

### 2. 安全性強化

#### 2.1 環境變數驗證 ✅ 已完成 (2025-12-17)
**問題**: 缺少啟動時的環境變數驗證。

**建議**:
```python
# main.py 啟動時檢查
REQUIRED_ENVS = ["GOOGLE_CLIENT_ID", "ENCRYPTION_KEY"]
for env in REQUIRED_ENVS:
    if not os.getenv(env):
        raise RuntimeError(f"Missing required environment variable: {env}")
```

#### 2.2 API Rate Limiting
**問題**: 沒有請求速率限制，容易被濫用。

**建議**:
- 新增 `slowapi` 或自定義中間件限制請求頻率
- 建議限制: 每用戶每分鐘 60 次請求

#### 2.3 敏感日誌過濾 ✅ 已完成 (2025-12-17)
**問題**: `services.py` 有時會輸出敏感資訊到日誌。

**現況**:
```python
print(f"Fetching Ad Accounts from: {url}", file=sys.stderr)
```

**建議**:
- 使用結構化 logging (如 `structlog`)
- 確保 Token 和 API Key 不會出現在日誌中

---

## 🟡 中優先級優化

### 3. 前端架構優化

#### 3.1 拆分巨型元件 ✅ 已完成 (2025-12-17)
**問題**: `Analytics.jsx` 有 **1808 行**，難以維護和測試。

**建議拆分架構**:
```
pages/Analytics/
├── index.jsx              # 主容器 (狀態管理)
├── AnalyticsHeader.jsx    # 標題區
├── ControlPanel.jsx       # 控制面板
├── MetricSelector.jsx     # 指標選擇器
├── KPISection.jsx         # KPI 卡片區
├── DataTable.jsx          # 資料表格
├── FilterToolbar.jsx      # 篩選工具列
└── hooks/
    ├── useAnalyticsData.js  # 資料抓取 Hook
    └── useFilters.js        # 篩選邏輯 Hook
```

> **實作說明**: 已建立 `constants/analyticsConfig.js`、`hooks/useAnalyticsFilters.js`、`components/Analytics/` 模組。Analytics.jsx 已整合使用模組化 constants。

#### 3.2 狀態管理優化 ✅ 已完成 (2025-12-17)
**問題**: `Analytics.jsx` 有 20+ 個 `useState`，狀態分散難追蹤。

**建議**:
- 使用 `useReducer` 整合相關狀態
- 考慮使用 Context 或 Zustand 管理全域狀態

```javascript
// 建議: 使用 useReducer 整合篩選狀態
const filterReducer = (state, action) => {
  switch (action.type) {
    case 'SET_KEYWORD': return { ...state, keyword: action.payload };
    case 'SET_MODE': return { ...state, mode: action.payload };
    // ...
  }
};
```

> **實作說明**: 已建立 `useAnalyticsFilters.js` hook，使用 useReducer 整合 15+ 個 useState。

#### 3.3 元件記憶化 (Memoization) ✅ 已完成 (2025-12-17)
**問題**: 缺少 `React.memo` 和 `useMemo` 優化，可能造成不必要的重渲染。

**建議**:
- 對純展示元件使用 `React.memo`
- 對複雜計算使用 `useMemo` (已有部分使用，可擴展)
- 對回呼函式使用 `useCallback`

> **實作說明**: 已建立 memoized 元件: `AnalyticsKPICard`, `AnalyticsTableRow`, `MetricSelector`。已導入 useMemo, useCallback, memo 到 Analytics.jsx。

#### 3.4 程式碼分割 (Code Splitting) ✅ 已完成 (2025-12-17)
**問題**: 所有頁面代碼都打包在一起。

**建議**:
```javascript
// App.jsx
const Analytics = React.lazy(() => import('./pages/Analytics'));
const AdminDashboard = React.lazy(() => import('./pages/AdminDashboard'));

// 搭配 Suspense
<Suspense fallback={<Loading />}>
  <Route path="/analytics" element={<Analytics />} />
</Suspense>
```

> **實作說明**: 已使用 `React.lazy()` 延遲載入 Dashboard, Analytics, TeamSettings, AdminDashboard 等頁面，並新增 `PageLoading.jsx` 作為 Suspense fallback。

---

### 4. 後端架構優化

#### 4.1 服務層重構 ✅ 已完成 (2025-12-17)
**問題**: `services.py` 有 678 行，混合了業務邏輯和 API 呼叫。

**建議拆分**:
```
services/
├── facebook_api.py       # 純 API 呼叫
├── metrics_calculator.py # 指標計算邏輯
├── report_service.py     # 報表生成
└── cache_service.py      # 快取管理
```

> **實作說明**: 已建立 `services/` 模組，包含 `facebook_api.py` (FacebookAPIClient) 和 `metrics.py` (MetricsCalculator)。原有 `services.py` 保留以維持向後相容。

#### 4.2 統一錯誤處理 ✅ 已完成 (2025-12-17)
**問題**: 錯誤處理分散在各處，格式不一致。

**建議**:
```python
# exceptions.py
class FacebookAPIError(Exception):
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code

# 統一處理器
@app.exception_handler(FacebookAPIError)
async def fb_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": exc.message, "code": exc.error_code}
    )
```

> **實作說明**: 已新增 `exceptions.py` 包含完整的 Exception 階層 (AppException, AuthenticationError, FacebookAPIError, ResourceNotFoundError, ValidationError, DatabaseError)，並在 `main.py` 中加入統一的 exception handlers。

---

### 5. 使用者體驗優化

#### 5.1 載入狀態骨架屏 ✅ 已完成 (2025-12-17)
**問題**: 資料載入時只顯示 loading spinner。

**建議**: 實作 Skeleton Loading UI

> **實作說明**: 已新增 `Skeleton.jsx` 和 `Skeleton.css`，並整合至 Dashboard 頁面。

#### 5.2 樂觀更新 (Optimistic Updates) ✅ 已完成 (2025-12-17)
**問題**: 每次操作都等待 API 回應。

**建議**: 對於團隊設定等操作，先更新 UI 再發送請求。

> **實作說明**: 已新增 `useOptimistic.js` hook，並在 `UserManagement.jsx` 中實作成員刪除和權限更新的樂觀更新，包含自動回滾機制。

#### 5.3 錯誤邊界 (Error Boundaries) ✅ 已完成 (2025-12-17)
**建議**: 加入 React Error Boundaries 防止單一元件錯誤導致整頁崩潰。

> **實作說明**: 已新增 `ErrorBoundary.jsx` 元件並包裹所有主要頁面。

---

## 🟢 低優先級優化

### 6. 可維護性改進

#### 6.1 TypeScript 遷移
**建議**: 逐步將 JavaScript 遷移至 TypeScript，提升類型安全。

**遷移評估**:

| 類別 | 檔案數 | 預估時間 |
|------|--------|---------|
| Hooks | 1 | 1 小時 |
| Services | 2 | 2 小時 |
| Components | ~15 | 6-8 小時 |
| Pages | 7 | 4-6 小時 |
| **總計** | **~25** | **13-17 小時** |

**遷移階段**:
```
階段 1: 環境設定 (1 小時)
├── 安裝 typescript, @types/react
├── 建立 tsconfig.json
└── 設定 Vite TypeScript 支援

階段 2: 新功能用 TypeScript (持續)
├── 新增的 hook → .ts
└── 新增的元件 → .tsx

階段 3: 漸進式遷移舊檔案 (可選)
├── 優先: hooks/, services/ (類型效益高)
├── 其次: components/ (共用元件)
└── 最後: pages/ (複雜度高)
```

**建議**: 
- 可先**維持現狀**，目前專案運作正常
- 若要遷移，建議從**新功能**開始用 TypeScript
- 舊程式碼可視需求**漸進式轉換**

#### 6.2 單元測試覆蓋
**現況**: 僅有少量測試檔案 (`test_phase4.py`, `test_phase5.py`)。

**建議**:
- 後端: 使用 `pytest` 覆蓋核心服務
- 前端: 使用 `Vitest` + `React Testing Library`

#### 6.3 文件自動生成
**建議**: 使用 FastAPI 的 OpenAPI 自動生成 API 文件。

---

## 📈 實施建議順序

### ✅ 已完成項目 (2025-12-17)

| # | 項目 | 類別 |
|---|------|------|
| 1 | 1.1 API 快取機制 (Memory Cache) | 效能 |
| 2 | 1.2 非同步 API 呼叫 (httpx) | 效能 |
| 3 | 2.1 環境變數驗證 | 安全 |
| 4 | 2.3 敏感日誌過濾 | 安全 |
| 5 | 3.1 拆分巨型元件 | 維護性 |
| 6 | 3.2 狀態管理優化 | 維護性 |
| 7 | 3.3 元件記憶化 | 效能 |
| 8 | 3.4 程式碼分割 (React.lazy) | 前端效能 |
| 9 | 4.1 服務層重構 | 維護性 |
| 10 | 4.2 統一錯誤處理 | 維護性 |
| 11 | 5.1 載入狀態骨架屏 | UX |
| 12 | 5.2 樂觀更新 | UX |
| 13 | 5.3 錯誤邊界 | 穩定性 |

### 📋 待完成項目 (依優先級排序)

| 優先級 | 項目 | 難度 | 預估時間 |
|--------|------|------|---------|
| 🔴 高 | 2.2 API Rate Limiting | ⭐⭐ | 1 小時 |
| 🟢 低 | 6.1 TypeScript 遷移 | ⭐⭐⭐⭐⭐ | 13-17 小時 |
| 🟢 低 | 6.2 單元測試覆蓋 | ⭐⭐⭐⭐ | 持續進行 |
| ✅ 內建 | 6.3 文件自動生成 | - | 已可用 (`/docs`) |

---

## 📝 參考資源

- [FastAPI Caching](https://fastapi.tiangolo.com/advanced/middleware/)
- [React Code Splitting](https://react.dev/reference/react/lazy)
- [httpx Async Client](https://www.python-httpx.org/async/)
