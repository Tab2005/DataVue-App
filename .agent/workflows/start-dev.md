---
description: 啟動開發環境 (Start Development Environment)
---

# 開發環境啟動指南

## 方式一：一鍵啟動（推薦）

在專案根目錄執行：

```powershell
.\start-dev.ps1
```

此腳本會：
1. 檢查 Python、Node.js、npm 是否安裝
2. 驗證 `.env` 環境變數設定
3. 啟動後端服務並等待健康檢查通過
4. 啟動前端服務
5. 顯示所有服務 URL

---

## 方式二：分開終端執行

// turbo
**Terminal 1 - 後端：**
```powershell
.\quick-start.ps1 backend
```

// turbo
**Terminal 2 - 前端：**
```powershell
.\quick-start.ps1 frontend
```

---

## 方式三：手動啟動

// turbo
**後端：**
```powershell
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

// turbo
**前端：**
```powershell
cd frontend
npm run dev
```

---

## 健康檢查

// turbo
```powershell
.\quick-start.ps1 check
```

或直接訪問：http://localhost:8000/api/health

---

## 服務位址

| 服務 | URL |
|------|-----|
| 前端 | http://localhost:5173 |
| 後端 API | http://localhost:8000 |
| API 文件 | http://localhost:8000/docs |
| 健康檢查 | http://localhost:8000/api/health |
