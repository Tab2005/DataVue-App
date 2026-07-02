# DataVue-App 優化行動具體實作方案（P0–P2）

> 產出日期：2026-07-01
> 對應審查報告：[`CODE_REVIEW_2026-07-01.md`](./CODE_REVIEW_2026-07-01.md)
> 用途：將審查報告中的 P0/P1/P2 建議展開為可執行的具體修改方案（含檔案、步驟、程式碼骨架、驗證方式）

---

## 目錄

- [P0 — 安全與資料完整性](#p0--安全與資料完整性)
  - [P0-1 收斂 DB Schema 管理為單一 Alembic 路徑](#p0-1-收斂-db-schema-管理為單一-alembic-路徑)
  - [P0-2 `/health` 端點資訊洩漏拆分](#p0-2-health-端點資訊洩漏拆分)
  - [P0-3 移除／隔離生產環境的除錯與一次性腳本](#p0-3-移除隔離生產環境的除錯與一次性腳本)
- [P1 — 架構收斂](#p1--架構收斂)
  - [P1-1 ga4 / gsc / ai_hub 空殼模組決策](#p1-1-ga4--gsc--ai_hub-空殼模組決策)
  - [P1-2 路由統一到 modules/*/router.py](#p1-2-路由統一到-modulesrouterpy)
  - [P1-3 config.py 遷移至 Pydantic BaseSettings](#p1-3-configpy-遷移至-pydantic-basesettings)
  - [P1-4 Meta Andromeda 記憶體內狀態改用 Redis](#p1-4-meta-andromeda-記憶體內狀態改用-redis)
- [P2 — 可維護性](#p2--可維護性)
  - [P2-1 拆分巨型檔案](#p2-1-拆分巨型檔案)
  - [P2-2 前端漸進導入 TypeScript](#p2-2-前端漸進導入-typescript)
  - [P2-3 補強測試覆蓋](#p2-3-補強測試覆蓋)
  - [P2-4 指標定義單一事實來源](#p2-4-指標定義單一事實來源)
- [執行順序總表](#執行順序總表)

---

## P0 — 安全與資料完整性

### P0-1 收斂 DB Schema 管理為單一 Alembic 路徑 ✅ 已完成（2026-07-01）

**原始問題定位**
目前有三套機制同時管理 schema：
1. `core/startup.py::run_migrations()` → 執行 Alembic（正統）
2. `core/startup.py::patch_database_schema(engine)`（原 L135-249）→ 手動 `ALTER TABLE ADD COLUMN` / `CREATE TABLE`
3. `database/__init__.py::init_db()` → `create_all()` + 額外兩處獨立的 fail-safe `ALTER TABLE`（`users.line_user_id`、`report_schedules.is_notify_line`）— **原計畫遺漏了這一層**，實際稽核時才發現這是第三套、與 `patch_database_schema` 各自獨立的補丁機制。

**實際稽核結果（用全新 SQLite 空庫直接跑 `alembic upgrade head` 實測，而非僅靜態比對）**

原計畫假設「大部分 patch 項目已被既有 migration 涵蓋，僅需少量補件」，但實測發現落差遠比預期大且會直接讓全新資料庫的 `alembic upgrade head` 中途崩潰：

| 項目 | 稽核結果 |
|---|---|
| `teams.visible_ad_account_ids` / `fb_app_id` / `fb_access_token` / `token_expires_at` | ✅ 已被 `0001_initial_schema.py` + `fe8441e71f69` 完整涵蓋，`patch_database_schema` 對應區塊本來就是 dead code |
| `users.ga4_*` / `openrouter_api_key` | ✅ 已涵蓋（`20260114_add_ga4_columns.py`、`46c781526b51`） |
| `saved_views` 表 | ⚠️ **鏈上存在孤立矛盾**：`230a10d75894` 已建出新版 schema（含 metrics/team_id/created_by），但 `403dfb0cfbd4` 的 `batch_alter_table` 卻假設舊版 raw-SQL 補丁 schema（type/config 欄位）存在並嘗試再次新增/刪除，全新資料庫上會直接拋 `KeyError`。**已修復**：於 `403dfb0cfbd4` 內加入 `type` 欄位存在性檢查，僅在偵測到舊版 schema 時才執行遷移邏輯 |
| `page_titles` 表 | 🔴 **從未被任何 migration 建立**，僅靠 `patch_database_schema`／`create_all()` 存在。`403dfb0cfbd4` 對它做 `batch_alter_table` 假設表已存在，全新資料庫上實測直接拋 `NoSuchTableError: page_titles` |
| `report_schedules` 表本體 | 🔴 **從未被任何 migration 建立**（只有後續 migration 對它 `add_column`），同樣僅靠 `create_all()` 存在 |
| `line_bindings` 表本體 | 🔴 同上，從未被任何 migration 建立 |
| `users.gsc_access_token/refresh_token/expires_at`、`zeabur_api_key`、`gemini_api_key`、`ai_provider`、`ai_model`、`line_user_id` | 🔴 從未被任何 migration `add_column`，僅靠執行期補丁存在 |
| `weekly_reports.share_token` | 🔴 從未被任何 migration 加入 |
| `report_schedules.is_notify_line` | 🔴 從未被任何 migration 加入（僅存在於 `init_db()` 的獨立 fail-safe） |
| （附帶發現）`ix_user_module_access_composite` 索引 | ⚠️ `20260223_p3_integrations_indexes.py` 因分支合併順序問題，在全新資料庫上此索引建立會被自身的 `try/except` 靜默吞掉，從未真正建立（效能索引，非阻斷性問題，已一併補上） |

**已完成的變更**

1. 新增 migration `backend/alembic/versions/20260701_consolidate_legacy_schema_patches.py`：
   - `down_revision` 指向 `20260331_merge_all_heads`，**插入**在 `403dfb0cfbd4` 之前執行（而非簡單接在 head 之後）——因為 `403dfb0cfbd4` 對 `page_titles`／`report_schedules` 的 `batch_alter_table` 需要這些表在它執行時就已存在。所有動作皆先檢查存在性，對已具備該欄位/表的環境（即所有目前運行中的既有環境，因為它們都已透過執行期補丁擁有這些欄位/表）為 no-op。
   - 補上 `report_schedules`、`line_bindings`、`page_titles` 三張表的 `create_table`；`users` 的 8 個舊版欄位；`weekly_reports.share_token`；`report_schedules.is_notify_line`；`ix_user_module_access_composite` 索引。
2. 修改 `403dfb0cfbd4_add_module_type_to_reports.py`：`down_revision` 改指向新 migration；`saved_views` 區塊加上「是否仍為舊版 schema」的存在性檢查後才執行（見上表）。
3. `core/startup.py`：**完整移除** `patch_database_schema()` 函式（115 行）與其呼叫，`run_startup_tasks()` 步驟重新編號。
4. `database/__init__.py::init_db()`：移除 `line_user_id`／`is_notify_line` 兩處獨立 fail-safe `ALTER TABLE`（現已由 migration 涵蓋）；保留 `required_tables` 存在性檢查與 SQLite-only 的 emergency `create_all()`（僅在 migrations 未執行的異常情況下才會觸發，且 PostgreSQL 生產環境不受影響，暫不在本次變更中移除，作為更保守的雙重保險）。

**驗證結果**
- ✅ 全新空 SQLite 資料庫執行 `alembic upgrade head`：完整跑完全部 20 個 migration 無崩潰。
- ✅ 事後以 `Base.metadata` 對照全新資料庫實際 schema：**零落差**（所有表、所有欄位完全一致）。
- ✅ 對現有本機開發資料庫（`facebook_dashboard.db`，起始於落後 head 一版）套用同一鏈：僅執行最後一版 migration（新 migration 因該庫已越過插入點而被 Alembic 判定為免執行，符合預期），資料列數量不變，無資料流失。
- ✅ 完整跑一次 `run_startup_tasks()`（migrations → init_db → Meta Andromeda seed → permission seed → super admin sync）於全新資料庫：全部成功，回傳 `True`。
- ✅ `pytest tests/` 前後比對：**79 passed / 12 failed，變更前後失敗清單完全相同**（12 個失敗為既有問題，與網路依賴的 Meta Andromeda 測試及一個時區相關的 scheduler 測試有關，與本次改動無關，已用 `git stash` 驗證基準）。
- ✅ `tests/test_health.py`：5 passed。

**發現但刻意不在本次修復範圍內的問題**（留給後續追蹤）：
1. `403dfb0cfbd4` 原本的 `downgrade()` 函式本身有預先存在的 bug（`batch_op.drop_constraint(None, type_='foreignkey')` 缺少具名約束，SQLAlchemy 較新版本會拋 `ValueError: Constraint must have a name`）。這與本次改動無關（我只改了它的 `upgrade()` 與 `down_revision`），且此專案的 19+ 個既有 migration 顯示 `downgrade()` 路徑從未被實際使用過。不建議現在修，因為需要對每支 migration 的 downgrade 個別檢查，屬於獨立的中型任務。
2. 本機開發資料庫 `facebook_dashboard.db` 的 `meta_andromeda_assets`（缺 `storage_backend`/`storage_key`/`public_url`）與 `meta_andromeda_score_events`（缺 `queued_at`/`started_at`/`completed_at`/`failed_at`/`attempt_count`/`runtime_job_id`）兩張表，相較於目前 ORM model 有欄位缺漏。**已確認這是本機開發資料庫特有的歷史殘留**（在全新資料庫上跑相同 migration 鏈完全沒有此問題，證明 migration 本身完整）；研判是這兩張表早年由 `create_all()` 以舊版 model 建立，之後 model 新增了這些欄位但從未有對應 migration 或補丁去 `ALTER` 既有的本機表。**建議**：在部署到 staging/production 前，用本文件描述的稽核手法（全新 DB 跑 `alembic upgrade head` + 對照 `Base.metadata`）先確認 staging/production 資料庫是否也有此殘留；若本機資料不重要可考慮直接刪除重建這兩張表，或另開一支 migration 修補。

**風險評估**：低（已完整驗證，含真實 PostgreSQL，見下）。

---

### P0-1 補充：真實 PostgreSQL 驗證，發現並修復 3 個獨立的既有 bug ✅ 已完成（2026-07-01）

**背景**：用戶詢問「上述情形（P0-1 的發現）跟直接部署在網路 PostgreSQL 資料庫有關嗎？」。為了給出實證而非推論的答案，用戶提供了一組正式環境的 PostgreSQL 連線資訊。經確認該資料庫已有 29 張表、3 個真實使用者、`alembic_version` 已在 head，屬於**正式環境**。因此**全程未對該資料庫本身做任何寫入操作**，改為在同一台 PostgreSQL 主機上另建一個完全獨立、用完即刪的空白資料庫 `datavue_p0_1_test` 進行驗證（PostgreSQL 18.3）。

這次驗證額外挖出 **3 個完全獨立於 P0-1 原始範圍、但同樣阻斷「全新 PostgreSQL 資料庫跑 `alembic upgrade head`」的既有 bug**。三者的共同根因：這個專案的 migration 鏈**從第一支（`0001_initial_schema.py`）開始，就從來沒有在真正全新的 PostgreSQL 資料庫上被完整測試過**——所有真實環境都是靠 `patch_database_schema()`／`create_all()` 建表，或被 `run_migration.py` 的 legacy-stamping 邏輯直接跳過大部分早期 migration。

#### 發現 1：`0001_initial_schema.py` — ENUM type 重複建立

**現象**：全新 PostgreSQL 資料庫上第一支 migration 就報錯：
```
psycopg2.errors.DuplicateObject: type "userrole" already exists
```
**根因**：程式碼裡手動用 `DO $$ BEGIN IF NOT EXISTS (...) THEN CREATE TYPE userrole ... END $$;` 先建立一次 ENUM type（防呆），但緊接著 `op.create_table('users', ...)` 裡 `sa.Enum(name='userrole')` 欄位會觸發 SQLAlchemy **自動且無條件**（`checkfirst=False`，Alembic 的預設行為）再建立一次同名 type，兩者互相打架。

**修復**：移除手動 `DO $$` 區塊，只保留 `op.create_table()` 自身的自動建立。SQLAlchemy 對同一個具名 type 在同一次 migration 執行過程中會透過內部 memo 去重，所以 `team_members` 表重複引用同一個 `userrole` type 不會導致重複建立。

（過程中曾嘗試用 `sa.Enum(..., create_type=False)` 修復，經追查 SQLAlchemy 原始碼確認 `create_type` 並非通用 `sa.Enum` 支援的參數、只在 `sqlalchemy.dialects.postgresql.ENUM` 上有效，此路不通，已改用上述根本修復。）

#### 發現 2：`20260223_p3_integrations_indexes.py` — try/except 在 PostgreSQL 下不安全

**現象**：修復發現 1 後，下一步報錯：
```
psycopg2.errors.InFailedSqlTransaction: current transaction is aborted, commands ignored until end of transaction block
```
**根因**：這支 migration 對 `ix_user_module_access_composite` 索引建立包了 `try/except Exception`，因為此時 `user_module_access` 表確實還不存在（分支合併順序問題，程式碼註解本身也承認這點）。**在 SQLite 上，單一語句失敗不會拖累同一交易內的後續語句，所以 try/except 能正常吞掉錯誤繼續跑；但 PostgreSQL 的交易語意不同——任何一條語句出錯，整個交易會被標記為 aborted，之後所有語句（包含另外兩個原本會成功的索引、以及 Alembic 自動更新 `alembic_version` 的 UPDATE）全部被拒絕**，導致整支 migration 中止，且因為 PostgreSQL 下 Alembic 預設把一次 `upgrade()` 呼叫內的所有 migration 包在同一個外層交易，最終連前面已成功的 `0001` 等 migration 也會被整批回滾。

**修復**：移除 `ix_user_module_access_composite` 這個確定會失敗的嘗試（改由本次新增的 `20260701_consolidate_legacy_schema_patches.py` 在該表確定存在後補建，原本就是為此設計）；另外兩個索引（`team_members`、`saved_views`，兩張表在此時間點確定已存在）改為直接呼叫，不再假裝需要防呆。

#### 發現 3：`20260224_fix_integrations_migration_compat.py` — 同樣的 try/except 交易汙染問題

**現象**：修復發現 2 後，下一步同樣報錯 `InFailedSqlTransaction`。
**根因**：與發現 2 同一種模式——`_migrate_tokens()` 函式對 `SELECT gsc_access_token FROM users ...` 包了 `try/except`（因為在此時間點 `gsc_access_token`／`zeabur_api_key`／`gemini_api_key` 等欄位確實還不存在，要等到本次新增的 migration 才會加上），在 SQLite 上能繼續跑，在 PostgreSQL 上會拖垮整條鏈。

**修復**：改為執行查詢前，先用 `inspect(conn).get_columns("users")` 檢查欄位是否存在，用**查詢前判斷**取代**查詢後補救**，行為完全等價但不會觸碰資料庫層級的錯誤狀態。

#### 發現 4：`run_migration.py`（正式環境的實際遷移入口）— `alembic_version` 欄位寬度不足

**現象**：修復發現 1-3 後，migration 鏈本身內容全部成功執行，但最後一步 Alembic 自動更新 `alembic_version.version_num` 時報錯：
```
psycopg2.errors.StringDataRightTruncation: value too long for type character varying(32)
```
**根因**：這個專案有多支 migration 使用超過 32 字元的自訂 revision id（例如 `20260224_fix_integrations_migration_compat`，44 字元），但 PostgreSQL 建立 `alembic_version` 表時的預設欄位寬度是 `VARCHAR(32)`（Alembic 沿用標準 32 字元 hex hash 的假設）。

有趣的是：**`run_migration.py` 本身已經有 `_ensure_alembic_version_column_capacity()` 函式專門處理這個問題**——但只處理「`alembic_version` 表已存在、欄位太窄」的情況，對「全新資料庫、`alembic_version` 表根本還不存在」的情況會直接 `return` 提前放棄，把建表工作交給 Alembic 自己（用預設的窄欄位），於是問題原封不動地發生。這證實團隊已經知道這類問題的存在（且已經修過一次類似的情境），只是沒覆蓋到最根本的「從零開始」情境。

**修復**：`_ensure_alembic_version_column_capacity()` 在偵測到 `alembic_version` 表不存在時（僅限 PostgreSQL），改為提前手動用足夠寬度（`VARCHAR(128)`，與既有補寬邏輯的目標寬度一致）建立這張表，讓 Alembic 直接沿用。

#### 驗證結果（全部基於真實 PostgreSQL 18.3，非 SQLite 模擬）

- ✅ 全新空 PostgreSQL 資料庫，透過**正式環境實際會執行的入口** `python run_migration.py`（而非直接呼叫 `alembic` CLI）：完整跑完全部 20 個 migration，`Migration upgrade successful.`。
- ✅ 事後以 `Base.metadata` 對照：**零落差**（29 張表、所有欄位完全一致）。
- ✅ 修復後重新驗證 SQLite 路徑（同樣全新空資料庫跑 `alembic upgrade head`）：仍然完整跑通，無回歸。
- ✅ `pytest tests/`：79 passed / 12 failed，與修復前後、與 SQLite-only 驗證階段完全一致（無新增失敗）。
- ✅ 全程未對用戶提供的正式資料庫 `zeabur` 做任何寫入，僅做過一次唯讀查詢確認其狀態；測試專用的 `datavue_p0_1_test` 資料庫已於驗證完成後 `DROP DATABASE` 清除，PostgreSQL 主機上僅剩 `postgres`（系統預設）與 `zeabur`（用戶正式資料庫）。

**修改檔案清單（本補充部分）**：
- `backend/alembic/versions/0001_initial_schema.py`
- `backend/alembic/versions/20260223_p3_integrations_indexes.py`
- `backend/alembic/versions/20260224_fix_integrations_migration_compat.py`
- `backend/run_migration.py`

**重要結論**：在這次修復之前，這個專案**沒有任何一條路徑能讓一個全新的 PostgreSQL 資料庫單靠程式碼自動建出完整可用的 schema**——無論是用 `alembic` CLI 或用正式環境實際使用的 `run_migration.py` 都會中途失敗。現有生產環境之所以正常運作，完全是因為它從來不是「全新」的（一路靠 `patch_database_schema()`／`create_all()`／legacy stamping 撐過來）。這意味著在移除 `patch_database_schema()` 這個安全網之前，**任何一次災難復原、staging 重建、或資料庫搬遷，理論上都會直接失敗在第一步**。現在，這條路徑已經被實測打通。

---

### P0-2 `/health` 端點資訊洩漏拆分 ✅ 已完成（2026-07-02）

**問題定位**
`main.py::health_check`（原 L249-365）為無需認證端點，卻回傳：各 API 金鑰長度、DB 中持有金鑰的用戶數（兩次 `count()` query）、`META_ANDROMEDA_SCORING_PROVIDER`、硬編碼的部署時間/分支。屬內部組態外洩，且每次探活都打 DB 做金鑰統計，並對每次請求 `subprocess` 呼叫 `git rev-parse`。

**已完成的變更**

1. **精簡公開 `/health`**（`backend/main.py`）：移除整段 `ai_config_debug`（API 金鑰長度、DB 金鑰統計、`META_ANDROMEDA_SCORING_PROVIDER`）與硬編碼的 `git_info`（`deployed_via_agent_at`／`target_branch`）。現在只回傳 `status`、`timestamp`、`uptime_seconds`、`version`、`commit`（見下）、`checks`（`database`／`redis`／`scheduler`／`meta_andromeda`，皆不含機密內容）。
2. **新增授權版 `/health/detail`**：掛 `Depends(require_super_admin())`（沿用既有 `modules/auth/dependencies.py::require_super_admin`，與其他 admin-only 端點一致的用法）。內部呼叫 `health_check()` 取得基礎欄位後，疊加原本的 `ai_config_debug`（API 金鑰長度、DB 金鑰統計、scoring provider）。未帶 token 回 401，非 super admin 回 403。
3. **git commit 快取**：`_GIT_COMMIT` 於模組載入時（app 啟動時）以 `subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])` 計算一次，失敗則 fallback 至 `ZEABUR_GIT_COMMIT_SHA` / `COMMIT_REF` 環境變數；`/health` 直接讀取此模組級變數，不再每次探活都 fork 子行程。

**驗證結果**
- ✅ `tests/test_health.py` 新增 4 個測試（原 5 個全數維持通過）：
  - `test_health_does_not_leak_internal_config`：未帶 token `GET /health` → 200，回應內**不含** `ai_config_debug` / `git_info`。
  - `test_health_detail_requires_auth`：未帶 token `GET /health/detail` → 401/403。
  - `test_health_detail_requires_super_admin`：一般使用者（非 super admin）`GET /health/detail` → 403。
  - `test_health_detail_returns_debug_info_for_super_admin`：super admin `GET /health/detail` → 200，含 `ai_config_debug` 與基礎 `checks`。
- ✅ `pytest tests/`：83 passed / 12 failed（較 P0-1 完成時的 79 passed 多出本次新增的 4 個測試，12 個既有失敗清單不變，與本次改動無關）。

**風險評估**：低（已完整驗證）。前端與監控若曾依賴舊 `/health` 內的 `ai_config_debug` / `git_info` 欄位需改讀 `/health/detail`（需 super admin token）；目前程式庫內未發現任何前端程式碼讀取這兩個欄位。

---

### P0-3 移除／隔離生產環境的除錯與一次性腳本

**問題定位**
- 根目錄 `tmp_migrate.py`、`run_migration.py` 疑似一次性腳本，留在可 import 路徑。
- `routers/debug.py` 受 `DEBUG_MODE` 控制（main.py L235-238），需確認生產為 false。

**修改方案**
1. 將 `tmp_migrate.py`、`run_migration.py` 移到 `scripts/maintenance/` 或直接刪除（若已被 Alembic 取代）。先 `grep -rn "tmp_migrate\|run_migration" backend/` 確認無其他 import。
2. 在 `core/startup.py` 啟動日誌中明確印出 `DEBUG_MODE` 與 `ENV` 值，方便運維確認生產態。
3. 於 `docs/06_部署指南.md` 補上生產環境必要環境變數檢查清單（`DEBUG_MODE=false`、`ENV=production`、`DATAVUE_SKIP_STARTUP_MIGRATIONS` 策略）。

**驗證**：`grep` 確認無殘留 import；生產啟動日誌顯示 `DEBUG_MODE=false`。
**風險**：低。

---

## P1 — 架構收斂

### P1-1 ga4 / gsc / ai_hub 空殼模組決策

**問題定位**
`modules/ga4/service.py`、`modules/gsc/service.py`、`modules/ai_hub/service.py` 僅 `from ga4_service import GA4Service` 這類 re-export；實作仍在根目錄 `ga4_service.py`(642)、`gsc_service.py`(338)、`ai_service.py`(263)。且 `routers/ga4.py` 直接 `from ga4_service import`（繞過模組）。屬「假模組化」。

**修改方案（建議選 A：真遷移）**

**方案 A — 真遷移（推薦，與 fb_ads/meta_andromeda 分層一致）**
1. 將根目錄實作檔內容搬入對應 `modules/<name>/service.py`（保留類別名）。
2. 全域改 import 路徑：`from ga4_service import GA4Service` → `from modules.ga4.service import GA4Service`。用 `grep -rln "from ga4_service\|import ga4_service" backend/` 全數替換（ga4/gsc/ai 三組）。
3. 在根目錄舊檔留一行相容 shim（過渡一個版本後刪除）：
   ```python
   # ga4_service.py (deprecated shim)
   from modules.ga4.service import GA4Service  # noqa: F401
   ```
4. 把 `routers/ga4.py`、`routers/gsc.py` 的 import 一併改為模組路徑（此步與 P1-2 合併做更有效率）。

**方案 B — 撤殼（若短期無力遷移）**
- 刪除三個 `modules/*/service.py` 空殼，router 明確 import 根目錄服務，並在 README 標註「這些為舊式服務，尚未模組化」。避免結構誤導。

**驗證**：`pytest backend/tests/` 全綠；啟動 app 無 ImportError；`grep` 確認無殘留舊路徑（方案 A 過渡期除外）。
**風險**：中（import 面積大，但機械性替換）。建議一次處理一個模組（先 ga4 → gsc → ai_hub）。

---

### P1-2 路由統一到 modules/*/router.py

**問題定位**
路由組織分裂：`modules/*/router.py`（auth/ga4/gsc/meta_andromeda）與 `routers/`（users/teams/invites/admin/ai/saved_views/permissions/facebook/reports/line/metrics）並存。

**修改方案（漸進，低風險）**
1. 訂定目標：所有 router 收斂到 `modules/<domain>/router.py`。對應關係：
   - `routers/users.py` → `modules/auth/`（或新增 `modules/users/`）
   - `routers/teams.py`、`routers/invites.py`、`routers/permissions.py` → `modules/teams/` / `modules/permissions/`
   - `routers/ai.py` → `modules/ai_hub/router.py`
   - `routers/reports.py` → `modules/reports/router.py`
   - `routers/facebook.py` → `modules/fb_ads/router.py`
   - `routers/metrics.py`、`routers/saved_views.py`、`routers/line.py`、`routers/admin.py` → 各自 domain 模組
2. 每次搬一個 router：移動檔案 → 更新 `main.py` 的 import（L201-232）→ 保持 `prefix`/`tags` 不變（API 路徑零變動）。
3. `main.py` 的 router 註冊區塊維持集中，僅改 import 來源。

**驗證**：對照 OpenAPI（`/docs`）搬移前後的路徑清單完全一致；`test_*` 全綠。
**風險**：低（純檔案位移，API 契約不變）。可與 P1-1 合併分批進行。

---

### P1-3 config.py 遷移至 Pydantic BaseSettings

**問題定位**
`core/config.py` 全部 `@property` + `os.getenv`，無型別驗證、每次存取重複解析、40+ 個 `META_ANDROMEDA_*` 擠在單一類別。

**修改方案**

1. 導入 `pydantic-settings`（Pydantic v2）。把 Meta Andromeda 設定抽成巢狀子設定：

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class MetaAndromedaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="META_ANDROMEDA_")
    scoring_provider: str = "auto"
    scoring_model: str = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
    score_max_concurrency: int = Field(2, ge=1)
    observation_max_concurrency: int = Field(5, ge=1)
    upload_max_bytes: int = 15 * 1024 * 1024
    # ...其餘 META_ANDROMEDA_* 對應欄位

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    GOOGLE_CLIENT_ID: str = ""
    ENCRYPTION_KEY: str = ""
    DATABASE_URL: str | None = None
    meta_andromeda: MetaAndromedaSettings = MetaAndromedaSettings()

    @property
    def is_postgres(self) -> bool:
        return bool(self.DATABASE_URL)
```

2. **保留相容存取**：現有大量呼叫 `settings.META_ANDROMEDA_SCORE_MAX_CONCURRENCY`。過渡期在 `Settings` 加 `@property` 代理到巢狀值，或用一支 codemod 全域改為 `settings.meta_andromeda.score_max_concurrency`。建議先加代理 property，之後再逐步改呼叫點。
3. 保留 `GOOGLE_AI_API_KEY` 的 fallback 鏈（用 `@model_validator` 或 property 實作），並加註解說明優先序。

**驗證**：新增 `test_config.py` 驗證預設值、env 覆蓋、型別轉換（如 `SCORE_MAX_CONCURRENCY=abc` 應報錯而非靜默）；全站啟動無迴歸。
**風險**：中（存取點多）。務必先建代理相容層，避免一次性大改。

---

### P1-4 Meta Andromeda 記憶體內狀態改用 Redis

**問題定位**
`modules/meta_andromeda/service.py`：
- `_observation_import_statuses: dict`（L32）+ `threading.Lock`（L33）：匯入進度存於 process 記憶體。
- `_score_event_semaphore` / `_observation_import_semaphore`（L34-35）：process 內並發閘。
- 讀寫點：L475-479 寫進度、L846 讀進度、L1277-1280 清理。

在 gunicorn/uvicorn 多 worker（多 process）部署下：
- 進度查詢端點（router L377 `.../status`）可能落在**未持有該進度**的 worker，回傳「查無」。
- 兩個 semaphore 只在單 process 內生效，跨 process 的總並發是 `worker數 × concurrency`，可能超過對 OpenRouter/DB 的預期上限。

**修改方案**

1. **進度狀態改存 Redis**（已有 `redis_cache.get_redis_client`）。封裝一個小 store：

```python
# modules/meta_andromeda/import_status_store.py
IMPORT_STATUS_KEY = "ma:import_status:{observed_creative_id}"
IMPORT_STATUS_TTL = 3600

def set_import_status(observed_creative_id: str, **updates) -> dict:
    redis = get_redis_client()
    if not redis:                     # Redis 不可用時 fallback 回本地 dict（開發）
        return _local_set(observed_creative_id, **updates)
    key = IMPORT_STATUS_KEY.format(observed_creative_id=observed_creative_id)
    current = json.loads(redis.get(key) or "{}")
    current.update(updates)
    redis.set(key, json.dumps(current), ex=IMPORT_STATUS_TTL)
    return current

def get_import_status(observed_creative_id: str) -> dict: ...
```
   將 service.py 中對 `_observation_import_statuses` 的三處存取改走此 store。TTL 順帶取代 L1273 的手動清理邏輯。

2. **跨 process 並發限流**：把 `asyncio.Semaphore` 改為 Redis 分散式限流（如 `redis` incr + expire 的滑動視窗，或 token bucket）。或者，若部署為**單一 web + 獨立 worker host**（config 已支援 `META_ANDROMEDA_QUEUE_HOST=database_queue`/`redis_stream`），則將真正的評分並發集中在 worker host，web 端只入列，semaphore 問題自然消解——**這是更根本的解法**，建議優先確立部署拓撲。

3. Redis 不可用時保留本地 dict fallback（開發／單機），確保降級可用。

**驗證**：以 2 個 uvicorn worker 啟動，A worker 觸發匯入、B worker 查 status 應查得到；壓測確認跨 process 總並發受控。
**風險**：中。與部署拓撲決策綁定，建議先定 queue host 策略再實作。此項亦回應既有 memory 記錄的批次匯入並發疑慮（router L362 `background_tasks.add_task` 目前僅靠 process 內 semaphore）。

---

## P2 — 可維護性

### P2-1 拆分巨型檔案

**後端 `modules/meta_andromeda/repository.py`（2124 行）**
現為單一 `MetaAndromedaRepository` 類含 40+ 方法。依聚合根拆分為多個 repository，用組合維持既有 `repository` 單例介面（呼叫點零改動）：

```
modules/meta_andromeda/repositories/
├── __init__.py            # 匯出組合後的 repository 單例（facade）
├── _serializers.py        # _score_to_list_item / _to_dict 等靜態轉換（L524-634）
├── score_events.py        # create/mark_*/requeue/delete/batch_delete（L634-664, 1545-1754）
├── review_queue.py        # list_review_queue / detail / timeline（L665-1050）
├── monitoring.py          # get_monitoring_summary / drift_trend（L845-1050, 2025-）
├── worker_events.py       # log/find worker event, dead_letter（L1598-1671）
├── observations.py        # observed_creative CRUD（L1462-1544）
├── calibration.py         # create_drift_report / sync_calibration_dataset（L1051-, 1888-）
├── release.py             # release overview/action（L1355-1438, 1810-）
└── profiles.py            # scoring profiles list/promote（L2072-）
```
Facade 範例：
```python
class MetaAndromedaRepository(ScoreEventRepo, ReviewQueueRepo, MonitoringRepo, ...):
    pass
repository = MetaAndromedaRepository()
```
> 用多重繼承或委派組合，確保 `from .repository import repository` 的既有 import 不變。

**後端 `service.py`(1466)** 依用例拆：`scoring_service` / `review_service` / `observation_import_service` / `calibration_service`，同樣以 facade 保持 `MetaAndromedaService` 介面。

**前端 `GSCStats.jsx`(3717) / `GA4Stats.jsx`(3184)**
1. 資料邏輯下沉到 `hooks/queries/`（如 `useGscStats`, `useGa4Report`）。
2. 抽 presentational 子元件：`<StatsFilterBar>`、`<StatsOverviewCards>`、`<StatsTrendCharts>`、`<StatsDataTable>`、`<StatsExportMenu>`。
3. 因 GSCStats 與 GA4Stats 結構相似，抽共用骨架 `<AnalyticsDashboard config={...}>`，兩者僅傳不同 config/欄位定義。

**做法**：一次拆一個檔，每步跑測試 + 手動煙霧測試。純結構重構，不改行為。
**風險**：低-中（面積大但機械性）。優先拆 repository（單元測試 `test_meta_andromeda_module.py` 2539 行可護航）。

---

### P2-2 前端漸進導入 TypeScript

**方案**
1. Vite 已支援 TS，只需加 `typescript`、`tsconfig.json`（`allowJs: true`, `strict: false` 起步），不必一次改完。
2. 導入順序：`src/types/` → `src/services/`（API 契約層最有價值）→ `src/hooks/` → 元件。
3. 先為後端 API 回應定義 interface（可依 OpenAPI schema 產生），讓 `apiClient` 泛型化 `request<T>()`。
4. ESLint 加 `@typescript-eslint`，CI 逐步收緊 `strict`。

**驗證**：`npm run build` 通過；先轉 `apiClient.ts` 並確保現有頁面無型別報錯。
**風險**：低（`allowJs` 讓 js/ts 共存）。

---

### P2-3 補強測試覆蓋

**現況**：後端 9 個測試檔（集中 auth/health/permissions/report/scheduler/meta_andromeda）；前端僅 4 個（全 MetaAndromeda 頁）。

**補強清單（依投報率排序）**
| 目標 | 測試類型 | 重點 |
|---|---|---|
| 前端 `services/apiClient.js` | 單元 | 重試（502/503/504）、逾時、401 重導、ApiError |
| 後端 `ga4_service` / `gsc_service` | 單元 | OAuth 交換、property 列舉、錯誤處理（mock google client）|
| 後端 `services/facebook_service` | 單元 | token 加解密、insights 聚合 |
| 前端關鍵 hooks（`useAnalyticsFilters` 等） | 單元 | 篩選狀態轉換 |
| 後端 `core/config`（P1-3 後）| 單元 | env 覆蓋 / 型別驗證 |

**基礎建設**：前端已有 vitest + testing-library；後端已有 pytest + conftest。補測試不需新框架。設定 CI 覆蓋率門檻（起步 40%，逐季提升）。

---

### P2-4 指標定義單一事實來源

**問題**：指標定義散落 `frontend/src/constants/metricsRegistry.js`(545)、`backend/modules/fb_ads/metrics_registry.py`、`backend/routers/metrics.py`、`backend/service_modules/metrics.py`。

**方案**
1. 以**後端為單一事實來源**（`modules/fb_ads/metrics_registry.py`）。
2. `routers/metrics.py` 提供 `GET /api/metrics/registry` 回傳完整定義。
3. 前端啟動時拉取並快取（React Query），移除 `constants/metricsRegistry.js` 的重複定義（保留純 UI 呈現用的補充設定即可）。
4. `service_modules/metrics.py` 與 `modules/fb_ads/metrics_registry.py` 若重疊，收斂為一。

**驗證**：前端指標下拉與後端計算欄位一致；改後端定義前端自動同步。
**風險**：低-中（需確認前端所有引用點）。

---

## 執行順序總表

| 順序 | 項目 | 預估 | 相依 | 風險 | 狀態 |
|---|---|---|---|---|---|
| 1 | P0-1 Schema 收斂至 Alembic | 2-3d | 需 DB 快照驗證 | 低（已驗證） | ✅ 2026-07-01 完成 |
| 2 | P0-2 `/health` 拆分 | 0.5d | — | 低（已驗證） | ✅ 2026-07-02 完成 |
| 3 | P0-3 移除除錯/一次性腳本 | 0.5d | — | 低 | 待處理 |
| 4 | P1-4 部署拓撲 + Redis 狀態 | 2-3d | 決定 queue host | 中 | 待處理 |
| 5 | P1-1 空殼模組真遷移（ga4→gsc→ai_hub）| 2d | — | 中 | 待處理 |
| 6 | P1-2 路由統一 | 2d | 可併 P1-1 | 低 | 待處理 |
| 7 | P1-3 config → BaseSettings | 1-2d | — | 中 | 待處理 |
| 8 | P2-1 拆分巨型檔案 | 持續 | 有測試護航更佳 | 中 | 待處理 |
| 9 | P2-3 補測試 | 持續 | — | 低 | 待處理 |
| 10 | P2-2 導入 TS | 持續 | — | 低 | 待處理 |
| 11 | P2-4 指標單一來源 | 1d | — | 低 | 待處理 |

**實際執行順序調整**：P0-1 實際上先於 P0-2/P0-3 完成（用戶指定順序）。原評估風險「中」，經完整實測（全新 DB 全鏈跑通、零 schema 落差、測試套件無回歸）後下修為「低」。下一步建議 P0-2、P0-3（快速降風險，工作量小）。P1 項目可與 P1-1/P1-2 合併分批。P2 為持續改善，穿插於功能開發間進行。

> ⚠️ 所有涉及 import 路徑大改（P1-1/P1-2）與 schema（P0-1）的項目，建議每完成一個子步驟即跑完整測試套件並保留 git 可回退點。實作前針對個別 runtime 行為（並發路徑、實際呼叫鏈）再做一次針對性驗證。
