# Permission Tables Migration & Seeding (長期修復)

目標：在 staging/production 正確建立並 seed 權限系統（`modules`, `permissions`, `roles`, `role_permissions`, `user_module_access`, `user_permissions`），並確保部署後不會因為缺表而導致授權失敗或 4xx/5xx。

---

## 1) 準備（務必在 non-production 做一次）
- 先備份資料庫（Postgres: `pg_dump`, SQLite: 直接備份檔案）

Postgres 範例：
```bash
pg_dump "$DATABASE_URL" -Fc -f backup_permissions_$(date +%F).dump
```

SQLite 範例：
```bash
cp backend/facebook_dashboard.db backend/facebook_dashboard.db.bak
```

---

## 2) 在 staging 環境執行（測試）
1. 檢查 migration 是否存在並檢視：
```bash
ls backend/alembic/versions | grep permissions
```
2. 套用 migration（staging）：
```bash
cd backend
alembic upgrade head
```
3. 驗證表已建立：
```bash
psql "$DATABASE_URL" -c "SELECT table_name FROM information_schema.tables WHERE table_name IN ('modules','permissions','roles','role_permissions','user_module_access','user_permissions');"
```
4. 執行 seeding：
```bash
python backend/seed_permissions.py
```
5. 驗證 seed 結果（簡單檢查）：
```bash
psql "$DATABASE_URL" -c "SELECT key,name FROM modules LIMIT 10;"
psql "$DATABASE_URL" -c "SELECT key,name FROM permissions LIMIT 10;"
```

---

## 3) Production 部署步驟（小心謹慎）
1. 備份 production DB（必要）
2. 在 maintenance window 下執行：
```bash
cd backend
alembic upgrade head
python backend/seed_permissions.py
```
3. 如果 seed 失敗，檢查錯誤並回滾（或依情況回復 DB 備份）：
```bash
# 若需要恢復：
pg_restore -d <db_connection_string> backup_permissions_<date>.dump
```

---

## 4) 驗證項目
- 前端登入後 `GET /api/users/me` 回傳正確的 `role` 與 `is_super_admin` 欄位
- Admin 後台可以列出 system modules (e.g., `fb_ads`, `gsc`)
- 權限檢查呼叫（use `permissions` endpoints）能回傳 expected results

---

## 5) 回滾計畫
- 如果 migration 引入問題，利用 `alembic downgrade <revision>` 回到先前版本，或從 DB 備份回復

---

## 6) 其他注意事項
- `main.py` 已新增 guarding：若缺少 permission 表，系統**不會**執行 seed（避免在啟動時觸發錯誤），並會印出明確訊息指示需套用 migration。