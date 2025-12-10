- 設定 OAuth 同意畫面 (OAuth Consent Screen)。
- 取得 **Client ID** (前端用) 和 **Client Secret** (後端驗證用，視架構而定)。

#### 2. 前端 (React)
- **套件**: 使用 `@react-oauth/google` (官方推薦的現代化套件)。
- **流程**:
  1. 新增一個「登入頁面」 (Login Page) 作為預設首頁。
  2. 放置 "Sign in with Google" 按鈕。
  3. 使用者登入成功後，Google 會回傳一個 `Credential` (JWT)。
  4. 前端將此 Credential 存入 LocalStorage 或 Context。
  5. 實作 `ProtectedRoute` 元件，檢查是否有 Token，若無則導回登入頁。

#### 3. 後端 (FastAPI) - 選用但推薦
雖然純前端驗證也可以擋住一使用者，但為了安全性，後端 API 也應該要驗證 Token。
- **套件**: `google-auth` 或 `pyjwt`。
- **流程**:
  1. 前端呼叫 API 時，將 Google Token 放在 Header (`Authorization: Bearer <token>`)。
  2. 後端 Middleware 攔截請求，驗證該 Token 是否為 Google 簽發且有效。
  3. 驗證通過才回傳數據。

### 預計變動檔案
- `frontend/package.json`: 新增 OAuth 套件。
- `frontend/src/App.jsx`: 新增路由 (Router) 與保護機制。
- `frontend/src/pages/Login.jsx`: 新增登入頁面。
- `backend/main.py`: 新增 Token 驗證邏輯 (Middleware)。

### 待確認事項
- 是否只需要前端擋住畫面就好？還是後端 API 也要做嚴格驗證？(建議兩者都做)

### 常見問題釐清 (Q&A)
**Q: Google 登入跟 Facebook API 設定有關聯嗎？**
**A: 完全沒有關聯，兩者是獨立的。**
- **Google 登入 (Authentication)**: 就像是「大門鑰匙」，決定誰可以進入這個網站看到畫面。
- **Facebook API (Data Source)**: 就像是「電視訊號」，決定畫面裡面有沒有數據可以看。
- **結論**: 即使設定了 Google 登入，如果沒有在設定頁面輸入正確的 Facebook App ID/Secret，進去後也只會看到空的儀表板，無法抓取數據。

**Q: 這樣還有需要驗證後端 API 嗎？**
**A: 強烈建議要驗證 (Security Best Practice)。**
- **如果只做前端驗證**: 只是把「門」關起來，但「窗戶」是開的。駭客或懂技術的人如果知道您的 API 網址 (例如 `https://.../api/dashboard-data`)，可以直接繞過登入頁面，發送請求把資料抓走。
- **如果加上後端驗證**: 就像是窗戶也加了鐵窗。後端會檢查每一個請求：「你有 Google 的通行證嗎？」如果沒有，就算知道網址也拿不到任何資料。
- **建議**: 如果您的數據很敏感，**後端驗證是必須的**。如果只是防君子不防小人，前端驗證勉強夠用。

## 2. 多人使用與資料庫規劃 (Multi-User Support & Database)

**日期**: 2025-12-08
**狀態**: 規劃中 (Planning)

### 問題描述
目前系統使用單一檔案 `tokens.json` 儲存 Facebook Token。這意味著**所有使用者共享同一個 Token**。
如果使用者 A 設定了他的 Facebook 帳號，使用者 B 進來也會看到 A 的數據；如果 B 修改了設定，A 的數據就會被覆蓋。

### 解決方案：導入資料庫 (Database Integration)
為了讓不同使用者擁有各自的 Facebook 設定，我們需要將「Google 帳號」與「Facebook Token」綁定。

#### 架構變更
1.  **廢除 `tokens.json`**: 改用資料庫儲存。
2.  **資料表設計 (Schema)**:
    - `users` table:
        - `id`: Primary Key
        - `google_id`: Google 唯一使用者 ID (來自 Google Login)
        - `email`: 使用者 Email
        - `fb_access_token`: 該使用者的 Facebook Long-Lived Token
        - `fb_app_id`: (選填) 該使用者的 App ID
        - `fb_app_secret`: (選填) 該使用者的 App Secret (需加密儲存)

#### 流程
1.  使用者透過 Google 登入 -> 後端取得 `google_id`。
2.  使用者設定 Facebook API -> 後端將 Token 存入資料庫，並關聯到該 `google_id`。
3.  使用者查看儀表板 -> 後端根據目前的 `google_id` 去資料庫撈出對應的 Token -> 呼叫 Facebook API。

#### 技術選擇
- **開發階段**: SQLite (輕量、無需額外安裝伺服器，Python 內建支援)。
- **正式階段**: PostgreSQL (Zeabur 有提供插件，適合多人同時連線)。

## 3. 開發路線圖 (Development Roadmap)

**建議順序**: 先完成登入 (Phase 1)，再導入資料庫 (Phase 2)。
**原因**: 資料庫需要 `google_id` 作為 Key 來區分使用者。如果沒有先完成登入功能，我們就拿不到 `google_id`，資料庫也無法設計。

### Phase 1: Google 登入整合 (Google Login)
- [x] 前端：新增登入頁面，實作 Google Sign-In。
- [x] 前端：實作路由保護 (未登入導回首頁)。
- [x] 後端：(選用) 實作 Token 驗證 Middleware。
- **目標**: 確保只有登入的使用者能看到畫面，並取得使用者的 `google_id`。

### Phase 2: 資料庫導入 (Database Integration)
- [x] 後端：設計 `User` 資料表 (SQLite)。
- [x] 後端：修改 API，將 Token 存入資料庫 (綁定 `google_id`)。
- [x] 後端：修改 API，從資料庫讀取 Token。
- **目標**: 實現多使用者支援，每個人的設定互不干擾。

## 4. 安全性強化 (Security Hardening)

**日期**: 2025-12-09
**狀態**: 建議實作 (Recommended)

### 風險評估
目前 Token 以明文 (Plain Text) 儲存在 SQLite 資料庫中。若駭客取得 `facebook_dashboard.db` 檔案，即可直接竊取所有使用者的 Token。

### 解決方案：資料加密 (Data Encryption)
使用 `cryptography` 套件對敏感欄位進行加密。

- **技術**: 對稱式加密 (Symmetric Encryption)，例如 Fernet。
- **金鑰管理**: 產生一把 `ENCRYPTION_KEY`，存放在 `.env` 檔案中 (不入庫)。
- **流程**:
    [x] 寫入資料庫前：`encrypt(token, key)`
    [x] 從資料庫讀取後：`decrypt(encrypted_token, key)`

### 實作細節紀錄 (Implementation Details)
> 此區塊紀錄已執行的實作計畫與技術細節。

#### 後端依賴 (Backend Dependencies)
- 新增 `cryptography` 套件。

#### 設定檔 (Configuration)
- `.env` 檔案新增 `ENCRYPTION_KEY` (自動生成，不可公開)。

#### 驗證邏輯 (Authentication Logic)
- **Lazy Migration (無痛轉移)**: 
  - 讀取 Token 時若解密失敗 (代表是舊的明文資料)，會自動回傳原始值，確保舊使用者不受影響。
  - 寫入 Token 時一律進行加密。
- **TokenManager 改動**:
  - `save_user_token`: 加密 `long_lived_token` 與 `app_secret` 後存入資料庫。
  - `get_user_token`: 從資料庫讀取 `fb_access_token` 後解密回傳。

#### 驗證測試 (Verification)
- 已建立並執行 `test_phase4.py`。
- 確認舊的明文 Token 可正常讀取。
- 確認新寫入的 Token 在資料庫中呈現亂碼 (`gAAAA...`)，且讀取時可正確還原。

## 5. 電商儀表板移植計畫 (E-commerce Dashboard Migration)

**日期**: 2025-12-10
**參考來源**: GAS 舊專案截圖 (User Provided Image)
**目標**: 完整重現三大類指標 (通用、電商、漏斗)

### A. 通用指標 (General Metrics)
**API Fields**: `spend`, `impressions`, `reach`, `cpm`, `cpc`, `ctr`, `inline_link_clicks`
- **花費金額 (Spend)**: `spend`
- **曝光次數 (Impressions)**: `impressions`
- **觸及人數 (Reach)**: `reach`
- **連結點擊次數 (Link Clicks)**: `inline_link_clicks` (注意：使用 inline 較準確反映導外流量)
- **連結點擊率 (CTR)**: `ctr`
- **CPC (單次連結點擊成本)**: `cpc`
- **CPM (每千次廣告曝光成本)**: `cpm`

### B. 電商指標 (E-commerce Metrics)
**API Fields**: `actions`, `action_values`, `purchase_roas`
需解析 `actions` list 取得特定 action_type 的 value。

- **內容查看次數**: `actions.view_content`
- **每次加入購物車成本**: `spend / actions.add_to_cart` (需後端計算)
- **加入購物車次數**: `actions.add_to_cart`
- **加入購物車的轉換值**: `action_values.add_to_cart`
- **開始結帳次數**: `actions.initiate_checkout`
- **新增付款資訊次數**: `actions.add_payment_info`
- **購買次數**: `actions.purchase`
- **購買轉換價值**: `action_values.purchase`
- **CPA (單次購買成本)**: `spend / actions.purchase` (或使用 `cost_per_action_type`)
- **ROAS**: `purchase_roas`

### C. 漏斗指標 (Funnel Metrics)
全數需由後端計算 (Derived Metrics)，需注意分母為 0 的情況。

1.  **購買轉換率 (CVR)**
    - 公式：`actions.purchase / inline_link_clicks`
2.  **查看後購物車加入率**
    - 公式：`actions.add_to_cart / actions.view_content`
3.  **購物車購買率**
    - 公式：`actions.purchase / actions.add_to_cart`
4.  **廣告購物車流失率**
    - 公式：`1 - (actions.purchase / actions.add_to_cart)`
5.  **購物車價值實現率**
    - 公式：`action_values.purchase / action_values.add_to_cart`

### 實作規劃
1.  **Backend (`services.py`)**:
    - 擴充 API 請求欄位。
    - 實作 `_process_actions(data)` helper function，將 list 轉為 dict 以利存取。
    - 實作 `_calculate_funnel(data)` function，處理所有除法邏輯。
2.  **Frontend (`Dashboard.jsx`)**:
    - 更新 UI 佈局，將原本單一 Grid 改為三個 Section (通用、電商、漏斗)。
    - 支援不同的數值格式 (貨幣、百分比、整數)。

## 6. Analytics Page: Advanced Reporting (深度分析與報表)

**日期**: 2025-12-10
**狀態**: 需求確認 (Requirements Confirmed) -> 規劃中

### 設計目標 (Objective)
與其說是單純的 Dashboard，不如說是 **「動態報表產生器 (Dynamic Report Generator)」**。
目標是復刻並超越 GAS 工具的彈性，讓您能自由篩選、比較不同層級 (Campaign/AdSet) 的數據。

### 核心功能模組 (Core Modules)

#### 1. 設定控制台 (Control Panel)
配置於頁面左側或頂部，提供完整的篩選條件：

*   **基礎設定**:
    *   **分析層級 (Level)**: 帳號 (Account) / 行銷活動 (Campaign) / 廣告群組 (AdSet) / 廣告 (Ad)。
    *   **日期範圍 (Date Range)**: 支援「自訂日期 (Custom Date)」選擇器，而非僅限 7/30 天。
    *   **比較模式 (Comparison)**: 開關 `V.S 比較模式` (上一期 / 去年同期)。

*   **進階篩選 (Filtering)**:
    *   **關鍵字篩選**: `包含 (Include)` / `排除 (Exclude)` 關鍵字輸入框。
    *   **快速勾選**: 列出所有Active Campaign供快速勾選 (如截圖 1)。

*   **指標自訂 (Metric Toggles)**:
    *   提供 Checkbox 讓使用者決定表格要顯示哪些欄位 (通用、電商、漏斗、互動)。

#### 2. 動態數據表格 (Dynamic Data Table)
根據上方設定產生的詳細報表。

*   **Columns**: 根據「指標自訂」動態增減。
*   **Rows**: 根據「分析層級」顯示 (例如選 Campaign 就列出所有 Campaigns)。
*   **Comparison**: 若開啟 VS 模式，數值旁顯示 `(diff%)` 或用顏色標示。

#### 3. 視覺化圖表 (Visualization)
*   **Funnel Chart**: 針對篩選後的總數據繪製漏斗。
*   **Dual-Axis Trend**: 允許自選兩軸 (e.g., Spend vs ROAS) 繪製所選範圍的趨勢。

### 實作階段規劃 (Implementation Phases)

為了穩健開發，建議分三階段完成：

*   **Phase 3.1: 基礎架構 (Foundation)**
    *   建立 `/analytics` 頁面。
    *   實作「自訂日期選擇器」與「層級選擇 (Level Selector)」。
    *   後端 API 支援 `level` 與 `custom_date` 參數。
    *   先顯示預設的指標 (E-commerce + Funnel)。

*   **Phase 3.2: 篩選與搜尋 (Filtering)**
    *   實作「關鍵字篩選 (Include/Exclude)」邏輯。
    *   實作「行銷活動多選 (Campaign Multi-select)」功能。

*   **Phase 3.3: 高度客製化 (Customization)**
    *   實作「指標勾選 (Metric Toggles)」UI。
    *   前端表格動態渲染 (Dynamic Columns)。

### 技術筆記
*   **API Update**: `/api/analytics-data` 需接受 `filters (json)`, `level`, `since`, `until` 等參數。
*   **State Management**: 前端需管理較複雜的 Filter State。


### Phase 3.3 Detail: Indicator Customization (Based on user request)

**Goal**: Implement a grouped metric selector identical to the provided screenshot to allow users to customize table columns.

#### 1. UI Structure (Sidebar/Modal Component)
A collapsible section or modal "自訂表格指標欄位 (Custom Table Metric Columns)" containing 5 groups:

*   **通用指標 (General Metrics)**
    *   [x] Link Clicks (連結點擊次數)
    *   [x] Reach (觸及人數)
    *   [x] CPC (單次連結點擊成本)
    *   [x] Spend (花費金額)
    *   [x] CTR (連結點擊率)
    *   [x] CPM (每千次廣告曝光成本)
    *   [x] Impressions (曝光次數)

*   **電商指標 (E-commerce Metrics)**
    *   [x] Payment Info Added (新增付款資訊次數)
    *   [x] Add to Cart Conversion Value (加到購物車的轉換值)
    *   [x] Initiate Checkout (開始結帳次數)
    *   [x] CPA (單次購買成本)
    *   [x] Add to Cart (加到購物車次數)
    *   [x] ROAS
    *   [x] Cost per Add to Cart (每次加入購物車成本)
    *   [x] Purchase Conversion Value (購買轉換價值)
    *   [x] Purchases (購買次數)
    *   [x] Content Views (內容查看次數)

*   **漏斗指標 (Funnel Metrics)**
    *   [x] Cart Purchase Rate (購物車購買率)
    *   [x] Cart Value Realization Rate (購物車價值實現率)
    *   [x] Ad Cart Drop-off Rate (廣告購物車流失率)
    *   [x] View-to-Cart Rate (查看後購物車加入率)
    *   [x] Purchase Conversion Rate (購買轉換率)

*   **互動指標 (Engagement Metrics)**
    *   [x] Post Comments (貼文留言)
    *   [x] Post Saves (貼文儲存)
    *   [x] Post Shares (貼文分享)
    *   [x] Post Engagement (貼文互動)
    *   [x] Post Reactions (貼文心情)
    *   [x] Page Likes (粉絲專頁按讚)

*   **品質診斷 (Quality Ranking)**
    *   [x] Quality Ranking (品質排名)
    *   [x] Conversion Rate Ranking (轉換率排名)
    *   [x] Engagement Rate Ranking (互動率排名)

#### 2. Implementation Strategy

**Frontend**:
-   **State**: `selectedMetrics` (Array of strings).
-   **Component**: `MetricSelector` (accepts selection state and update function).
-   **Logic**:
    -   Table Header: Dynamically map `selectedMetrics` to `<th>`.
    -   Table Body: Dynamically map `selectedMetrics` to `<td>`.
-   **Enhancement**: "Save as Preset" button to save the current selection (localStorage).

**Backend**:
-   **Field Expansion**:
    -   Add `actions` and `action_values` processing for engagement metrics.
    -   Add `quality_ranking`, `conversion_rate_ranking`, `engagement_rate_ranking` to API request fields.
-   **Calculations**:
    -   Engagement metrics are simple sums from `actions`.
    -   Quality rankings are direct string return values (e.g., "Above Average", "Average", "Below Average 35%").

#### 3. Suggestions
-   **Presets**: Default checking "General" + "E-commerce" is recommended for quick start.
-   **Drag & Drop**: In the future, allow column reordering.

