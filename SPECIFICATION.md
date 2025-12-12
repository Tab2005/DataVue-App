# Facebook Dashboard Web App - 專案規格書 (Project Specification)

> **Version**: v1.4.3
> **Last Updated**: 2025-12-12

## 1. 專案概述 (Project Overview)
本專案為一個高效能的 Facebook 廣告數據儀表板，旨在提供行銷人員一個整合、視覺化且具備深度分析能力的監控平台。系統整合了 Google Login 與 Facebook Graph API，支援跨帳號管理、自訂指標分析、漏斗視圖與長期趨勢比較。

---

## 2. 技術架構 (Tech Stack)

### 前端 (Frontend)
- **框架**: React 18
- **建置工具**: Vite
- **語言**: JavaScript (ES6+)
- **樣式**: CSS Modules / Inline Styles (Glassmorphism 半透明玻璃擬態風格)
- **圖表庫**: Recharts (支援雙軸、組合圖表)
- **圖標庫**: React Icons (Feather Icons)
- **其他**: React Router (路由), React OAuth Google (登入)

### 後端 (Backend)
- **框架**: FastAPI (Python 3.9+)
- **伺服器**: Uvicorn (ASGI)
- **ORM**: SQLAlchemy
- **資料庫**: 
  - **Local**: SQLite (`facebook_dashboard.db`)
  - **Production**: PostgreSQL (Zeabur default)
- **API 整合**: Facebook Graph API v24.0
- **加密**: Fernet (Cryptography) 對稱式加密，用於保護 FB Access Tokens。

---

## 3. 系統架構圖 (System Architecture)

```mermaid
graph TD
    User[使用者] -->|Google Login| FE[React Frontend]
    FE -->|API Request (Bearer Token)| BE[FastAPI Backend]
    
    subgraph "Backend Services"
        BE -->|Auth & Token Mgmt| DB[(SQL Database)]
        BE -->|Data Processing| Service[Facebook Service]
        Service -->|Graph API Requests| FB[Facebook API]
        
        DB <-->|Read/Write Encrypted Tokens| Crypto[Encryption Module]
    end
    
    subgraph "Features"
        FE -->|v1.4 Token Notification| Header[Header Alert]
        FE -->|v1.3 Analytics| Analytics[Advanced Analytics Page]
        FE -->|v1.2 Overview| Dashboard[Performance Dashboard]
    end
```

---

## 4. 核心功能 (Core Features)

### 4.1 認證與授權 (Authentication)
- **Google OAuth 2.0 Integration**: 安全的第三方登入。
- **Long-Lived Token Exchange**: 支援將短期 FB Token 自動交換為 60 天長期 Token。
- **Token Expiration Notification**: (v1.4.3 New)
  - 系統自動偵測 Token 過期時間。
  - **Header Notification**: 剩餘 3 天內於 Header 鈴鐺顯示紅點警示。
  - **Interactive Alert**: 點擊鈴鐺可查看過期天數並快速跳轉重登。

### 4.2 廣告帳號管理 (Ad Account Management)
- **Auto-Discovery**: 自動列出使用者權限下的所有廣告帳號。
- **Context Switching**: 下拉選單即時切換帳號上下文 (Global Context)，所有頁面數據同步更新。

### 4.3 數據儀表板 (Dashboard)
- **Performance Overview**: 8-Grid 卡片佈局，顯示關鍵指標 (Spend, ROAS, Purchases 等)。
- **Comparison View**: 支援與上一期 (Previous Period) 進行同時段比對，顯示數值差異 (`Diff`) 與百分比變化 (`Change %`)。
- **Daily Trend Chart**: 每日花費與成效趨勢圖。

### 4.4 進階分析 (Advanced Analytics)
- **Deep Dive Reporting**: 支援 Account / Campaign / AdSet / Ad 四種層級的數據報表。
- **Custom Metrics**: 支援四大類指標切換：
  - **General**: Spend, Impressions, CPM, CTR, Link Clicks, CPC.
  - **E-commerce**: ROAS, Purchases, CPA, Purchase Value.
  - **Funnel**: View Content, Add to Cart (ATC), Initiate Checkout, Add Payment Info.
  - **Collaborative Ads (CPAS)**: Shared Purchases, Shared ROAS, Shared ATC.
- **Funnel Vision**: 自動計算漏斗轉換率 (View to Cart, Cart Conversion Rate, Cart Dropoff)。
- **Smart Filtering**: 表格內建關鍵字篩選與欄位排序功能。
- **Comparison Trend Chart**: 雙軸線圖，可疊加比較兩個不同指標 (e.g., Spend vs ROAS) 的每日走勢，並支援虛線顯示同期比較。

### 4.5 行動裝置優化 (Mobile UX)
- **Responsive Design**: 全站適配手機版面。
- **Adaptive Components**:
  - 用戶選單與導航欄自動摺疊為漢堡選單。
  - 表格支援橫向捲動 (Horizontal Scroll)。
  - KPI 卡片自動調整為單欄顯示。

---

## 5. 數據指標定義 (Metrics Definition)

後端 `FacebookService` 統一處理以下指標計算：

| Category | Metrics | Notes |
| :--- | :--- | :--- |
| **General** | Spend, Impressions, Reach, CPM, CPC, CTR, Link Clicks | 基礎成效指標 |
| **E-commerce** | Purchases, Purchase Value, ROAS, CPA | 電商核心指標 |
| **Funnel** | View Content, Add to Cart, Initiate Checkout, Add Pay Info | 購物車漏斗 |
| **Engagement** | Post Comments, Shares, Saves, Reactions, Page Likes | 貼文互動 (v1.3.2) |
| **Diagnosis** | Quality Ranking, Engagement Ranking, Conversion Ranking | 廣告品質診斷 (v1.3.4) |
| **CPAS** | Shared Purchases, Shared Purchase Value, Shared ROAS, Shared ATC | 協作廣告指標 (v1.3.7) |
| **Derived** | View to Cart (%), Cart Conversion (%), Cart Dropoff (%) | 後端計算之衍生轉換率 |

---

## 6. API 規格 (API Endpoints)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **Auth** | | |
| `GET` | `/api/auth/token-status` | **[New]** 取得目前的 FB Token 過期狀態與剩餘天數。 |
| `POST` | `/api/auth/exchange-token` | 交換 Long-Lived Token 並加密儲存。 |
| **Account** | | |
| `GET` | `/api/ad-accounts` | 取得使用者可存取的廣告帳號列表。 |
| **Reporting** | | |
| `GET` | `/api/dashboard-data` | 取得 Dashboard 頁面的總覽 KPI 與簡單圖表。 |
| `GET` | `/api/analytics-data` | 取得 Analytics 頁面的詳細報表 (支援 Level, Date Range)。 |
| `GET` | `/api/analytics-trend` | 取得 Analytics 頁面的詳細趨勢圖數據 (含同期比較)。 |

---

## 7. 資料庫設計 (Database Schema)

### Table: `users`
| Column | Type | Description |
| :--- | :--- | :--- |
| `google_id` | `VARCHAR` (PK) | Google 使用者唯一識別碼 |
| `email` | `VARCHAR` | 使用者 Email |
| `fb_access_token` | `VARCHAR` | **[Encrypted]** FB Long-Lived Token |
| `fb_app_id` | `VARCHAR` | FB App ID |
| `fb_app_secret` | `VARCHAR` | **[Encrypted]** FB App Secret |
| `token_expires_at` | `DATETIME` | **[New]** Token 到期時間 (UTC) |

---

## 8. 環境佈署 (Deployment)

### 環境變數 (.env)
- **Backend**:
  - `DATABASE_URL`: 資料庫連線字串 (PostgreSQL / SQLite)。
  - `GOOGLE_CLIENT_ID`: 用於驗證前端傳來的 Google Token。
  - `ENCRYPTION_KEY`: 用於加解密 Access Token 的對稱金鑰。
- **Frontend**:
  - `VITE_API_URL`: 後端 API 位址。
  - `VITE_GOOGLE_CLIENT_ID`: Google OAuth Client ID。

### 部署平台
- **Zeabur**: 專案預設部署平台。
  - Frontend: Static Site Hosting.
  - Backend: Dockerized Service.
  - Database: PostgreSQL Service.

---

> **Note**: 本規格書反映截至 v1.4.3 版本的功能狀態。未來開發應以本規格書為基準進行擴充。
