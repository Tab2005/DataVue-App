# P0 安全漏洞修復 — 實作報告

> **執行分支**：`dev-saas`  
> **實作日期**：2026-02-23  
> **提交 Hash**：`b34b108`  
> **狀態**：✅ 全部完成

---

## 執行摘要

依據 `01_P0_security_critical.md` 的要求，完成以下三項 P0 安全修復：

| 項目 | 說明 | 狀態 |
|------|------|------|
| 3.2 | Token 驗證 LRU Cache → TTLCache | ✅ 完成 |
| 6.1 | `.env` Git 追蹤狀態確認與 `.gitignore` 更新 | ✅ 完成 |
| 6.2 | SQLite DB 文件從 Git 追蹤中移除 | ✅ 完成 |

---

## 3.2 — Token 驗證 TTLCache 修復

### 修改檔案

`backend/dependencies.py`

### 變更內容

**移除**：

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def _verify_token_cached(token: str):
    """Internal helper to verify token with caching."""
    return id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=60)
```

**替換為**：

```python
from cachetools import TTLCache, cached
import threading

# 初始化 TTL 快取：最多 128 個 Token，每個快取 5 分鐘（300 秒）
_token_cache: TTLCache = TTLCache(maxsize=128, ttl=300)
_token_cache_lock = threading.Lock()

@cached(cache=_token_cache, lock=_token_cache_lock)
def _verify_token_cached(token: str) -> dict:
    """
    驗證 Google ID Token 並快取結果（TTL: 5 分鐘）。
    使用 TTLCache 替代 lru_cache 以確保撤銷的 Token 在 5 分鐘內失效。
    多執行緒環境下使用 threading.Lock 保護快取操作。
    """
    return id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=60)
```

### 驗收標準確認

- [x] `@lru_cache` 已完全移除，替換為 `TTLCache + @cached`
- [x] TTL 設定為 300 秒（5 分鐘），遠小於 Token 1 小時有效期
- [x] 多執行緒鎖已添加（`threading.Lock()`）
- [x] `cachetools` 已加入 `requirements.txt` 並釘定版本

---

## 6.1 — `.env` Git 追蹤狀態確認

### 調查結果

```
git ls-files backend/.env  →  （無輸出，表示未被追蹤）✅
git log --all -- "*.env"   →  （無歷史記錄）✅
```

**`.env` 從未進入 Git 歷史**，無需執行 `filter-repo` 清理。

### 修改檔案

`.gitignore`（根目錄）與 `backend/.env.example`

### `.gitignore` 變更

補全了以下缺漏規則：

| 新增規則 | 說明 |
|----------|------|
| `.env` | 根目錄 .env（通用規則） |
| `.env.local` | 本地覆蓋設定 |
| `.env.*.local` | 環境特定本地設定 |
| `backend/.env.*` | backend 所有 .env 變體 |
| `*.sqlite` | SQLite 資料庫（副檔名變體） |
| `*.sqlite3` | SQLite3 資料庫 |
| `backend/*.db` | backend 目錄下所有 DB 文件（明確指定） |
| `*.py[cod]` | Python 編譯快取（取代 `*.pyc`） |
| `*.pyo` | Python 優化位元組碼 |
| `env/` | 另一常見虛擬環境目錄名稱 |
| `.vscode/settings.json` | 個人 IDE 設定（保留 .vscode/ 其他檔案） |
| `debug_*.log` | Debug 日誌 |
| `.coverage` | 測試覆蓋率資料 |
| `htmlcov/` | 覆蓋率 HTML 報告 |
| `.pytest_cache/` | pytest 快取 |
| `*.egg-info/` | Python 套件元資料 |
| `dist/` | 建置輸出目錄 |
| `build/` | 建置中間產物 |

### `.env.example` 更新

更新 `backend/.env.example` 為完整版，新增：

- `ZEABUR_AI_HUB_API_KEY`（AI 服務）
- `GOOGLE_AI_API_KEY`（Gemini AI）
- `ENV`（環境類型）
- 完整的中文說明與生成指令
- 安全警告標語

### 驗收標準確認

- [x] `git ls-files backend/.env` 返回空結果（未追蹤）
- [x] `.gitignore` 已包含 `.env`、`*.db`、`*.log` 等規則
- [x] `.env.example` 已更新並包含所有環境變數

---

## 6.2 — SQLite DB 文件從 Git 追蹤中移除

### 調查結果

```
git ls-files "*.db"  →  backend/facebook_dashboard.db  ⚠️（曾被追蹤）
git log -- "backend/facebook_dashboard.db"（有 4 筆提交記錄）
```

**DB 文件已進入 Git 歷史**（4 筆 commit），但本儲存庫為**私有／開發環境**，評估為低風險。

### 行動

```powershell
git rm --cached backend/facebook_dashboard.db
git add .gitignore
git commit -m "security(P0): ..."
```

DB 文件已從追蹤中移除，本地檔案保留不受影響。

### 歷史足跡說明

雖然 DB 文件從 Git 追蹤中移除，過去的 commit 歷史仍包含此文件的快照。若需要**完全清除歷史**（適用於公開儲存庫或確認資料洩露的情況），需執行：

```powershell
# 使用 git filter-repo 清除歷史（需要先安裝：pip install git-filter-repo）
git filter-repo --path backend/facebook_dashboard.db --invert-paths
git push origin --force --all
```

> ⚠️ 目前未執行 filter-repo，因儲存庫為開發私有環境，風險可接受。  
> 若未來轉為公開儲存庫，**必須**執行上述清理並重新生成所有金鑰。

### 驗收標準確認

- [x] `git ls-files "*.db"` 返回空結果（已從追蹤移除）
- [x] `.gitignore` 已包含 `*.db`、`*.sqlite`、`*.sqlite3`
- [x] 已記錄歷史足跡風險與清除方案

---

## `requirements.txt` 版本釘定

### 修改前

```
cachetools
```

### 修改後

```
cachetools>=5.3.0,<6.0.0
```

釘定主版本範圍，防止破壞性版本升級。

---

## Git 提交記錄

```
commit b34b108
Branch: dev-saas
Message: security(P0): fix token cache TTL, gitignore, remove DB tracking

Files changed (5):
  M  .gitignore
  M  backend/.env.example
  M  backend/dependencies.py
  M  backend/requirements.txt
  D  backend/facebook_dashboard.db
```

---

## 待後續處理項目

> 以下項目目前評估為低風險，但建議在特定情境下執行：

1. **Git 歷史清理**（若儲存庫需公開）：執行 `git filter-repo` 清除 `backend/facebook_dashboard.db` 歷史
2. **定期 Token 快取監控**：可考慮加入快取命中率指標至 logging，監控 TTLCache 效能
3. **Redis Session 管理**（長期）：若安全需求進一步提升，可將 Token 驗證結果改存 Redis，支援主動撤銷功能
