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


## 7. Analytics Page UI Improvements (針對橫向捲動問題)

**日期**: 2025-12-10
**狀態**: 待討論 (Pending Discussion)
**問題**: 當使用者勾選過多自訂指標時，表格寬度過大，導致橫向捲動不便，且容易迷失方向 (看不到最左邊的名稱或是最右邊的數據)。

### 提案解決方案 (Proposed Solutions)

#### 方案 A: 凍結首欄 (Sticky Columns) - **推薦**
- **描述**: 將最左側的「名稱 (Name)」欄位固定 (Position Sticky)。
- **效果**: 無論橫向捲動到哪裡，都能知道現在看的是哪個行銷活動/廣告的數據。
- **技術**: CSS `position: sticky; left: 0; z-index: 10;`.

#### 方案 B: 快速視圖切換 (View Presets)
- **描述**: 在「自訂指標」區塊增加快速按鈕，例如 [只看電商]、[只看漏斗]、[精簡模式]。
- **效果**: 鼓勵使用者一次只專注在一類指標，減少同時顯示的欄位數量。

#### 方案 C: 雙軸捲動同步與樣式優化 (Scroll Sync & Styling)
- **描述**: 
    - 增加 **Sticky Header**: 表格標題列固定在頂部，垂直捲動時標題不消失。
    - **Compact Mode (緊湊模式)**: 縮小 Cell Padding，讓同樣寬度能顯示更多欄位。
    - **Scroll Shadows**: 當有內容溢出時，在邊緣顯示陰影提示。

### 建議實作步驟
1. 優先實作 **Sticky First Column** 與 **Sticky Header**，這能最直接改善體驗。
2. 調整 CSS Padding 使表格更緊湊。

#### 方案 D: 指標視圖分頁 (Metric View Tabs) - **針對「勾選過多導致過寬」的終極解法**
- **描述**: 在「自訂指標」區塊上方新增 **快速視圖按鈕 (View Tabs)**，例如：
    - `[ 📊 總覽 (Summary) ]`: 僅顯示花費、ROAS、CPA、購買數。 (最窄)
    - `[ 🛒 電商詳情 (E-commerce) ]`: 顯示加入購物車、結帳、購買等詳細流程。
    - `[ 🌪️ 漏斗分析 (Funnel) ]`: 顯示各階段轉換率。
    - `[ ⚙️ 自訂 (Custom) ]`: 允許使用者自由勾選 (即目前的模式)。
- **解決點**: 
    - 預設情境下 (總覽/電商) 表格寬度適中，不會有橫向捲動問題。
    - 當使用者需要看特定領域 (如漏斗) 時，點擊切換，**自動取消勾選**不相關的欄位，保持畫面簡潔。
    - 只有在使用者真的「全都要」時，才切換到 Custom 模式讓他自己承擔捲動責任。
- **優化勾選介面**: 將勾選區塊收合在「自訂模式」中，或是預設隱藏，避免佔用上方太多空間。

## 8. 系統架構與效能優化 (Architecture & Performance Notes)

**日期**: 2025-12-11
**主題**: 資料流向與大規模數據的潛在風險分析

### 1. 目前架構：即時暫存 (Real-time Proxy)
*   **資料流向**: Frontend (Browser) -> Backend (Python Memory) -> Facebook API
*   **儲存特性**: 
    *   **無資料庫 (No Database)**: 數據僅存在於處理請求的短暫記憶體中，未寫入硬碟。
    *   **無持久化 (No Persistence)**: 瀏覽器關閉或重新整理後，資料即消失，需重新請求。

### 2. 潛在風險 (Potential Risks)
當廣告量級極大 (e.g., > 10,000 Ads) 時可能遇到的瓶頸：
1.  **Network Latency (網路延遲)**: 
    *   目前採 Full-Fetch (一次抓全量)，若資料量大，等待時間可能超過 10~30 秒。
    *   可能觸發 HTTP Timeout (通常 60s)。
2.  **API Rate Limiting (API 限制)**:
    *   Facebook API 有呼叫頻率限制。頻繁全量拉取可能導致 `(#17) User request limit reached`。
3.  **Browser Performance (瀏覽器效能)**:
    *   前端一次渲染數千列 DOM (TableRow) + 數千張圖片縮圖，會大量消耗 Client 端記憶體，導致頁面卡頓。

### 3. 優化策略 (Optimization Strategies)
若未來遇到效能瓶頸，建議依序採取的優化方案：
1.  **分頁機制 (Pagination) [High Priority]**: 
    *   改為 On-Demand Fetching，一次只抓第一頁 (e.g., 50 筆)。
    *   大幅降低單次 API 負載與前端渲染壓力。
2.  **快取機制 (Caching)**: 
    *   後端實作 TTL Cache (e.g., 5分鐘內相同請求直接回傳記憶體舊資料)。
    *   減少重複呼叫 Facebook API。
3.  **資料庫導入 (Database)**:
    *   僅在需要「跨長期歷史分析」或「複雜交叉比對」時才考慮引入。

## 9. 協作廣告指標 (Collaborative Ads / CPAS Metrics)

**日期**: 2025-12-11
**狀態**: 待實作 (Pending Implementation)

### 協作廣告簡介 (Overview)
協作廣告 (Collaborative Ads, CPAS) 允許品牌商使用零售商 (Retailer) 的目錄 (Catalog) 投放廣告，並追蹤在零售商網站上的轉換。

### 關鍵指標與 API 欄位 (Key Metrics & Fields)

協作廣告的指標主要透過 `catalog_segment_value` 與 `catalog_segment_actions` 來獲取，或是透過特定的 breakdown。但在一般的 Marketing API 報表中，最核心的關注點在於「歸因於協作目錄的轉換」。

#### A. 核心轉換指標 (Core Conversion Metrics)
這些指標與一般電商指標類似，但數據來源是「零售商分享的目錄」。

*   **Catalog Sales (目錄銷售)**:
    *   `actions` list 中 `action_type` 為 `omni_purchase` 或 `purchase`。
    *   需確認是否需過濾 `action_device`, `action_canvas_component_name` 等。
*   **Shared Catalog Purchase Value (目錄銷售金額)**:
    *   `action_values` list 中 `action_type` 為 `omni_purchase` 或 `purchase`。
*   **Add to Cart (加入購物車)**:
    *   `mobile_app_add_to_cart` 或 `add_to_cart`。
*   **View Content (查看內容)**:
    *   `view_content`。
*   **Shared Items Purchases (共享項目購買次數)**:
    *   對應 API: `catalog_segment_actions` -> `action_type: purchase`
    *   意義: 歸因於該協作目錄商品的購買次數。
*   **Shared Items Purchase Value (僅限共享項目的購買轉換值)**:
    *   對應 API: `catalog_segment_value` -> `action_type: purchase`
    *   意義: 購買共享項目的總金額。
*   **Shared Items Purchase ROAS (共享項目的購買 ROAS)**:
    *   計算公式: `Shared Items Purchase Value` / `Spend`
    *   意義: 廣告花費在推廣共享項目上的投資報酬率。
*   **Shared Items Adds to Cart (將共享項目加到購物車的次數)**:
    *   對應 API: `catalog_segment_actions` -> `action_type: add_to_cart`
    *   意義: 使用者將共享商品加入購物車的次數。
*   **Shared Items Add to Cart Conversion Value (僅限共享項目的加到購物車轉換值)**:
    *   對應 API: `catalog_segment_value` -> `action_type: add_to_cart`
    *   意義: 加入購物車的共享商品總價值。
*   **Shared Items Content Views (含有共享項目的內容瀏覽次數)**:
    *   對應 API: `catalog_segment_actions` -> `action_type: view_content`
    *   意義: 使用者瀏覽共享商品詳情頁的次數。

#### B. 協作特定欄位 (CPAS Specific Fields)
若要區分「自有官網」與「協作零售商」的成效，通常需要查看：

1.  **Catalog Segment Statistics (目錄分眾統計)**:
    *   `catalog_segment_value`: 顯示各目錄分眾 (Segment) 的轉換價值。
    *   `catalog_segment_actions`: 顯示各目錄分眾的轉換次數。
    *   這對於同時與多家零售商 (如 Shopee, Momo) 合作時非常重要，可區分業績來自哪個通路。

2.  **Breakdowns (細分)**:
    *   雖然 API 不直接支援 `breakdowns=retailer_id`，但可透過 Campaign Name 命名規則或 Tag 來區分。
    *   若使用 Graph API，可嘗試 `catalog_segment_id` breakdown (需驗證)。

### 建議實作方向 (Implementation Plan)

1.  **API 请求擴充 (`services.py`)**:
    *   新增欄位: `catalog_segment_value`, `catalog_segment_actions`。
2.  **前端顯示 (`Dashboard.jsx` / `Analytics.jsx`)**:
    *   在「電商指標」群組中，新增一個子群組 "CPAS (Collaborative)"。
    *   顯示 "Retailer Sales (通路銷售額)" 與 "Retailer ROAS"。
3.  **濾掉重複數據**:
    *   注意 CPAS 數據可能會與 Pixel 數據混淆（若 Pixel 埋設不當）。但在 API 層級，`catalog_segment` 開頭的欄位通常是專屬於目錄銷售的。

### 備註 (Notes)
*   Facebook API 對於協作廣告的權限控管較嚴格，需確保 User Token 擁有該 Catalog 的讀取權限。
*   部分細節指標可能需要 `read_insights` 之外的權限。

## 10. 進階趨勢比較圖表 (Trend Comparison Charts) (✅ Implemented v1.4.0)

**日期**: 2025-12-11
**狀態**: 已完成 (Completed)

### 功能概述 (Overview)
提供一個可互動的趨勢圖表，允許使用者同時比較兩個不同的指標 (如 Spend vs ROAS) 的歷史趨勢，以分析成效波動。

### 核心功能 (Core Features)
1.  **動態指標選擇 (Dynamic Metrics)**:
    *   下拉選單自動包含所有目前數據表中選用的指標 (e.g., CPAS Metrics, Funnel Metrics)。
    *   自動加入 "Core Metrics" (Spend, Purchases, ROAS...) 以確保基礎分析能力。
2.  **雙座標軸 (Dual Axis)**:
    *   左軸 (Left Axis): 柱狀圖/區域圖 (Bar/Area) 呈現量級指標 (如 Spend, Impressions)。
    *   右軸 (Right Axis): 線圖 (Line) 呈現比率或趨勢指標 (如 ROAS, CTR)。
3.  **智慧座標同步 (Smart Axis Scaling)**:
    *   當選擇同質性指標 (如 Purchases vs Add to Cart) 時，自動同步左右軸的最大值，避免視覺誤導。
    *   異質指標 (如 Spend vs ROAS) 保持獨立座標軸。
4.  **比較模式 (Comparison Mode)**:
    *   支援顯示上一期 (Previous Period) 數據（虛線呈現）。
5.  **手機優化 (Mobile Optimization)**:
    *   響應式設計，自動調整控制項排列與圖表高度。

## 11. SaaS 商業化架構藍圖 (SaaS Commercialization & User Management)

**日期**: 2025-12-11 (Updated 2025-12-12)
**主題**: 多人協作、權限管理與商業化架構設計

### 1. 核心目標 (Core Objective)
從目前的「單人/無狀態」工具，轉型為支援「多人協作」與「訂閱制」的商業化平台 (B2B SaaS)。

### 2. 架構演進 (Architecture Evolution)

*   **Phase 1: 單人版 (Current)**
    *   `User` (Google ID) -> `Token` (Local DB)
    *   缺點：資料無法雲端同步，無法多人共管。
*   **Phase 2: 多人管理 (User Management)** (Technical Foundation)
    *   引入 PostgreSQL 資料庫。
    *   建立 `User` 資料表：儲存 Name, Email, Role, Status。
    *   實現 RBAC (Role-Based Access Control)：Admin vs Viewer。
*   **Phase 3: 團隊協作 (Team Workspaces)** (Commercial Feature)
    *   引入 `Workspace` (Team) 概念。
    *   **Token 共享**：團隊 Admin 綁定一次 FB Token，所有成員皆可使用。
    *   **權限隔離**：成員登入後進入特定工作區，數據互不干擾。

### 3. 資料庫設計 (Database Schema)

*   **`users`**:
    *   `id` (UUID), `email`, `name`, `avatar_url`
*   **`teams`** (New):
    *   `id` (UUID), `name`, `owner_id`
    *   `fb_token` (Encrypted, Shared)
    *   `subscription_plan` (Free/Pro)
*   **`team_members`** (Relation):
    *   `team_id`, `user_id`, `role` (Admin/Editor/Viewer)

### 4. 功能規劃 (Features)

#### 後端 (Backend)
1.  **Auth System**: 升級為 Session/JWT based auth，支援多租戶 (Multi-tenant) 檢查。
2.  **Team API**: 支援 邀請成員 (Invite)、移除成員、切換工作區。
3.  **Audit Logs**: 記錄誰修改了廣告設定 (商業版重要功能)。

#### 前端 (Frontend)
1.  **Admin Portal**: 「成員管理」頁面，顯示列表與權限設定。
2.  **Workspace Switcher**: Header 新增工作區切換下拉選單。
3.  **Subscription Page**: 整合 Stripe 結帳頁面 (預備)。

### 5. 開發階段 (Phasing)

1.  **Phase 1 - DB & Auth**: 建立 PostgreSQL 與 User Table，完成 Google Login 的資料庫綁定。
2.  **Phase 2 - Team Logic**: 實作 Team/Member 關聯與 Token 共享邏輯。
3.  **Phase 3 - UI/UX**: 完成成員管理介面與權限防護。

## 12. Phase 5: SaaS Multi-Tenant Architecture (SaaS 多租戶架構)

**日期**: 2025-12-12
**狀態**: 已確認需求 (Requirements Confirmed) -> 規劃中
## 12. Phase 5: Hybrid SaaS Architecture (混合式 SaaS 架構)

**日期**: 2025-12-13
**狀態**: ✅ 已完成 (Completed) - v1.5.0
**核心理念**: **「個人優先，團隊為輔 (Individual First, Team Optional)」**

### 1. 用戶模型 (User Model)
*   **預設狀態 (Independent)**: 每個註冊用戶都是獨立的個體。
    *   擁有自己的 `fb_access_token` (存在 `users` 表)。
    *   預設進入 **「個人工作區 (Personal Workspace)」**。
    *   可以看到自己的廣告數據。

### 2. 團隊協作機制 (Team Collaboration Mechanics)

#### A. 邀請方式 (Invitation Method)
*   **方法**: **邀請連結 (Invite Link)**。
*   **流程**:
    1.  A (團隊管理員) 在後台點擊「產生邀請連結」。
    2.  系統產生一個帶有 Token 的 URL (e.g., `.../invite?code=xyz`).
    3.  A 將連結複製傳給 B (Line/Slack/Email)。
    4.  B 點擊連結 -> Google 登入 -> 系統自動將 B 加入該團隊。
    5.  **安全機制**: 連結預設 **24小時後失效**，過期需重新產生。
    *   **狀態**: ✅ 已實作 (Implemented)

#### B. 數據權限 (Data Visibility)
*   **核心邏輯**: **Token 繼承 (Token Inheritance)**。
*   **答案**: **是的，B 可以看到 A 設定的廣告帳號。**
*   **運作原理**:
    *   當 A 設定好團隊的 Facebook Token 後，這個 Token 是綁定在 `Team` 物件上的。
    *   當 B 切換到這個團隊時，後端 API 統一使用該 `Team` 的 Token 去向 Facebook 要資料。
    *   **結果**: B 不需要擁有自己的 Facebook 廣告帳號，他只是「透過 A 的授權」來查看數據。這正是企業版協作的核心價值。
    *   **安全性**: B (若為一般成員) **無法修改/移除** 這個 Token，只有 A (管理員) 可以。
    *   **狀態**: ✅ 已實作 (Implemented)

### 3. 超級管理員 (Super Admin)
*   **全域管理**: 創始人擁有一個獨立的分頁 (Admin Portal)。
*   **功能**:
    *   條列所有註冊用戶 (User List)。
    *   條列所有已建立的團隊 (Team List)。
    *   管理用戶狀態 (停權/刪除)。
    *   **狀態**: ✅ 已實作基礎版 (Basic Implementation)

### 4. 介面呈現 (UI Presentation)
*   **Header Switcher**:
    *   預設選項: `👤 個人工作區 (My Workspace)`
    *   其他選項: `🏢 行銷部 A 組 (Marketing Team A)`
*   **Settings**:
    *   在個人工作區時，設定的是 `User Token`。
    *   在團隊工作區時，設定的是 `Team Token` (僅 Admin 可見)。
    *   **狀態**: ✅ 已實作 (Implemented)

這個架構保留了 Phase 1 的簡單性 (註冊即用)，同時疊加了 Phase 5 的團隊擴充性。

## 13. 角色與權限階級制度 (Role Hierarchy & Permissions)

**日期**: 2025-12-13
**狀態**: ✅ 已實作 (Implemented)

本系統採用 **雙層級權限架構**：系統層級 (System Level) 與 團隊層級 (Team Level)。

### 1. 系統層級 (System Level)
決定使用者對整個平台的控制權。

*   **SUPER ADMIN (超級管理員)**
    *   **定義**: 系統的最高管理者 (System God)。
    *   **權限**:
        *   可存取 `/admin` 儀表板。
        *   可查看系統中所有使用者 (All Users) 與所有團隊 (All Teams)。
        *   可強制刪除任何使用者帳號。
        *   **不受團隊權限限制** (即便是非成員也能查看團隊資訊)。
    *   **目前帳號**: `tabchen2005@gmail.com`

*   **USER (一般使用者)**
    *   **定義**: 註冊進來的普通成員。
    *   **權限**: 僅能管理自己的個人資料、建立團隊、或接受邀請加入團隊。

### 2. 團隊層級 (Team Level)
當使用者進入特定團隊 (Workspace) 後，適用該團隊的角色規則。

*   **OWNER (團隊擁有者)**
    *   **定義**: 團隊的創建者。
    *   **特性**:
        *   **不可被移除**: 擁有至高無上的地位，即便是其他管理員也無法將其踢出。
        *   **最高權限**: 可解散團隊、管理所有成員。
        *   **繼承**: 自動擁有 ADMIN 的所有權限。

*   **ADMIN (團隊管理員)**
    *   **定義**: 由 Owner 指派的協助管理者。
    *   **權限**:
        *   **邀請成員**: 可產生邀請連結。
        *   **移除成員**: 可將 MEMBER 或其他 ADMIN 踢出團隊 (但在系統中帳號保留)。
        *   **編輯角色**: 可調整成員的權限 (e.g., 升級 Member 為 Admin)。
        *   **Token 管理**: 可設定團隊共用的 Facebook Token。
    *   **限制**: **無法移除 OWNER**。

*   **MEMBER (一般成員)**
    *   **定義**: 被邀請加入團隊的協作者。
    *   **權限**:
        *   **唯讀**: 只能查看數據 (Dashboard, Analytics)。
        *   **隱藏**: 看不到「成員管理」頁面中的操作按鈕 (Delete/Edit)。
        *   **被動**: 無法管理 Token，使用的是團隊共享的 Token。

### 3. 設計哲學備忘 (Design Philosophy Note)

**Q: 為什麼團隊擁有者不能「停用 (Suspend)」成員的帳號？**

*   **設計邏輯**: 
    *   **權限範圍 (Scope)**: 團隊擁有者的權限僅限於「該團隊」內部。
    *   **多重身分**: 一個使用者可能同時屬於多個團隊，或者是平台的付費會員。如果 A 團隊擁有者可以「停用」某人的帳號，將導致該成員無法登入平台，進而影響他參與 B 團隊或使用個人功能的權益。
    *   **正確做法**: 若不希望某成員存取團隊資料，直接將其「**移除 (Remove)**」出團隊即可。
    *   **停用權限**: 請參閱 [1. 系統層級] -> **SUPER ADMIN**，只有超級管理員才有權限執行平台層級的帳號停權。

## 14. 超級管理員後台 2.0 (Admin Dashboard 2.0)
**日期**: 2025-12-14
**狀態**: ✅ 已完成 (Completed)

針對超級管理員後台介面優化，已完成下列改進：

1.  **介面風格統一 (UI Unification)**:
    *   移除舊版 Tab 分頁設計，改為「單頁式垂直滾動 (Single View)」。
    *   全面套用 **Glassmorphism (玻璃擬態)** 風格，與 `TeamSettings` 一致。
    *   表格與卡片採用半透明背景與深色表頭。

2.  **使用者體驗優化 (UX Enhancement)**:
    *   **即時搜尋 (Search)**: 為「所有使用者 (All Users)」與「所有團隊 (All Teams)」新增搜尋欄，支援即時過濾。
    *   **智慧分頁 (Pagination)**: 當資料超過 10 筆自動分頁，並整合搜尋結果。
    *   **國際化 (i18n)**: 支援中/英雙語切換，預設為繁體中文 (Traditional Chinese)。

3.  **技術細節**:
    *   移除 Tailwind Class，改用 Vanilla CSS (Inline Styles) 以避免樣式衝突。

## 15. 團隊廣告帳號隔離機制 (Team Ad Account Isolation)
**日期**: 2025-12-14
**狀態**: 🚧 規劃中 (Planning)

**需求背景**:
目前團隊綁定 Facebook Access Token 後，系統會列出該 Token 權限下「所有」的廣告帳號。
但在團隊協作情境中，我們不希望團隊成員看到 Owner 個人或其他不相關的廣告帳號。

**解決方案 (Solution)**:
建立「廣告帳號白名單 (Whitelist)」機制。

### 1. 資料庫設計 (Schema Change)
需新增一個關聯表或是欄位來儲存「團隊」與「廣告帳號」的對應關係。
*   **Table**: `team_ad_accounts` (或在 `teams` 表中新增 JSON 欄位 `visible_ad_account_ids`)
*   **Columns**:
    *   `team_id` (FK)
    *   `ad_account_id` (String, e.g., "act_12345678")
    *   `ad_account_name` (Snapshot string)

### 2. 運作邏輯 (Logic Flow)
1.  **授權 (Auth)**: Team Owner 完成 Facebook 授權。
2.  **擷取 (Fetch)**: 後端從 FB API 抓回該 Token 能看到的所有帳號 (e.g., 20 個帳號)。
3.  **過濾 (Filter)**:
    *   **預設**: 抓回來的帳號列表，預設對團隊是「不可見 (Hidden)」或是尚未選取。
    *   **設定**: Team Owner 進入「團隊設定」->「廣告帳號管理」，勾選「這個團隊可以操作這些帳號：[A, B, C]」。
4.  **展示 (Display)**:
    *   當團隊成員 (Admin/Member) 進入 Dashboard，前端呼叫 API 時。
    *   後端只回傳「被勾選 (Whitelisted)」的 [A, B, C] 帳號資訊。

### 3. UI 介面
*   新增「廣告帳號選擇器 (Ad Account Selector)」：複選 Checkbox List。
*   位置：`TeamSettings` -> `General` 或獨立的 `Ad Accounts` 分頁。



## 16. 部署問題與解決方案 (Deployment Issues & Solutions)
**日期**: 2025-12-14
**狀態**: ✅ 已解決 (Resolved)

在本次 2025-12-14 的正式機部署與團隊功能測試中，發現並修復了以下三個關鍵問題。

### 1. 資料庫結構同步問題 (Schema Drift)
*   **症狀**: 建立團隊時發生 `500 Internal Server Error`，Log 顯示 `UndefinedColumn: visible_ad_account_ids`。
*   **原因**: 正式機資料庫使用舊版 Schema 建立，缺少了新功能所需的欄位 (`fb_access_token`, `visible_ad_account_ids`)。
*   **解法**:
    1.  緊急：在 `main.py` 加入「自動 Schema 修補 (Auto-Patching)」邏輯，啟動時自動檢測並 `ALTER TABLE` 新增遺失欄位。
    2.  長遠：建立了 `docs/database_migration_guide.md`，未來應嚴格遵守 Alembic Migration 流程。

### 2. 邀請頁面無限登入循環 (Infinite Login Loop)
*   **症狀**: 使用者點擊「登入並接受」，登入 Google 後又跳回邀請頁，按鈕仍顯示「登入並接受」，無法完成加入。
*   **原因**: 變數命名不一致。
    *   `Login.jsx` 將 Token 存為 `google_token`。
    *   `InvitePage.jsx` 卻檢查 `id_token`。
*   **解法**: 統一前端所有頁面使用 `google_token`。

### 3. 廣告帳號選單空白 (Empty Ad Account Selector)
*   **症狀**: 團隊擁有者進入「團隊設定」要勾選廣告帳號時，選單顯示空白。但 Dashboard 的下拉選單卻有資料。
*   **原因**:
    *   新團隊建立時沒有 `fb_access_token`。
    *   後端邏輯嘗試使用「團隊 Token」去抓取列表，結果為空。
    *   雖然有 fallback 到 Owner，但程式誤判「您不是 Owner」或是「Owner 個人 Token 抓取失敗」。
*   **解法**: 
    1.  實作 **「雙重保險 (Double Fallback)」** 機制。
    2.  優先強制使用 Owner 的 **User Token** 抓取 (最乾淨)。
    3.  若失敗，自動退回使用 **Team Token Logic** (後備)。
    4.  修正權限判斷，確保 Owner 絕對不會被白名單過濾器擋住。

### 4. 跨團隊權限洩漏 (Cross-Team Token Leak)
*   **症狀**: 當新建立團隊的 Owner (尚未綁定 FB) 進入設定頁時，竟然看到平台管理員 (Super Admin) 的廣告帳號列表。
*   **原因**: `TokenManager.get_user_token` 有一個設計用於協作的「Admin Fallback」機制 (若找不到 Token 就借用 Admin 的)。這在「設定團隊」場景下是不適當的，造成資料洩漏。
*   **解法**:
    1.  引入 `strict_token` (嚴格模式) 參數。
    2.  在團隊設定頁面抓取帳號時，強制開啟嚴格模式，禁止借用 Admin Token。
    3.  確保 Owner 若無 Token，就真的看到空白列表 (Empty State)，而非錯誤的資料。

### 5. 前端狀態錯亂 (Frontend Race Condition)
*   **症狀**: 快速切換團隊 (A -> B) 時，B 團隊的設定頁面短暫顯示 A 團隊的權限設定。
*   **原因**: 前端 `localStorage` 的更新速度慢於頁面載入速度。API 請求時使用了舊的 `Team ID` (從 Storage 讀取)，導致後端回傳了舊團隊的資料。
*   **解法**: 修改 `TeamService` 與 `AdAccountSelector`，強制在 API 請求時傳入當前頁面的 `teamId` 作為 Header，不再依賴全域 Storage 狀態。

## 17. 手機版使用者體驗優化 (Mobile Experience Optimization)
**日期**: 2025-12-15
**狀態**: ✅ 已完成 (Completed) - v1.5.1

針對日益增長的手機端管理需求，進行了全站的響應式改版與行為優化。

### 1. 智慧側邊欄 (Smart Sidebar)
*   **問題**: 舊版側邊欄在手機上佔用空間，且切換工作區後不會自動收合，遮擋視線。
*   **解法**:
    *   **Auto-Collapse**: 實作自動收合邏輯。當使用者點擊「導覽連結」、「工作區切換」、「建立團隊」等動作時，Sidebar 自動隱藏。
    *   **Z-Index Fix**: 修復圖層堆疊問題，確保 Sidebar 高於 Header，但低於 Modal。

### 2. 表頭個人選單 (Header Profile Menu)
*   **問題**: 受限於 Header 的 `overflow: hidden` 與 `backdrop-filter` 屬性，下拉選單無法延伸到 Header 之外，且點擊外部無法順利收合。
*   **解法 (React Portal)**:
    *   使用 `React.createPortal` 將下拉選單直接渲染到 `document.body` (Root Level)。
    *   徹底解決 CSS Stacking Context 問題。
    *   實作全螢幕透明遮罩 (Backdrop)，點擊畫面任意處皆可關閉選單。

### 3. 團隊設定頁面 (Responsive Team Settings)
*   **問題**: 表格在手機寬度下會造成橫向捲動，且 Padding 過大導致內容擠壓。
*   **解法**:
    *   **Card View**: 成員列表在手機版自動切換為「卡片式佈局 (Card View)」，垂直排列資訊。
    *   **Adaptive Padding**: 根據螢幕寬度動態調整頁面邊距 (48px -> 16px)。

### 4. 系統穩定性 (System Stability)
*   **Super Admin Check**: 修復本地開發環境下，因 Session 快取導致 Super Admin 選單偶發性消失的問題。
*   **Auto-Refresh**: 修復 API Key 設定後，Ad Account 列表未自動刷新的 UX 瑕疵。

## 18. 進階指標客製化系統 (Advanced Metric Customization System)
**日期**: 2025-12-15
**狀態**: 🚀 規劃中 (Future Roadmap)
**參考**: FB Ads Manager Column Customization (User Screenshots)

為了滿足不同產業用戶（電商、App、影音、名單）的多元需求，將從目前的「硬編碼指標」轉型為「模組化指標庫」。

### 1. 核心概念 (Core Concepts)
*   **指標超市 (Metric Library)**: 
    *   建立一個完整的指標定義檔 (JSON/DB)，包含分類 (Category)、API 欄位 (Field Key)、顯示名稱 (Label)、計算公式 (Formula)。
    *   不再預設載入所有數據，而是讓用戶「進超市挑選」。
*   **動態抓取 (Dynamic Fetching)**:
    *   後端 API (`services.py`) 需重構，不再使用固定的 `base_fields`。
    *   改為接收前端傳來的 `requested_fields` 陣列，動態組裝 Facebook API URL。
    *   **優點**: 大幅降低 API 負載，只抓需要的資料。

### 2. 功能模組 (Features)

#### A. 自訂欄位視窗 (Customize Columns Modal)
*   **介面參考**: 類似 Facebook 廣告後台的「自訂直欄」視窗。
*   **功能**:
    *   **搜尋 (Search)**: 支援關鍵字搜尋 (e.g., "ROAS", "Cost").
    *   **分類瀏覽**: 左側導航列 (Performance, Engagement, Conversions, Settings).
    *   **拖排序 (Drag & Drop)**: 右側面板顯示「已選欄位」，允許拖曳調整順序。
    *   **全選/全消**: 針對特定分類的快速操作。

#### B. 儲存視圖 (Saved Views / Presets)
*   **痛點解決**: 避免用戶每次都要重新勾選 20 個指標。
*   **功能**:
    *   **Save as Preset**: 將目前的欄位配置儲存為「我的最愛 (e.g., 老闆週報, 影片成效)」。
    *   **Set as Default**: 設定某個 Preset 為登入後的預設值。
    *   **預設範本**: 系統內建幾款經典範本 (E-commerce Default, Video Engagement, App Growth)。

### 3. 技術實作建議 (Technical Strategy)
1.  **Frontend**:
    *   擴充 `MetricSelector` 元件，從單純的 Popover 改為 Modal 形式。
    *   實作 `ColumnOrder` state 管理欄位順序。
2.  **Backend**:
    *   實作 `MetricRegistry` class，管理 Field Mapping。
    *   API `/api/analytics/report` 新增參數 `metrics=["spend", "video_p75_watched_actions", ...]`.

### 4. 預期效益
*   **高彈性**: 完美適應各種非電商產業 (Gaming, B2B)。
*   **高效能**: 減少不必要的資料傳輸與處理。
*   **SaaS 化基礎**: 這是邁向通用型行銷工具的關鍵一步。

## 19. 用戶教育與支援系統 (User Education & Support System)
**日期**: 2025-12-15
**狀態**: 🚀 規劃中 (Future Roadmap)

為了降低 SaaS 產品的使用門檻，建立一套分層級的教學引導系統。採用 **「混和模式 (Hybrid Model)」**：

### 1. 核心架構 (Core Architecture)

#### A. 獨立教學中心 (Dedicated Help Center) - *深度學習*
*   **入口**: 左側 Sidebar 新增 `📘 使用指南 (Help)`。
*   **形式**: 靜態頁面 (Static Page) 為主，無需複雜 CMS。
*   **內容規劃**:
    1.  **快速入門 (Quick Start)**: 如何註冊、取得 FB Token、連結廣告帳號。
    2.  **團隊協作 (Collaboration)**: 如何邀請成員、權限說明。
    3.  **常見問題 (FAQ)**: 數據更新頻率？為什麼數據對不上？

#### B. 情境式提示 (Contextual Tooltips) - *即時解惑*
*   **痛點**: 用戶看到 "ROAS", "CPM" 不懂意思。
*   **實作**: 在專有名詞旁新增 `(i)` 或 `?` 小圖示。
*   **互動**: 滑鼠懸停 (Hover) 或點擊時，顯示簡易定義。
    *   *e.g., "ROAS: 廣告投資報酬率 (購買價值 / 花費)"*

### 2. 實作階段 (Implementation Phases)

#### Phase 1: 靜態內容 (Static Content) - **推薦優先執行**
*   **技術**: 直接將教學內容寫在前端 Component 中 (Hardcoded or Markdown files)。
*   **優點**: 開發極快，零維護成本，適合內容變動不頻繁的初期階段。
*   **缺點**: 修改文字需重新部署 (Acceptable for MVP)。

#### Phase 2: 動態 CMS (Dynamic CMS) - **未來擴充**
*   **時機**: 當文章數量超過 50 篇，或需要非技術人員維護時。
*   **技術**: 串接 Headless CMS (e.g., Strapi, Contentful) 或自建後台。

### 3. 未來優化 (Future Enhancements)
*   **Onboarding Tour**: 新用戶第一次登入時的「逐步教學導覽 (Step-by-step Walkthrough)」。
*   **Video Tutorials**: 嵌入 30秒短影片教學。

## 20. AI 智慧投手引擎 (AI Intelligence Engine)
**日期**: 2025-12-15
**狀態**: 🧪 創新實驗 (Experimental / Future)
**目標**: 將產品從「被動的報表工具」升級為「主動的 AI 廣告顧問」。

### 1. 三階段演進 (Three-Phase Evolution)

#### Phase 1: 診斷報告 (The Analyst) - **MVP 起點**
*   **概念**: 「一鍵體檢」。
*   **流程**: 用戶點擊「分析本週成效」 -> 後端撈取數據 -> 整理成 JSON -> 送給 LLM (GPT-4o/Gemini) -> 產生文字報告。
*   **能解決的問題**:
    *   **素材疲乏 (Ad Fatigue)**: "廣告 A 的頻率超過 3.0 且 CTR 正在下降，建議更換素材。"
    *   **受眾飽和**: "CPM 上漲 40% 但轉換率不變，競爭變激烈了。"

#### Phase 2: 對話助手 (The Copilot)
*   **概念**: 隨身數據助理 (Chatbot)。
*   **情境**: 用戶問「為什麼昨天 ROAS 掉了？」，AI 自動比對昨天 vs 前天數據，回答「主要是 CPM 暴漲導致」。
*   **技術**: RAG (Retrieval-Augmented Generation) + Function Calling (讓 AI 呼叫我們的 API 查數據)。

#### Phase 3: 自動巡航 (The Autopilot) - **SaaS Pro Feature**
*   **概念**: 24小時自動盯盤。
*   **功能**: 結合自動化規則 (Automation Rules)。
    *   *e.g., "如果 CPA > $50 且 ROAS < 1.0，自動關閉該廣告組。"*

### 2. 技術考量 (Technical Considerations)
*   **隱私 (Privacy)**: 送往 LLM 的數據需進行去識別化 (移除 User ID, Account ID)，僅保留數據趨勢與廣告名稱特徵。
*   **成本 (Cost)**: LLM Token 成本較高，需作為加值付費功能 (Add-on)。
*   **模型**: 建議使用具備強大推理能力的模型 (e.g., GPT-4o, Claude 3.5 Sonnet) 以確保分析精準度。

## 21. 隱藏受眾挖掘器 (Hidden Interest Discovery)
**日期**: 2025-12-15
**狀態**: 🚀 規劃中 (Future Roadmap)
**價值**: 提供 FB 官方介面未顯示的「長尾興趣」，幫助用戶尋找藍海受眾，降低 CPM。

### 1. 核心功能 (Core Features)
*   **關鍵字擴充搜尋**: 
    *   使用者輸入單一關鍵字 (e.g., "Golf")。
    *   系統呼叫 API 列出所有 500+ 個相關標籤 (官方後台通常只顯示前 25 個熱門選項)。
*   **數據透視**: 即時顯示每個興趣的 **受眾規模 (Audience Size)** 與 **路徑 (Topic Path)**。
*   **一鍵複製**: 用戶勾選心儀的「小眾標籤」後，複製 ID 或名稱，貼回 FB 後台或直接在本平台建立廣告組。

### 2. 技術原理 (Technical)
*   **API Endpoint**: `GET /search`
    *   Parameters: `type=adinterest`, `q={keyword}`, `limit=1000`.
    *   也可使用 `targetingvalidation` 確認標籤有效性。
*   **權限需求**: 使用現有的標準 User Access Token 即可，無需額外審查。
*   **應用場景**: 作為強大的 **Lead Magnet (引流工具)**，吸引免費戶註冊使用，再轉化為付費會員。

 
 