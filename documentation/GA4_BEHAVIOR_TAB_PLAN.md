# GA4 用戶行為分頁實作計劃

> 狀態：✅ **已完成**

## 目標

在現有 GA4 儀表板的「用戶行為」Tab 中實作完整的用戶分析功能：
- 分析維度選單（裝置類別、裝置型號、國家/地區、區域、年齡、語言）
- 動態篩選器（根據選擇的維度顯示對應篩選選項）
- 9 個 KPI 卡片和表格欄位

---

## 一、用戶行為維度選擇器

| 選項 | API 維度名稱 | 說明 |
|------|-------------|------|
| 裝置類別 | `deviceCategory` | Desktop / Mobile / Tablet |
| 裝置型號 | `deviceModel` | 具體裝置型號 |
| 國家/地區 | `country` | 根據 IP 判斷的國家 |
| 區域 | `region` | 地理區域（如：台北市） |
| 年齡 | `userAgeBracket` | 年齡層（需啟用 Google Signals）|
| 語言 | `language` | 瀏覽器語言設定 |

---

## 二、動態篩選器

根據選擇的維度，右側篩選器動態顯示對應選項：

| 分析維度 | 篩選器標籤 | 選項來源 |
|---------|-----------|---------|
| 裝置類別 | 裝置篩選 | 全部裝置 / Desktop / Mobile / Tablet |
| 裝置型號 | 型號篩選 | 從 API 數據產生 |
| 國家/地區 | 國家篩選 | 從 API 數據產生 |
| 區域 | 區域篩選 | 從 API 數據產生 |
| 年齡 | 年齡篩選 | 全部年齡 / 18-24 / 25-34 / ... |
| 語言 | 語言篩選 | 從 API 數據產生 |

---

## 三、KPI 卡片（9 個指標）

| 指標 | API 名稱 | 格式 |
|------|---------|------|
| 總人數 | `totalUsers` | 數字 |
| 互動工作階段 | `engagedSessions` | 數字 |
| 瀏覽 | `screenPageViews` | 數字 |
| 參與度 | `engagementRate` | 百分比 |
| 平均參與時間 | `averageSessionDuration` | 時間 |
| 加入購物車 | `addToCarts` | 數字 |
| 購買 | `ecommercePurchases` | 數字 |
| 總購買收益 | `purchaseRevenue` | 貨幣 |
| 轉換率 | (計算) `ecommercePurchases / totalUsers * 100` | 百分比 |

---

## 四、實作進度

- [x] 儲存實作計劃
- [x] 新增用戶行為維度常數 (BEHAVIOR_DIMENSIONS)
- [x] 新增動態篩選器標籤常數 (BEHAVIOR_FILTER_LABELS)
- [x] 新增用戶行為狀態 (behaviorDimension, behaviorFilter)
- [x] 更新 TABS 配置使用正確的 metrics
- [x] 修改 fetchAnalytics 支援用戶行為維度
- [x] 實作 getBehaviorKPIData 函數
- [x] 實作動態篩選器選項產生器
- [x] 渲染用戶行為分頁 UI
- [x] 表格第一欄動態顯示維度標頭
- [x] 表格 9 個指標欄位（含轉換率計算）
- [x] 本地測試驗證

---

## 五、注意事項

⚠️ **年齡維度限制**：
- 需要在 GA4 管理介面啟用 Google Signals
- 資料可能因隱私門檻被隱藏（用戶數太少時）
- 若無數據應顯示友善提示
