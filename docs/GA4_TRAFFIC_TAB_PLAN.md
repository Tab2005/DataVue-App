# GA4 流量分頁增強實作計劃

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

## 二、KPI 卡片（9 個指標，與總覽一致）

| 指標 | API 名稱 |
|------|---------|
| 活躍使用者 | `activeUsers` |
| 總人數 | `totalUsers` |
| 新使用者人數 | `newUsers` |
| 瀏覽 | `screenPageViews` |
| 購買 | `ecommercePurchases` |
| 總購買收益 | `purchaseRevenue` |
| 加入購物車 | `addToCarts` |
| 客單價 | (計算) `purchaseRevenue / ecommercePurchases` |
| 購買轉換率 | (計算) `ecommercePurchases / totalUsers * 100` |

---

## 三、動態來源篩選

- 從 API 數據自動產生來源選項
- 預設「全部來源」
- 選擇特定來源後篩選計算 KPI

---

## 四、實作順序

- [x] 儲存實作計劃
- [x] 新增流量維度選項常數 (TRAFFIC_DIMENSIONS)
- [x] 新增來源篩選狀態 (sourceFilter, trafficDimension)
- [x] 修改流量分頁 API 請求支援動態維度
- [x] 實作動態來源選項產生器
- [x] 實作維度選擇下拉選單
- [x] 實作 9 個 KPI 卡片（隨來源篩選動態更新）
- [x] 表格第一欄動態顯示維度標頭
- [x] 表格 9 個指標欄位（含轉換率計算）
- [x] 本地測試驗證


