# Facebook Dashboard SaaS - 專案路線圖與創意筆記

**最後更新**: 2025-12-16
**專案狀態**: v1.5.1 (Stable Phase - 穩定版)

本文檔用於追蹤 Facebook Dashboard SaaS 平台的開發路線圖、已完成的里程碑以及未來的架構計畫。

---

## 🚧 Active Development (開發進行中)

目前正在構建或即將進行的功能。

### 1. AI 智慧分析引擎 (Phase 1: 分析師)
**目標**: 將儀表板從被動的報表工具轉變為「主動的 AI 顧問」。
*   **✅ 後端服務**: 已實作透過 Google Gemini 整合的 `AIService`。
*   **✅ 前端介面**: 完成 "AI Analyst" 側邊滑出面板與連線測試按鈕。
*   **✅ 診斷模式**: 自動分析目前畫面數據 (Campaign/AdSet)，找出關鍵問題與機會點。
*   **🚧 分層金鑰管理 (Scope Key Management)**:
    *   **個人金鑰 (User Level)**: 存於 `users` 資料表，僅限個人工作區使用。
    *   **團隊金鑰 (Team Level)**: 存於 `teams` 資料表，供團隊成員協作使用。
    *   **分享邏輯**: 明確的「複製到團隊 (Copy to Team)」按鈕 (不採用隱式共享)。
*   **🚧 AI 自訂指令系統 (Custom AI Instructions)**:
    *   **概念**: 允許用戶/團隊定義 System Prompts，客製化 AI 的分析風格 (Persona)。
    *   **儲存**: 資料庫 (`ai_system_prompt` 欄位)。
    *   **優先級**: 團隊指令 (Team Prompt) > 個人指令 (User Prompt) > 系統預設 (System Default)。

---

## ✅ Completed Features (已完成功能)

### 1. 核心架構與安全性 (Core Architecture)
*   **✅ Google OAuth 登入**: 採用 JWT 的安全驗證流程。
*   **✅ 角色權限控制 (RBAC)**: 支援 超級管理員、團隊擁有者、管理員、一般成員 等角色。
*   **✅ 資料庫整合**: 從 SQLite/JSON 遷移至 PostgreSQL (Zeabur Ready)。
*   **✅ 安全性強化**: FB Access Tokens 儲存採用 Fernet 加密。
*   **✅ Token 隔離**: 嚴格區分「個人工作區」與「團隊工作區」的數據權限。

### 2. 儀表板與數據分析 (Dashboard & Analytics)
*   **✅ 多層級分析**: 支援 Campaign / Ad Set / Ad 層級切換與動態日期範圍。
*   **✅ 比較模式 (Comparison)**: 支援「年增率 (YoY)」與「上期比較」邏輯。
*   **✅ 進階指標**:
    *   **漏斗 (Funnel)**: 轉換率 (CVR)、流失率 (Drop-off)、購物車價值實現率。
    *   **電商 (E-commerce)**: ROAS, CPA, 客單價 (ATV)。
    *   **互動 (Engagement)**: 貼文分享、留言、收藏數。
*   **✅ 視覺化圖表**: 支援雙軸趨勢圖 (Dual-Axis)，例如 Spend vs ROAS。
*   **✅ UI 優化**: 凍結表頭 (Sticky Headers)、緊湊型表格、穩健的錯誤處理。

### 3. 團隊協作 (SaaS Features)
*   **✅ 團隊工作區**: 建立、管理與切換多個團隊。
*   **✅ 邀請系統**: 產生 24小時有效期的邀請連結。
*   **✅ 廣告帳號白名單**: 精細控制團隊成員可見的廣告帳號列表。
*   **✅ 超級管理員後台**: 全域的使用者與團隊管理介面。

### 4. 使用者體驗與手機版 (UX & Mobile)
*   **✅ 響應式設計**: 手機版完全優化 (智慧側邊欄、卡片式列表)。
*   **✅ 語系支援**: 繁體中文 / English 切換。
*   **✅ 智慧導覽**: 側邊欄自動收合、快速情境切換。

---

## 🚀 Future Roadmap (未來規劃)

預計於 v1.6+ 版本推出的功能。

### 1. 進階報表工具
*   **自訂指標 (Metric Customization)**: 「指標超市」讓用戶自由勾選想看的欄位。
*   **下鑽分析 (Drill-down)**: 點擊圖表直接查看底層 Ad Sets 數據。
*   **儲存報表 (Saved Reports)**: 將篩選條件與指標設定存為預設值 (e.g., "老闆視角", "素材視角")。

### 2. AI 演進 (Phase 2 & 3)
*   **Copilot (Phase 2)**: 對話式助理 (Chatbot)，例如問：「為什麼昨天 ROAS 掉了？」。
*   **Autopilot (Phase 3)**: 自動化規則執行 (e.g., "CPA > $50 自動暫停廣告")。
*   **RAG 整合**: 結合知識庫，提供具備上下文的回答。

### 3. 商業化與金流
*   **Stripe 整合**: 訂閱制金流 (Free / Pro / Enterprise)。
*   **用量配額 (Quotas)**: 根據方案限制 AI 分析次數或團隊成員數。
*   **稽核紀錄 (Audit Logs)**: 記錄企業級的操作軌跡 (Compliance)。

### 4. 渠道擴充
*   **協作廣告 (CPAS)**: 針對零售通路的銷售指標 (Catalog 邏輯)。
*   **Google 整合**: 串接 GA4 實現全漏斗歸因 (Full-funnel Attribution)。
*   **隱藏受眾挖掘**: 尋找低競爭廣告關鍵字的工具。

---

## 📚 Technical Notes (技術筆記)

### Google 整合規則 (OAuth)
*   **測試模式 (Testing Mode)**: 需要手動將 Email 加入白名單。
*   **正式模式 (Production Mode)**: 若索取敏感權限 (如 GA4) 需通過 Google 驗證，否則會有 "Unverified App" 警告。
*   **策略**: 目前僅使用 `email/profile` 權限，避免繁瑣驗證。

### 部署與效能
*   **Zeabur 部署**: 需設定特定環境變數 (`ZEABUR_AI_HUB_API_KEY`)。
*   **效能優化**:
    *   **分頁機制 (Pagination)**: 對於超過 50 個 Active Campaign 的帳號至關重要。
    *   **快取 (Caching)**: 使用 Redis/Memory cache 減少頻繁 API 呼叫。