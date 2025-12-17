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

#### 1.1 自訂指標 (Metric Customization) - 「指標超市」
**目標**: 讓用戶自由選擇想要顯示的欄位，打造個人化報表體驗。

**現況**: ⏳ 部分完成
- ✅ `constants/analyticsConfig.js` 已定義 METRIC_GROUPS
- ✅ Analytics 頁面已有 View 切換 (總覽/電商/漏斗/自訂)
- ✅ MetricSelector 元件已建立 (Memoized)

**待完成**:
| 功能 | 說明 | 優先級 |
|------|------|--------|
| 偏好儲存 | 記住使用者上次選擇的指標 (localStorage) | 🔴 高 |
| 拖曳排序 | 拖曳調整欄位顯示順序 (react-dnd) | 🟡 中 |
| 快速篩選 | 搜尋框快速找到指標 | 🟢 低 |

**資料結構**:
```json
// localStorage: analytics_preferences_{user_id}
{
  "selectedMetrics": ["general:spend", "ecommerce:roas", "ecommerce:purchases"],
  "columnOrder": ["spend", "roas", "purchases", "ctr"],
  "lastUpdated": "2025-12-17T00:00:00Z"
}
```

---

#### 1.2 下鑽分析 (Drill-down)
**目標**: 點擊圖表或表格行，直接深入查看底層數據。

**現況**: 🔲 未實作

**使用者流程**:
```
Account Overview → 點擊 Campaign → 顯示該 Campaign 的 Ad Sets
                → 點擊 Ad Set  → 顯示該 Ad Set 的 Ads
                → 點擊 Ad      → 顯示 Ad 詳細素材預覽
```

**技術需求**:
| 項目 | 說明 |
|------|------|
| 圖表點擊事件 | Recharts `onClick` handler |
| 動態 API 呼叫 | 傳入 `campaign_id` 或 `adset_id` 過濾 |
| 麵包屑導航 | `All Campaigns > Campaign A > Ad Set B` |
| URL 參數 | 支援直接分享連結 `?campaign_id=123` |

**API 端點 (現有)**:
```python
GET /api/analytics-data?account_id={id}&level=adset&campaign_id={cid}
GET /api/analytics-data?account_id={id}&level=ad&adset_id={asid}
```

**UI 設計方向**:
- 點擊表格 Row → 展開子表格 (Accordion Style)
- 或: 右側滑出 Panel 顯示詳細資訊

---

#### 1.3 儲存報表 (Saved Reports)
**目標**: 將篩選條件與指標設定存為預設值，一鍵還原常用視角。

**現況**: 🔲 未實作

**使用情境**:
| 預設名稱 | 說明 | 指標 |
|----------|------|------|
| 老闆視角 | 高層總覽 | Spend, ROAS, Purchases |
| 素材視角 | 廣告測試 | CTR, CPC, Engagement |
| 電商視角 | 購買漏斗 | ATC, CVR, Cart Dropoff |

**資料結構**:
```json
// saved_reports table
{
  "id": "uuid",
  "user_id": 123,
  "team_id": null,  // null = 個人, non-null = 團隊共享
  "name": "老闆視角",
  "icon": "📊",
  "config": {
    "level": "campaign",
    "datePreset": "last_7d",
    "metrics": ["spend", "roas", "purchases", "cpa"],
    "filters": {
      "keyword": "",
      "activeOnly": false
    },
    "sortBy": "spend",
    "sortOrder": "desc"
  },
  "is_default": false,
  "created_at": "2025-12-17T00:00:00Z"
}
```

**儲存位置策略**:
| 類型 | 儲存位置 | 說明 |
|------|----------|------|
| 臨時偏好 | localStorage | 不需登入，立即生效 |
| 個人報表 | 資料庫 users.saved_reports | 跨裝置同步 |
| 團隊報表 | 資料庫 team_reports | 團隊成員共用 |

**UI 設計**:
```
[View 選擇器]
├── 📊 總覽 (系統預設)
├── 🛒 電商 (系統預設)
├── 🌪️ 漏斗 (系統預設)
├── ─────────────────
├── ⭐ 老闆視角 (我的報表)
├── ⭐ 素材視角 (我的報表)
├── ─────────────────
├── 👥 團隊週報 (團隊共用)
└── ⚙️ 自訂...
```

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