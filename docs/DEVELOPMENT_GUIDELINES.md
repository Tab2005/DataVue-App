# 開發指南 (Development Guidelines)

本文檔描述 DataVue App 的開發最佳實踐，特別是資料庫變更相關的注意事項。

---

## 資料庫欄位變更檢查清單

當新增、修改或刪除資料庫欄位時，**必須同時更新以下三處**：

### ✅ 必要步驟

| 步驟 | 檔案位置 | 說明 |
|------|----------|------|
| 1️⃣ | `backend/database.py` | 更新 SQLAlchemy Model 定義 |
| 2️⃣ | `backend/alembic/versions/` | 建立新的 Alembic migration 檔案 |
| 3️⃣ | `backend/core/startup.py` | 加入 `user_patches` 或 `team_patches`（Fallback 機制）|

### 📝 Migration 檔案命名規則

```
YYYYMMDD_描述.py
例如: 20260114_add_ga4_columns.py
```

### ⚠️ 常見錯誤

- ❌ 只更新 `database.py`，忘記寫 migration
- ❌ 本地 SQLite 測試正常，但雲端 PostgreSQL 缺少欄位
- ❌ 新功能合併後，雲端服務出現 500 錯誤

---

## AI 協助開發指令範本

當請求 AI 協助開發涉及資料庫的功能時，請使用以下指令範本：

### 🤖 新增功能（含資料庫欄位）

```
請幫我實作 [功能名稱]。

需求：
- [功能描述]

注意事項：
- 如果需要新增資料庫欄位，請同時：
  1. 更新 backend/database.py 的 Model
  2. 建立 Alembic migration 檔案
  3. 更新 backend/core/startup.py 的 schema patcher
```

### 🤖 修改現有功能（可能涉及資料庫）

```
請幫我修改 [功能名稱]。

修改內容：
- [具體修改描述]

提醒：如果涉及資料庫變更，請確保同時更新 migration 和 startup.py。
```

### 🤖 快速檢查指令

```
請檢查 backend/database.py 的 Model 定義與 Alembic migrations 是否一致，
列出所有缺少 migration 的欄位。
```

---

## 本地開發環境

### 推薦：使用 PostgreSQL 進行本地測試

為了與雲端環境一致，建議使用 Docker 運行 PostgreSQL：

```bash
# 啟動 PostgreSQL
docker run -d --name datavue-postgres \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=datavue \
  -e POSTGRES_DB=datavue \
  postgres:15

# 設定環境變數
DATABASE_URL=postgresql://postgres:datavue@localhost:5432/datavue
```

### 現有開發腳本

```powershell
# 一鍵啟動開發環境
.\start-dev.ps1

# 或分開啟動
.\quick-start.ps1 backend
.\quick-start.ps1 frontend
```

---

## PR Review Checklist

提交 PR 時，如果包含資料庫變更，請在 PR 描述中確認：

```markdown
## 資料庫變更確認

- [ ] 已更新 `backend/database.py` Model
- [ ] 已建立 Alembic migration
- [ ] 已更新 `backend/core/startup.py` schema patcher
- [ ] 已在本地測試 migration 執行成功
```

---

## 相關檔案

- [database.py](../backend/database.py) - SQLAlchemy Models
- [startup.py](../backend/core/startup.py) - Schema Patcher
- [alembic/versions/](../backend/alembic/versions/) - Migration 檔案
