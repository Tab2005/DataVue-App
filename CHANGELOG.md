# Changelog

## v1.6.4 (2025-12-31) - AI Search Intent Classifier

### New Features
- **🔮 AI Intent Classifier**:
    - Added `AIIntentClassifier` class in `backend/services/ai/intent_classifier.py` for classifying search query intents using AI models.
    - Supports 4 intent types: Informational (資訊型), Commercial (商業型), Navigational (導航型), Transactional (交易型).
    - Uses Zeabur AI Hub (Gemini 2.5 Flash by default) for intelligent classification.
    - Returns intent distribution percentages and confidence scores for each query.
    - Designed for future integration with GSC page analysis to show page-level search intent.

### 新功能
- **🔮 AI 搜尋意圖分類器**：
    - 新增 `AIIntentClassifier` 類別於 `backend/services/ai/intent_classifier.py`，使用 AI 模型分類搜尋關鍵字意圖。
    - 支援 4 種意圖類型：資訊型、商業型、導航型、交易型。
    - 使用 Zeabur AI Hub（預設 Gemini 2.5 Flash）進行智慧分類。
    - 回傳各意圖分布比例與信心分數。
    - 設計用於未來整合至 GSC 頁面分析，顯示頁面層級的搜尋意圖。

### Files Added
- `backend/services/ai/intent_classifier.py` - AI Intent Classifier core module

---

## v1.6.3 (2025-12-31) - Cost Per Outbound Click KPI Card Fix

### Fixed
- **🔧 Cost Per Outbound Click Not Showing in KPI Cards**:
    - Fixed an issue where "Cost Per Outbound Click" metric displayed correctly in the data table but showed `$0` in KPI summary cards.
    - **Root Cause**: In `backend/async_services.py`, the `METRICS_REGISTRY` incorrectly mapped `outbound_clicks` as `'source': 'actions'`, but Facebook API returns it as a **direct field** (array format), not as an action type.
    - **Solution**: Changed `outbound_clicks` mapping from `{'source': 'actions', 'action_type': 'outbound_click'}` to `{'source': 'direct', 'fb_field': 'outbound_clicks'}`.
    - Added `outbound_clicks` to default API fields and frontend's `essentialMetrics` list.

### 修復
- **🔧 單次外連點擊成本 KPI 圖卡無法顯示數據**：
    - 修復了「單次外連點擊成本」指標在數據表格正常顯示，但在 KPI 圖卡顯示 `$0` 的問題。
    - **根本原因**：`backend/async_services.py` 中的 `METRICS_REGISTRY` 錯誤地將 `outbound_clicks` 映射為 `'source': 'actions'`，但 Facebook API 實際上是以**獨立欄位**（陣列格式）回傳此數據。
    - **解決方案**：將 `outbound_clicks` 的映射從 `{'source': 'actions'}` 改為 `{'source': 'direct', 'fb_field': 'outbound_clicks'}`。
    - 同時將 `outbound_clicks` 加入後端預設 API 欄位與前端的 `essentialMetrics` 列表。

---
## v1.6.2 (2025-12-31) - Analytics Cost Metrics Enhancement

### New Features
- **📊 Expanded Cost Metrics**:
    - Added comprehensive Cost & Spend metrics to Analytics dashboard: `CPP` (Cost per 1,000 People Reached), `Cost Per Unique Click`, `Cost Per Inline Link Click`, `Cost Per Outbound Click`, `Cost Per Conversion`, `Cost Per ThruPlay`.
    - Removed `Social Spend` metric as per user request (marked as unused in system).
- **🧮 Enhanced Metric Reliability**:
    - **Backend Calculation Fallback**: Implemented manual calculation logic for cost metrics (e.g., `Spend / Unique Clicks`) in `metrics.py` and `async_services.py`.
    - This ensures valid data values are displayed in the table even when the direct Facebook API field returns null or missing data.

### Fixed
- **🔧 Missing Table Data**:
    - Fixed an issue where new cost metrics appeared correctly in KPI cards but showed as empty/dash in the data table.
    - Root cause: `get_custom_report` in `async_services.py` was missing the mapping logic for these specific new metrics in the row processing loop.
    - Solution: Added explicit calculation and mapping for all new cost metrics in the table row generation logic.

### 新功能
- **📊 成本指標擴充**：
    - 在分析儀表板中新增完整的成本數據：`CPP` (每千人觸及成本)、`單次不重複點擊成本`、`單次連結點擊成本`、`單次外連點擊成本`、`單次轉換成本`、`單次 ThruPlay 成本`。
    - 應需求移除 `社交互動花費` 指標 (系統標記為不使用)。
- **🧮 指標可靠性提升**：
    - **後端計算備援**：在 `metrics.py` 與 `async_services.py` 中實作了成本指標的手動計算邏輯 (如 `花費 / 不重複點擊`)。
    - 確保即使 FB API 直接欄位回傳空值，表格仍能顯示有效的計算數值。

### 修復
- **🔧 表格數據遺失**：
    - 修復了新成本指標在 KPI 卡片顯示正常，但在數據表格中顯示為空/橫線的問題。
    - 原因：`async_services.py` 中的 `get_custom_report` 處理每列數據時，遺漏了這些新指標的映射邏輯。
    - 解決方案：在表格列生成邏輯中補上所有新成本指標的明確計算與映射。

---

## v1.6.1 (2025-12-30) - Permission System Bug Fixes & Token Status Enhancement

### Fixed
- **🔧 Google ID Mismatch Issue**:
    - Fixed critical login failure caused by mismatched `google_id` in database vs current Google account.
    - Root cause: User lookup by `google_id` failed, system tried to create new user, but email unique constraint blocked it.
    - Solution: Updated `google_id` in database to match current login credentials.

- **🔧 SQLAlchemy NULL Comparison**:
    - Fixed `UserModuleAccess.team_id == None` comparison using `.is_(None)` for proper SQL NULL handling.
    - Applied fix to both `dependencies.py` and `permission_service.py`.

- **🔧 Super Admin Module Access**:
    - Added direct Super Admin bypass at API endpoint level (`/me/module/{key}`) to ensure immediate access without PermissionService queries.

- **🔧 Deployment Permission Data**:
    - Integrated automatic permission seeding (`seed_permissions`) into backend startup sequence to ensure missing roles/modules are populated on deployment (Zeabur).

### New Features
- **✨ Token Existence Indicator**:
    - API `/api/auth/token-status` now returns `token_exists` field (checks if `fb_access_token` has actual content).
    - Frontend shows warning "⚠️ 權杖資料不同步" when expiration date exists but token is missing.
    - Helps users identify data sync issues between expiration date and actual token.

### 修復
- **🔧 Google ID 不匹配問題**：
    - 修復因資料庫 `google_id` 與當前 Google 帳號 ID 不一致導致的登入失敗。
- **🔧 SQLAlchemy NULL 比較**：
    - 修正 `team_id == None` 的 SQL NULL 比較語法錯誤。
- **🔧 Super Admin 模組存取**：
    - 在 API 端點層級新增直接 Super Admin bypass。
- **🔧 部署環境權限資料**：
    - 將權限初始化腳本 (`seed_permissions`) 整合至後端啟動流程，修復部署環境 (Zeabur) 缺失系統模組與角色的問題。

### 新功能
- **✨ 權杖存在性指示器**：
    - Token Status API 新增 `token_exists` 欄位。
    - 前端顯示警告當到期日期存在但權杖遺失的資料不同步狀況。

---

## v1.6.0 (2025-12-29) - Permission & Access Control System


### New Features
- **🔐 Permission Management System**:
    - Modular permission architecture for FB Ads, GSC, GA4 modules.
    - 6 new database models for roles, permissions, and module access.
    - PermissionService class with check/grant/revoke methods.
    - 14 new API endpoints for permission management.

- **👤 Super Admin Dashboard - Permissions Tab**:
    - View system modules, permissions, and roles.
    - Expandable module details showing all permissions.
    - User Module Manager: Grant/revoke module access for users.

- **🛡️ Module Access Control**:
    - `require_module` decorator for API protection.
    - GSC API now requires 'gsc' module access.
    - Auto-grant default modules (fb_ads, gsc) for new users.

- **⚛️ Frontend Permission Hooks**:
    - `useModuleAccess` - Check if user can access a module.
    - `usePermission` - Check if user has a specific permission.
    - `useUserModules` / `useUserPermissions` - Get all user permissions.
    - `<ProtectedModule>` / `<ProtectedPermission>` components.

### 新功能
- **🔐 權限管理系統**：
    - 模組化權限架構（FB Ads, GSC, GA4）。
    - 6 個新資料庫模型：模組、權限、角色等。
    - PermissionService 類別：檢查/授予/撤銷權限。
    - 14 個新 API 端點。

- **👤 超級管理員後台 - 權限管理 Tab**：
    - 檢視系統模組、權限和角色。
    - 使用者模組授權管理：開通/關閉模組存取。

- **🛡️ 模組存取控制**：
    - GSC API 現在需要 'gsc' 模組權限。
    - 新使用者自動獲得預設模組權限。

- **⚛️ 前端權限 Hooks**：
    - `useModuleAccess`, `usePermission` 等 4 個 Hook。
    - `<ProtectedModule>` 路由保護組件。

### Files Added/Modified
- Backend: `database.py`, `dependencies.py`, `routers/permissions.py`, `services/permission_service.py`
- Frontend: `hooks/usePermission.js`, `components/PermissionManager.jsx`, `components/UserModuleManager.jsx`

---

## v1.5.8 (2025-12-29) - GSC Country & Device Distribution

### New Features
- **🌍 Country Distribution Tab**:
    - Traffic breakdown by country/region.
    - 80+ countries translated to Chinese names.
    - Visual share percentage bar chart.
    - Sortable by clicks, impressions, CTR.
- **📱 Device Distribution Tab**:
    - Card-based visual layout (not table).
    - Mobile (green), Desktop (blue), Tablet (orange).
    - Percentage bars with animations.
    - CTR and position stats per device.

### 新功能
- **🌍 地區分佈 Tab**：
    - 按國家/地區的流量分佈。
    - 80+ 國家中文翻譯。
    - 視覺化佔比進度條。
- **📱 裝置分佈 Tab**：
    - 卡片式視覺設計。
    - 手機（綠色）、桌機（藍色）、平板（橙色）。
    - 百分比進度條 + 動畫效果。

---

## v1.5.7 (2025-12-29) - GSC Page Trends & Title Enhancement

### New Features
- **📊 Page Trends Tab**:
    - New tab for comparing page performance between current and previous periods.
    - Sub-tabs: 頂層 (Top) / 走勢向上 (Trending Up) / 走勢向下 (Trending Down).
    - Shows percentage change with color indicators (green ↑ / red ↓).
- **Real Page Titles**:
    - Backend API `POST /api/gsc/page-titles` scrapes actual `<title>` tags from URLs.
    - Displays real page titles in Page Analysis and Page Trends tabs.
    - Falls back to URL-extracted title if scraping fails.
- **Top/Bottom Indicators**:
    - Top 5 pages highlighted in green 🏆, Bottom 5 in red ⚠️.
- **Core Keywords per Page**:
    - Each page shows its top 5 associated keywords with clicks/impressions.
    - Expandable row to view detailed keyword list.
- **Date Range Fix**:
    - "Last 7 days" now correctly shows the 7 complete days before today.

### 新功能
- **📊 頁面趨勢 Tab**：
    - 新增頁面趨勢分頁，比較本期與前期的表現變化。
    - 子分頁：頂層 / 走勢向上 / 走勢向下。
    - 顯示百分比變化及顏色標示（綠色 ↑ / 紅色 ↓）。
- **真實頁面標題**：
    - 後端 API 抓取網頁實際 `<title>` 標籤。
    - 頁面分析與趨勢 Tab 顯示真實標題。
- **Top/Bottom 標示**：
    - Top 5 頁面綠色 🏆，Bottom 5 紅色 ⚠️。
- **頁面核心關鍵字**：
    - 每個頁面顯示關聯的 Top 5 關鍵字及點擊/曝光數。
- **日期範圍修正**：
    - 「過去 7 天」現正確顯示今天之前的完整 7 天。

---

## v1.5.6 (2025-12-29) - GSC Keyword & Page Analysis

### New Features
- **GSC Tab Navigation**:
    - Added 3 analysis tabs: 📈 Daily Performance, 🔍 Keyword Analysis, 📄 Page Analysis.
    - Each tab uses different GSC API dimensions (`date`, `query`, `page`).
- **Keyword Analysis**:
    - Top keywords ranking table with sortable columns (Clicks, Impressions, CTR, Position).
    - Keyword search/filter input.
    - Row limit selector (Top 50/100/200).
- **Keyword Grouping** 📦:
    - Toggle button to group similar keywords together.
    - Similarity algorithm: Jaccard word overlap + substring detection.
    - Expandable/collapsible group rows with aggregated statistics.
    - +N badge showing additional keywords in each group.
- **Page Analysis**:
    - Top pages ranking with clickable URLs (opens in new tab).
    - URL auto-simplified display (removes domain prefix).

### 新功能
- **GSC 分頁導航**：
    - 新增 3 個分析分頁：📈 每日成效、🔍 關鍵字分析、📄 頁面分析。
- **關鍵字分析**：
    - 熱門關鍵字排行表格，支援欄位排序。
    - 關鍵字搜尋篩選與數量限制選擇器。
- **關鍵字群組功能** 📦：
    - 一鍵將類似關鍵字歸為一組，可展開/收合查看。
    - 群組顯示總點擊數與總曝光數。
- **頁面分析**：
    - 頁面 URL 可點擊跳轉，自動簡化顯示。

---

## v1.5.5 (2025-12-29) - Google Search Console Deployment Fix

### Fixed
- **GSC Deployment Error (405 → 500)**:
    - **Root Cause 1 (405)**: GSC components (`GSCConnect.jsx`, `GSCStats.jsx`, `SearchConsole.jsx`) were using relative API paths (`/api/gsc/...`) instead of `VITE_API_URL`. In production, these requests hit the static frontend server instead of the backend API.
    - **Root Cause 2 (500)**: Missing `GOOGLE_CLIENT_SECRET` environment variable on Zeabur backend, required for OAuth token exchange.
    - **Fix**: Updated 3 frontend files to use `VITE_API_URL` and documented `GOOGLE_CLIENT_SECRET` as required in `.env.example`.
- **GSC 部署錯誤修復**:
    - **原因 1 (405)**：GSC 元件使用相對路徑而非 `VITE_API_URL`，導致請求打到前端靜態伺服器。
    - **原因 2 (500)**：Zeabur 後端缺少 `GOOGLE_CLIENT_SECRET` 環境變數。
    - **修復**：更新 3 個前端檔案使用 `VITE_API_URL`，並在 `.env.example` 中新增 `GOOGLE_CLIENT_SECRET` 說明。

---

## v1.5.4 (2025-12-23) - View Management Optimization

### New Features
- **View Edit/Rename**:
    - Added ability to edit and rename saved metric views directly in Metrics Manager.
    - New edit modal allows modifying view name and adjusting selected metrics.
    - Backend: New `PATCH /api/saved-views/{view_id}` API endpoint with authorization check.
- **視角編輯/重新命名**:
    - 在指標管理頁面新增編輯已儲存視角功能。
    - 新的編輯視窗可修改視角名稱及調整選取的指標。
    - 後端：新增 `PATCH /api/saved-views/{view_id}` API 端點，含權限檢查。

---

## v1.5.3 (2025-12-19) - Analytics Data Accuracy & UI Simplification

### Fixed
- **KPI Calculation Accuracy**:
    - **Backend Derived Metrics**: Refactored `_format_kpi` to manually calculate ROAS, CPA, CPC, CTR from base values instead of relying on potentially missing API aggregations.
    - **Purchase Value Backfill**: Added fallback logic to calculate `purchase_value` from `ROAS * Spend` when the API returns ROAS but not purchase value.
    - **Essential Metrics**: Frontend now always requests core base metrics (`spend`, `impressions`, `link_clicks`, `purchases`, `purchase_value`) regardless of user selection, ensuring derived calculations work correctly.
    - **Async Service Sync**: Fixed `async_services.py` missing `frequency`, `unique_clicks`, and video metrics in both API request fields and data processing. This was the root cause of these metrics showing 0 despite being available from Facebook API.

### Changed
- **Analytics Page Simplification**:
    - **View Presets**: Reduced fixed view tabs from 5 to 2 (Summary + Custom). Removed E-commerce, Engagement, and Funnel presets - users can create these via Metrics Manager.
    - **Tab Order**: Repositioned AI Analysis button directly after Custom tab, before saved views.
- **Metrics Manager**:
    - **UI Cleanup**: Removed "Default/Extended" badges and technical format/source badges from metric cards.
    - **Default Metrics**: Only 10 "General" category metrics are now set as default, providing a cleaner starting state.
    - **Grid Layout**: Adjusted to 5 columns per row for optimal density.
    - **Unified Groups**: Merged extended metrics directly into main categories without "(Extended)" suffix.

### Improved
- **Mobile Responsiveness (Metrics Manager)**:
    - Action buttons now use horizontal scroll instead of stacking.
    - Saved view names truncate with ellipsis to prevent layout breaking.
    - Category tabs use horizontal scroll.
    - Reduced font sizes and padding for compact mobile display.


### Improvements
- **Mobile Experience**:
    - **Smart Sidebar**: 
        - Sidebar now automatically collapses when switching workspaces, creating new teams, or navigating to pages on mobile devices.
        - Fixed `z-index` layering issue where the mobile sidebar blocked the header's workspace switcher.
    - **Responsive Team Settings**:
        - Optimized padding and layout for Team Settings page on mobile.
        - **Card View**: Replaced the wide user table with a vertical "Card View" for `UserManagement` on mobile screens to prevent horizontal scrolling.
    - **Header Profile Menu**:
        - **Portal Implementation**: Re-engineered the user dropdown menu using `React Portal`. This resolves `z-index` and clipping issues caused by backdrop filters, ensuring the menu covers the entire screen and closes reliably when clicking anywhere outside.

### Fixed
- **Local Environment**:
    - **Super Admin Visibility**: Resolved an issue where Super Admin menus were hidden in local development environments due to stale user session checking logic.
- **Workflow**:
    - **Auto-Refresh**: Fixed a bug where Ad Accounts list wouldn't automatically refresh after a user successfully set their Facebook API key.

## v1.5.0 (2025-12-13) - Hybrid SaaS Architecture & Team Management
### New Features
- **Team Management System**:
    - **CRUD Operations**: Support for Creating, Updating (with rename), and Disbanding teams.
    - **Cascade Deletion**: safely removes all associated members and invite links when a team is disbanded.
- **Invitation System**:
    - **Secure Links**: Generate time-limited (24h) invitation links for easy team onboarding.
    - **Role Assignment**: Automatically assigns 'Member' role to joined users.
- **Role-Based Access Control (RBAC)**:
    - **Dual Hierarchy**: Implemented System-Level (Super Admin) vs. Team-Level (Owner, Admin, Member, Viewer) roles.
    - **Permission Barriers**: UI elements (e.g., Delete Button, Invite Button) hide/disable based on user role.
- **API Connection Manager**:
    - **Context Aware**: 'API Settings' modal now intelligently switches between "Personal Token" and "Team Token" modes based on active workspace.
    - **Token Inheritance**: Team members automatically inherit access to the Team's Facebook Token without needing their own ad account access.

### Improvements
- **Localization**:
    - **Bilingual Alerts**: Critical system alerts (e.g., "Final Warning" before team deletion) now support English/Chinese switching.
- **Stability**:
    - **Windows Compatibility**: Fixed a major server crash caused by Unicode Emoji characters (`ℹ️`, `🚀`) in console logs on Windows environments.

## v1.4.3 (2025-12-12) - Facebook Token Expiration Notification
- **New Feature**:
    - **Token Expiration Warning**: Implemented a notification system to alert users when their Facebook Access Token is expiring within 3 days.
    - **Header Integration**: Added a "Red Dot" indicator to the Bell icon in the header.
    - **Interactive Notification**: Clicking the bell opens a dropdown with a warning message that links directly to re-authentication.
    - **"Mark as Read" Logic**: The red dot automatically disappears after the user opens the notification menu, persisting the read state locally until the day count changes.
- **Backend**:
    - **Database Migration**: Added `token_expires_at` column to `users` table with auto-migration support.
    - **Token Logic**: Updated authentication flow to capture and store absolute expiration timestamps.
    - **API**: New endpoint `/api/auth/token-status` to fetch expiration status.

## v1.4.2 (2025-12-12) - Stability & Mobile UX
- **Stability**:
    - **Crash Fix**: Resolved a critical "Black Screen" crash in the Analytics page caused by a reference error (`summaryData` vs `currentSummaryData`) during KPI card rendering.
- **Mobile Experience**:
    - **KPI Header**: Optimized the "Metrics Overview" header for mobile devices.
        - Implemented a flexible wrapping layout (`flex-wrap`) to allow the date range to sit next to the title when space permits.
        - Reduced font size for date ranges on mobile to conserve screen space.
        - Improved date format in Comparison Mode to clearly show Current vs Previous periods on separate lines if needed.
- **UI Improvements**:
    - **Date Display**: Enhanced the KPI section to explicitly show the comparison date range (e.g., `2025-12-05 ~ 2025-12-11 vs 2025-11-28 ~ 2025-12-04`) when in Comparison Mode.

## v1.4.1 (2025-12-12) - Metrics Organization & Table Enhancements
- **Metrics Refinement**:
    - **General Metrics**: Reordered sequence (Spend -> CPM -> Link Clicks) and simplified names (CPC/CPM).
    - **E-commerce Metrics**: Reordered to match funnel flow (ROAS -> Purchases -> ... -> View Content removed).
    - **Funnel Metrics**: Reordered (View to Cart -> Cart Dropoff).
    - **Renaming**: Changed "Key Metrics Overview" to "Metrics Overview" (指標總覽).
- **Table Functionality**:
    - **Sorting**: Implemented clickable column headers to toggle ascending/descending sort.
    - **Table Header**: Added visual sort indicators (arrows) and active state styling.
- **UI/UX Improvements**:
    - **Column Width**: Adjusted first column (Name) width to 200px.
    - **Readability**: Enabled multi-line text wrapping (max 2 lines) for long names in the first column.

## v1.4.0 (2025-12-11) - Trend Comparison Chart
- **New Feature**: Added collapsible "Trend Comparison Chart" section to Analytics page.
- **Dynamic Metrics**: Chart dropdowns now dynamically include any metrics selected in the data table (e.g., CPAS, Funnel metrics).
- **Comparison Mode**: Visualizes "vs Previous Period" trends with dashed lines.
- **Smart Axis Scaling**: Automatically synchronizes Y-axis scales when comparing similar metric types (e.g., Purchases vs Add to Cart) to prevent misleading visuals.
- **Mobile Optimization**: Responsive layout for Trend Chart controls (vertical stacking, full-width dropdowns) on smaller screens.
- **Backend Upgrade**: Updated `/api/analytics-trend` to calculate all available system metrics on a daily basis.

## v1.3.7 (2025-12-11) - Collaborative Ads (CPAS) Metrics & Dynamic Headers
- **New Metrics**: Added "Collaborative Ads" category with 6 key metrics:
    - Shared Purchases, Shared Purchase Value, Shared ROAS, Shared ATC, Shared ATC Value, Shared View Content.
- **Dynamic Table Headers**: 
    - 數據表格第一欄標題現在會根據選擇的層級 (Campaign/AdSet/Ad/Account) 自動切換顯示名稱 (e.g., Campaign Name, AdSet Name)。
- **Backend**: Enhanced `get_custom_report` to process `catalog_segment_value` and `catalog_segment_actions`.
- **Frontend**: Updated Metric Selector and Summary logic to support CPAS data.

## v1.3.6 (2025-12-11)
### Added
- **Mobile Responsiveness**:
    - **Sidebar**: Mobile overlay mode with backdrop.
    - **Header**: Responsive layout with hamburger menu.
    - **Dashboard**: Responsive KPI grid (1 column on mobile) and control panel.
    - **Analytics**: Responsive filter toolbar and table (scrollable).
- **Mobile UX**: Swapped Title with Account Selector on mobile for better usability.

## [v1.3.5] - 2025-12-11
### Added
- **Advanced Filtering**: 新增「進階篩選」工具列。
  - **Keyword Search**: 支援關鍵字搜尋 (包含/排除)。
  - **Active Only**: "只看快篩" 功能，一鍵過濾僅顯示目前投放中的廣告。
- **KPI Export**: 
  - **Image Export**: 支援將「關鍵指標總覽」區塊匯出為 PNG 圖片 (包含日期與亂數檔名)。
- **Backend Stability**: 
  - 優化 API 請求邏輯，針對不同層級 (Account vs Ad) 動態調整抓取欄位 (`effective_status`)，解決 Fetch Error。

## [1.3.4] - 2025-12-11
### Added
- **Quality Diagnosis**: 
  - 新增「品質診斷 (Quality Diagnosis)」指標分類，包含品質排名、轉換率排名、互動率排名。
  - Backend API 更新：支援抓取 Ad Quality Ranking 相關欄位。
- **Metric Groups**: 
  - 全面調整指標分類 (E-commerce, Funnel) 以符合設計需求，加入 `Add Payment Info` 等新指標。

### Fixed
- **Metric Sync**: 
  - 修正「自訂指標」與「KPI 卡片」及「表格欄位」不同步的問題。
  - 實作 Group-Scoped Selection (Composite Keys)，解決跨群組同名指標 (e.g., Purchases) 的選取衝突。
  - 確保切換 View Presets 時能正確映射到各分組指標。

## [1.3.3] - 2025-12-11
### Added
- **Ad Creative Thumbnails**: 
  - **Table View**: 廣告層級 (Ad Level) 表格新增素材縮圖顯示。
  - **Hover Preview**: 滑鼠懸停顯示 300px 高解析度素材預覽圖 (Portal Implementation)。
  - **Backend**: 優化 `services.py` 優先抓取 HQ Image URL，解決縮圖模糊問題。
- **Metric Controls**: 
  - **Bulk Actions**: 自訂指標選單新增「全選 / 全消 (Select All / Deselect All)」快速操作功能。

### Fixed
- **Comparison Data**: 
  - 修正 Comparison Mode 下，Campaign/AdSet/Ad 層級抓不到前期數據 (顯示為 0) 的問題。
  - 原因：Backend 回傳通用 `id` 導致 Frontend ID Matching 失敗。
  - 解法：Backend 明確回傳 `campaign_id`, `adset_id`, `ad_id` 以供精確比對。
- **Naming Logic**: 
  - 修正 Ad/AdSet 層級報表名稱錯誤顯示為 Campaign Name 的問題 (Backend Name Priority Fix)。
- **Formatting**: 
  - **Overview Cards**: 將「花費 (Spend)」與其他金額指標調整為整數顯示 (無小數點)，提升閱讀性 (CPA 保留小數位)。

## [v1.5.2] - 2025-12-16
### Improved
- **API Settings UI**: Added real-time token expiration display (Date & Days Remaining) in the Settings Modal for better visibility.
- **API 設定介面**: 在設定視窗中新增即時權杖到期日顯示（日期與剩餘天數），方便用戶確認連線狀態。

## [1.3.2] - 2025-12-10
### Added
- **Analytics UI**: 
  - **View Tabs**: 新增指標視圖分頁功能 (總覽 / 電商 / 漏斗 / 自訂)，快速切換不同分析場景。
  - **Engagement Metrics**: 新增「互動指標」分類，支援 6 種關鍵互動數據 (貼文留言, 儲存, 分享, 互動, 心情, 粉絲頁按讚)。
  - **Compact Mode**: 優化表格排版，縮減儲存格間距，解決寬度溢出問題。
  - **Sticky Header**: 表格標頭固定功能，提升長列表閱讀體驗。
- **Logic**:
  - **Dynamic Limits**: 實作「單一分類最多 7 個指標」的動態限制機制，防止版面過寬。
  - **Auto-Logout**: 新增 Token 過期自動偵測機制 (401 Error Handling)，失效時自動導回登入頁。

### Changed
- **Analytics Presets**:
  - **Summary View**: 調整預設指標與 Dashboard Overview 一致 (含 Impressions, Link Clicks, CTR, CPC, Spend, Purchases, ATC, ROAS)。
  - **E-commerce View**: 更新預設指標為 7 項核心電商數據 (依漏斗順序排列)。
- **User Experience**: 優化錯誤訊息提示，當指標選擇超過限制時給予明確反饋。

## [1.3.1] - 2025-12-10
### Added
- **Analytics KPI Cards**: 新增關鍵指標總覽卡片 (通用、電商、漏斗指標)。
- **Custom Metric Selector**: 實作自訂指標欄位選擇器，支援連動控制 KPI 卡片與表格欄位顯示。
- **Funnel Metrics**: 後端新增漏斗指標計算 logic (View-to-Cart, Cart Purchase Rate, Cart Value Realization)。

### Changed
- **UI Layout**: 調整 Analytics 頁面佈局，將 KPI Cards 移至主要設定與表格之間。

## [1.3.0] - 2025-12-10
### Added
- **Localization**: 全站中英文語系切換 (Global Language Switch) - 支援 Header, Sidebar, Dashboard, Analytics。
- **User Interface**: 
  - 新增 **User Dropdown Menu** (使用者頭像下拉選單)。
  - 實作 **Logout Functionality** (登出與 Session 清除)。
  - 實作使用者資訊持久化 (顯示 Google 頭像與名稱)。
- **Analytics**: 
  - 建立 Analytics 頁面基礎架構 (Control Panel, Date Presets, Comparison Toggle)。
  - 響應式側邊欄 (Collapsible Sidebar)。

### Fixed
- **Bug**: 修正 Dashboard 重新整理後數據消失 ("No Data") 的問題 (Frontend Data Parsing)。
- **Bug**: 修正 Trends Chart 無法顯示數據的問題 (Dynamic `dataKey` fix)。
- **Bug**: 修正 Analytics 頁面在部署環境跳出 "Local Network Access" 警告的問題 (移除 Hardcoded URL)。
- **UX**: 修正 User Info 在重新整理後恢復預設值的問題 (LocalStorage Persistence)。

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
