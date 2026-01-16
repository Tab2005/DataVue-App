# GA4 流量分頁增強實作計劃

> 狀態：✅ **已完成**

## 目標

增強 GA4 流量分頁，新增維度選擇器、動態來源篩選 KPI 卡片、以及完整 9 欄指標表格。

---

## 一、維度選擇器

| 選項 | API 維度名稱 |
|------|-------------|
| 管道分組 | `sessionDefaultChannelGrouping` |
| 來源 | `sessionSource` |
| 媒介 | `sessionMedium` |
| 來源/媒介 | `sessionSourceMedium` |
| 廣告活動 | `sessionCampaignName` |

---

## 二、KPI 卡片（9 個指標）

| 指標 | API 名稱 |
|------|---------|
| 總人數 | `totalUsers` |
| 工作階段 | `sessions` |
| 互動工作階段 | `engagedSessions` |
| 參與度 | `engagementRate` |
| 平均工作階段時間 | `averageSessionDuration` |
| 加入購物車 | `addToCarts` |
| 購買 | `ecommercePurchases` |
| 總購買收益 | `purchaseRevenue` |
| 轉換率 | (計算) `ecommercePurchases / totalUsers * 100` |

---

## 三、來源篩選功能

- 從 API 數據自動產生來源選項
- 預設「全部來源」
- 支援來源分組（Facebook、Google、AI 等）
- 支援用戶自定義分組
- 選擇特定來源/分組後篩選計算 KPI
- KPI 卡片支援比較模式（前一時段/去年同期）

---

## 四、實作進度

- [x] 儲存實作計劃
- [x] 新增流量維度選項常數 (TRAFFIC_DIMENSIONS)
- [x] 新增來源篩選狀態 (sourceFilter, trafficDimension)
- [x] 修改流量分頁 API 請求支援動態維度
- [x] 實作動態來源選項產生器
- [x] 實作維度選擇下拉選單
- [x] 實作 9 個 KPI 卡片（隨來源篩選動態更新）
- [x] 表格第一欄動態顯示維度標頭
- [x] 表格 9 個指標欄位（含轉換率計算）
- [x] 來源分組篩選（預設 8 個分組）
- [x] 用戶自定義分組（新增/編輯/刪除）
- [x] KPI 卡片比較模式支援
- [x] 比較模式+來源篩選組合正確運作
- [x] 本地測試驗證
