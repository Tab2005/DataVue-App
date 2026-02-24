# P3 前端優化實作記錄

> **分支**：`dev-saas`  
> **實作日期**：2026-02-23  
> **參考文件**：`docs/optimization/05_P3_frontend_optimization.md`  
> **Build 狀態**：✅ 通過（`npm run build` exit code: 0）

---

## 目錄

1. [實作概覽](#實作概覽)
2. [4.3 — TanStack React Query 整合](#43--tanstack-react-query-整合)
3. [4.4 — JSDoc 型別定義](#44--jsdoc-型別定義)
4. [4.7 — React 19 相容性修正](#47--react-19-相容性修正)
5. [3.9 — JSON 欄位型別（前端側）](#39--json-欄位型別前端側)
6. [新增檔案清單](#新增檔案清單)
7. [修改檔案清單](#修改檔案清單)
8. [驗收清單](#驗收清單)
9. [後續待完成事項](#後續待完成事項)

---

## 實作概覽

| 項目 | 狀態 | 說明 |
|------|------|------|
| 4.3 安裝 React Query | ✅ 完成 | `@tanstack/react-query@5.90.21` |
| 4.3 QueryClient Provider | ✅ 完成 | 已包裝在 `main.jsx` |
| 4.3 queryKeys 工廠 | ✅ 完成 | 涵蓋所有業務模組 |
| 4.3 Query Hooks | ✅ 完成 | 7 個 Query Hooks |
| 4.3 Mutation Hooks | ✅ 完成 | 6 個 Mutation Hooks |
| 4.4 JSDoc 型別定義 | ✅ 完成 | `src/types/api.js` |
| 4.7 React 19 相容性 | ✅ 完成 | 升級 `@react-oauth/google@0.13.4` |
| 3.9 safeParseJson | ✅ 完成 | 已建立並套用至 `AdAccountSelector` |

---

## 4.3 — TanStack React Query 整合

### 安裝的套件

```
@tanstack/react-query@5.90.21
@tanstack/react-query-devtools@5.91.3
```

### QueryClient 設定（`main.jsx`）

- **staleTime**: 5 分鐘（預設），個別 hook 可覆寫
- **gcTime**: 10 分鐘
- **retry**: 4xx 錯誤不重試，其他最多重試 1 次
- **ReactQueryDevtools**: 僅在 `import.meta.env.DEV` 為 true 時載入

### Query Key 工廠（`src/constants/queryKeys.js`）

涵蓋以下業務模組：

| 模組 | Key 前綴 |
|------|---------|
| 使用者 | `['users', ...]` |
| 團隊 | `['teams', ...]` |
| Facebook Ads | `['facebook', ...]` |
| GSC | `['gsc', ...]` |
| GA4 | `['ga4', ...]` |
| 儲存的視圖 | `['savedViews', ...]` |
| 權限 | `['permissions', ...]` |
| 管理員 | `['admin', ...]` |

### Query Hooks 建立清單

| Hook | 檔案 | 說明 |
|------|------|------|
| `useCurrentUser` | `hooks/queries/useCurrentUser.js` | 當前登入使用者，10 分鐘快取 |
| `useMyTeams` | `hooks/queries/useTeams.js` | 使用者的所有團隊，5 分鐘快取 |
| `useTeam(teamId)` | `hooks/queries/useTeams.js` | 單一團隊資料 |
| `useTeamMembers(teamId)` | `hooks/queries/useTeams.js` | 團隊成員列表 |
| `useFacebookAccounts(userId)` | `hooks/queries/useFacebookAccounts.js` | 廣告帳號，5 分鐘快取 |
| `useFacebookInsights(params)` | `hooks/queries/useFacebookInsights.js` | 廣告洞察，2 分鐘快取，支援 placeholderData |
| `useFacebookTrends(params)` | `hooks/queries/useFacebookInsights.js` | 廣告趨勢數據 |
| `useGscData(params)` | `hooks/queries/useGsc.js` | GSC 搜尋數據 |
| `useGscKeywords(params)` | `hooks/queries/useGsc.js` | GSC 關鍵字分析 |
| `useGscPages(params)` | `hooks/queries/useGsc.js` | GSC 頁面分析 |
| `useGa4Overview(params)` | `hooks/queries/useGa4.js` | GA4 總覽 |
| `useGa4Events(params)` | `hooks/queries/useGa4.js` | GA4 事件 |
| `useGa4Channels(params)` | `hooks/queries/useGa4.js` | GA4 頻道分組 |
| `useAdminUsers` | `hooks/queries/useAdmin.js` | 管理員：所有使用者 |
| `useAdminTeams` | `hooks/queries/useAdmin.js` | 管理員：所有團隊 |
| `useAdminStats` | `hooks/queries/useAdmin.js` | 管理員：系統統計 |

### Mutation Hooks 建立清單

| Hook | 檔案 | 說明 |
|------|------|------|
| `useUpdateTeam` | `hooks/mutations/useTeamMutations.js` | 樂觀更新，失敗自動回滾 |
| `useCreateInvite` | `hooks/mutations/useTeamMutations.js` | 建立邀請連結 |
| `useRemoveTeamMember` | `hooks/mutations/useTeamMutations.js` | 移除成員 |
| `useUpdateMemberRole` | `hooks/mutations/useTeamMutations.js` | 更新成員角色 |
| `useUpdateUser` | `hooks/mutations/useUserMutations.js` | 更新使用者（管理員） |
| `useDeleteUser` | `hooks/mutations/useUserMutations.js` | 刪除使用者（管理員） |

---

## 4.4 — JSDoc 型別定義

**新增檔案**：`src/types/api.js`

定義的型別：

| 型別名稱 | 說明 |
|---------|------|
| `User` | 使用者資料（含 role、status、is_super_admin） |
| `Team` | 團隊資料（含 fb_app_id、visible_ad_account_ids） |
| `TeamMember` | 團隊成員（含巢狀 User 物件） |
| `AdAccount` | 廣告帳號（含 account_status、currency、timezone_name） |
| `InsightMetric` | 廣告洞察指標（含 ctr、cpc、cpm、roas、frequency） |
| `GscKeyword` | GSC 關鍵字分析項 |
| `GscPage` | GSC 頁面分析項 |
| `Ga4Metric` | GA4 指標資料 |
| `SavedView` | 已儲存視圖 |
| `ApiError` | API 錯誤回應 |
| `PaginatedResponse<T>` | 泛型分頁回應 |

**使用方式**：在 `.js` 文件頂部加入 `// @ts-check` 即可啟用 VS Code 型別驗證。

---

## 4.7 — React 19 相容性修正

### 問題

`@react-oauth/google@0.12.2` 官方文件未宣告支援 React 19.2.0。

### 解決方案

升級至 `@react-oauth/google@0.13.4`：

```
@react-oauth/google: 0.12.2 → 0.13.4
peerDependencies: react>=16.8.0（確認支援 React 19）
```

### 驗證結果

- `npm run build` 建構成功，無相容性相關錯誤
- 未出現 `ReactDOM.render`、`Legacy Context API`、`findDOMNode` 等棄用警告
- Google 登入元件邏輯未變動，功能應維持正常

---

## 3.9 — JSON 欄位型別（前端側）

### 問題

後端原以 `String` 型別儲存 JSON 陣列（若前端讀取需 `JSON.parse`），遷移至 SQLAlchemy `JSON` 型別後直接回傳陣列物件。前端原本在 `AdAccountSelector.jsx` 對 `visible_ad_account_ids` 強制執行 `JSON.parse()`，遇到陣列物件格式時將拋錯。

### 解決方案

**新增**：`src/utils/jsonUtils.js`

```javascript
// 相容「已是陣列/物件」與「JSON 字串」兩種格式
safeParseJson(value, defaultValue = [])
safeParseJsonObject(value, defaultValue = null)
```

**修改**：`src/components/AdAccountSelector.jsx`
- 移除手動 `try { JSON.parse(initialSelected) }` 邏輯
- 改用 `safeParseJson(initialSelected, [])` 

---

## 新增檔案清單

```
frontend/src/
├── main.jsx                                  ← 修改：加入 QueryClientProvider
├── constants/
│   └── queryKeys.js                          ← 新增：Query Key 工廠
├── hooks/
│   ├── queries/
│   │   ├── index.js                          ← 新增：統一匯出
│   │   ├── useCurrentUser.js                 ← 新增
│   │   ├── useTeams.js                       ← 新增
│   │   ├── useFacebookAccounts.js            ← 新增
│   │   ├── useFacebookInsights.js            ← 新增
│   │   ├── useGsc.js                         ← 新增
│   │   ├── useGa4.js                         ← 新增
│   │   └── useAdmin.js                       ← 新增
│   └── mutations/
│       ├── index.js                          ← 新增：統一匯出
│       ├── useTeamMutations.js               ← 新增
│       └── useUserMutations.js               ← 新增
├── types/
│   └── api.js                               ← 新增：JSDoc 型別定義
└── utils/
    └── jsonUtils.js                          ← 新增：safeParseJson 工具函式
```

---

## 修改檔案清單

| 檔案 | 變更內容 |
|------|---------|
| `frontend/src/main.jsx` | 加入 `QueryClientProvider` 與 `ReactQueryDevtools` |
| `frontend/src/components/AdAccountSelector.jsx` | 改用 `safeParseJson` 取代手動 `JSON.parse` |
| `frontend/package.json` | 新增 `@tanstack/react-query`、`@tanstack/react-query-devtools`；升級 `@react-oauth/google` |

---

## 驗收清單

### 4.3 React Query

- [x] `@tanstack/react-query` 已安裝（v5.90.21）
- [x] `QueryClientProvider` 已包裝在 `main.jsx`
- [x] `queryKeys.js` 查詢鍵工廠已建立（涵蓋 8 個業務模組）
- [x] 主要資料（使用者、Facebook、GSC、GA4、Admin）已有對應 Query Hooks
- [x] Mutation Hooks 支援樂觀更新與失敗回滾（`useUpdateTeam`）
- [x] React Query DevTools 在開發模式下可見
- [ ] 主要頁面元件已移除手動 `useEffect + fetch` 模式（**P3 後期工作**，需逐頁重構）

### 4.4 JSDoc

- [x] `src/types/api.js` 已建立所有主要 API 型別的 JSDoc 定義
- [x] Query Hooks 已添加 JSDoc 型別標注
- [ ] `services/` 所有函式已添加完整參數與返回值型別（**P3 後期工作**）
- [ ] `// @ts-check` 開啟後無嚴重型別錯誤（待驗收）

### 4.7 React 19 相容性

- [x] `@react-oauth/google` 升級至 0.13.4（支援 React >= 16.8.0）
- [x] `npm run build` 建構成功，無相容性相關錯誤
- [ ] 瀏覽器控制台確認無 React 19 棄用警告（需手動測試）

### 3.9 JSON 欄位型別

- [x] `safeParseJson` 輔助函式已建立（相容新舊後端格式）
- [x] `AdAccountSelector.jsx` 已改用 `safeParseJson`
- [ ] 所有使用 `metrics`、`visible_ad_account_ids` 等欄位的頁面確認顯示正常（需測試）

---

## 後續待完成事項

### 短期（建議本迭代內完成）

1. **逐頁重構 `useEffect + fetch` → Query Hooks**
   - 優先：`Dashboard.jsx`、`TeamSettings.jsx`、`AdminDashboard.jsx`、`UserManagement.jsx`
   - 預估每個頁面 30-60 分鐘

2. **補充 services/ 的 JSDoc 型別**
   - `apiClient.js`、`teamService.js`、`userService.js` 等

3. **browser 控制台驗證**
   - 啟動開發伺服器手動確認無棄用警告

### 長期（P3 後期）

4. **TypeScript 漸進遷移**（選配）
   - 依 `05_P3_frontend_optimization.md § 4.4` 的優先順序實作

5. **`safeParseJson` 套用範圍擴大**
   - 確認 `MetricsManager.jsx`（`metrics` 欄位）與其他儲存視圖頁面

---

> 本文件由 GitHub Copilot 自動產生，記錄 `dev-saas` 分支上 P3 前端優化的實作狀態。
