# Zeabur 完整佈署指南 (Full Deployment Guide)

本指南將引導您從零開始，在 Zeabur 平台上佈署 Facebook Dashboard 應用程式。

## 專案結構
此專案分為兩個部分，需要在 Zeabur 上分別建立兩個服務：
1.  **Backend (後端)**: Python FastAPI，負責處理資料庫與 API。
2.  **Frontend (前端)**: React/Vite，負責顯示網頁畫面。
3.  **Database (資料庫)**: PostgreSQL，負責儲存資料。

---

## 1. 建立專案與資料庫 (Project & Database)

1.  登入 [Zeabur Dashboard](https://dash.zeabur.com).
2.  點擊 **"Create Project"**，輸入專案名稱 (例如 `Facebook-Dashboard`)。
3.  點擊 **"Create Service"** -> **"Marketplace"**。
4.  搜尋並選擇 **"PostgreSQL"**。
5.  建立完成後，點擊該 PostgreSQL 服務，切換到 **"Connection"** 分頁。
6.  複製 **"Connection String"**。
    > [!IMPORTANT]
    > **強烈建議使用私有連線 (Private Connectivity)**
    > public URL (`cgk1.clusters.zeabur.com`) 可能會導致連線逾時。
    > 1. 請尋找 **"Private Connectivity"** 或 **"內網存取"** 區塊。
    > 2. Host 通常是 `postgresql.zeabur.internal`，Port 是 `5432`。
    > 3. 請自行組裝連線字串：`postgresql://root:您的密碼@postgresql.zeabur.internal:5432/postgres`
    > 4. 使用這個 **內網連線字串** 作為 `DATABASE_URL`。

---

## 2. 佈署後端 (Backend Service)

1.  回到專案，點擊 **"Create Service"** -> **"Git"**。
2.  選擇您的 GitHub Repository (`Facebook-Dashboard-Web-App`)。
3.  建立後，點擊該服務進入設定頁面：
    *   **Settings** -> **Root Directory**: 輸入 `backend` (若未正確設定，Zeabur 會抓不到 requirements.txt)。
4.  **Networking**:
    *   確認 Port 為 `8000` (FastAPI 預設)。
    *   點擊 "Public" 產生一個公開網址 (例如 `backend-api.zeabur.app`)。**複製這個網址**。
5.  **Variables** (環境變數):
    *   `DATABASE_URL`: 貼上 Step 1 複製的 PostgreSQL 連線字串。
    *   `ENCRYPTION_KEY`: 貼上您本機 `.env` 的金鑰。
    *   `GOOGLE_CLIENT_ID`: 貼上您的 Google Client ID。
6.  **Redeploy**: 設定完變數後，若沒自動重啟，請手動 Redeploy。

---

## 3. 佈署前端 (Frontend Service)

1.  再次點擊 **"Create Service"** -> **"Git"**。
2.  同樣選擇 `Facebook-Dashboard-Web-App` Repository。
3.  點擊該服務進入設定頁面：
    *   **Settings** -> **Root Directory**: 輸入 `frontend`。
    *   **Settings** -> **Build Command**: 輸入 `npm install && npm run build` (通常 Zeabur 會自動偵測)。
    *   **Settings** -> **Output Directory**: 輸入 `dist`。
4.  **Variables** (環境變數) - **這一步很重要！**:
    *   `VITE_API_URL`: 貼上 Step 2 產生的 **後端網址** (不用加 `/api`，例如 `https://backend-api.zeabur.app`)。
    *   `VITE_GOOGLE_CLIENT_ID`: 貼上您的 Google Client ID。
5.  **Networking**:
    *   點擊 "Public" 產生前端的公開網址 (例如 `my-dashboard.zeabur.app`)。
6.  **Redeploy**: 環境變數設定完後，務必重新佈署，前端程式碼才會吃到變數。

---

## 4. Google Cloud Console 設定更新 (重要)

由於您的網址變了 (不再是 localhost)，您必須去 Google Cloud Console 更新設定，否則 Google 登入會失敗。

1.  前往 Google Cloud Console -> APIs & Services -> Credentials。
2.  編輯您的 OAuth 2.0 Client ID。
3.  **Authorized Javascript Origins**: 新增您的**前端網址** (例如 `https://my-dashboard.zeabur.app`)。
4.  **Authorized Redirect URIs**: 雖然此專案主要用 Popup，但建議將前端網址也加進去。

---

## 5. 驗證與除錯

1.  開啟前端網址。
2.  嘗試登入 Google。
3.  **檢查連線**:
    *   如果登入成功但沒數據：檢查後端 Log，看是否有 `✅ Database connected: PostgreSQL detected`。
    *   如果顯示 "Failed to fetch"：檢查前端變數 `VITE_API_URL` 是否正確指向後端，且後端是否正常運作。


---

## 6. 部署分支版本 (Deploying Branch Versions)

如果您需要部署非 `main` 分支 (例如 `dev-saas` 或其他測試分支)，請依照以下步驟：

### 步驟 1：本地端推送 (Local Push)
確保您已將目標分支推送到 GitHub：

```bash
# 切換到目標分支 (例如 dev-saas)
git checkout dev-saas
git pull origin dev-saas

# 推送更新到 GitHub
git push origin dev-saas
```

### 步驟 2：Zeabur 設定 (Zeabur Dashboard)
1. 進入 [Zeabur Dashboard](https://dash.zeabur.com) 並點選您的專案。
2. 針對 **Backend** 與 **Frontend** 服務分別執行：
   - 點擊服務進入 **Settings (設定)**。
   - 找到 **Source** 區塊的 **Branch** 選項。
   - 切換為您想部署的分支 (例如 `dev-saas`)。
   - Zeabur 將會自動觸發重新部署 (Redeploy)。

> [!TIP]
> **多環境部署**：建議在 Zeabur 建立一個新的 Service (例如 `frontend-staging`) 並連結到測試分支，這樣您可以同時保有 `main` (正式站) 與 `dev-saas` (測試站) 兩個運作中的環境。

---

祝佈署順利！

---

## 6. 建立測試環境 (Staging Environment Setup)

為了開發商業化版本而不影響正式版，我們採用 **多環境佈署 (Multi-Environment)** 策略。

### 作法
1.  **進入 GitHub**: 確認您有 **`dev-saas`** 分支。
2.  **進入 Zeabur**:
    *   **新增服務**: 建議建立一個新的 Project (例如 `FB-Dashboard-Staging`) 或在原 Project 下新增 Service。
    *   **選擇來源**: 同樣選擇 `Facebook-Dashboard-Web-App` Repository。
    *   **關鍵設定 (Branch)**: 在 Settings > Git 中，將 Branch 從 `main` 改為 **`dev-saas`**。
3.  **環境變數**:
    *   設定方式與正式版相同，但 `DATABASE_URL` 建議使用一個**全新的資料庫**，以免開發測試時弄髒正式資料。
4.  **網址區隔**:
    *   正式版: `your-app.zeabur.app`
    *   測試版: `your-app-dev.zeabur.app` (自訂 Domain)

### 開發流程
1.  本地端切換分支: `git checkout dev-saas`
2.  寫程式 -> Commit -> Push。
3.  Zeabur 測試版會自動更新。
4.  測試無誤後，發起 Pull Request 合併回 `main`，正式版才會更新。

---

## 7. 設定超級管理員權限 (Setting Up Super Admin)

為了確保您擁有系統的最高管理權限 (即使資料庫被清空也能隨時取回)，請在 Zeabur 上設定專屬的環境變數。

### 步驟
1.  進入 [Zeabur Dashboard](https://dash.zeabur.com) 並點選您的專案。
2.  選擇 **Backend (後端)** 服務。
3.  切換到 **"Variables"** 分頁。
4.  新增變數：
    *   **Key**: `SUPER_ADMIN_EMAIL`
    *   **Value**: 您的 Google Email (例如 `yourname@gmail.com`)
5.  儲存變數。Zeabur 會自動重新部署服務。

### 驗證
重新部署完成後，使用該 Email 登入。如果成功，您應該能在選單中看到「超級管理員後台」的選項。
