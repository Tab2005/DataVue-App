# 🚀 Zeabur 部署指南 (Comprehensive Guide)

本指南說明如何將 **DataVue Analytics** 系統部署至 [Zeabur](https://zeabur.com/) 雲端平台。本系統已針對 Zeabur 的容器化環境進行優化，支援自動化部署、PostgreSQL 內網連線及獨立的背景排程 Worker。

---

## 🏗️ 系統架構概要
在 Zeabur 上，建議將系統拆分為以下服務：
1.  **PostgreSQL**: 持久化資料庫。
2.  **Backend (API Server)**: 處理前端請求與核心邏輯。
3.  **Scheduler Worker**: 專門負責週報自動化生成的背景程序（確保任務不遺漏）。
4.  **Frontend**: 靜態網站託管 (Static Hosting)。

---

## 🛠️ 1. 資料庫配置 (PostgreSQL)
1.  在 Zeabur 建立一個 **PostgreSQL** 服務。
2.  複製其 **Private Connectivity** (內網連線地址)。
    *   格式範例：`postgresql://root:password@postgresql.zeabur.internal:5432/postgres`

---

## 🐍 2. 後端部署 (Backend / Worker)

### 2.1 基礎設定
1.  服務建立：選擇 Git 儲存庫，並將 **Root Directory** 設為 `backend`。
2.  **API Server**: 
    - Port 改為 `8000`。
    - 環境變數 `ENABLE_REPORT_SCHEDULER` 設為 `false`。
3.  **Scheduler Worker**:
    - **Start Command**: 改為 `python scheduler_worker.py`。
    - 環境變數 `ENABLE_REPORT_SCHEDULER` 設為 `true`。

### 2.2 核心環境變數 (Backend Variables)
請在 Zeabur 的 Variables 頁面配置以下項目：

| 變數名稱 | 說明 | 範例/來源 |
| :--- | :--- | :--- |
| `DATABASE_URL` | 資料庫連線字串 | 使用步驟 1 的 PostgreSQL 內網地址 |
| `ENCRYPTION_KEY` | Fernet 安全加密金鑰 | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `GOOGLE_CLIENT_ID` | Google OAuth ID | Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | Google Client Secret | Google Cloud Console (GSC 整合必填) |
| `SUPER_ADMIN_EMAIL` | 最高管理員帳號 | `admin@example.com` (多個以逗號分隔) |
| `GOOGLE_AI_API_KEY` | Gemini API Key | Google AI Studio (用於週報 AI 摘要) |
| `LINE_CHANNEL_SECRET` | LINE 密鑰 | LINE Developers (Webhook 驗證用) |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE 權杖 | LINE Developers (發送通知用) |
| `ALLOWED_ORIGINS` | 允許的前端來源 | `https://your-app.zeabur.app` |
| `FRONTEND_URL` | 前端連結網址 | 用於週報與 LINE 訊息中的回連導向 |
| `LINE_BOT_QR_URL` | LINE 官方帳號 QR Code 連結 | 從 LINE 後台取得的加友連結 (如 `https://lin.ee/xxx`) |
| `ENV` | 執行環境 | `production` |

---

## 🌐 3. 前端部署 (Frontend)
1.  服務建立：選擇 Git 儲存庫，並將 **Root Directory** 設為 `frontend`。
2.  **Build Command**: `npm install && npm run build`。
3.  **Output Directory**: `dist` (Vite 預設輸出)。
4.  **環境變數**:
    - `VITE_API_URL`: 後端 API 的**公網網址**。
    - `VITE_GOOGLE_CLIENT_ID`: 必須與後端一致。

---

## 🔄 4. 資料庫遷移 (Migrations)
合併或部署後，請透過 Zeabur 的 **Console** 連結至 Backend 服務並執行：
```bash
alembic upgrade head
```
*註：這會建立週報、LINE 綁定及權限系統所需的最新表格。*

---

## 🛡️ 常見問題與除錯 (Troubleshooting)

> [!TIP]
> **排程沒跑？** 
> 請確認 `scheduler_worker.py` 的日誌中是否顯示 `Scheduler started`。
> 您也可以呼叫 `/health` 檢查 `checks.scheduler.running` 是否為 `true`。

> [!WARNING]
> **CORS 錯誤？**
> 請確保後端的 `ALLOWED_ORIGINS` 變數包含您的前端 URL，且不帶結尾斜線（如 `https://xxx.zeabur.app`）。

---
**DataVue 開發團隊** | 最後更新: 2026-04-16
