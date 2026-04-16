# Zeabur 部署指南 (Deployment Guide)

本指南說明如何將 DataVue Analytics 部署至 Zeabur 平台，並配置目前系統架構所需的所有環境變數。

---

## 1. 後端部署參數 (Backend Environment Variables)

在 Zeabur 的 **Service > Variables** 中設定以下變數：

### 核心認證與安全
*   **`ENCRYPTION_KEY`**: (必填) 用於解密資料庫中的密鑰。透過 `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` 產生。
*   **`GOOGLE_CLIENT_ID`**: (必填) Google OAuth 用戶端 ID。
*   **`GOOGLE_CLIENT_SECRET`**: (必填) 用於 Google Search Console 等 API 權限交換。
*   **`SUPER_ADMIN_EMAIL`**: (必填) 指定最高管理員 Email（支援逗號分隔）。

### 資料庫與連線
*   **`DATABASE_URL`**: (建議) PostgreSQL 內網連線字串。若未填寫則預設使用 SQLite。
*   **`ALLOWED_ORIGINS`**: 允許的跨網域來源（如 `https://your-frontend.zeabur.app`）。
*   **`FRONTEND_URL`**: 前端服務網址，用於發送通知郵件中的連結。

### AI 與功能設定
*   **`GOOGLE_AI_API_KEY`**: Gemini AI API 金鑰，用於週報 AI 摘要功能。
*   **`ZEABUR_AI_HUB_API_KEY`**: 若使用 Zeabur AI Hub 服務時選填。
*   **`ENABLE_REPORT_SCHEDULER`**: 
    - 設為 `false`: 純 API 模式（推薦用於 Web 服務）。
    - 設為 `true`: 啟動背景排程任務（建議單獨部署一個 Worker 使用）。

### LINE 整合通知 (選填)
*   **`LINE_CHANNEL_ACCESS_TOKEN`**: LINE Messaging API 權杖。
*   **`LINE_CHANNEL_SECRET`**: LINE Channel 密鑰（用於驗證 Webhook）。

---

## 2. 前端部署參數 (Frontend Environment Variables)

*   **`VITE_API_URL`**: 指向後端 API 的公網網址（結尾不含 `/api`）。
*   **`VITE_GOOGLE_CLIENT_ID`**: 必須與後端設定一致。

---

## 🚀 部署架構建議

為了確保週報排程的準確性而不受 Web 服務重啟影響，建議在 Zeabur 部署兩個後端服務：
1.  **API Server**: `Root: backend`, `ENABLE_REPORT_SCHEDULER: false`。
2.  **Scheduler Worker**: `Root: backend`, `ENABLE_REPORT_SCHEDULER: true`, `Start Command: python scheduler_worker.py`。

