# Facebook Dashboard SaaS - ROADMAP

**最後更新**: 2025-12-30
**品牌名稱**: **DataVue**

---

## 🎨 品牌定位 (Brand Identity)

### DataVue
**整合 FB Ads、Google Search Console、GA4 的全方位行銷數據儀表板**

- **名稱由來**: Data (數據) + Vue (法語「視野」)
- **品牌口號**:
  - 英文: *"See the complete picture."*
  - 中文: *「數據全景，一目了然」*
- **目標用戶**: 行銷團隊、數位廣告代理商、電商企業
- **核心價值**: 多數據源整合、即時洞察、團隊協作

---

## 🚧 Active Development (開發進行中)

### 1. AI 智慧分析引擎 (Phase 1: 分析師)
**目標**: 將儀表板從被動的報表工具轉變為「主動的 AI 顧問」。
*   **✅ 後端服務**: 已實作透過 Google Gemini 整合的 `AIService`。
*   **✅ 前端介面**: 完成 "AI Analyst" 側邊滑出面板與連線測試按鈕。
*   **✅ 診斷模式**: 自動分析目前畫面數據 (Campaign/AdSet)，找出關鍵問題與機會點。
*   **🚧 分層金鑰管理 (Scope Key Management)**:
    *   **個人金鑰 (User Level)**: 存於 `users` 資料表，僅限個人工作區使用。
    *   **團隊金鑰 (Team Level)**: 存於 `teams` 資料表，供團隊成員協作使用。
*   **🚧 AI 自訂指令系統 (Custom AI Instructions)**

---

## 🚀 未來規劃 (Future Roadmap)

### 1. 進階報表工具
- **自訂指標 (Metric Customization)**: 完善指標超市體驗。
- **報告產生器 (Report Generator)**: 優化 PDF 匯出排版與多樣化模板。

### 2. 資料整合擴展
- **GA4 整合**: 引入 Google Analytics 4 數據對齊。
- **Line 廣告整合**: 針對台灣市場的擴展計畫。

### 3. AI 演進 (Phase 2 & 3)
- **Copilot (Phase 2)**: 對話式助理 (Chatbot)。
- **Autopilot (Phase 3)**: 自動化規則執行。
