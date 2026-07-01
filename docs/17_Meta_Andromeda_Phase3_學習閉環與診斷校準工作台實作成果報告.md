# 19 Meta Andromeda Phase 3 學習閉環與診斷校準工作台實作成果報告

本報告摘要了 **Meta Andromeda Phase 3: 學習閉環 (Learning Loop)** 在前端操作工作台、版本釋出控台發佈安全鎖 (Release Gate Lock) 的完整實作成果，並附帶了單元測試與生產環境編譯的驗證。

---

## 🛠️ 實作項目與功能說明

### 1. 補齊監控工作台樣式宣告
* **檔案位置**：`frontend/src/pages/MetaAndromedaMonitoring.jsx`
* **修正內容**：在底部樣式區宣告了遺漏的 `badgeStyle` 物件，解決了原本會導致 Vite 生產環境編譯失敗的變數未定義風險。

### 2. 線上實測對照證據面板 (Online Performance Evidence Panel)
* **檔案位置**：`frontend/src/pages/MetaAndromedaRelease.jsx`
* **UI 呈現**：
  * 在 `/meta-andromeda/release` 頁面上，重構了第二列的格狀排版，左側採用 `flex-column` 容器容納 **線上實測對照證據** 與 **候選版本** 兩個面板。
  * 系統載入時，透過 `fetchMetaAndromedaMonitoringSummary` 異步讀取後端最新產生的漂移監控報告（Drift Report），並將其呈現在 Glassmorphism 毛玻璃卡片中。
  * 卡片直觀展示目前線上模型的：
    * **報告狀態**（`STABLE` / `WARNING` / `DRIFTED`），不同狀態配有不同漸變指示燈與色調。
    * **預測準確率 (Accuracy)** 與 **平均絕對偏差 (MAE)**。
    * **觸發人員** 與 **更新時間**。

### 3. 模型發佈安全鎖 (Release Gate Lock)
* **檔案位置**：`frontend/src/pages/MetaAndromedaRelease.jsx`
* **安全機制**：
  * 當檢測到線上 Drift 報告狀態為 `drifted`（嚴重漂移）時，候選版本卡片中的 **「批准 (Approve)」** 按鈕將會被**置灰禁用 (disabled)**。
  * 鼠標懸浮於按鈕上時會顯示鎖定提示：`因線上模型漂移而鎖定發佈`，防止營運人員在模型精度低落時發佈劣質模型。
  * 在按鈕下方顯示紅色警告訊息區：
    > ⚠️ 線上模型已檢測出顯著漂移 (Accuracy: 40.0% < 60%)。為了避免劣質預估，已自動鎖定發佈。請先進入監控工作台執行「資料校準」，再行核准新模型。

### 4. 前端單元測試與 Mock 機制優化
* **檔案位置**：`frontend/src/pages/__tests__/MetaAndromedaRelease.test.jsx`
* **新增測試案例**：
  * `it('disables Approve button and shows warning if online model is drifted')`
  * 該測試實作了對 `fetchMetaAndromedaMonitoringSummary` 介面的 Mock，藉由模擬一個 `drifted` 報告的 payload，渲染中文語境，成功驗證：
    1. 狀態標記 `DRIFTED` 正確出現在頁面。
    2. 「批准」按鈕處於 `disabled` 狀態。
    3. 紅色發佈警告語 `再行核准新模型` 正確印出。

---

## 🧪 驗證結果

### 1. 前端單元測試通過 (Vitest)
我們執行了前端單元測試，所有的 4 個測試檔案與 6 個測試案例全數 100% 通過：
```bash
 RUN  v3.2.6 C:/Users/BWM2/Documents/python/DataVue-App/frontend

 ✓ src/pages/__tests__/MetaAndromedaScoreLab.test.jsx (1 test) 146ms
 ✓ src/pages/__tests__/MetaAndromedaReviewQueue.test.jsx (1 test) 159ms
 ✓ src/pages/__tests__/MetaAndromedaRelease.test.jsx (2 tests) 175ms
 ✓ src/pages/__tests__/MetaAndromedaMonitoring.test.jsx (2 tests) 189ms

 Test Files  4 passed (4)
      Tests  6 passed (6)
   Start at  13:47:45
   Duration  1.75s
```

### 2. 生產環境建置成功 (Vite Production Build)
我們執行了生產環境打包驗證，編譯流程極為健康，且無任何 TS/JSX 或 CSS 變數錯誤：
```bash
vite v7.2.7 building client environment for production...
transforming...
✓ 3392 modules transformed.
rendering chunks...
dist/assets/MetaAndromedaRelease-BkSbBO-T.js             10.52 kB │ gzip:   3.40 kB
dist/assets/MetaAndromedaMonitoring-BOIksmo7.js          20.76 kB │ gzip:   5.74 kB
✓ built in 5.41s
```
