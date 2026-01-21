# DataVue-App 專案技能與工作流總覽

本文件紀錄了專案中可供 Agent 使用的擴充技能 (Skills) 與自動化工作流 (Workflows)。

## 1. 擴充技能 (Skills)

技能通常位於 `skills/` 目錄下，包含詳細的 API 參考、設計模式與實作範例，協助 Agent 快速理解特定領域。

### 🛠️ [Skill Seekers](file:///c:/Users/user/Documents/Python/DataVue-App/skills/skill-seekers/SKILL.md)
*   **功能**: 自動將技術文件、GitHub 儲存庫或 PDF 轉換為結構化的 AI 技能。

### 🎭 Anthropic 專業擴充 (Anthropic Skills)
*   **來源**: [Anthropic Skills Repository](https://github.com/anthropics/skills)
*   **分類功能**:
    *   **開發與測試**: 
        *   [`webapp-testing`](file:///c:/Users/user/Documents/Python/DataVue-App/skills/webapp-testing/SKILL.md): 網頁應用整合測試流程。
        *   [`frontend-design`](file:///c:/Users/user/Documents/Python/DataVue-App/skills/frontend-design/SKILL.md): 前端 UI/UX 設計規範。
        *   [`web-artifacts-builder`](file:///c:/Users/user/Documents/Python/DataVue-App/skills/web-artifacts-builder/SKILL.md): 建立互動式 React Artifacts。
    *   **技能與工具建置**:
        *   [`skill-creator`](file:///c:/Users/user/Documents/Python/DataVue-App/skills/skill-creator/SKILL.md): 建立與優化 Agent 技能的指南。
        *   [`mcp-builder`](file:///c:/Users/user/Documents/Python/DataVue-App/skills/mcp-builder/SKILL.md): 建置 Model Context Protocol (MCP) Server。
    *   **文件處理**:
        *   [`docx`](file:///c:/Users/user/Documents/Python/DataVue-App/skills/docx/SKILL.md), [`pdf`](file:///c:/Users/user/Documents/Python/DataVue-App/skills/pdf/SKILL.md), [`pptx`](file:///c:/Users/user/Documents/Python/DataVue-App/skills/pptx/SKILL.md), [`xlsx`](file:///c:/Users/user/Documents/Python/DataVue-App/skills/xlsx/SKILL.md): 各類辦公文件的高級讀寫與轉換。
    *   **設計與創意**:
        *   [`brand-guidelines`](file:///c:/Users/user/Documents/Python/DataVue-App/skills/brand-guidelines/SKILL.md), [`theme-factory`](file:///c:/Users/user/Documents/Python/DataVue-App/skills/theme-factory/SKILL.md), [`canvas-design`](file:///c:/Users/user/Documents/Python/DataVue-App/skills/canvas-design/SKILL.md)。

---

## 2. 自動化工作流 (Workflows)

工作流位於 `.agent/workflows/` 下，定義了執行特定專案任務的具體步驟。

### 🚀 [/start-dev](file:///c:/Users/user/Documents/Python/DataVue-App/.agent/workflows/start-dev.md)
*   **功能**: 啟動完整的開發環境。
*   **步驟內容**:
    *   檢查 Python 與 Node.js 環境。
    *   執行 `.\start-dev.ps1`。
    *   啟動後端 API (Port 8000) 與前端 Vite 伺服器 (Port 5173/5174)。
    *   自動進行健康檢查。

---

## 3. 最近實作的功能優化 (Recent Feature Optimizations)

雖然不是獨立技能，但屬於專案目前強化的核心能力。

### 🔍 GSC 效能優化 (GSC Performance Optimization)
*   **核心能力**: 支援 Google Search Console 大數據的高效處理。
*   **技術特點**: 
    *   **後端分頁**: 使用 `limit` 與 `offset` (預設每批 2000-5000 筆)。
    *   **快取機制**: 整合 Redis 達成秒級讀取。
    *   **前端優化**: 支援「載入更多」與載入時間追蹤 (Lightning Badge)。

---

*最後更新日期: 2026-01-21*
