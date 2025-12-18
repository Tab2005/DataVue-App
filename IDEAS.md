# Facebook Dashboard SaaS - 專案路線圖與創意筆記

**最後更新**: 2025-12-18
**專案狀態**: v1.5.3 (Stable Phase - 穩定版)

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
*   **✅ Strict Token Mode**: 強制個人工作區使用個人 Token，防止 Fallback 導致資料洩漏。
*   **✅ 團隊 Token 管理**: 支援儲存與顯示 Token 到期時間，並提供即將過期通知。

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
*   **✅ 廣告帳號白名單**: 精細控制團隊成員可見的廣告帳號列表 (含 Robust Filtering 修復)。
*   **✅ 視角共享**: 支援資料庫層級的「個人視角」與「團隊視角」儲存策略。
*   **✅ 超級管理員後台**: 全域的使用者與團隊管理介面。

#### 團隊角色權限設計 (Team RBAC)

| 角色 | 說明 | 取得方式 |
|------|------|----------|
| **Owner** | 團隊創建者，最高權限 | 建立團隊時自動成為 `team.owner_id` |
| **Admin** | 可管理團隊設定與成員 | 創建者預設為 Admin，手動指派 |
| **Member** | 可查看數據，無管理權限 | 透過邀請連結加入時的預設角色 |
| **Viewer** | 僅能查看數據 | 手動指派 |

| 功能 | Owner | Admin | Member | Viewer |
|------|:-----:|:-----:|:------:|:------:|
| 查看數據 | ✅ | ✅ | ✅ | ✅ |
| 產生邀請連結 | ✅ | ✅ | ❌ | ❌ |
| 修改團隊 API 設定 | ✅ | ✅ | ❌ | ❌ |
| 設定廣告帳號白名單 | ✅ | ✅ | ❌ | ❌ |
| 更改成員角色 | ✅ | ✅ | ❌ | ❌ |
| 踢除成員 | ✅ | ✅ | ❌ | ❌ |
| 解散團隊 | ✅ | ❌ | ❌ | ❌ |

> **已知設計問題**: Member 和 Viewer 目前功能相同（都只能查看數據），未來可考慮區分：
> - **Member**: 可儲存視角、設定個人偏好
> - **Viewer**: 純粹只讀

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

**現況**: ✅ 已完成 (v1.5.3)
- ✅ `constants/analyticsConfig.js` 已定義 METRIC_GROUPS
- ✅ Analytics 頁面已有 View 切換 (總覽/電商/漏斗/自訂)
- ✅ MetricSelector 元件已建立 (Memoized)

**核心問題**: 現有 METRIC_GROUPS 僅包含 ~35 個指標，但 Facebook 有 100+ 可用指標。

##### 現有指標 vs 缺少的指標

| 類別 | 現有 | 缺少 |
|------|------|------|
| 通用 | spend, reach, impressions, cpc, ctr | frequency, unique_clicks |
| 電商 | roas, purchases, add_to_cart, cpa | checkout_initiated, payment_info_added |
| 漏斗 | cvr, cart_conversion, cart_dropoff | ✅ 已完整 |
| 互動 | comments, saves, shares, reactions | video_plays, photo_views |
| **影音** | ❌ 無 | video_p25_watched, video_p50_watched, video_p75_watched, video_p100_watched, video_avg_time_watched, thruplay |
| **訊息** | ❌ 無 | messaging_first_reply, messaging_conversation_started_7d |
| **潛在客戶** | ❌ 無 | leads, lead_cost, onsite_conversion.lead_grouped |
| **應用程式** | ❌ 無 | app_installs, mobile_app_install, app_custom_event |
| **歸因視窗** | ❌ 無 | 1d_click, 7d_click, 28d_click, 1d_view |

##### 架構設計：指標資料庫 (Metrics Registry)

```
┌─────────────────────────────────────────────────────────┐
│                    Facebook Graph API                    │
│  (actions, action_values, video_views, video_p25, ...)  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│           📦 指標資料庫 (Metrics Registry)               │
│  - 完整 FB 可用指標清單 (100+)                           │
│  - 各指標的中英文名稱、格式、計算方式                      │
│  - 分類標籤 (video, messaging, lead, ecommerce...)      │
│  - 是否需要特殊解析 (actions array 或直接欄位)           │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│            🛒 使用者啟用的指標 (Supermarket)              │
│  - 從 Registry 選取需要的指標                            │
│  - user_enabled_metrics / team_enabled_metrics          │
│  - 儲存到 localStorage (臨時) 或資料庫 (永久)            │
└─────────────────────────────────────────────────────────┘
```

##### 指標資料庫結構 (metrics_registry.json)

```json
{
  "video_p25_watched": {
    "key": "video_p25_watched",
    "label_zh": "影片觀看 25%",
    "label_en": "Video 25% Watched",
    "category": "video",
    "format": "number",
    "source": "actions",           // "actions" | "action_values" | "direct"
    "action_type": "video_view",   // actions array 內的 action_type
    "description_zh": "影片播放至 25% 的次數",
    "requires_video_objective": true,
    "is_default": false
  },
  "leads": {
    "key": "leads",
    "label_zh": "潛在客戶",
    "label_en": "Leads",
    "category": "lead_gen",
    "format": "number",
    "source": "actions",
    "action_type": "lead",
    "description_zh": "表單送出的潛在客戶數量",
    "is_default": false
  },
  "messaging_first_reply": {
    "key": "messaging_first_reply",
    "label_zh": "首次訊息回覆",
    "label_en": "First Message Reply",
    "category": "messaging",
    "format": "number",
    "source": "actions",
    "action_type": "onsite_conversion.messaging_first_reply",
    "description_zh": "用戶首次回覆訊息的數量",
    "is_default": false
  }
}
```

##### 實作優先級

| 優先級 | 項目 | 說明 | 工作量 |
|--------|------|------|--------|
| 🔴 P1 | 建立 `metricsRegistry.js` | 定義 100+ 指標的完整資料庫 | 2-3 小時 |
| 🔴 P1 | 更新後端解析邏輯 | 支援動態指標欄位請求 | 1-2 小時 |
| 🔴 P1 | 指標選擇 UI | 分類瀏覽 + 搜尋 | 2-3 小時 |
| 🟡 P2 | 偏好儲存 | localStorage + 資料庫同步 | 1-2 小時 |
| 🟢 P3 | 團隊指標設定 | 團隊層級的預設指標 | 1-2 小時 |

##### ⚠️ 安全實作策略 (Backward Compatible)

**原則**: 新增檔案，不修改現有程式碼。出問題時刪除新檔案即可回復。

```
📁 現有檔案 (保留不動)
├── constants/analyticsConfig.js  ← 原有 METRIC_GROUPS，完全不改
└── services.py                   ← 原有解析邏輯，完全不改

📁 新增檔案 (獨立擴展)
├── constants/metricsRegistry.js  ← 新的指標資料庫
└── hooks/useMetricsRegistry.js   ← 新的 React Hook (可選)
```

**切換機制**:
```javascript
// 功能開關 (預設關閉)
const USE_METRICS_REGISTRY = localStorage.getItem('feature_metrics_registry') === 'true';

// 使用時
const metrics = USE_METRICS_REGISTRY 
  ? getMetricsFromRegistry()   // 新系統
  : METRIC_GROUPS;              // 原系統 (預設)
```

**回滾步驟**:
| 步驟 | 操作 | 效果 |
|------|------|------|
| 1️⃣ | 關閉功能開關 | 立即切回原系統 |
| 2️⃣ | 刪除 `metricsRegistry.js` | 完全移除新程式碼 |
| 3️⃣ | `git revert` | 版本層級回退 |

##### 已完成功能 (2025-12-17 ~ 2025-12-18)

| 功能 | 說明 | 狀態 |
|------|------|------|
| 指標資料庫 | `metricsRegistry.js` - 70+ 指標 | ✅ 完成 |
| ~~指標實驗室~~ 指標管理 | `MetricsManager.jsx` - 瀏覽/搜尋 UI | ✅ 完成 |
| 儲存視角功能 | ~~localStorage~~ → 資料庫 `saved_views` 表儲存個人/團隊視角 | ✅ 完成 (升級) |
| 動態欄位 API | 後端支援 `?fields=` 參數動態請求 | ✅ 完成 |
| 側邊欄整合 | 「指標管理」選單已加入側邊欄 (`/metrics`) | ✅ 完成 |

> **命名變更 (2025-12-18)**:
> - `MetricsLab.jsx` → `MetricsManager.jsx`
> - `/lab` → `/metrics`
> - 🧪 指標實驗室 → 📋 指標管理

###### 儲存視角功能詳細說明 (Step 1)

| 功能 | 說明 |
|------|------|
| 儲存視角按鈕 | 點擊藍色「儲存視角」按鈕開啟命名 Modal |
| 命名 Modal | 輸入視角名稱，支援 Enter/Escape 快捷鍵 |
| 已儲存視角區塊 | 顯示所有已儲存視角，含指標數量標籤 |
| 載入視角 | 點擊「載入」恢復已儲存的指標選擇 |
| 刪除視角 | 點擊垃圾桶圖標刪除視角 |
| Toast 提示 | 操作成功後右上角顯示綠色提示 |
| 雙語支援 | 中文/英文介面完整翻譯 |

**技術實作**:
- localStorage Key: `metricslab_saved_views`
- 資料結構: `{ id, name, metrics[], createdAt }`

###### 儲存策略規劃

| 階段 | 儲存位置 | 說明 | 狀態 |
|------|----------|------|------|
| Phase 1 | ~~localStorage~~ | ~~瀏覽器本地儲存~~ | ✅ 已棄用 (遷移至資料庫) |
| Phase 2 | 資料庫 `saved_views` | 個人報表，跨裝置同步 | ✅ 已完成 (2025-12-18) |
| Phase 3 | 資料庫 `saved_views (team_id)` | 團隊共享報表 | ✅ 已完成 (2025-12-18) |

**localStorage 限制**:
- ❌ 無法跨裝置同步（換電腦/換瀏覽器就沒了）
- ❌ 無法分享給團隊成員
- ✅ 不需後端 API，開發快速

**升級路徑** (Phase 2):
```
1. 新增後端 API: POST /api/saved-views, GET /api/saved-views
2. 新增資料表: saved_views (id, user_id, team_id, name, metrics, created_at)
3. 前端改為呼叫 API，同時保留 localStorage 作為快取
```

**工作區視角共用策略** (2025-12-18 決議):

| 階段 | 模式 | 說明 |
|------|------|------|
| 現階段 | **共用** | 所有工作區（個人/團隊）共享同一份視角列表 |
| 未來 | 混合模式 | 個人視角跟著使用者；團隊視角存資料庫，僅團隊成員可見 |

> **設計理由**:
> - 現階段使用 localStorage，無法區分工作區
> - 共用模式可讓使用者在任何工作區都使用自己建立的視角
> - 未來實作資料庫同步時，再區分「個人視角」和「團隊視角」

##### 完整流程設計

```
┌─────────────────────────────────────────────────────────┐
│           🧪 MetricsLab (/lab)                           │
│                                                          │
│  [通用] [電商] [影音] [訊息] [潛在客戶] [應用程式]         │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ ☑ spend   ☑ roas   ☐ video_p25   ☐ messaging_reply │ │
│  │ ☑ reach   ☑ cpa    ☐ video_p50   ☐ leads           │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  [儲存為: 我的電商視角] [💾 儲存]                          │
└─────────────────────────────────────────────────────────┘
                           ↓
                    localStorage / DB
                           ↓
┌─────────────────────────────────────────────────────────┐
│           📊 Analytics (/analytics)                      │
│                                                          │
│  [總覽] [電商] [漏斗] [⭐ 我的電商視角]                    │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Campaign   │ spend │ roas │ video_p25 │ msgs_reply │ │
│  │ ────────── │ ───── │ ──── │ ───────── │ ────────── │ │
│  │ Campaign A │ $500  │ 2.5  │ 1,234     │ 89         │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

##### 待完成功能 (後續步驟)

| 優先級 | 功能 | 說明 | 工作量 | 狀態 |
|--------|------|------|--------|------|
| ~~🔴 P1~~ | ~~儲存為預設~~ | ~~MetricsLab 新增「儲存為我的視角」按鈕~~ | ~~1-2 小時~~ | ✅ 完成 |
| ~~🔴 P1~~ | ~~Analytics 讀取~~ | ~~Analytics 頁面讀取自訂視角並顯示~~ | ~~2-3 小時~~ | ✅ 完成 |
| ~~🟡 P2~~ | ~~後端動態欄位~~ | ~~根據選擇的指標動態請求 FB API 欄位~~ | ~~2-3 小時~~ | ✅ 完成 |
| 🟡 P2 | 拖曳排序 | 拖曳調整欄位顯示順序 (react-dnd) | 1-2 小時 | |
| ~~🟢 P3~~ | ~~團隊共享~~ | ~~團隊層級的自訂視角儲存~~ | ~~2-3 小時~~ | ✅ 已完成 (2025-12-18) |

##### 待優化項目 (UX 改進)

| 項目 | 說明 | 優先級 |
|------|------|--------|
| 視角數量上限 | 設定最多 5-10 個視角，避免 UI 擁擠 | 🟢 低 |
| 摺疊選單 | 超過 3 個視角時改用下拉選單 | 🟢 低 |
| 視角管理介面 | MetricsLab 提供編輯/重新命名功能 | 🟡 中 |
| 視角排序 | 支援拖曳調整視角順序 | 🟢 低 |
| 團隊視角刪除權限 | 讓團隊擁有者/管理員可刪除成員建立的團隊視角 | 🟡 中 |

##### 刪除權限設計 (Current Design)

目前採用**「誰創建，誰管理」**原則：

| 視角類型 | 刪除權限 |
|----------|----------|
| 個人視角 (`user_id` = 我) | ✅ 只有自己可刪除 |
| 團隊視角 (`created_by` = 我) | ✅ 只有創建者可刪除 |
| 別人建的團隊視角 | ❌ 無法刪除 (即使是 Team Owner) |

> **設計理由**:
> - 防止意外刪除他人辛苦建立的視角
> - 責任歸屬明確：創建者對自己的視角負責
>
> **未來考量** (如有需求再實作):
> - Super Admin / Team Owner / Team Admin 可刪除該團隊的所有視角
> - 參考 `routers/saved_views.py` 第 144 行的授權邏輯

##### 實作順序

```
Step 1: MetricsLab 新增「儲存」功能 ✅ 已完成 (2025-12-17)
        → localStorage.setItem('metricslab_saved_views', [...])

Step 2: Analytics 新增已儲存視角 ✅ 已完成 (2025-12-17)
        → 金色星號按鈕顯示已儲存視角
        → 點擊載入對應指標組合

Step 3: Analytics 讀取 localStorage ✅ 已整合至 Step 2
        → const customMetrics = localStorage.getItem('metricslab_saved_views')

Step 4: 後端支援動態欄位 ✅ 已完成 (2025-12-18)
        → /api/analytics-data?fields=spend,roas,video_p25
        → 後端 build_fb_fields() 動態建構 API 請求
        → 前端 fetchAnalytics() 傳送 fields 參數
        → calculateSummary() 支援所有 57 個指標

Step 5: 完整整合測試 ✅ 已完成 (2025-12-18)
        → Video, Messaging, Lead, App 指標正常顯示
        → KPI 卡片摘要正確計算
        → 已推送至 dev-saas 分支
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

**現況**: ✅ 已完成 (資料庫儲存 + 自動遷移)

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
| 臨時偏好 | ~~localStorage~~ | [已棄用] 改用資料庫儲存，已實作自動遷移至 `saved_views` 表 |
| 個人報表 | 資料庫 `saved_views` (user_id) | ✅ 已實作 (2025-12-18)，支援跨裝置同步 |
| 團隊報表 | 資料庫 `saved_views` (team_id) | ✅ 已實作 (2025-12-18)，團隊成員共用 |

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
*   **架構隔離 (Architecture Isolation)**:
    *   **個人 API 設定**: 存於 `users` 表，僅限個人工作區使用 (Strict Token Mode 保護)。
    *   **團隊 API 設定**: 存於 `teams` 表，僅限團隊工作區使用。兩者互不干擾。
*   **權限控制 (Permissions)**:
    *   **團隊 API 配置**: 僅限 **Team Owner** 與 **Team Admin** 有權限修改。
    *   **一般成員 (Member/Viewer)**: 僅能查看數據，無法更改 API 連線設定。

### 部署與效能
*   **Zeabur 部署**: 需設定特定環境變數 (`ZEABUR_AI_HUB_API_KEY`)。
*   **效能優化**:
    *   **分頁機制 (Pagination)**: 對於超過 50 個 Active Campaign 的帳號至關重要。
    *   **快取 (Caching)**: 使用 Redis/Memory cache 減少頻繁 API 呼叫。