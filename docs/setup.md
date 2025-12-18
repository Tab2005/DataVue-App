# 安裝與設定指南 (Setup & Configuration Guide)

本指南將協助您在本地端架設開發環境，或遷移至新電腦進行開發。

---

## 🚀 快速開始 (Quick Start)

### 1. 取得程式碼
```bash
git clone https://github.com/Tab2005/Facebook-Dashboard-Web-App.git
cd Facebook-Dashboard-Web-App
git checkout dev-saas
```

### 2. 後端環境設定 (Backend)
```bash
cd backend
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 前端環境設定 (Frontend)
```bash
cd frontend
npm install
```

### 4. 啟動服務
**後端**:
```bash
cd backend
python main.py
```
**前端**:
```bash
cd frontend
npm run dev
```

---

## 🔑 Google OAuth 設定

本專案使用 Google 登入。您需要前往 [Google Cloud Console](https://console.cloud.google.com/) 申請 Client ID。

### 核心步驟
1. **建立專案**: 在 Google Cloud Console 建立新專案。
2. **OAuth 同意畫面**: 設定為 "External"，加入您的測試 Email。
3. **建立憑證**: 選擇 "Web application"。
4. **授權來源**: 
   - 加入 `http://localhost:5173` (本地測試)
   - 加入 `https://your-app.zeabur.app` (正式網址)
5. **環境變數**:
   - 前端 (`frontend/.env.development`): `VITE_GOOGLE_CLIENT_ID=您的ID`
   - 後端 (`backend/.env`): `GOOGLE_CLIENT_ID=您的ID`

> [!TIP]
> 詳細逐步截圖教學請參考原 `GOOGLE_SETUP_GUIDE.md` (已整合至此)。

---

## 💻 遷移至新電腦 (New Machine Setup)

如果您更換電腦，請注意以下事項：

1. **GitHub 不包含機密檔案**: `.env` 與 `.db` 檔案被 `.gitignore` 排除。
2. **轉移 .env**: 手動複製 `backend/.env` 到新電腦。
3. **資料庫 (.db)**:
   - 若要保留本地測試資料，複製 `backend/facebook_dashboard.db`。
   - 若不複製，系統啟動時會自動建立全新資料庫。
4. **OneDrive 注意事項**:
   - 若使用 OneDrive 同步，建議**刪除** `node_modules` 與 `venv` 並重新執行 `npm install` 與 `pip install`，避免路徑寫死導致的錯誤。

---

## 📧 語系說明
本專案開發過程中使用繁體中文。地端環境需要更新時，請執行更新動作並確認連結。
