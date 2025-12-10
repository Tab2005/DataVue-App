# Changelog

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
