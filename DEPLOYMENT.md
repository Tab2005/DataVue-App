# Zeabur 佈署指南 (Deployment Guide)

## 1. 關於資料庫 (Database Question)
**Q: 需要在專案程式碼內建立 PostgreSQL 資料庫嗎？**
**A: 不需要。** 
PostgreSQL 是一個獨立運行的伺服器軟體。您不需要（也就無法）把它像 SQLite 檔案一樣放在程式碼資料夾裡。
您只需要在 **Zeabur 的網頁控制台** 上新增一個 PostgreSQL 服務，Zeabur 就會自動管理它，並提供連線網址 (`DATABASE_URL`) 給您的程式使用。

## 2. 佈署步驟 (Step-by-Step)

### Step 1: 建立 Zeabur 專案
1. 登入 [Zeabur Dashboard](https://dash.zeabur.com)。
2. 建立一個新專案 (Project)，可以命名為 `Facebook-Dashboard`。

### Step 2: 建立 PostgreSQL 服務
1. 在專案中點擊 **"Create Service"** (建立服務)。
2. 選擇 **"Marketplace"** (市集)。
3. 搜尋並選擇 **"PostgreSQL"**。
4. 等待它建立完成。

### Step 3: 佈署應用程式 (Backend & Frontend)
1. 再次點擊 **"Create Service"**。
2. 選擇 **"Git"**。
3. 連結您的 GitHub 帳號並選擇 `Facebook-Dashboard-Web-App` Repository。
4. Zeabur 會自動偵測到這是一個 Python/Node.js 專案。
   - *注意*: 由於我們是前後端分離 (Frontend + Backend)，Zeabur 可能會預設只抓到其中一個。
   - **建議做法 (Monorepo)**: 您可以在 Zeabur 設定中指定 "Root Directory" 或者建立兩個服務分別佈署 `frontend` 和 `backend` 資料夾。
   - **簡單做法**: 先佈署 Backend。

### Step 4: 設定環境變數 (Environment Variables)
在您的應用程式服務 (App Service) 的 "Settings" -> "Variables" 中，新增以下變數：

| Key | Value | 說明 |
| --- | --- | --- |
| `DATABASE_URL` | (自動) | 通常點擊 "Connect to PostgreSQL" Zeabur 會自動注入，或手動從 Postgres 服務複製。 |
| `ENCRYPTION_KEY` | `...` | **重要！** 請查看您本機 `.env` 檔案中的值，複製貼上。 |
| `GOOGLE_CLIENT_ID` | `...` | 您的 Google Client ID。 |
| `GOOGLE_CLIENT_SECRET` | `...` | (如果後端驗證有用到) |

### Step 5: 驗證
1. 等待佈署成功 (Build Success)。
2. 開啟 Zeabur 提供的公開網址 (Domain)。
3. 嘗試登入。

## 常見問題
- **Port**: Zeabur 自動偵測 Port。FastAPI 預設 8000，Vite 預設 5173。確保 Zeabur 的 Networking 設定有對應到正確的 Port。
