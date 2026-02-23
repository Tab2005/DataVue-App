# P0：安全漏洞立即修復

> **優先級**：🔴 P0 — 必須在下次部署前完成  
> **預估工時**：4-8 小時  
> **涵蓋項目**：3.2、6.1、6.2

---

## 目錄

1. [3.2 — 修復 Token 驗證 LRU Cache 安全漏洞](#32--修復-token-驗證-lru-cache-安全漏洞)
2. [6.1 — 確認並修復 .env 未提交至 Git](#61--確認並修復-env-未提交至-git)
3. [6.2 — 確認並修復 SQLite DB 文件未提交至 Git](#62--確認並修復-sqlite-db-文件未提交至-git)

---

## 3.2 — 修復 Token 驗證 LRU Cache 安全漏洞

### 問題說明

`dependencies.py` 使用 Python 標準庫的 `@lru_cache` 快取 Google Token 驗證結果：

```python
# 目前程式碼（有安全漏洞）
@lru_cache(maxsize=128)
def _verify_token_cached(token: str):
    return id_token.verify_oauth2_token(...)
```

**風險**：`lru_cache` 沒有 TTL（存活時間）。Google ID Token 有效期為 1 小時，但快取結果會**永久保留直到進程重啟**。這表示：
- 使用者登出後，被撤銷的 Token 仍可通過驗證
- 帳號被停用的使用者仍能繼續存取 API
- 攻擊者取得舊 Token 後可維持非法存取

### 修復步驟

**步驟 1：安裝 `cachetools`（若尚未安裝）**

```bash
cd backend
pip install cachetools
```

**步驟 2：修改 `dependencies.py`**

找到現有的 `lru_cache` 實作並替換：

```python
# ❌ 移除以下程式碼
from functools import lru_cache

@lru_cache(maxsize=128)
def _verify_token_cached(token: str):
    return id_token.verify_oauth2_token(
        token, google_requests.Request(), GOOGLE_CLIENT_ID,
        clock_skew_in_seconds=60
    )
```

```python
# ✅ 替換為以下程式碼
from cachetools import TTLCache, cached
import threading

# 初始化 TTL 快取：最多 128 個 Token，每個快取 5 分鐘（300 秒）
# TTL 設定遠短於 Google Token 的 1 小時有效期，確保撤銷的 Token 在 5 分鐘內失效
_token_cache: TTLCache = TTLCache(maxsize=128, ttl=300)
_token_cache_lock = threading.Lock()

@cached(cache=_token_cache, lock=_token_cache_lock)
def _verify_token_cached(token: str) -> dict:
    """
    驗證 Google ID Token 並快取結果（TTL: 5 分鐘）。
    
    使用 TTLCache 替代 lru_cache 以確保撤銷的 Token 在 5 分鐘內失效。
    多執行緒環境下使用 threading.Lock 保護快取操作。
    
    Args:
        token: Google ID Token 字串
        
    Returns:
        Google 返回的 id_info 字典
        
    Raises:
        ValueError: Token 無效或已過期
    """
    return id_token.verify_oauth2_token(
        token,
        google_requests.Request(),
        settings.GOOGLE_CLIENT_ID,
        clock_skew_in_seconds=60
    )
```

**步驟 3：更新 `requirements.txt`（確保 cachetools 已列出）**

```
cachetools>=5.3.0,<6.0.0
```

**步驟 4：驗證修復**

```python
# 可在 Python REPL 中測試快取行為
from cachetools import TTLCache, cached
import time

cache = TTLCache(maxsize=10, ttl=5)  # 5 秒 TTL（測試用）

@cached(cache=cache)
def test_func(x):
    print(f"  → 實際計算 {x}")
    return x * 2

print("第一次呼叫（應執行計算）：", test_func("abc"))
print("第二次呼叫（應使用快取）：", test_func("abc"))
time.sleep(6)
print("6秒後呼叫（TTL 過期，應重新計算）：", test_func("abc"))
```

### 驗收標準

- [ ] `@lru_cache` 已完全移除，替換為 `TTLCache + @cached`
- [ ] TTL 設定為 300 秒（5 分鐘），遠小於 Token 1 小時有效期
- [ ] 多執行緒鎖已添加（`threading.Lock()`）
- [ ] `cachetools` 已加入 `requirements.txt` 並釘定版本
- [ ] 伺服器重啟後驗證 Token 快取正常運作

---

## 6.1 — 確認並修復 `.env` 未提交至 Git

### 問題說明

`backend/.env` 包含極度敏感的設定值：
- Google OAuth Client ID / Secret
- Facebook App ID / Secret
- 資料庫連線字串
- JWT Secret Key
- Redis 密碼
- AI API Keys

若 `.env` 已提交至 Git 歷史，即使後來刪除，任何能存取儲存庫的人仍可透過 git log 取得歷史記錄。

### 修復步驟

**步驟 1：檢查目前 Git 追蹤狀態**

```powershell
cd "d:\users\Qoo\Documents\python\DataVue-App"

# 檢查 .gitignore 是否已排除 .env
Get-Content .gitignore | Select-String "\.env"
Get-Content backend\.gitignore -ErrorAction SilentlyContinue | Select-String "\.env"

# 檢查 .env 是否被 Git 追蹤
git ls-files backend/.env
git ls-files --error-unmatch backend/.env 2>&1
```

**步驟 2：確認 `.gitignore` 內容**

確保根目錄或 `backend/` 目錄下的 `.gitignore` 包含：

```gitignore
# 敏感設定檔（絕對不能提交）
.env
.env.local
.env.*.local
backend/.env
backend/.env.*

# 資料庫文件
*.db
*.sqlite
*.sqlite3
backend/*.db

# 除錯日誌
debug_*.log
backend/debug_*.log
*.log

# Python 快取
__pycache__/
*.py[cod]
*.pyo
venv/
.venv/
env/
*.egg-info/

# IDE 設定
.idea/
.vscode/settings.json
*.swp
*.swo

# 測試與覆蓋率
.coverage
htmlcov/
.pytest_cache/

# 建置產物
dist/
build/
node_modules/
frontend/dist/
```

**步驟 3：若 `.env` 已被 Git 追蹤，立即停止追蹤**

```powershell
# 從 Git 追蹤中移除（不刪除本地文件）
git rm --cached backend/.env

# 提交此變更
git add .gitignore
git commit -m "security: remove .env from git tracking"
```

**步驟 4：若 `.env` 已提交至 Git 歷史（嚴重情況）**

```powershell
# 選項 A：使用 BFG Repo Cleaner（推薦，比 filter-branch 快）
# 1. 下載 BFG: https://rtyley.github.io/bfg-repo-cleaner/
java -jar bfg.jar --delete-files .env

# 選項 B：使用 git filter-repo（新版替代方案）
pip install git-filter-repo
git filter-repo --path backend/.env --invert-paths

# 完成後必須強制推送
git push origin --force --all
git push origin --force --tags
```

> ⚠️ **強制推送後所有協作者必須重新 clone 儲存庫！**

**步驟 5：立即撤銷所有已洩露的金鑰**

若確認 `.env` 已進入 Git 歷史，必須立即重新生成所有密鑰：

| 金鑰類型 | 撤銷方式 |
|----------|----------|
| Google OAuth | [Google Cloud Console](https://console.cloud.google.com/) → API & Services → Credentials → 重新生成 |
| Facebook App Secret | [Facebook Developers](https://developers.facebook.com/) → App Settings → 重設 App Secret |
| Fernet Key（JWT） | 執行 `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| Redis Password | 更新 Redis 設定並重新部署 |
| Zeabur AI Key | 在 Zeabur 控制台重新生成 |
| Gemini API Key | [Google AI Studio](https://aistudio.google.com/) → Get API Key → 刪除舊的並建立新的 |

**步驟 6：建立 `.env.example` 範本**

```bash
# backend/.env.example（安全的範本，不含真實值，可以提交至 Git）
# 複製此文件為 .env 並填入真實值

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Facebook
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret

# 資料庫
DATABASE_URL=sqlite:///./facebook_dashboard.db
# 生產環境使用 PostgreSQL:
# DATABASE_URL=postgresql://user:password@host:5432/datavue

# 安全加密金鑰（使用 Fernet 生成）
SECRET_KEY=your-fernet-key-here

# Redis（選配）
REDIS_URL=redis://localhost:6379/0

# AI 服務
AI_PROVIDER=gemini  # 或 zeabur
GEMINI_API_KEY=your-gemini-api-key
ZEABUR_API_KEY=your-zeabur-api-key

# 應用設定
ENVIRONMENT=development  # development | production
DEBUG=true
ALLOWED_ORIGINS=http://localhost:5173
```

### 驗收標準

- [ ] `backend/.env` 不在 `git ls-files` 的結果中
- [ ] `.gitignore` 已包含 `.env`、`*.db`、`*.log` 等規則
- [ ] `.env.example` 已建立並提交至儲存庫
- [ ] 若有歷史洩露，所有金鑰已重新生成
- [ ] 所有協作者已收到通知並更新本地設定

---

## 6.2 — 確認並修復 SQLite DB 文件未提交至 Git

### 問題說明

`backend/facebook_dashboard.db`（SQLite 資料庫文件）可能包含：
- 使用者真實 Email 地址
- 加密的 Facebook / Google OAuth Tokens
- 廣告帳號 ID
- 搜尋查詢歷史

SQLite `.db` 文件是二進位制格式，可直接用 SQLite Browser 等工具開啟讀取所有資料。

### 修復步驟

**步驟 1：檢查 DB 文件的 Git 狀態**

```powershell
cd "d:\users\Qoo\Documents\python\DataVue-App"

# 列出所有被 Git 追蹤的 .db 文件
git ls-files "*.db" "*.sqlite" "*.sqlite3"

# 檢查 Git 歷史中是否曾有 .db 文件
git log --all --full-history -- "*.db" "*.sqlite"
```

**步驟 2：從 Git 追蹤中移除**

```powershell
# 移除追蹤（保留本地文件）
git rm --cached backend/facebook_dashboard.db
git rm --cached "backend/*.db" 2>$null

# 確認 .gitignore 已包含 *.db
Add-Content -Path .gitignore -Value "`n# SQLite 資料庫文件`n*.db`n*.sqlite`n*.sqlite3"

# 提交
git add .gitignore
git commit -m "security: remove SQLite DB files from git tracking"
```

**步驟 3：若 DB 文件已在 Git 歷史中（嚴重情況）**

```powershell
# 使用 git filter-repo 清除歷史
git filter-repo --path backend/facebook_dashboard.db --invert-paths

# 強制推送（所有協作者需重新 clone）
git push origin --force --all
```

**步驟 4：通知可能受影響的使用者**

若 DB 文件曾進入公開儲存庫，需：
1. 評估哪些使用者資料可能洩露
2. 根據 GDPR / 個資法進行事件通報（若適用）
3. 撤銷所有儲存在 DB 中的 OAuth Token（讓使用者重新授權）

**步驟 5：設定 Alembic 不追蹤 DB 文件**

確認 `alembic.ini` 的 `sqlalchemy.url` 在開發環境使用相對路徑，並確保產生的 DB 文件在 `.gitignore` 覆蓋範圍內：

```ini
# alembic.ini
sqlalchemy.url = sqlite:///./facebook_dashboard.db
# 此文件（facebook_dashboard.db）應在 .gitignore 中
```

### 驗收標準

- [ ] `git ls-files "*.db"` 返回空結果
- [ ] `.gitignore` 已包含 `*.db`、`*.sqlite`、`*.sqlite3`
- [ ] 若有歷史洩露，已通知相關使用者並撤銷相關授權 Token
- [ ] `backend/` 目錄的 `.gitignore` 或根目錄 `.gitignore` 已更新

---

## 執行清單總結

```
今天必須完成：

□ 1. 執行 git ls-files 確認 .env 和 .db 的追蹤狀態
□ 2. 更新 .gitignore（若未包含相關規則）
□ 3. 執行 git rm --cached 移除敏感文件的追蹤
□ 4. 若已洩露至歷史：執行 filter-repo 清理 + 強制推送 + 重新生成所有金鑰
□ 5. 建立 .env.example 並提交
□ 6. 修改 dependencies.py：lru_cache → TTLCache (TTL=300s)
□ 7. 確認 cachetools 在 requirements.txt 中有版本釘定
□ 8. 重啟伺服器並測試登入功能正常
```
