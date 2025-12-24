# 專案統計 (Project Statistics)

**最後更新**: 2024-12-24

---

## 📊 程式碼統計

### 後端 (Backend - Python)

| 位置 | 行數 |
|------|------|
| `backend/*.py` (主程式) | 4,230 行 |
| `backend/routers/*.py` | 745 行 |
| `backend/service_modules/*.py` | 410 行 |
| **後端合計** | **~5,385 行** |

### 前端 (Frontend - JS/JSX/CSS)

| 位置 | 行數 |
|------|------|
| `frontend/src/**/*` | 10,642 行 |

### 總計

| 項目 | 數值 |
|------|------|
| **總程式碼行數** | **~16,027 行** |

---

## 📅 開發時程

| 項目 | 數值 |
|------|------|
| **專案開始日期** | 2025-12-08 |
| **統計截止日期** | 2025-12-24 |
| **開發天數** | 16 天 |
| **Git Commits** | 201 次 |

---

## 📈 開發效率

| 指標 | 數值 |
|------|------|
| **平均每日程式碼** | ~1,002 行 / 天 |
| **平均每日 Commits** | ~12.5 次 / 天 |

---

## 🛠️ 技術棧

### 後端
- Python 3.11+
- FastAPI
- PostgreSQL / SQLite
- Google OAuth 2.0
- Google Gemini AI

### 前端
- React 18
- Vite
- CSS (Vanilla)
- Recharts (圖表)

---

> 📌 **更新方式**: 執行以下 PowerShell 指令可重新計算行數
> ```powershell
> # 後端
> Get-ChildItem -Path backend -Filter *.py | ForEach-Object { (Get-Content $_.FullName | Measure-Object -Line).Lines } | Measure-Object -Sum
> 
> # 前端
> Get-ChildItem -Path frontend\src -Recurse -Include *.jsx,*.js,*.css | ForEach-Object { (Get-Content $_.FullName | Measure-Object -Line).Lines } | Measure-Object -Sum
> ```
