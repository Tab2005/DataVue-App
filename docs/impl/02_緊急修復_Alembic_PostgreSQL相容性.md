# H-1：修復 Alembic 遷移腳本 PostgreSQL 相容性

> **優先級**：🟠 High  
> **預計工時**：2–3 小時  
> **執行時程**：部署前完成（啟用 PostgreSQL 環境前必須修復）  
> **審查問題編號**：H-1

---

## 問題說明

`backend/alembic/versions/20260223_p3_integrations_indexes.py` 中的資料遷移 SQL 使用了 **SQLite 專用函式**，在 PostgreSQL 環境執行 `alembic upgrade head` 時會立即失敗。

### 問題 SQL（第 69–89 行）

```sql
-- SQLite 專用函式，PostgreSQL 完全不支援
INSERT INTO user_integrations (id, ...)
SELECT
  lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || ...  -- ❌ SQLite UUID 生成
  json_object('app_id', fb_app_id, ...)                                  -- ❌ SQLite JSON 函式
FROM users
WHERE fb_access_token IS NOT NULL
```

### 失敗錯誤（PostgreSQL 環境）

```
sqlalchemy.exc.OperationalError: (psycopg2.errors.UndefinedFunction)
function randomblob(integer) does not exist
LINE 3: lower(hex(randomblob(4))) || '-' || ...
```

---

## 修復策略

**選擇方案：使用 Python-Level 資料遷移**

直接在 `upgrade()` 函式中使用 Python 的 `uuid` 模組生成 UUID，搭配 SQLAlchemy `text()` 執行 INSERT，完全繞開方言差異。

此方案：
- ✅ 對 SQLite 和 PostgreSQL 均相容
- ✅ 不依賴任何資料庫特定函式
- ✅ UUID 在 Python 層生成，確保唯一性
- ❌ 若資料量極大（>10 萬筆）效能略低於純 SQL（但使用者資料通常不會有此問題）

---

## 實作步驟

### Step 1：備份現有遷移腳本

```powershell
cd backend
Copy-Item `
  "alembic/versions/20260223_p3_integrations_indexes.py" `
  "alembic/versions/20260223_p3_integrations_indexes.py.bak"
```

### Step 2：建立新的修復遷移腳本

```powershell
cd backend
alembic revision --autogenerate -m "fix_sqlite_compat_in_integrations_migration"
```

或手動建立（推薦，以精確控制內容）：

**檔案**：`backend/alembic/versions/20260224_fix_integrations_migration_compat.py`

```python
"""fix_integrations_migration_compat

修復 20260223_p3_integrations_indexes.py 中的 SQLite-only 資料遷移語法。
使用 Python uuid 模組生成 UUID，確保在 SQLite 和 PostgreSQL 均可正常執行。

Revision ID: 20260224_fix_integrations_migration_compat
Revises: 0303de3f01eb  （merge head）
Create Date: 2026-02-24
"""
import uuid
import logging
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = "20260224_fix_integrations_migration_compat"
down_revision = "0303de3f01eb"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.migration")


def _migrate_provider_tokens(
    conn,
    provider: str,
    access_token_col: str,
    refresh_token_col: str | None = None,
    expiry_col: str | None = None,
    extra_data_builder=None,
):
    """
    通用函式：將 users 表中的 Token 欄位遷移至 user_integrations 表。
    
    Args:
        conn: SQLAlchemy connection
        provider: 整合提供方名稱 (e.g. "facebook", "google_ads")
        access_token_col: users 表中 access token 欄位名稱
        refresh_token_col: users 表中 refresh token 欄位名稱（可選）
        expiry_col: users 表中 token 過期時間欄位名稱（可選）
        extra_data_builder: 接受 row 並回傳 extra_data dict 的函式（可選）
    """
    # 動態建立 SELECT 語法（只選存在的欄位）
    select_cols = ["id", access_token_col]
    if refresh_token_col:
        select_cols.append(refresh_token_col)
    if expiry_col:
        select_cols.append(expiry_col)

    select_sql = f"SELECT {', '.join(select_cols)} FROM users WHERE {access_token_col} IS NOT NULL"

    try:
        rows = conn.execute(text(select_sql)).fetchall()
    except Exception as e:
        logger.warning(f"遷移 {provider} Token 時發生錯誤（欄位可能不存在）：{e}")
        return 0

    migrated_count = 0
    for row in rows:
        row_dict = dict(row._mapping)
        user_id = row_dict["id"]
        access_token = row_dict[access_token_col]
        refresh_token = row_dict.get(refresh_token_col) if refresh_token_col else None
        token_expiry = row_dict.get(expiry_col) if expiry_col else None

        # 檢查是否已存在（避免重複遷移）
        existing = conn.execute(
            text(
                "SELECT id FROM user_integrations "
                "WHERE user_id = :user_id AND provider = :provider"
            ),
            {"user_id": user_id, "provider": provider},
        ).fetchone()

        if existing:
            logger.debug(f"跳過已存在的整合：user_id={user_id}, provider={provider}")
            continue

        # 建立 extra_data（若有提供的話）
        extra_data = None
        if extra_data_builder:
            try:
                extra_data = extra_data_builder(row_dict)
            except Exception:
                extra_data = None

        conn.execute(
            text("""
                INSERT INTO user_integrations
                    (id, user_id, provider, access_token, refresh_token, token_expiry,
                     extra_data, is_active, created_at, updated_at)
                VALUES
                    (:id, :user_id, :provider, :access_token, :refresh_token, :token_expiry,
                     :extra_data, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """),
            {
                "id": str(uuid.uuid4()),    # ✅ Python 層生成 UUID，跨資料庫相容
                "user_id": user_id,
                "provider": provider,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_expiry": token_expiry,
                "extra_data": str(extra_data) if extra_data else None,
            },
        )
        migrated_count += 1

    logger.info(f"已遷移 {migrated_count} 筆 {provider} 整合資料")
    return migrated_count


def upgrade() -> None:
    conn = op.get_bind()

    # 1. 遷移 Facebook Token
    _migrate_provider_tokens(
        conn,
        provider="facebook",
        access_token_col="fb_access_token",
        expiry_col="token_expires_at",
    )

    # 2. 遷移 Google Ads Token（若存在）
    _migrate_provider_tokens(
        conn,
        provider="google_ads",
        access_token_col="google_ads_access_token",
        refresh_token_col="google_ads_refresh_token",
        expiry_col="google_ads_token_expires_at",
    )

    # 3. 補充建立索引（若尚未存在）
    try:
        op.create_index(
            "ix_user_integrations_lookup",
            "user_integrations",
            ["user_id", "provider"],
        )
    except Exception:
        logger.debug("ix_user_integrations_lookup 索引可能已存在，跳過。")


def downgrade() -> None:
    """
    回滾：刪除此次遷移插入的整合資料。
    注意：此操作不可恢復原始 Token，謹慎執行。
    """
    conn = op.get_bind()

    conn.execute(
        text("DELETE FROM user_integrations WHERE provider IN ('facebook', 'google_ads')")
    )

    try:
        op.drop_index("ix_user_integrations_lookup", table_name="user_integrations")
    except Exception:
        pass
```

---

### Step 3：處理原始遷移腳本

原始腳本 `20260223_p3_integrations_indexes.py` 的資料遷移部分需要修改，以避免在 PostgreSQL 環境重複執行 SQLite-only 語法。

**選項 A（推薦）**：修改原始腳本，移除 SQLite-only 的 INSERT 語句，只保留建表和索引邏輯，資料遷移改由新腳本負責：

```python
# 在 20260223_p3_integrations_indexes.py 的 upgrade() 中
# 移除以下這段 SQL（由新腳本接手）：
# conn.execute("""
#     INSERT INTO user_integrations (id, ...)
#     SELECT lower(hex(randomblob(4))) ...
# """)

# 保留以下部分（建表和索引，這些是跨方言相容的）
op.create_table("user_integrations", ...)
op.create_index("ix_user_integrations_lookup", ...)
```

**選項 B**：將整個舊腳本的 `upgrade()` 包在 `try/except` 中，讓 PostgreSQL 上的舊語法靜默失敗，由新腳本補償。（不推薦，可讀性差）

---

### Step 4：驗證遷移腳本

```powershell
cd backend

# 驗證遷移版本鏈完整性
alembic history --verbose

# 在 SQLite（開發環境）測試
alembic upgrade head

# 在 PostgreSQL（若可用）測試
# 先用 docker compose 啟動 PostgreSQL
docker compose -f ../docker-compose.dev.yml --profile postgres up -d postgres
# 設定 DATABASE_URL 後再執行
$env:DATABASE_URL = "postgresql://..."
alembic upgrade head
```

---

### Step 5：更新遷移版本說明文件

在 `backend/alembic/versions/` 目錄下確保版本鏈清晰：

```
0001_initial_schema
  ↓
20260106_add_permissions_tables
  ↓
20260114_add_ga4_columns
  ↓
230a10d75894_add_saved_views_table
  ↓
fe8441e71f69_add_team_token_expires_at
  ↓
20260223_p3_integrations_indexes（建表+索引，移除舊 SQLite INSERT）
  ↓ (merge)
0303de3f01eb_merge_ga4_and_integrations_heads
  ↓
20260224_fix_integrations_migration_compat（新增：Python-level 資料遷移）
```

---

## 驗收標準

- [ ] `alembic upgrade head` 在 SQLite 環境成功執行（無 ERROR）
- [ ] `alembic upgrade head` 在 PostgreSQL 環境成功執行（無 ERROR）
- [ ] 遷移後 `user_integrations` 表中有正確的資料列
- [ ] `alembic downgrade -1` 可正常回滾
- [ ] 版本鏈 `alembic history` 顯示完整且無分叉

---

## 注意事項

### 已存在遷移的修改風險

若已有生產環境執行過 `20260223_p3_integrations_indexes.py`（SQLite），直接修改此腳本會導致 `alembic_version` 表記錄的 revision ID 與實際執行內容不符。

**建議做法**：
1. **不修改**已執行的舊腳本（保持歷史記錄完整）
2. **新增**新的修復腳本（`20260224_fix_integrations_migration_compat.py`）
3. 新腳本中加入 `IF NOT EXISTS` 保護和重複資料檢查

### CURRENT_TIMESTAMP 跨方言差異

```python
# SQLite: CURRENT_TIMESTAMP → 回傳文字 "YYYY-MM-DD HH:MM:SS"
# PostgreSQL: CURRENT_TIMESTAMP → 回傳 timestamptz 型別

# 若欄位類型為 DateTime，兩者均可正確插入。
# 若欄位為文字型別，需要在 PostgreSQL 中加 ::text 或在 Python 層格式化。

# Python 層最安全的做法：
from datetime import datetime, timezone
now = datetime.now(timezone.utc).isoformat()
```
