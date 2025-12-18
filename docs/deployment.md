# Zeabur 部署指南 (Deployment Guide)

本指南說明如何將 Facebook Dashboard 部署至 Zeabur 平台，包含後端 FastAPI、前端 React 與 PostgreSQL 資料庫。

---

## 🏗️ 系統架構
本專案在 Zeabur 上由三個部分組成：
1. **Database**: PostgreSQL (儲存用戶與團隊資料)
2. **Backend**: FastAPI 服務 (處理 API 請求)
3. **Frontend**: Static Site Hosting (顯示 React UI)

---

## 1. 資料庫設定 (PostgreSQL)
1. 在 Zeabur 建立 **PostgreSQL** 服務。
2. **內網連線 (重要)**: 
   - 為了效能與穩定性，請使用 **Private Connectivity**。
   - 連線字串範例：`postgresql://root:密碼@postgresql.zeabur.internal:5432/postgres`

---

## 2. 後端部署 (Backend)
1. 建立 Git 服務，連接專案 Repository。
2. **Settings**: Root Directory 設定為 `backend`。
3. **Networking**: 確認 Port 為 `8000`。
4. **環境變數 (Variables)**:
   - `DATABASE_URL`: 填入 PostgreSQL 內網連線字串。
   - `ENCRYPTION_KEY`: 您的 Fernet 加密金鑰。
   - `GOOGLE_CLIENT_ID`: 您的 Google OAuth Client ID。
   - `SUPER_ADMIN_EMAIL`: 您的最高管理員 Email。

---

## 3. 前端部署 (Frontend)
1. 建立 Git 服務，連接同一 Repository。
2. **Settings**:
   - Root Directory: `frontend`
   - Build Command: `npm install && npm run build`
   - Output Directory: `dist`
3. **環境變數 (Variables)**:
   - `VITE_API_URL`: **後端服務的公開網址** (不含 `/api`)。
   - `VITE_GOOGLE_CLIENT_ID`: 與後端相同。

---

## 4. 各種環境部署 (Multi-Environment)

### 部署特定分支 (如 dev-saas)
1. 在服務的 **Settings > Git** 中，將 Branch 更改為 `dev-saas`。
2. Zeabur 會自動重新部署該分支的內容。

### 建立測試站 (Staging)
建議建立不同的 Zeabur 專案或服務，並連結至 `dev-saas` 分支，同時使用不同的外部網址，以區隔開發環境與正式環境。

---

## 🛠️ 除錯 (Troubleshooting)
- **登入無反應**: 檢查 `VITE_API_URL` 是否正確指向後端，且 Google Cloud Console 是否已授權新的前端網址。
- **資料庫連線失敗**: 檢查後端 Log，確認 `DATABASE_URL` 是否正確，並確認使用的是內網連線。
