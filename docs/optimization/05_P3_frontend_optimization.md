# P3：前端優化（長期，1-2 個月）

> **優先級**：🔵 P3 — 長期優化，可漸進式實作  
> **預估工時**：2-3 週  
> **涵蓋項目**：4.3、4.4、4.7、3.9（前端側）

---

## 目錄

1. [4.3 — 引入 TanStack React Query](#43--引入-tanstack-react-query)
2. [4.4 — 漸進式導入 TypeScript / JSDoc 型別](#44--漸進式導入-typescript--jsdoc-型別)
3. [4.7 — React 19 相容性驗證](#47--react-19-相容性驗證)
4. [3.9 — JSON 欄位型別（前端側）](#39--json-欄位型別前端側)

---

## 4.3 — 引入 TanStack React Query

### 問題說明

所有頁面元件直接在 `useEffect` 中手動管理 `loading`、`error`、`data` 狀態，造成：
- 無快取：每次元件掛載都重新請求
- 重複請求：多個元件各自請求相同資料
- 無法輕易實現樂觀更新

### 實作步驟

**步驟 1：安裝依賴**

```bash
cd frontend
npm install @tanstack/react-query @tanstack/react-query-devtools
```

**步驟 2：設定 QueryClient Provider**

```jsx
// frontend/src/main.jsx

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 請求失敗自動重試 1 次（排除 4xx 錯誤）
      retry: (failureCount, error) => {
        if (error?.statusCode >= 400 && error?.statusCode < 500) return false;
        return failureCount < 1;
      },
      // 視窗重新聚焦時重新取得（若資料超過 5 分鐘）
      staleTime: 5 * 60 * 1000,
      // 快取保留 10 分鐘
      gcTime: 10 * 60 * 1000,
    },
    mutations: {
      // 突變失敗不自動重試
      retry: false,
    },
  },
});

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  </StrictMode>
);
```

**步驟 3：建立 Query Key 工廠**

```javascript
// frontend/src/constants/queryKeys.js

/**
 * 統一管理所有 React Query 的 Query Key。
 * 使用工廠函式確保 key 的一致性與型別安全。
 */
export const queryKeys = {
  // 使用者
  users: {
    all: ['users'],
    me: () => ['users', 'me'],
    byId: (id) => ['users', id],
    list: () => ['users', 'list'],
  },

  // 團隊
  teams: {
    all: ['teams'],
    byId: (id) => ['teams', id],
    members: (teamId) => ['teams', teamId, 'members'],
    invites: (teamId) => ['teams', teamId, 'invites'],
  },

  // Facebook Ads
  facebook: {
    accounts: (userId) => ['facebook', 'accounts', userId],
    insights: (accountId, dateRange) => ['facebook', 'insights', accountId, dateRange],
    campaigns: (accountId) => ['facebook', 'campaigns', accountId],
    trends: (accountId, params) => ['facebook', 'trends', accountId, params],
  },

  // GSC
  gsc: {
    data: (params) => ['gsc', 'data', params],
    keywords: (params) => ['gsc', 'keywords', params],
    pages: (params) => ['gsc', 'pages', params],
  },

  // GA4
  ga4: {
    overview: (params) => ['ga4', 'overview', params],
    events: (params) => ['ga4', 'events', params],
  },

  // 儲存的視圖
  savedViews: {
    all: ['savedViews'],
    byTab: (tab) => ['savedViews', tab],
  },
};
```

**步驟 4：建立 Query Hooks**

```javascript
// frontend/src/hooks/queries/useCurrentUser.js

import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';
import { queryKeys } from '../../constants/queryKeys';

export function useCurrentUser() {
  return useQuery({
    queryKey: queryKeys.users.me(),
    queryFn: () => apiClient.get('/api/users/me'),
    // 使用者資料不常變更，快取較長時間
    staleTime: 10 * 60 * 1000,
  });
}

// frontend/src/hooks/queries/useFacebookAccounts.js

import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';
import { queryKeys } from '../../constants/queryKeys';

export function useFacebookAccounts(userId) {
  return useQuery({
    queryKey: queryKeys.facebook.accounts(userId),
    queryFn: () => apiClient.get('/api/facebook/accounts'),
    // 廣告帳號列表 5 分鐘快取
    staleTime: 5 * 60 * 1000,
    // userId 不存在時不請求
    enabled: Boolean(userId),
  });
}

// frontend/src/hooks/queries/useFacebookInsights.js

import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';
import { queryKeys } from '../../constants/queryKeys';

export function useFacebookInsights({ accountId, startDate, endDate, metrics }) {
  return useQuery({
    queryKey: queryKeys.facebook.insights(accountId, { startDate, endDate, metrics }),
    queryFn: () => apiClient.post('/api/facebook/insights', {
      account_id: accountId,
      start_date: startDate,
      end_date: endDate,
      metrics,
    }),
    // 廣告數據 2 分鐘快取（相對即時）
    staleTime: 2 * 60 * 1000,
    enabled: Boolean(accountId && startDate && endDate),
    // 保留之前的資料在新請求進行時（避免 loading 閃爍）
    placeholderData: (previousData) => previousData,
  });
}
```

**步驟 5：建立 Mutation Hooks**

```javascript
// frontend/src/hooks/mutations/useUpdateTeam.js

import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';
import { queryKeys } from '../../constants/queryKeys';

export function useUpdateTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ teamId, data }) =>
      apiClient.put(`/api/teams/${teamId}`, data),

    // 樂觀更新：立即更新 UI，若失敗則回滾
    onMutate: async ({ teamId, data }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.teams.byId(teamId) });
      const previousTeam = queryClient.getQueryData(queryKeys.teams.byId(teamId));
      queryClient.setQueryData(queryKeys.teams.byId(teamId), (old) => ({
        ...old,
        ...data,
      }));
      return { previousTeam };
    },

    onError: (error, { teamId }, context) => {
      // 回滾至之前的資料
      queryClient.setQueryData(queryKeys.teams.byId(teamId), context.previousTeam);
      console.error('更新團隊失敗:', error.message);
    },

    onSuccess: (data, { teamId }) => {
      // 使相關快取失效，觸發重新取得
      queryClient.invalidateQueries({ queryKey: queryKeys.teams.byId(teamId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.teams.all });
    },
  });
}
```

**步驟 6：更新頁面元件使用 Query Hooks**

```jsx
// 重構前（舊寫法）
function FacebookDashboard() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetch('/api/facebook/accounts', { headers: getAuthHeaders() })
      .then(res => res.json())
      .then(data => {
        setAccounts(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <Spinner />;
  if (error) return <ErrorMessage message={error} />;
  return <AccountList accounts={accounts} />;
}

// 重構後（React Query 寫法）
function FacebookDashboard() {
  const { data: user } = useCurrentUser();
  const {
    data: accounts,
    isLoading,
    isError,
    error,
    refetch,
  } = useFacebookAccounts(user?.id);

  if (isLoading) return <Spinner />;
  if (isError) return <ErrorMessage message={error.message} onRetry={refetch} />;
  return <AccountList accounts={accounts} />;
}
```

### 驗收標準

- [ ] `@tanstack/react-query` 已安裝
- [ ] `QueryClientProvider` 已包裝在 `main.jsx`
- [ ] `queryKeys.js` 查詢鍵工廠已建立
- [ ] 主要資料（使用者、Facebook 帳號、廣告數據）已有對應的 Query Hooks
- [ ] 主要頁面元件已移除手動 `useEffect + fetch` 模式
- [ ] React Query DevTools 在開發模式下可見

---

## 4.4 — 漸進式導入 TypeScript / JSDoc 型別

### 問題說明

純 JavaScript 缺乏靜態型別，API 回應結構變更時難以發現錯誤。

### 方案選擇

本專案建議採用 **漸進式策略**：先用 JSDoc 為關鍵模組添加型別定義，再逐步遷移至 TypeScript。

**第一階段：JSDoc 型別定義（可立即開始，無需改動建置設定）**

```javascript
// frontend/src/types/api.js
/**
 * @fileoverview API 回應型別定義
 * 所有後端 API 回應的 JSDoc 型別
 */

/**
 * @typedef {Object} User
 * @property {string} id - 使用者 UUID
 * @property {string} email - Google Email
 * @property {string} name - 顯示名稱
 * @property {string|null} picture - 頭像 URL
 * @property {'super_admin'|'admin'|'member'|'viewer'} role - 角色
 * @property {'active'|'disabled'|'pending'} status - 帳號狀態
 * @property {boolean} is_super_admin - 是否為超級管理員
 * @property {string} created_at - ISO 8601 時間字串
 */

/**
 * @typedef {Object} Team
 * @property {string} id - 團隊 UUID
 * @property {string} name - 團隊名稱
 * @property {string} owner_id - 擁有者 ID
 * @property {string|null} fb_app_id - Facebook App ID
 * @property {string[]} visible_ad_account_ids - 可見廣告帳號列表
 * @property {string} created_at - 建立時間
 */

/**
 * @typedef {Object} AdAccount
 * @property {string} id - 廣告帳號 ID（格式：act_xxxxxxxx）
 * @property {string} name - 帳號名稱
 * @property {number} account_status - 帳號狀態（1=active, 2=disabled, 3=unsettled）
 * @property {string} currency - 貨幣代碼（如：TWD, USD）
 * @property {string} timezone_name - 時區（如：Asia/Taipei）
 */

/**
 * @typedef {Object} InsightMetric
 * @property {string} date_start - 開始日期
 * @property {string} date_stop - 結束日期
 * @property {string} impressions - 曝光次數
 * @property {string} clicks - 點擊次數
 * @property {string} spend - 花費金額
 * @property {string} reach - 覆蓋人數
 * @property {string|undefined} ctr - 點擊率
 * @property {string|undefined} cpc - 每次點擊成本
 * @property {string|undefined} cpm - 每千次曝光成本
 */

/**
 * @typedef {Object} ApiError
 * @property {string} detail - 錯誤詳情
 * @property {number} status_code - HTTP 狀態碼
 */
```

**第二階段：在關鍵服務中使用 JSDoc 型別**

```javascript
// frontend/src/services/facebookService.js

import apiClient from './apiClient';

/**
 * 取得使用者的廣告帳號列表
 * @returns {Promise<import('../types/api').AdAccount[]>}
 */
export async function getAdAccounts() {
  return apiClient.get('/api/facebook/accounts');
}

/**
 * 取得廣告洞察數據
 * @param {string} accountId - 廣告帳號 ID
 * @param {Object} params - 查詢參數
 * @param {string} params.startDate - 開始日期（YYYY-MM-DD）
 * @param {string} params.endDate - 結束日期（YYYY-MM-DD）
 * @param {string[]} params.metrics - 指標列表
 * @returns {Promise<import('../types/api').InsightMetric[]>}
 */
export async function getInsights(accountId, { startDate, endDate, metrics }) {
  return apiClient.post('/api/facebook/insights', {
    account_id: accountId,
    start_date: startDate,
    end_date: endDate,
    metrics,
  });
}
```

**第三階段（選配）：遷移至 TypeScript**

若決定全面遷移至 TypeScript：

```bash
# 安裝 TypeScript 與相關依賴
npm install -D typescript @types/react @types/react-dom

# 生成 tsconfig.json
npx tsc --init
```

```json
// tsconfig.json（建議設定）
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,        // 漸進式遷移初期先關閉
    "noUnusedParameters": false,    // 漸進式遷移初期先關閉
    "noFallthroughCasesInSwitch": true,
    "allowJs": true,                // 允許混合 JS/TS（漸進式遷移用）
    "checkJs": false                // JS 文件暫不做型別檢查
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**遷移優先順序**

```
第 1 週：型別定義文件（types/）
第 2 週：services/ 層（apiClient、各 service）
第 3 週：hooks/（query hooks、mutation hooks）
第 4 週：components/（核心共用元件）
後續：pages/（逐一遷移）
```

### 驗收標準（JSDoc 方案）

- [ ] `src/types/api.js` 已建立所有主要 API 型別的 JSDoc 定義
- [ ] `services/` 所有函式已添加參數與返回值型別
- [ ] VS Code 可在 `.js` 文件中顯示 JSDoc 型別提示
- [ ] `// @ts-check` 開啟後無嚴重型別錯誤

---

## 4.7 — React 19 相容性驗證

### 問題說明

`@react-oauth/google` 0.12.2 官方支援宣告截至 React 18，使用 React 19.2.0 可能有相容性問題。

### 驗證步驟

**步驟 1：檢查控制台警告**

```javascript
// 在瀏覽器開發者工具執行，確認無 React 19 相關棄用警告
// 特別注意：
// - "Warning: ReactDOM.render is no longer supported"
// - "Warning: Legacy Context API"
// - "Warning: findDOMNode is deprecated"
```

**步驟 2：確認 `@react-oauth/google` 的 React 19 相容性**

```bash
# 檢查是否有更新版本
npm info @react-oauth/google versions --json | tail -5

# 或直接升級嘗試
npm install @react-oauth/google@latest
```

**步驟 3：若 `@react-oauth/google` 有問題，考慮替代方案**

```javascript
// 替代方案：使用 Google Identity Services 原生 API
// 可直接使用 Google 提供的 JS 庫而不依賴 React 封裝

// index.html
// <script src="https://accounts.google.com/gsi/client" async defer></script>

// frontend/src/hooks/useGoogleAuth.js
export function useGoogleAuth({ onSuccess, onError }) {
  const initGoogleSignIn = useCallback(() => {
    if (!window.google) return;

    window.google.accounts.id.initialize({
      client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
      callback: ({ credential }) => {
        onSuccess(credential);
      },
      auto_select: false,
    });

    window.google.accounts.id.renderButton(
      document.getElementById('google-signin-btn'),
      { theme: 'outline', size: 'large' }
    );
  }, [onSuccess]);

  useEffect(() => {
    // 等待 Google SDK 載入
    if (window.google) {
      initGoogleSignIn();
    } else {
      window.addEventListener('load', initGoogleSignIn);
    }
    return () => window.removeEventListener('load', initGoogleSignIn);
  }, [initGoogleSignIn]);
}
```

### 驗收標準

- [ ] 瀏覽器控制台無 React 19 相關棄用警告
- [ ] Google 登入功能正常運作
- [ ] `@react-oauth/google` 版本已更新至最新（若支援 React 19）
- [ ] 替代方案已評估並在必要時實施

---

## 3.9 — JSON 欄位型別（前端側）

### 問題說明

後端改用 SQLAlchemy `JSON` 型別後，前端需確認 JSON 資料的處理邏輯。

### 確認並更新前端解析邏輯

```javascript
// 舊版本（後端返回 JSON 字串）
const metrics = JSON.parse(savedView.metrics);
const accountIds = JSON.parse(team.visible_ad_account_ids);

// 新版本（後端已返回 JSON 物件/陣列，不需再 parse）
const metrics = savedView.metrics;             // 已是 Array
const accountIds = team.visible_ad_account_ids; // 已是 Array

// 建立安全的解析輔助函式（相容兩種格式）
function safeParseJson(value, defaultValue = []) {
  if (Array.isArray(value) || typeof value === 'object') return value ?? defaultValue;
  if (typeof value === 'string') {
    try {
      return JSON.parse(value);
    } catch {
      return defaultValue;
    }
  }
  return defaultValue;
}

// 使用
const metrics = safeParseJson(savedView.metrics, []);
const accountIds = safeParseJson(team.visible_ad_account_ids, []);
```

### 驗收標準

- [ ] 前端已確認不再對 JSON 型別欄位執行 `JSON.parse()`
- [ ] `safeParseJson` 輔助函式已建立（相容新舊後端格式）
- [ ] 所有使用 `metrics`、`visible_ad_account_ids` 等欄位的頁面顯示正常
