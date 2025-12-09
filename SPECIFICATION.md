# Facebook Dashboard Web App - 專案規格書 (Project Specification)

## 1. 專案概述 (Project Overview)
本專案為一個 Facebook 廣告數據儀表板，旨在提供使用者一個簡單的介面來查看其 Facebook 廣告帳號的關鍵績效指標 (KPI) 和趨勢圖表。系統包含前端網頁介面與後端 API 服務，並支援多語系 (繁體中文/英文)。

## 2. 技術架構 (Tech Stack)

### 前端 (Frontend)
- **框架**: React 18
- **建置工具**: Vite
- **語言**: JavaScript (ES6+)
- **樣式**: CSS Modules / Inline Styles (搭配 Glassmorphism 設計風格)
- **圖表庫**: Recharts
- **部署**: Zeabur (Static Site)

### 後端 (Backend)
- **框架**: FastAPI (Python 3.9+)
- **伺服器**: Uvicorn
- **HTTP 請求**: Requests
- **資料儲存**: SQL 資料庫 (支援 SQLite / PostgreSQL) via SQLAlchemy
- **安全性**: Fernet 對稱式加密 (用於保護 Token 與 Secret)
- **部署**: Zeabur (Dockerized Python App)

## 3. 系統架構 (System Architecture)

```mermaid
graph LR
    User[使用者] -->|Google Login| Frontend[React Frontend]
    Frontend -->|HTTP/HTTPS (Bearer Token)| Backend[FastAPI Backend]
    Backend -->|Graph API| FB[Facebook Graph API]
    Backend -->|Read/Write (Encrypted)| DB[(Database: SQLite/PostgreSQL)]
```

## 4. 功能列表 (Features)

### 4.1 認證與授權 (Authentication)
- **Google 登入**: 使用 Google OAuth 2.0 進行身分驗證，確保只有授權使用者能存取。
- **Token 交換**: 使用者輸入 App ID, App Secret 和 Short-Lived Token，後端將其交換為 Long-Lived Token (效期 60 天)。
- **多用戶支援**: 每個 Google 帳號綁定獨立的 Facebook 設定，互不干擾。

### 4.2 安全性 (Security)
- **資料加密**: 敏感資料 (Access Token, App Secret) 在寫入資料庫前使用 `Fernet` 加密，讀取時解密。
- **路由保護**: 前後端皆有驗證機制，未登入無法呼叫 API 或查看儀表板。

### 4.3 廣告帳號管理 (Ad Account Management)
- **帳號列表**: 自動抓取使用者權限下的所有廣告帳號。
- **帳號切換**: 支援在前端下拉選單切換不同廣告帳號，即時更新數據。

### 4.4 數據儀表板 (Dashboard)
- **KPI 卡片**: 顯示最近 30 天的關鍵指標：
  - 花費 (Spend)
  - 曝光數 (Impressions)
  - 點擊數 (Clicks)
  - 觸及數 (Reach)
- **趨勢圖表**: 顯示過去一年的每月數據趨勢 (折線圖)。

### 4.5 系統設定
- **多語系**: 支援繁體中文 (zh) 與英文 (en) 切換。
- **部署支援**: 支援環境變數 `VITE_API_URL` 與 `DATABASE_URL` 設定。

## 5. API 規格 (API Endpoints)

| Method | Endpoint | Description | Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Health Check | None |
| `POST` | `/api/auth/exchange-token` | 交換並儲存 Long-Lived Token (加密存入 DB) | `app_id`, `app_secret`, `short_token` |
| `GET` | `/api/ad-accounts` | 取得所有廣告帳號列表 | None |
| `GET` | `/api/dashboard-data` | 取得特定帳號的 KPI 與圖表數據 | `account_id` (Query Param) |

## 6. 資料結構 (Database Schema)

### Users Table
| Column | Type | Description |
| :--- | :--- | :--- |
| `google_id` | String (PK) | Google 唯一使用者 ID |
| `email` | String | 使用者 Email |
| `fb_access_token` | String | **[Encrypted]** Facebook Long-Lived Token |
| `fb_app_id` | String | Facebook App ID |
| `fb_app_secret` | String | **[Encrypted]** Facebook App Secret |

## 7. 部署與環境變數 (Deployment & Env)

### Frontend (`.env.production`)
- `VITE_API_URL`: 後端 API 的完整網址。
- `VITE_GOOGLE_CLIENT_ID`: Google OAuth Client ID。

### Backend
- `DATABASE_URL`: 資料庫連線字串 (PostgreSQL for Zeabur, SQLite for Local)。
- `GOOGLE_CLIENT_ID`: 用於後端驗證。
- `ENCRYPTION_KEY`: 資料加密金鑰 (Base64 URL-safe)。

## 8. 待優化項目 (Future Improvements)
- [ ] **錯誤處理**: 增強 API 錯誤回傳的詳細度與前端提示。
- [ ] **圖表欄位修正**: 前端圖表目前顯示 "Followers/Engagement"，但後端回傳的是 "Spend/Clicks"，需統一命名。
