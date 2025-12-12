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

## 11. 使用者帳號管理系統規劃 (User Management System Planning)

**日期**: 2025-12-11
**主題**: 多人協作與權限管理架構設計

若要從目前的「單人/無狀態」模式擴展為「多使用者管理系統」，需要引入資料庫與權限控制機制。

### 1. 架構變更 (Architecture Changes)

*   **資料庫 (Database)**:
    *   **必要性**: 必須引入資料庫來儲存使用者資料、角色與設定。
    *   **建議方案**:
        *   **SQLAlchemy + SQLite (初期)**: 輕量、無需額外伺服器，適合 MVP。
        *   **PostgreSQL (後期)**: 若需部署到 Cloud (如 Zeabur) 且有多個實例 (Scale out)，則需獨立 DB。
*   **資料模型 (User Model)**:
    *   `id`: UUID
    *   `email`: String (Unique)
    *   `name`: String
    *   `role`: Enum (`admin`, `member`, `viewer`)
    *   `status`: Enum (`active`, `suspended`)
    *   `last_login`: DateTime
    *   `created_at`: DateTime

### 2. 功能模組 (Features)

#### 後端 (Backend)
1.  **Authentication & Authorization**:
    *   擴充 `dependencies.py`，加入 `get_current_active_user` 與 `check_admin_role`。
    *   JWT Token Payload 加入 `role` 欄位。
2.  **User CRUD API**:
    *   `GET /users`: 取得使用者列表 (Admin only)。
    *   `POST /users`: 邀請/新增使用者 (Admin only)。
    *   `PUT /users/{id}`: 修改角色或停用帳號 (Admin only)。
    *   `DELETE /users/{id}`: 刪除帳號。

#### 前端 (Frontend)
1.  **Admin Portal (管理後台)**:
    *   新增 `/settings/users` 頁面。
    *   **使用者列表表格**: 顯示頭像、姓名、Email、角色、狀態、最後登入時間。
    *   **操作功能**:「新增成員」、「編輯權限」、「停用/啟用」。
2.  **Role-Based UI (權限控管)**:
    *   **Admin**: 擁有完整權限。
    *   **Viewer**: 僅能查看報表 (`Analytics`), 無法執行「產生報表」或「匯出圖片」等耗能操作 (可設定)。

### 3. 實作階段 (Phasing)

1.  **Phase 1: DB 初始化**: 設定 SQLAlchemy 與 Alembic (Migration)，建立 User Table。
2.  **Phase 2: Seed Admin**: 系統啟動時自動建立第一位超級管理員 (Super Admin)。
3.  **Phase 3: 後台介面**: 開發前端管理介面。
4.  **Phase 4: 權限鎖定**: 將敏感 API (如 `delete`, `settings`) 加上 Admin Check 裝飾器。
