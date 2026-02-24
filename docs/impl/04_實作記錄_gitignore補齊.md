# 實作記錄：M-2 更新 backend/.gitignore

> **執行日期**：2026-02-24  
> **對應計畫**：`04_緊急修復_gitignore補齊.md`（審查問題 M-2）  
> **優先級**：🟡 Medium（安全性相關）  
> **執行結果**：✅ 完成

---

## 執行摘要

`backend/.gitignore` 原本只有 5 條規則，存在敏感檔案（DB、log、env）意外被提交的風險。本次將其擴充為完整的 70+ 條規則，並修正根目錄 `.gitignore` 的例外規則衝突。

---

## 變更清單

### 1. `backend/.gitignore` — 全面擴充

**變更前**（5 條規則）：
```gitignore
venv/
__pycache__/
*.pyc
.env
tokens.json
```

**變更後**（70+ 條規則，含分類註解）：

| 分類 | 新增規則 | 風險等級 |
|------|---------|---------|
| Python 編譯產物 | `*.py[cod]`、`*.pyo`、`*.pyd`、`*.so`、`*.egg`、`*.egg-info/`、`dist/`、`build/`、`wheels/` | 🔵 低 |
| 虛擬環境 | `.venv/`、`env/`、`.env_backup/` | 🔵 低 |
| 環境變數 | `.env.*`、`!.env.example`、`*.key`、`*.pem`、`*.p12` | 🔴 高 |
| 資料庫 | `*.db`、`*.sqlite`、`*.sqlite3`、`*.db-shm`、`*.db-wal` | 🔴 高 |
| 日誌檔案 | `*.log`、`debug_*.log`、`logs/`、`*.out` | 🟠 高 |
| 備份與臨時 | `*.backup`、`*.bak`、`*.orig`、`*_orig.*`、`*_backup.*`、`*.tmp`、`*.temp`、`*~` | 🟡 中 |
| 測試與覆蓋率 | `.pytest_cache/`、`.coverage`、`.coverage.*`、`htmlcov/`、`coverage.xml`、`.tox/`、`.nox/` | 🔵 低 |
| IDE / 編輯器 | `.idea/`、`.vscode/`、`*.swp`、`*.swo`、`.DS_Store`、`Thumbs.db` | 🔵 低 |
| 工具產物 | `.mypy_cache/`、`.ruff_cache/`、`.hypothesis/` | 🔵 低 |

### 2. 根目錄 `.gitignore` — 補充例外規則

**問題**：根目錄規則 `backend/.env.*` 會匹配 `backend/.env.example`，導致該檔案被標記為「已追蹤但應被忽略」的衝突狀態。

**變更**：在 `backend/.env.*` 規則後新增例外：
```gitignore
backend/.env
backend/.env.*
!backend/.env.example  # 範例檔案可安全提交
```

### 3. `backend/.env.example` — 確認現況

檔案已存在且內容完整（涵蓋 `ENCRYPTION_KEY`、`GOOGLE_CLIENT_ID`、`DATABASE_URL` 等所有必要環境變數），本次無需修改。

---

## 驗證結果

### git check-ignore 測試

| 測試檔案 | 匹配規則 | 結果 |
|---------|---------|------|
| `backend/test.db` | `backend/.gitignore:33 *.db` | ✅ 正確忽略 |
| `backend/debug_test.log` | `backend/.gitignore:41 debug_*.log` | ✅ 正確忽略 |
| `backend/backup.bak` | `backend/.gitignore:47 *.bak` | ✅ 正確忽略 |
| `backend/.env.example` | — （exit code 1，不被忽略） | ✅ 正確保留 |

### 違規追蹤檔案清查

執行 `git ls-files --ignored --exclude-standard -c -- backend/` 結果：**無輸出**，即無任何已追蹤但應被忽略的檔案。

---

## 驗收標準確認

- [x] `backend/.gitignore` 包含 `*.db`、`*.sqlite` 規則
- [x] `backend/.gitignore` 包含 `*.log`、`debug_*.log` 規則
- [x] `backend/.gitignore` 包含 `.env.*` 規則
- [x] `backend/.gitignore` 包含 `.pytest_cache/`、`htmlcov/` 規則
- [x] `backend/.env.example` 可安全提交，不被 gitignore 規則遮蔽
- [x] 執行 `git ls-files --ignored -c` 無違規追蹤檔案

---

## 備註

- `backend/.gitignore` 作為 `backend/` 子目錄的獨立保護層，在 Docker Build Context（`COPY . .`）、Git Subtree、部分 IDE 工具等場景中獨立生效
- 根目錄 `.gitignore` 與 `backend/.gitignore` 共存無衝突，為雙重保護
- 測試完成後已清理所有臨時測試檔案（`test.db`、`debug_test.log`、`backup.bak`）
