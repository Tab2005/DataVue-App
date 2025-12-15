# Database Migration Workflow & Best Practices

此文件詳細說明如何在多裝置（A/B 電腦）與多分支（dev-saas / main）的開發環境下，安全地管理資料庫變更。

## ⚠️ 核心原則 (Golden Rules)

1.  **Migration 檔案即真理**：資料庫的所有變更（新增欄位、改名等）都必須透過 Alembic 產生 `.py` 檔案，嚴禁手動進入資料庫執行 SQL 修改。
2.  **保持線性 (Linearity)**：版本號必須像鍊子一樣接續 (`v1 -> v2 -> v3`)，不能有斷層或分岔。
3.  **正式環境禁改**：`main` 分支部署到 Zeabur 時，會自動執行 `upgrade head`。**絕對不要**在 Zeabur 的資料庫上手動修改結構。

---

## 🛠️ 開發標準作業流程 (SOP)

當您需要修改資料庫結構時，請務必**嚴格遵守**以下順序，每一項都不能跳過：

### 1. 準備工作 (Sync First)
在開始寫程式之前，先確保本地環境是最新的。這可以避免您基於舊的版本產生衝突。

```bash
# 1. 把別台電腦 (B) 的進度抓下來
git checkout dev-saas
git pull origin dev-saas

# 2. 讓本地資料庫跟上最新進度
cd backend
alembic upgrade head
```

### 2. 修改與產生 (Modify & Generate)
修改 `database.py` 或相關 Model 程式碼後：

```bash
# 產生新的遷移檔 (請將 "add_user_column" 換成有意義的描述)
alembic revision --autogenerate -m "add_user_column"
```

> **重要檢查點**：
> 執行後，請去 `backend/alembic/versions/` 資料夾看一眼，確認是否真的產生了一個新的 `.py` 檔案，且內容是您預期的修改。

### 3. 提交變更 (Commit & Push)
產生的 `.py` 檔案必須進入版本控制，否則另一台電腦會因為找不到檔案而報錯 (Ghost Revision)。

```bash
# 回到根目錄
cd ..

# 將 migration 檔案加入 Git
git add backend/alembic/versions/*.py

# 提交
git commit -m "db: update database schema for new features"
git push origin dev-saas
```

---

## 💥 衝突解決 (Conflict Resolution)

如果在 `git pull` 時發現別人也改了資料庫，導致 Alembic 報錯（有多個 Heads）：

1.  **查看狀況**：
    ```bash
    cd backend
    alembic heads
    # 輸出範例: 
    # 1a2b3c (head)
    # 4d5e6f (head)  <-- 發現有兩個頭
    ```

2.  **合併分支 (Merge Heads)**：
    ```bash
    alembic merge heads -m "merge_migration_branches"
    ```
    這會產生一個新的 migration 檔，把兩條岔路接回來。

3.  **執行升級與提交**：
    ```bash
    alembic upgrade head
    # 沒錯報後，將新產生的 merge 檔提交
    git add alembic/versions/*.py
    git commit -m "db: merge heads"
    ```

---

## 🚀 部署流程 (Deployment)

### 測試環境 (Dev) -> 正式環境 (Main)

1.  確保 `dev-saas` 分支上的所有功能與資料庫運作正常。
2.  執行 Merge：
    ```bash
    git checkout main
    git merge dev-saas
    git push origin main
    ```
3.  **Zeabur 自動化**：
    Zeabur 偵測到 `main` 更新後，會自動執行 `backend/main.py` 啟動腳本中的 `alembic.command.upgrade(..., "head")`。
    只要您的 Migration 檔案完整，資料庫就會自動更新到最新架構。

---

## 🆘 緊急救援 (Emergency Reset)

如果開發環境資料庫爛掉了（例如 Ghost Revision 無法修復），且資料不重要，可以執行**本地重置**：

1.  刪除本地資料庫檔案：`del facebook_dashboard.db`
2.  重新生成資料庫（不需刪除 migrations，除非是專案初期重構）：
    ```bash
    alembic upgrade head
    ```
3.  如果連 migrations 都亂了，那就是目前的狀況（專案重置），需清空 versions 資料夾並重新 init。

