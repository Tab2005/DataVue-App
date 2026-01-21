# 資料庫管理與遷移指南 (Database Management & Migration)

本專案使用 **SQLAlchemy** 作為 ORM，並透過 **Alembic** 管理資料庫遷移（Migrations）。這確保了開發環境與正式環境的資料庫結構保持同步。

---

## ⚠️ 核心原則 (Golden Rules)

1. **Migration 檔案即真理**: 所有欄位異動必須透過 Alembic 產生檔案，嚴禁手動修改資料庫結構。
2. **保持線性 (Linearity)**: 資料庫版本號必須連續，不能有斷層或分岔。
3. **提交遷移檔**: 產生的 `.py` 遷移檔案**必須**進入 Git 版本控制，否則部署時會出錯。

---

## 🛠️ 開發作業流程 (SOP)

當您修改了 `backend/database.py` 中的模型（Model）後，請執行以下步驟：

### 1. 產生遷移腳本
在 `backend` 目錄下執行：
```bash
alembic revision --autogenerate -m "描述變更內容"
```
這會在 `backend/alembic/versions/` 下產生一個新的編號檔案。

### 2. 檢查腳本內容
開啟產生的小檔案，確認 `upgrade()` 和 `downgrade()` 內容符合預期。

### 3. 套用至本地資料庫
```bash
alembic upgrade head
```

### 4. 提交變更
```bash
git add backend/alembic/versions/*.py
git commit -m "db: update schema"
```

---

## 🚀 部署與自動更新
本專案在 Zeabur 啟動時，會自動執行 `alembic upgrade head`：
- **本地環境**: 使用 SQLite，啟動時會自動同步或建立。
- **正式環境**: 使用 PostgreSQL，Zeabur 會自動偵測新的遷移檔並套用。

---

## 💥 衝突解決 (Conflict Resolution)

如果在 `git pull` 後發現多個 Heads：
1. **查看狀況**: `alembic heads`
2. **合併分支出口**: `alembic merge heads -m "merge_migration"`
3. **套用與提交**: 執行 `upgrade head` 並提交新產生的 merge 檔案。

---

## 🆘 緊急重置 (Emergency Reset)
如果本地資料庫毀損，可刪除 `facebook_dashboard.db` 並執行 `alembic upgrade head` 重建。正式環境如有結構毀損，請務必先備份資料再聯繫管理員。
