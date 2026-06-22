# 16 Zeabur 部署與持久化儲存設定指南

## 目的

本指南詳細說明如何將 **DataVue Analytics** 系統部署至 [Zeabur](https://zeabur.com/) 雲端平台，並重點介紹新增的 **Meta Andromeda 儲存持久化掛載 (Volume Mount)** 機制之設定方式。

本系統已針對 Zeabur 的容器化與多服務架構進行優化，支援自動化部署、PostgreSQL/SQLite 持久化、以及獨立的背景排程 Worker 運作。

---

## 🏗️ 系統服務架構

在 Zeabur 上，建議將系統拆分為以下服務：
1. **PostgreSQL** 或 **SQLite** (持久化 Volume 掛載)：資料庫。
2. **Backend (API Server)**：處理前端請求與核心邏輯。
3. **Scheduler Worker**：專門負責週報自動化生成的背景程序（確保服務重啟時不漏掉任務）。
4. **Frontend**：靜態網站託管 (Static Hosting)。

---

## 🛠️ 第一階段：資料庫與儲存持久化設定

### 方案 A：Zeabur 持久化磁碟掛載 (本地儲存，推薦)
適用於不需要額外付費購買 S3 雲端儲存的場景。本方案將廣告圖片/影片快照與 SQLite 資料庫一同存放在 Zeabur 的持久化磁碟中。

#### 1. 建立 Volume
1. 進入 Zeabur 控制台的 **後端服務 (Backend Service)**。
2. 前往 **「儲存 (Volumes)」** 分頁，點擊 **「新增儲存區 (Add Volume)」**。
3. 將掛載路徑 (Mount Path) 設定為：`/app/backend/storage`。

#### 2. 設定環境變數
切換到 **「變數 (Variables)」** 分頁，配置以下持久化變數：
```bash
# 指定使用本地 filesystem
META_ANDROMEDA_STORAGE_BACKEND=filesystem
# 將素材落檔根目錄指向掛載點
META_ANDROMEDA_STORAGE_ROOT=/app/backend/storage/meta_andromeda
# 若使用 SQLite，需將資料庫檔案一併指向掛載點（極度重要，防止重新部署後資料被清空）
DATABASE_URL=sqlite:////app/backend/storage/facebook_dashboard.db
```

---

### 方案 B：S3 相容物件儲存 (雲端儲存)
適用於多後端節點水平擴充，或希望靜態檔案透過獨立 CDN 加速的生產場景。

#### 1. 儲存桶準備
* 在 AWS S3、Cloudflare R2 等平台建立 BUCKET（如 `datavue-assets`）。
* 設定 CORS 政策，允許您的前端網域（如 `https://datavue-dev-saas.sitetegy.com`）跨域存取。

#### 2. Zeabur 環境變數設定
在後端服務的 **「變數 (Variables)」** 分頁配置：
```bash
META_ANDROMEDA_STORAGE_BACKEND=s3_compatible
META_ANDROMEDA_STORAGE_S3_BUCKET=datavue-assets
META_ANDROMEDA_STORAGE_S3_REGION=ap-northeast-1
META_ANDROMEDA_STORAGE_S3_ACCESS_KEY_ID=YOUR_S3_ACCESS_KEY
META_ANDROMEDA_STORAGE_S3_SECRET_ACCESS_KEY=YOUR_S3_SECRET_ACCESS_KEY
# 非 AWS S3（如 Cloudflare R2 / MinIO）需指定自訂 Endpoint URL
META_ANDROMEDA_STORAGE_S3_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
# 設定公開 CDN 或 Base URL 供前端讀取素材圖片
META_ANDROMEDA_STORAGE_PUBLIC_BASE_URL=https://assets.sitetegy.com/meta-andromeda
```

---

## 🐍 第二階段：後端與排程服務部署

### 2.1 基礎設定
1. 選擇 Git 儲存庫，並將 **Root Directory** 設為 `backend`。
2. **API Server (Web 服務)**:
   * Port 改為 `8000`。
   * 環境變數 `ENABLE_REPORT_SCHEDULER` 設為 `false`。
3. **Scheduler Worker (排程背景服務)**:
   * 新增另一個服務，Root Directory 同樣是 `backend`。
   * **Start Command** 改為 `python scheduler_worker.py`。
   * 環境變數 `ENABLE_REPORT_SCHEDULER` 設為 `true`。

### 2.2 核心環境變數對照表
請在 Zeabur 後端與 Worker 的 Variables 頁面配置以下項目：

| 變數名稱 | 說明 | 範例/來源 |
| :--- | :--- | :--- |
| `DATABASE_URL` | 資料庫連線字串 | PostgreSQL 內網地址 或 方案 A 的本地掛載路徑 |
| `ENCRYPTION_KEY` | Fernet 安全加密金鑰 | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `GOOGLE_CLIENT_ID` | Google OAuth ID | Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | Google Client Secret | Google Cloud Console (GSC 整合必填) |
| `SUPER_ADMIN_EMAIL` | 最高管理員帳號 | `admin@example.com` (多個以逗號分隔) |
| `GOOGLE_AI_API_KEY` | Gemini API Key | Google AI Studio (用於週報 AI 摘要) |
| `ALLOWED_ORIGINS` | 允許的前端來源 | `https://datavue-dev-saas.sitetegy.com` |
| `ENV` | 執行環境 | `production` |

---

## 🌐 第三階段：前端部署

1. 建立服務，選擇您的 Git 儲存庫。
2. **Root Directory**: 設定為 `frontend`。
3. **Build Command**: `npm install && npm run build`。
4. **Output Directory**: `dist` (Vite 預設輸出)。
5. **環境變數 (Variables)**：
   - `VITE_API_URL`: 後端 API 的**公網網址** (不含末尾的 `/api`)。
   - `VITE_GOOGLE_CLIENT_ID`: 必須與後端一致。

---

## 🔄 第四階段：資料庫遷移 (Migrations)

部署完成後，請透過 Zeabur 的 **Console (控制台)** 連線至 API 後端服務，並執行：
```bash
alembic upgrade head
```
此步驟會在您的 PostgreSQL/SQLite 資料庫中，建立最新的 Meta Andromeda 評估表與 Lineage 表格。

---

## 🛡️ 常見問題與除錯 (Troubleshooting)

> [!TIP]
> **排程沒跑？**
> 可呼叫 `/health` 檢查 `checks.scheduler.running` 是否為 `true`。請確保 Web 服務與 Scheduler Worker 服務的 `ENABLE_REPORT_SCHEDULER` 變數互斥（一為 `false`，另一為 `true`），避免重複觸發。

> [!WARNING]
> **CORS 跨網域政策攔截？**
> * **檢查後端設定**：確保後端的 `ALLOWED_ORIGINS` 包含前端的完整網址，且不帶結尾斜線（如 `https://datavue-dev-saas.sitetegy.com`）。
> * **例外 CORS 保險**：後端已在 [main.py](file:///C:/Users/BWM2/Documents/python/DataVue-App/backend/main.py) 的 Exception Handlers 中實作 CORS 保修機制。如果後端拋出 500、403 等未捕獲錯誤，回傳回應仍會被加上正確的 CORS 標頭，以便於前端在 Console 印出正確的錯誤 JSON，而不是被 CORS 政策訊息遮蔽。

> [!IMPORTANT]
> **觀察事實素材下載與儲存失敗？**
> * **S3 權限或 Volume 權限**：檢查後端日誌是否有 `[Observation Import] Failed to download or store asset` 警告。
> * **容錯保護**：後端已在 [service.py](file:///C:/Users/BWM2/Documents/python/DataVue-App/backend/modules/meta_andromeda/service.py) 實作下載與 S3 寫入的 try-except 容錯。就算 S3 金鑰失效或本地儲存寫入失敗，廣告績效與文字數據依然能正常匯入，僅實體圖片會回退讀取 FB 的原始網址。
