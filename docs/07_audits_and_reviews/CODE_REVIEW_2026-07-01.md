# DataVue-App 全專案架構審查報告

> 產出日期：2026-07-01
> 審查範圍：`backend/`（FastAPI）與 `frontend/`（React 19 + Vite）全模組
> 審查方式：架構掃描 + 各模組代表性檔案抽讀（後端約 30k LOC、前端約 33k LOC）

---

## 0. 總覽（TL;DR）

DataVue 是一套多平台數據分析 SaaS，整合 Facebook Ads、GSC、GA4，並包含一個大型的 **Meta Andromeda** 廣告素材評分／診斷子系統。整體採「模組化」演進，方向正確，但目前處於**新舊架構並存的過渡期**，存在數個需要收斂的技術債。

| 面向 | 評價 | 說明 |
|------|------|------|
| 架構分層 | 🟡 中 | 有 `modules/` 分層意圖，但根目錄仍散落大量舊 service，且部分 `modules/*` 只是 re-export 殼層 |
| 資料庫演進 | 🔴 需注意 | 同時存在 Alembic migration 與 `patch_database_schema()` 手動 `ALTER TABLE`，雙軌並行風險高 |
| Meta Andromeda | 🟢 佳（但過大） | 設計完整（queue host / runtime / storage 可插拔），但 `repository.py` 2124 行、`service.py` 1466 行過於臃腫 |
| 前端結構 | 🟡 中 | 元件過大（GSCStats 3717 行、GA4Stats 3184 行），無 TypeScript，測試僅覆蓋 Meta Andromeda |
| 安全性 | 🟡 中 | `/health` 洩漏過多內部設定；CORS 例外處理散落；金鑰以 property 動態讀取 env |
| 測試覆蓋 | 🔴 低 | 後端 9 個測試檔集中在少數模組；前端僅 4 個測試檔 |

---

## 1. 專案架構總覽

```
backend/
├── main.py                 # FastAPI 入口（381 行，已控制在合理範圍）
├── core/                   # config / startup / scheduler / security / logging
├── modules/                # 目標分層：ai_hub / auth / fb_ads / ga4 / gsc / meta_andromeda
├── routers/                # 15 個 router（舊式，與 modules/*/router.py 並存）
├── services/               # 舊式 service 層 + services/ai/
├── service_modules/        # 又一層 service（facebook_api / metrics）
├── database/               # engine + models/
└── *.py (根目錄)           # ai_service / ga4_service / gsc_service / batch_api ... 散落的舊服務

frontend/src/
├── pages/                  # 路由頁（含 5 個 MetaAndromeda 頁）
├── components/             # 大型元件（GSCStats/GA4Stats/Analytics）
├── hooks/ (queries/mutations) # React Query 封裝
├── services/               # API client 封裝層
└── constants / utils / types
```

**核心觀察**：後端存在**四層 service 概念**（`modules/*/service.py`、`services/`、`service_modules/`、根目錄 `*_service.py`），職責邊界模糊，是最大的認知負擔來源。

---

## 2. 後端逐模組審查

### 2.1 `main.py`（入口）
**現況**：結構清晰，啟動邏輯已抽到 `core/startup.py`，router 註冊集中。

**可優化**：
- 🔴 **`/health` 端點洩漏過多內部資訊**（L269-317）：回傳各 API 金鑰長度、DB 中持有金鑰的用戶數、scoring provider 等。這是無需認證的公開端點，等同對外揭露內部組態。建議：拆成 `/health`（極簡 200/503）與 `/health/detail`（需 admin 權限）。
- 🟡 **`_add_cors_headers_to_response` 手動補 CORS**（L128-137）：因 exception handler 會繞過 CORSMiddleware 而手動補。可改用自訂 middleware 統一處理，避免每個 handler 重複呼叫。
- 🟡 **`git_info` 硬編碼**（L301-303）：`deployed_via_agent_at`、`target_branch: dev-saas` 為寫死字串，與實際部署脫節，屬誤導性資訊，建議移除或改由環境變數注入。
- 🟢 health check 內每次 `subprocess` 呼叫 `git rev-parse` 有輕微成本，可於啟動時快取一次。

### 2.2 `core/config.py`
**現況**：集中式 `Settings`，全部以 `@property` 動態讀 `os.getenv`。Meta Andromeda 佔了約 40 個設定項。

**可優化**：
- 🟡 **每次存取都呼叫 `os.getenv`**：雖有 `@lru_cache` 快取 `Settings` 實例，但 property 本身無快取，高頻存取（如 `META_ANDROMEDA_SCORE_MAX_CONCURRENCY`）會重複解析。建議遷移到 **Pydantic `BaseSettings`**，一次解析、型別驗證、集中預設值。
- 🟡 **設定項爆炸**：40+ 個 `META_ANDROMEDA_*` 建議拆成 `MetaAndromedaSettings` 子設定類（巢狀 nested settings），降低單一類別的認知負擔。
- 🟢 `GOOGLE_AI_API_KEY` fallback 到 `ZEABUR_AI_HUB_API_KEY`（L72-77）這種隱式 fallback 鏈建議加註解說明優先序，避免除錯困惑。

### 2.3 `core/startup.py` ⚠️ 重點
**可優化**：
- 🔴 **`patch_database_schema()` 與 Alembic 雙軌並存**（L135-249）：手動 `ALTER TABLE ADD COLUMN`、`CREATE TABLE` 與 Alembic migration 同時存在。這是**高風險技術債**——兩者可能對同一 schema 有不同認知，在新環境部署順序敏感。建議：將所有 patch 邏輯正式收斂為 Alembic migration，移除 `patch_database_schema`。
- 🟡 **`init_db()` 的 `create_all` 也會建表**（L359）：與 migration、patch 三者職責重疊，生產環境應只信任 Alembic。
- 🟡 啟動任務為線性順序執行且多數失敗只 `warning` 不中斷（graceful degradation），good，但缺乏「degraded mode」的明確狀態上報，運維難以察覺半殘狀態。

### 2.4 `core/scheduler.py`（701 行）
**現況**：APScheduler 管理週報 + Meta Andromeda queue sweep / redis stream consumer / reclaim 三種 job。

**可優化**：
- 🟡 職責過載：報表排程與 Meta Andromeda 佇列調度混在同一檔。建議把 Meta Andromeda 相關 job 定義移到 `modules/meta_andromeda/` 內，scheduler 只負責註冊。
- 🟡 全域單例 `scheduler = AsyncIOScheduler(...)` 在 import 時就建立，測試時難以隔離。
- 🟢 時區處理（local naive/aware 轉換函式）散落多個 helper，可抽成小工具模組。

### 2.5 `database/engine.py`
**現況**：SQLite（開發）/ PostgreSQL（生產）雙模式，pool 參數可由 env 調整，佳。

**可優化**：
- 🟡 **module import 時即執行 `check_db_connection()`**（L108）：import side-effect 會在測試、CLI 工具載入時觸發真實連線。建議延後到明確初始化時機。
- 🟢 pool_size 預設 3、max_overflow 5 偏小（見 memory 記錄的批次匯入耗盡 thread pool 疑慮），若有大量並發背景任務需重新評估。

### 2.6 `modules/meta_andromeda/` ⭐ 核心子系統
**現況**：設計最完整的模組——`runtime`（scoring provider 抽象）、`queue_host`（apscheduler/local_async/database_queue/redis_stream/external_webhook 可插拔）、`storage`（filesystem/s3）、`calibration_pipeline`（drift 自動校準）。這是專案的技術亮點。

**可優化**：
- 🔴 **`repository.py` 2124 行、`service.py` 1466 行、`runtime.py` 1071 行**：單檔過大，難維護。建議 repository 依聚合根拆分（score_event / worker_event / dead_letter / profile / observation），service 依用例拆分（scoring / review_queue / observation_import / calibration）。
- 🟡 **模組級可變全域狀態**（service.py L32-35）：`_observation_import_statuses` dict + `threading.Lock` + `asyncio.Semaphore`。在多 worker（gunicorn 多 process）部署下這些狀態不跨進程共享，import 進度查詢會不一致。既然已有 Redis，建議進度狀態改存 Redis。
- 🟡 **匯入背景任務並發控制**（對應 memory 記錄）：`_observation_import_semaphore` 已存在，但需確認批次匯入的 `BackgroundTask` 確實走 semaphore 而非直接開 thread。
- 🟢 `README.md` 齊全，值得作為其他模組的分層範本。

### 2.7 `modules/ai_hub/`、`modules/ga4/`、`modules/gsc/` — 殼層模組 ⚠️
**現況**：這三個模組的 `service.py` **只是 re-export 根目錄的舊 service**：
```python
# modules/ga4/service.py
from ga4_service import GA4Service   # 實作仍在 backend/ga4_service.py（642 行）
```
`ai_hub/service.py` 同理 re-export `ai_service.AIService`。

**可優化**：
- 🔴 **完成遷移或撤除殼層**：目前是「假模組化」——目錄結構像模組化，但實作仍在根目錄。router 也直接 `from ga4_service import`（繞過模組）。應選一條路：(a) 真正把實作搬進 `modules/ga4/service.py`；或 (b) 移除空殼，承認這些仍是舊式服務。現狀是最糟的中間態（兩處都要維護、import 路徑混亂）。

### 2.8 `modules/fb_ads/`
**現況**：切分較細（accounts / analytics / insights / trends / metrics_registry），有 `_base.py`。相對健康。

**可優化**：
- 🟡 與根目錄 `services/facebook_service.py`（811 行）、`service_modules/facebook_api.py` 職責重疊，需確認呼叫關係並收斂。
- 🟢 `metrics_registry.py` 與前端 `constants/metricsRegistry.js`、後端 `routers/metrics.py` 有指標定義重複風險，建議單一事實來源（後端為準，前端由 API 拉取）。

### 2.9 `routers/`（15 個）vs `modules/*/router.py`
**可優化**：
- 🔴 **路由分層不一致**：auth/ga4/gsc/meta_andromeda 有 `modules/*/router.py`，但 users/teams/reports/admin/permissions 等仍在 `routers/`。同一專案兩種路由組織方式，新人難以定位端點。建議統一到 `modules/*/router.py`。
- 🟡 `routers/debug.py` 受 `DEBUG_MODE` 控制，good，但確認生產環境確實關閉。

### 2.10 根目錄散落檔案
`ai_service.py`、`async_services.py`、`batch_api.py`、`cache.py`、`redis_cache.py`、`crash_reporter.py`、`ga4_service.py`、`gsc_service.py`、`schemas.py`、`tmp_migrate.py`、`run_migration.py` 等直接放在 `backend/` 根。

**可優化**：
- 🟡 `tmp_migrate.py`、`run_migration.py` 疑似一次性腳本，應移到 `scripts/` 或刪除。
- 🟡 `cache.py` 與 `redis_cache.py` 並存，確認快取策略是否統一。
- 🟡 根目錄 `schemas.py` 與各 `modules/*/schemas.py` 並存，Pydantic model 定義分散。

---

## 3. 前端逐模組審查

### 3.1 巨型元件問題 🔴
| 檔案 | 行數 |
|------|------|
| `components/GSCStats.jsx` | 3717 |
| `components/GA4Stats.jsx` | 3184 |
| `pages/Analytics.jsx` | 2777 |
| `pages/MetaAndromedaMonitoring.jsx` | 2004 |
| `components/SettingsModal.jsx` | 1122 |

**可優化**：這些單檔動輒 2000-3700 行，是前端最大的維護風險。單一元件包含資料抓取、狀態管理、圖表、表格、匯出等多重職責。建議：
- 抽出 presentational 子元件（圖表區、篩選列、表格區各自獨立）。
- 資料邏輯下沉到 `hooks/queries`（已有此目錄，應擴大使用）。
- GSCStats 與 GA4Stats 結構高度相似，可抽共用的 `<AnalyticsDashboard>` 骨架。

### 3.2 無 TypeScript 🟡
全前端為 `.jsx`/`.js`，`types/api.js` 僅是 JS。以此規模（33k LOC、多平台 API 回應形狀複雜），缺型別是回歸 bug 溫床。建議：漸進式導入 TS（先 `services/` 與 `types/`）。

### 3.3 `services/`（API 層）
**現況**：`apiClient.js` 統一封裝 fetch、重試（502/503/504）、逾時、401 重導，設計良好。各功能有獨立 service（metaAndromeda 就有 5 個 service 檔）。

**可優化**：
- 🟢 良好基礎。建議所有資料抓取都透過 React Query hooks 包裝 service，避免元件直接呼叫 service 造成快取不一致。
- 🟡 5 個 `metaAndromeda*Service.js` 可考慮合併為單一命名空間物件。

### 3.4 測試覆蓋 🔴
前端僅 4 個測試檔（全在 `pages/__tests__/MetaAndromeda*`）。核心的 Analytics/GSCStats/GA4Stats/apiClient **零測試**。建議至少補上 `apiClient` 與關鍵 hooks 的單元測試。

---

## 4. 跨模組共通問題

1. 🔴 **雙軌 Schema 管理**（Alembic + 手動 patch + create_all）— 最高風險，優先收斂。
2. 🔴 **假模組化**（ga4/gsc/ai_hub 空殼 re-export）— 分層債。
3. 🟡 **路由 / service 分層不一致**（routers/ vs modules/，四層 service）。
4. 🟡 **`/health` 資訊洩漏** — 安全性。
5. 🟡 **多 process 部署下的記憶體內狀態**（Meta Andromeda import 進度、全域 semaphore）。
6. 🟡 **測試覆蓋不足**，尤其前端與非 Meta Andromeda 後端模組。
7. 🟡 **指標定義重複**（前端 constants / 後端 registry / router）。

---

## 5. 優先級行動建議

### P0（安全 / 資料完整性，1-2 週）
- [ ] 收斂 DB schema 管理為單一 Alembic 路徑，移除 `patch_database_schema` 與生產 `create_all`。
- [ ] `/health` 拆分為公開精簡版 + 需授權詳細版，移除金鑰長度與 DB 統計外洩。
- [ ] 確認 `DEBUG_MODE`、`tmp_migrate.py` 等在生產已停用/移除。

### P1（架構收斂，1 個月）
- [ ] 決策並執行 ga4/gsc/ai_hub 的真遷移或撤殼。
- [ ] 統一路由到 `modules/*/router.py`。
- [ ] `core/config.py` 遷移至 Pydantic `BaseSettings`，Meta Andromeda 設定巢狀化。
- [ ] Meta Andromeda 記憶體內狀態改用 Redis（支援多 process）。

### P2（可維護性，持續）
- [ ] 拆分 `repository.py`(2124) / `service.py`(1466) / `GSCStats.jsx`(3717) / `GA4Stats.jsx`(3184)。
- [ ] 前端漸進導入 TypeScript（自 `services/` 開始）。
- [ ] 補強測試：後端 fb_ads/ga4/gsc、前端 apiClient 與核心 hooks。
- [ ] 指標定義建立單一事實來源。

---

## 6. 值得肯定的設計

- Meta Andromeda 的 **queue host / runtime / storage 可插拔抽象**是優秀的擴充性設計，可作為其他模組的範本。
- `apiClient.js` 的統一重試 / 逾時 / 401 處理成熟。
- 前端已採用 lazy loading（`React.lazy`）+ React Query，效能基礎良好。
- `core/config.py` 對 Zeabur PaaS 部署（`postgres://` → `postgresql://`、相對 SQLite 路徑正規化）的相容處理細緻。
- graceful degradation 的啟動策略對 PaaS 環境友善。

---

*本報告基於架構掃描與代表性檔案抽讀，個別行為細節（如實際呼叫鏈、runtime 並發路徑）建議於實作各項優化前再行針對性驗證。*
