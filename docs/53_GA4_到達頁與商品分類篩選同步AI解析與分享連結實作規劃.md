# 53_GA4 到達頁與商品分類篩選同步 AI 解析與分享連結實作規劃

## 背景

使用者發現到達頁分頁的「分類」篩選（全部／商品／文章／功能／其他按鈕）目前只是前端顯示層的二次篩選，沒有真的影響：

1. **AI 白話解讀**：`LandingPagesTab.jsx` 送給 AI 的 `buildPayload()` 固定用 `landingSnapshot.payload.landing_pages`（完整、未分類篩選的清單），不管畫面上選了哪個分類，AI 分析的都是全部分類混在一起的資料
2. **分享連結**：`serialize_shared_snapshot()` 直接回傳整份 snapshot payload，分享頁的 `LandingPagesTable` 也是直接渲染 `payload.landing_pages` 全部列，沒有分類篩選 UI/邏輯

跟「關鍵事件」「渠道」篩選不同——那兩者會改變抓的是哪一份 snapshot（會反映在 AI 解讀跟分享連結上），但「分類」篩選完全是前端 `useMemo` 二次過濾同一份 payload，從來沒有傳回後端或影響過 AI/分享的內容。

**規劃過程中額外發現**：商品分頁（`ItemsTab.jsx`）有一模一樣的架構與問題——`itemsCategoryFilter` 同樣只在前端 `filteredSortedItems` 這個 `useMemo` 裡篩選，`buildPayload()` 一樣固定用未篩選的 `itemsSnapshot?.payload?.items`，分享頁的 `ItemsTable` 也是直接渲染 `payload.items` 全部列。修法完全一樣，所以這次一併處理，不分兩次做。

## 採用方案

**分享連結網址帶分類參數＋分享頁也放篩選 UI** 的混合做法——產生分享連結時把目前選的分類附加在網址上（`?category=xxx`）當作預設顯示，分享頁沿用跟分頁本身同一套分類篩選 UI，收件人拿到連結後預設看到分享當下選的分類，但仍可自行切換看其他分類。到達頁與商品兩個分頁都採同一套做法。

理由：這個功能完全不需要改後端／資料庫——payload 本來就是全量回傳（`category_counts` 兩邊都已經存在於 payload 裡），只是**預設顯示哪個分類**是前端層面的事，比起「產生連結時就把資料裁切成只含選定分類存成新快照」輕量很多，也讓收件人拿到連結後能自行探索其他分類，體驗更接近直接開分頁看。

**取捨**：如果之後有「連結只能看到當初選的那個分類，其他分類資料完全不可見」的需求（例如不想讓對方看到「商品」數字），這個做法做不到，因為底層 payload 仍是全量的，URL 參數只是預設值，任何拿到連結的人都能在畫面上點別的分類看到全部——這種情境需要另外評估（見「不在本次範圍內」）。

## 到達頁與商品兩個分頁的差異（實作時要注意）

| | 到達頁 | 商品 |
|---|---|---|
| 分類篩選 UI | 一排按鈕 | 一個 `<select>` 下拉 |
| 分類清單 | 固定 4 種（`LANDING_CATEGORY_ORDER`：product/article/functional/other） | 依 GA4 實際分類／自訂規則動態產生（`Object.keys(category_counts)`），另有 `(not set)` 顯示成「未分類」 |
| payload 欄位 | `landing_pages` / `category_counts` | `items` / `category_counts` |
| 分類欄位名 | `row.category` | `row.item_category` |

分享頁重建篩選 UI 時要各自比照對應分頁的既有寫法，不要混用（商品分類是動態清單，不能套用到達頁的固定 4 分類陣列）。

## 實作步驟（依序執行）

### 步驟 1：AI 解析改用目前篩選後的清單 ✅ 已完成

- 檔案：`frontend/src/components/GA4Insights/LandingPagesTab.jsx`
  - `buildPayload()` 的 `landing_pages` 改用已經算好的 `filteredSortedLandingPages`，取代 `landingSnapshot?.payload?.landing_pages || []`
  - `contextLabel` 補上目前分類篩選狀態（比照既有 `channelScopeLabel` 的模式寫一個小函式，`landingCategoryFilter === 'all'` 時回傳 `null`、不影響現況文字；否則回傳類似「分類篩選：商品」的句子），跟既有的 key_event/channel 描述用同樣的 `.filter(Boolean).join('；')` 接起來
- 檔案：`frontend/src/components/GA4Insights/ItemsTab.jsx`
  - `buildPayload()` 的 `items` 改用已經算好的 `filteredSortedItems`，取代 `itemsSnapshot?.payload?.items || []`
  - `contextLabel` 同樣補上目前分類篩選狀態（`itemsCategoryFilter === 'all'` 時不顯示）
- **兩邊都注意**：`category_counts` 欄位維持傳完整版（不用跟著篩選），因為那是「各分類各自有幾筆」的統計，篩選後只會剩一個分類的數字，AI 反而少了「這個屬性分類分布」的全貌資訊

### 步驟 2：分享連結網址帶上目前的分類篩選 ✅ 已完成

- 檔案：`frontend/src/components/GA4Insights/GA4InsightsShared.jsx::AIInsightNote`
  - 新增一個可選 prop `shareUrlParams`（預設 `{}`，物件形式，例如 `{ category: 'product' }`），只有到達頁／商品分頁會傳這個 prop，其餘分頁（渠道對照/商品頁面比對/當日總覽）不受影響
  - `shareUrl` 的組成（目前寫死 `${window.location.origin}/ga4-insights/share/${shareToken}`）改成用 `URLSearchParams` 把 `shareUrlParams` 裡有值的欄位接在後面（例如變成 `.../share/{token}?category=product`），`handleCopyLink` 複製的網址也要是帶參數的完整版
- 檔案：`frontend/src/components/GA4Insights/LandingPagesTab.jsx`：`<AIInsightNote>` 呼叫多帶一個 `shareUrlParams={landingCategoryFilter !== 'all' ? { category: landingCategoryFilter } : {}}`
- 檔案：`frontend/src/components/GA4Insights/ItemsTab.jsx`：`<AIInsightNote>` 呼叫多帶一個 `shareUrlParams={itemsCategoryFilter !== 'all' ? { category: itemsCategoryFilter } : {}}`

### 步驟 3：分享頁支援分類篩選（預設值來自網址參數，可自由切換） ✅ 已完成

- 檔案：`frontend/src/pages/SharedGA4Insight.jsx`
- 用 `useSearchParams()`（react-router-dom，`useMetaAndromedaMonitoring.js` 已有既有前例）讀取網址上的 `category` 參數
- `LandingPagesTable`：
  - 內部加 `category` state，初始值讀網址參數；非法值（不在 `LANDING_CATEGORY_ORDER` 內）一律退回 `'all'`，不擋頁面渲染
  - 加一排分類篩選按鈕，樣式/文案比照到達頁分頁既有按鈕（`全部/商品/文章/功能/其他 (筆數)`，筆數讀 `payload.category_counts`）
  - 表格 `rows` 依 `category` state 篩選（`category === 'all' || row.category === category`）
- `ItemsTable`：
  - 內部加 `category` state，初始值讀網址參數；非法值（不在 `Object.keys(payload.category_counts || {})` 內，且不是 `'all'`）一律退回 `'all'`
  - 加一個分類篩選 `<select>`，選項依 `payload.category_counts` 動態產生（比照商品分頁既有寫法），`(not set)` 顯示成「未分類」
  - 表格 `rows` 依 `category` state 篩選（`category === 'all' || row.item_category === category`）
- 只有這兩個表格元件受影響，`ChannelsTable`/`ItemLandingCrossTable` 不用改

### 步驟 4：測試

- 這次完全沒有後端/資料庫變動，純前端修改，不需要新增 pytest
- 前端：`vite build` 編譯驗證；人工在瀏覽器操作確認（到達頁、商品兩個分頁都要各測一次）：
  1. 選一個非「全部」的分類，點「開始 AI 解讀」，確認生成的內容只針對該分類的資料（不再混雜其他分類）
  2. 選好分類後點「產生分享連結」，確認複製出來的網址帶有正確的 `?category=` 參數
  3. 開啟分享連結，確認預設就顯示該分類，且分類篩選 UI 可以正常切換看其他分類
  4. 分類選「全部」時，AI 解析與分享連結網址都維持現況（不帶 `category` 參數），確保沒有改變既有行為
  5. 商品分頁額外測：分類是「未分類」（`(not set)`）時，分享連結網址與分享頁篩選也要能正確對應

## 不在本次範圍內

- 「分享連結只能看到選定分類、其他分類資料完全隱藏」——需要在產生分享連結時把資料裁切存成新快照，屬於較大改動，之後有明確需求再評估
- 商品頁面比對分頁（`ItemLandingCrossTab.jsx`）——這個分頁目前沒有分類篩選功能，不適用本次修法
