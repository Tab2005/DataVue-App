# Changelog

## [1.3.0] - 2025-12-10
### Added
- **Localization**: 全站中英文語系切換 (Global Language Switch) - 支援 Header, Sidebar, Dashboard, Analytics。
- **User Interface**: 
  - 新增 **User Dropdown Menu** (使用者頭像下拉選單)。
  - 實作 **Logout Functionality** (登出與 Session 清除)。
  - 實作使用者資訊持久化 (顯示 Google 頭像與名稱)。
- **Analytics**: 
  - 建立 Analytics 頁面基礎架構 (Control Panel, Date Presets, Comparison Toggle)。
  - 響應式側邊欄 (Collapsible Sidebar)。

### Fixed
- **Bug**: 修正 Dashboard 重新整理後數據消失 ("No Data") 的問題 (Frontend Data Parsing)。
- **Bug**: 修正 Trends Chart 無法顯示數據的問題 (Dynamic `dataKey` fix)。
- **Bug**: 修正 Analytics 頁面在部署環境跳出 "Local Network Access" 警告的問題 (移除 Hardcoded URL)。
- **UX**: 修正 User Info 在重新整理後恢復預設值的問題 (LocalStorage Persistence)。

## [1.2.0] - 2025-12-10
### Added
- **Frontend**: 全新 "Performance Overview" 儀表板設計 (8-Grid Layout)。
  - 實作 8 個關鍵指標卡片，顯示 `Current`, `(Previous)`, `Diff`, `Percent`。
  - 實作 "Cost Trend" 趨勢圖表 (Daily Granularity)。
  - 新增日期區間顯示 (e.g., `2024-12-03 ~ 2024-12-09`)。
- **Backend**: 進階 KPI 比較邏輯。
  - 實作 "Inverse Metric" 邏輯 (花費/成本上升顯示為紅色，下降為綠色)。
  - 實作絕對數值增減 (`Diff`) 計算。

### Fixed
- **Backend**: 修復當該時段無數據時 (Empty Data)，導致 API 崩潰與前端白畫面的問題 (Added Manual Date Fallback)。
- **Data**: 將 KPI "Clicks" 更換為更精確的 "Link Clicks" (連結點擊次數)。

## [1.1.0] - 2024-12-09
### Fixed
- **Deployment**: 修復 Zeabur 部署問題 (Build Failures & Runtime Crashes)。
- **Frontend**: 增強 Ad Account 載入的 Retry 機制，解決 Cold Start 問題。

## [1.0.0] - 2024-12-08
### Added
- **Core**: 初始專案架構建立 (FastAPI + React)。
- **Auth**: Google Login 整合與 Facebook Token 綁定。
- **Feature**: 支援手動選擇廣告帳號 (Dropdown Selector)。
