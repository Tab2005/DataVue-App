# M-2：更新 backend/.gitignore

> **優先級**：🟡 Medium（安全性相關，建議儘快處理）  
> **預計工時**：15 分鐘  
> **執行時程**：本週內  
> **審查問題編號**：M-2

---

## 問題說明

`backend/.gitignore` 目前只有 5 條規則，嚴重不足，可能導致敏感檔案或開發產物被意外提交至 Git：

### 現有規則（全部）

```gitignore
venv/
__pycache__/
*.pyc
.env
tokens.json
```

### 缺漏的關鍵規則及風險

| 缺漏規則 | 可能洩漏的檔案 | 風險等級 |
|---------|-------------|---------|
| `*.db` / `*.sqlite` / `*.sqlite3` | `facebook_dashboard.db`、測試 DB | 🔴 高（含使用者資料） |
| `*.log` / `debug_*.log` | `debug_fields.log`、應用程式日誌 | 🟠 高（含敏感操作記錄） |
| `*.backup` / `*.bak` / `*.orig` | 手動備份檔案 | 🟡 中（可能含舊版設定或 Token） |
| `.pytest_cache/` | pytest 快取 | 🔵 低（資訊洩漏） |
| `htmlcov/` / `.coverage` | 測試覆蓋率報告 | 🔵 低 |
| `*.pyo` / `*.pyd` | Compiled Python 檔案 | 🔵 低 |
| `.env.*` | `.env.local`、`.env.production` 等 | 🔴 高（環境變數） |

### 為什麼 backend/.gitignore 需要獨立維護？

雖然根目錄的 `.gitignore` 已完整涵蓋這些規則，但 `backend/` 子目錄的 `.gitignore` 在以下情境下會獨立生效：

1. **Docker Build Context**：`COPY . .` 時，Docker 不使用根目錄 `.gitignore`
2. **Git Subtree / Submodule**：若 `backend/` 被獨立作為一個 repo 使用
3. **IDE 排除設定**：部分 IDE 工具只讀取最近的 `.gitignore`

---

## 實作步驟

### Step 1：更新 backend/.gitignore

**完整內容**（直接替換現有檔案）：

```gitignore
# ===================================
# DataVue Backend — .gitignore
# ===================================

# ─── Python 編譯產物 ──────────────
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.so
*.egg
*.egg-info/
dist/
build/
wheels/

# ─── 虛擬環境 ────────────────────
venv/
.venv/
env/
.env_backup/

# ─── 環境變數與設定 ──────────────
.env
.env.*
!.env.example        # 保留範例檔案
tokens.json
*.key
*.pem
*.p12

# ─── 資料庫 ──────────────────────
*.db
*.sqlite
*.sqlite3
*.db-shm
*.db-wal

# ─── 日誌檔案 ────────────────────
*.log
debug_*.log
logs/
*.out

# ─── 備份與臨時檔案 ──────────────
*.backup
*.bak
*.orig
*_orig.*
*_backup.*
*.tmp
*.temp
*~

# ─── 測試與覆蓋率報告 ────────────
.pytest_cache/
.coverage
.coverage.*
htmlcov/
coverage.xml
.tox/
.nox/

# ─── IDE / 編輯器 ────────────────
.idea/
.vscode/
*.swp
*.swo
.DS_Store
Thumbs.db

# ─── 其他工具產物 ────────────────
.mypy_cache/
.ruff_cache/
.hypothesis/
```

---

### Step 2：確認根目錄 .gitignore 仍完整

```powershell
# 確認根目錄 .gitignore 存在且涵蓋關鍵規則
Get-Content ".gitignore" | Select-String "\.db|\.env|\.log"
```

若根目錄 `.gitignore` 已完整，`backend/.gitignore` 只是額外保護層，兩者共存無衝突。

---

### Step 3：清除已被追蹤的違規檔案（若存在）

```powershell
# 檢查是否有應被忽略但已被 git 追蹤的檔案
git ls-files --ignored --exclude-standard backend/ | Format-Table

# 若有發現（例如 backend/debug.log），停止追蹤但保留本地檔案：
git rm --cached backend/some_file.db
git rm --cached backend/debug_fields.log

# 提交此清理
git commit -m "chore: untrack files that should be gitignored"
```

---

### Step 4：驗證新規則

```powershell
cd backend

# 建立測試檔案
New-Item -Name "test.db" -ItemType File
New-Item -Name "debug_test.log" -ItemType File
New-Item -Name "backup.bak" -ItemType File

# 確認 git 不追蹤這些檔案
git status --short

# 這些檔案應顯示為 "?? " 或完全不出現（表示被 .gitignore 忽略）
# 它們不應顯示 "A " 或 "M "（表示被追蹤）

# 驗證後清理測試檔案
Remove-Item test.db, debug_test.log, backup.bak
```

---

## 驗收標準

- [ ] `backend/.gitignore` 包含 `*.db`、`*.sqlite` 規則
- [ ] `backend/.gitignore` 包含 `*.log`、`debug_*.log` 規則
- [ ] `backend/.gitignore` 包含 `.env.*` 規則
- [ ] `backend/.gitignore` 包含 `.pytest_cache/`、`htmlcov/` 規則
- [ ] 執行 `git status` 後，本地的 `*.db`、`*.log` 等檔案不出現在 untracked 列表

---

## 附加建議：新增 .env.example

為了讓新進開發者清楚需要設定哪些環境變數，建議補充建立範例檔案：

**檔案**：`backend/.env.example`

```dotenv
# ─── 資料庫 ──────────────────────
DATABASE_URL=sqlite:///./app.db
# 生產環境 PostgreSQL：
# DATABASE_URL=postgresql://user:password@localhost/datavue

# ─── 安全性 ──────────────────────
SECRET_KEY=your-secret-key-here
FERNET_KEY=your-fernet-key-here

# ─── Google OAuth ────────────────
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# ─── Facebook ────────────────────
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret

# ─── Redis ───────────────────────
REDIS_URL=redis://localhost:6379/0

# ─── 應用程式設定 ────────────────
DEBUG_MODE=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:5173,https://your-domain.com

# ─── AI 服務（可選）──────────────
ZEABUR_API_KEY=your-zeabur-api-key
```

此檔案應提交至 git（已在 .gitignore 中透過 `!.env.example` 明確排除忽略規則）。
