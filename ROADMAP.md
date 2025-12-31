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

---

## ⚡ 效能優化 (Performance Optimization)

### 後端啟動速度優化
**狀態**: 待實作
**問題描述**: Zeabur 部署啟動速度慢，影響冷啟動回應時間。

**已識別的瓶頸**:

| 優先級 | 問題 | 位置 | 預期改善 |
|--------|------|------|----------|
| 🔴 高 | 每次啟動都執行 Alembic Migration | `main.py:143-146` | -3~5 秒 |
| 🔴 高 | 多次 Schema Patching 檢查 (teams, users, saved_views) | `main.py:152-231` | -3~5 秒 |
| 🔴 高 | Router 被重複註冊兩次 | `main.py:382-388, 456-460` | 減少混亂 |
| 🟡 中 | 每次啟動都執行 Permission Seeding | `main.py:237-242` | -2~3 秒 |
| 🟡 中 | AI 模組同步 import (google-genai, openai) | `ai_service.py` | -1~2 秒 |
| 🟢 低 | 大量 debug print 輸出 | 全域 | 減少 log 量 |

**建議優化方案**:
1. 使用環境變數 `SKIP_MIGRATION=true` 控制是否執行 migration
2. 將 schema patching 改為「僅首次部署」或「手動觸發」
3. 移除重複的 router include
4. AI 模組使用 lazy import（首次呼叫時才載入）
5. 優化 seed_permissions 只在資料不存在時執行

