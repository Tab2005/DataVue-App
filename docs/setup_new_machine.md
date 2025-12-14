# 新電腦開發環境架設指南 (Setup Guide for New Machine)

如果你要更換電腦進行開發，僅從 GitHub 下載程式碼是不夠的。因為安全與架構原因，GitHub **不包含** 你的私鑰 (.env) 與本地資料庫 (.db)。

請依照以下步驟進行遷移：

## 1. 取得程式碼 (Code)
在目標電腦上執行：
```bash
git clone https://github.com/Tab2005/Facebook-Dashboard-Web-App.git
cd Facebook-Dashboard-Web-App
```
*切換到對應的分支 (如果需要)*:
```bash
git checkout dev-saas
```

## 2. 轉移機密設定 (Config)
`.env` 檔案被 `.gitignore` 排除，**不會** 出現在 GitHub 上。你需要手動複製：
*   **來源:** 舊電腦的 `backend/.env`
*   **目的:** 新電腦的 `backend/.env`
(可以用 USB、LINE、或私有雲端硬碟傳輸，不要傳到公開網路)

## 3. 安裝依賴 (Dependencies)
虛擬環境與套件庫不會同步，需重新安裝。

### Backend (後端)
```bash
cd backend
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
# source venv/bin/activate

pip install -r requirements.txt
```

### Frontend (前端)
```bash
cd ../frontend
npm install
```

## 4. 資料庫 (Database)
### 本地開發 (SQLite)
*   **GitHub 不含資料庫**: `backend/*.db` 檔案被忽略。
*   **全新開始**: 如果你直接執行程式，系統會自動建立一個全新的空資料庫。
*   **保留舊資料**: 如果你想延續舊電腦的測試資料，請**手動複製**舊電腦的 `backend/facebook_dashboard.db` 到新電腦的相同位置。

### 正式環境 (PostgreSQL / Zeabur)
*   正式環境資料庫在雲端，只要 `.env` 內的 `DATABASE_URL` 設定正確，新電腦連線過去看到的就是同一份資料。

## 5. 啟動 (Start)
```bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend
cd frontend
npm run dev
```

---

### ⚠️ 特別注意: OneDrive 使用者
我看您的專案放在 `OneDrive` 資料夾內。
*   **優點**: `.env` 和 `.db` 可能已經被 OneDrive 自動同步過去了。
*   **缺點**: `node_modules` (前端套件) 和 `venv` (後端環境) 透過 OneDrive 同步非常容易壞掉 (因為包含成千上萬小檔案且路徑寫死)。
*   **建議**: 在新電腦上，建議**刪除**同步過來的 `node_modules` 與 `venv` 資料夾，然後重新執行上述的「安裝依賴」步驟，這樣最穩當。
