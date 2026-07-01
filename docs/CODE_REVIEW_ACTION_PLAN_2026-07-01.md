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

### P0-1 收斂 DB Schema 管理為單一 Alembic 路徑

**問題定位**
目前有三套機制同時管理 schema，彼此職責重疊、部署順序敏感：
1. `core/startup.py::run_migrations()` → 執行 Alembic（正統）
2. `core/startup.py::patch_database_schema(engine)`（L135-249）→ 手動 `ALTER TABLE ADD COLUMN` / `CREATE TABLE`
3. `core/startup.py::init_db()`（L359）→ SQLAlchemy `create_all`

現有 Alembic versions 已有 19 個 migration（含 `20260114_add_ga4_columns.py`、`403dfb0cfbd4_add_module_type_to_reports.py` 等），與 `patch_database_schema` 補的欄位**高度重複**（如 ga4 欄位、module_type、share_token）。

**修改方案（分階段，確保安全）**

**階段 A：稽核落差（不改行為）**
1. 建立一次性稽核腳本 `scripts/audit_schema_drift.py`：對照 `Base.metadata` 與實際 DB `inspect(engine)`，列出缺漏欄位/表。
2. 逐一確認 `patch_database_schema` 補的每個欄位是否已被某個 migration 涵蓋：

   | patch 項目 | 對應 migration | 狀態 |
   |---|---|---|
   | `users.ga4_*` | `20260114_add_ga4_columns.py` | ✅ 已涵蓋 |
   | `weekly_reports.module_type` / `report_schedules.module_type` | `403dfb0cfbd4_add_module_type_to_reports.py` | 待確認 |
   | `weekly_reports.share_token` | `20260331_add_weekly_reports.py` | 待確認 |
   | `teams.fb_*` / `token_expires_at` | `fe8441e71f69_add_team_token_expires_at.py` | 待確認 |
   | `page_titles` / `saved_views` 表 | `230a10d75894_add_saved_views_table.py` | 待確認 |
   | `users.gemini_api_key` / `zeabur_api_key` / `openrouter_api_key` | `46c781526b51_add_openrouter_api_key.py` | 待確認 |

**階段 B：補齊缺口的 migration**
- 對稽核發現「只有 patch 有、migration 沒有」的欄位，新增一支 migration `alembic revision -m "consolidate legacy schema patches"`，把這些 DDL 正式化，並在 `upgrade()` 中用 `op.get_bind()` + `inspector.has_column` 做冪等保護（相容既有已補過的環境）：

```python
def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing = {c["name"] for c in insp.get_columns("teams")}
    if "fb_access_token" not in existing:
        op.add_column("teams", sa.Column("fb_access_token", sa.String(), nullable=True))
    # ...其餘欄位比照
```

**階段 C：移除舊機制**
1. `core/startup.py`：刪除 `patch_database_schema` 函式與其在 `run_startup_tasks()` 的呼叫（原 L356）。
2. `init_db()` 的 `create_all`：改為**僅在 SQLite 開發模式**執行，生產（PostgreSQL）只信任 Alembic：

```python
# core/startup.py run_startup_tasks()
from core.config import settings
if not settings.is_postgres:
    init_db()   # 僅開發用 SQLite 快速建表
```

3. 保留 `DATAVUE_SKIP_STARTUP_MIGRATIONS` 機制（部署 entrypoint 已跑 migration 時可跳過）。

**驗證**
- 在乾淨 SQLite 與乾淨 PostgreSQL 各跑一次 `alembic upgrade head` → 執行 `scripts/audit_schema_drift.py` 應回報「無落差」。
- 既有生產 DB 執行新 migration 應為 no-op（冪等保護生效）。
- `backend/tests/test_health.py` 應綠燈。

**風險**：中。務必先在既有生產 DB 快照上驗證冪等性再上線。

---

### P0-2 `/health` 端點資訊洩漏拆分

**問題定位**
`main.py::health_check`（L249-365）為無需認證端點，卻回傳：各 API 金鑰長度、DB 中持有金鑰的用戶數（兩次 `count()` query）、`META_ANDROMEDA_SCORING_PROVIDER`、硬編碼的部署時間/分支。屬內部組態外洩，且每次探活都打 DB 做金鑰統計。

**修改方案**

1. **精簡公開 `/health`**：只保留 liveness/readiness 必要欄位，移除 `ai_config_debug` 整段與 `git_info` 硬編碼字串：

```python
@app.get("/health", tags=["system"])
async def health_check():
    health = {"status": "healthy", "timestamp": ..., "uptime_seconds": ..., "version": "2.1.0", "checks": {}}
    # 只保留：database（必要）、redis / scheduler / meta_andromeda（選用，不含機密）
    # 移除 ai_config_debug、git_info、db_users_with_*_count
    ...
    return health if healthy else JSONResponse(status_code=503, content=health)
```

2. **新增授權版 `/health/detail`**：把金鑰長度、DB 統計、scoring provider 等移到此端點，掛 `Depends(require_super_admin)`（沿用現有 `modules/auth/dependencies.py` 的權限依賴）：

```python
@app.get("/health/detail", tags=["system"])
async def health_detail(_admin=Depends(require_super_admin)):
    ...  # 原 ai_config_debug + db 金鑰統計移到這裡
```

3. **git commit 快取**：`git rev-parse HEAD` 於啟動時執行一次存入 module 級變數，`/health` 直接讀取，避免每次探活 `subprocess`。

**驗證**
- 未帶 token `GET /health` → 200，回應內**不含**任何金鑰長度或 provider 名稱。
- 非 admin `GET /health/detail` → 401/403；super admin → 200 含詳細資訊。
- 更新 `test_health.py` 斷言公開端點不含 `ai_config_debug`。

**風險**：低。注意若前端或監控有依賴舊 `/health` 欄位需同步調整。

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

| 順序 | 項目 | 預估 | 相依 | 風險 |
|---|---|---|---|---|
| 1 | P0-2 `/health` 拆分 | 0.5d | — | 低 |
| 2 | P0-3 移除除錯/一次性腳本 | 0.5d | — | 低 |
| 3 | P0-1 Schema 收斂至 Alembic | 2-3d | 需 DB 快照驗證 | 中 |
| 4 | P1-4 部署拓撲 + Redis 狀態 | 2-3d | 決定 queue host | 中 |
| 5 | P1-1 空殼模組真遷移（ga4→gsc→ai_hub）| 2d | — | 中 |
| 6 | P1-2 路由統一 | 2d | 可併 P1-1 | 低 |
| 7 | P1-3 config → BaseSettings | 1-2d | — | 中 |
| 8 | P2-1 拆分巨型檔案 | 持續 | 有測試護航更佳 | 中 |
| 9 | P2-3 補測試 | 持續 | — | 低 |
| 10 | P2-2 導入 TS | 持續 | — | 低 |
| 11 | P2-4 指標單一來源 | 1d | — | 低 |

**建議節奏**：先做 P0-2、P0-3（快速降風險），再排 P0-1（需謹慎驗證）。P1 項目可與 P1-1/P1-2 合併分批。P2 為持續改善，穿插於功能開發間進行。

> ⚠️ 所有涉及 import 路徑大改（P1-1/P1-2）與 schema（P0-1）的項目，建議每完成一個子步驟即跑完整測試套件並保留 git 可回退點。實作前針對個別 runtime 行為（並發路徑、實際呼叫鏈）再做一次針對性驗證。
