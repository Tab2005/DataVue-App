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
   - `GOOGLE_CLIENT_SECRET`: 您的 Google OAuth Client Secret（GSC 整合必要）。
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

## 5. Super Admin 管理

### 環境變數自動同步
伺服器每次啟動時會自動將 `SUPER_ADMIN_EMAIL` 同步到資料庫，確保指定的用戶具有超級管理員權限。

```
# 支援逗號分隔的多個 Email
SUPER_ADMIN_EMAIL=admin1@example.com,admin2@example.com
```

### CLI 管理工具
在 `backend` 目錄下可使用 CLI 工具管理超級管理員：

```bash
# 列出所有超級管理員
python manage_admin.py list

# 授予超級管理員權限
python manage_admin.py grant user@example.com

# 撤銷超級管理員權限 (無法撤銷最後一位)
python manage_admin.py revoke user@example.com

# 檢查用戶狀態
python manage_admin.py check user@example.com
```

### 連線 Zeabur PostgreSQL
若要在本地端管理線上資料庫：

```powershell
# 設定環境變數 (使用 Zeabur PostgreSQL 公開連線字串)
$env:DATABASE_URL = "postgresql://root:密碼@xxx.zeabur.app:5432/postgres"

# 執行管理指令
python manage_admin.py list
```

> **注意**：建議使用 Zeabur Terminal 直接在後端服務中執行，可使用內網連線。

---

## 🛠️ 除錯 (Troubleshooting)
- **登入無反應**: 檢查 `VITE_API_URL` 是否正確指向後端，且 Google Cloud Console 是否已授權新的前端網址。
- **資料庫連線失敗**: 檢查後端 Log，確認 `DATABASE_URL` 是否正確，並確認使用的是內網連線。
- **超級管理員權限遺失**: 
  1. 確認 `SUPER_ADMIN_EMAIL` 環境變數已正確設定
  2. 重新部署後端服務 (觸發啟動時同步)
  3. 或使用 `/api/debug/super-admin-check?token=YOUR_TOKEN` 診斷
