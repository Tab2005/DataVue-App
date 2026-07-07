# Meta Andromeda 評分管線 Event Loop 阻塞修復與模組優化實作計劃

日期：2026-07-07
狀態：**已立案，未動工**

## 1. 問題確認

### 1.1 問題一：成效分析匯入素材後，Andromeda 分頁卡在「權限讀取」

症狀：從成效分析批次匯入素材後，點選 Andromeda 相關分頁會停在權限載入畫面（`ProtectedModule` 的「載入中...」），直到整批評估跑完才恢復正常。

已對照程式碼驗證根因鏈：

1. 前端每次進入 Andromeda 分頁，`ProtectedModule` 會打 `/api/permissions/me/module/meta_andromeda`（`frontend/src/hooks/usePermission.jsx:93`），拿到回應前整個分頁不渲染。
2. **評分/匯入 worker 與 API server 跑在同一個 process、同一條 asyncio event loop**：
   - 匯入端點（`router.py:403`）把 async 的 `run_observed_facebook_ad_import_job`（`service.py:799`）丟進 `BackgroundTasks`，async background task 直接在主 loop 執行。
   - 評分 dispatch 的 `META_ANDROMEDA_QUEUE_HOST` 預設 `auto` → 走 APScheduler，而 `core/scheduler.py:31` 用的是 `AsyncIOScheduler`，掛在 FastAPI 同一條 loop 上；`local_async` fallback 更是直接 `asyncio.create_task`。
3. 評分 pipeline 內有大量**同步阻塞呼叫直接跑在 event loop 上**：
   - **最大元兇**：影片 keyframe 抽取 — `runtime.py:1365` 呼叫 `extract_video_keyframes_base64()`，內部是同步 `subprocess.run(ffmpeg, timeout=20)` × 3 個時間點（`video_utils.py:54`），一支影片素材最多可卡 loop 60 秒。
   - 素材讀檔 + base64：`runtime.py:1320/1328` 同步 `read_bytes()` 加 base64 編碼整張圖/整支影片；S3 模式下 `runtime.py:1335` 的 boto3 `get_object().read()` 是同步網路 I/O。
   - 同步 SQLAlchemy 查詢：`generate_score_result`（`runtime.py:1298-1308`）、`process_score_event`（`service.py:1169` 起）、匯入 job（`service.py:799` 起）裡的 repository 呼叫都直接在 loop 上跑，且每個狀態轉換都會寫一筆 worker event。
   - 匯入狀態的同步 Redis 呼叫（`import_status_store.py` 的 `set_import_status`/`get_import_status`）。
4. Event loop 被佔住時，後端**連任何 HTTP 請求都無法回應**（accept/parse/dispatch/回寫全在 loop 上），權限 API 因此懸住 → 分頁假死到批次結束。
5. 已排除的嫌疑：LLM 呼叫本身已用 `asyncio.to_thread` 包好（`runtime.py:932/956`），卡的不是「等 AI 回應」，而是前後的同步段落。

批次匯入 N 筆素材時，匯入（並發 5，`META_ANDROMEDA_OBSERVATION_MAX_CONCURRENCY`）+ 評分（並發 2，`META_ANDROMEDA_SCORE_MAX_CONCURRENCY`）連續佔用 loop，與觀察到的行為完全吻合。

### 1.2 問題二：模組其餘可優化項

盤點結果見第 6 節，依 P1（健壯性）/ P2（效能與體驗）/ P3（既有殘項）分級。

## 2. 目標

1. **可用性（P0）**：批次匯入 + 評分執行期間，整站 API（含權限檢查）維持正常回應，Andromeda 分頁即點即開。
2. **架構（長期）**：評分/匯入 worker 與 web process 解耦，評分負載不影響線上請求，且 worker 可獨立水平擴充。
3. **品質**：清除盤點出的殘留 debug 碼、typo、不當 log level 等健壯性問題。

## 3. 方案評估（問題一）

### 方案 A：短期止血 — 同 process 內用 `asyncio.to_thread` 包住所有同步阻塞段

**優點**：改動小、立即見效、不動部署拓撲。
**缺點**：評分負載（CPU/記憶體/threadpool）仍在 web process 內；ffmpeg 抽幀、大檔 base64 的記憶體峰值仍會影響線上服務；單 process 的 threadpool 是共用資源。

### 方案 B：長期方案 — 評分/匯入 worker 拆成獨立 process（**本計劃採用**）

利用 queue_host 既有基礎建設（`redis_stream` 消費者、`database_queue` sweeper、跨 process 的 `DistributedSemaphore` Redis token bucket 皆已存在且經 P1-4 修復驗證），只差「真的跑一個獨立 worker process」而不是讓 web process 自己消化。

**優點**：
- 評分負載完全隔離，web process 的 event loop 永遠不會被評分工作佔用，這是唯一能徹底解決問題的架構。
- 基礎建設完備度高：`queue_host.py` 的 `consume_redis_stream_batch`/`reclaim_redis_stream_pending`、`core/scheduler.py` 的 `sweep_meta_andromeda_queue`、`concurrency.py` 的跨 process 限流全部已實作並有測試，本次主要工作是「角色拆分」而非新建機制。
- worker 可獨立調整資源與副本數（Zeabur 加一個 service、同 image 不同啟動命令）。

**缺點/風險**：
- 部署拓撲多一個 service（多一份常駐資源費用）。
- 單機開發不想跑兩個 process，需保留單 process 模式（見 4.2 的 `SERVICE_ROLE=all`）。
- worker process 內部若不做方案 A 的 to_thread 包裝，worker 自己的 loop 一樣會被卡住（影響同 process 內其他排程 job 與並發評分），所以**方案 A 不是丟棄式工程，是方案 B 的前置必要工作**。

**結論：A + B 都做，分兩波**。Wave 1 先止血（同 process 也不卡），Wave 2 完成架構拆分（長期解法），Wave 3 前端防禦與問題二清理。

## 4. 長期架構設計（Wave 2 核心）

### 4.1 目標拓撲

```
┌─────────────────────┐         ┌──────────────────────────┐
│  web process         │         │  worker process           │
│  (FastAPI)           │         │  (backend/worker_main.py) │
│                      │  Redis  │                            │
│  匯入/評分請求        │ Stream  │  AsyncIOScheduler          │
│  → enqueue (xadd) ───┼────────►│  → stream consumer         │
│  → 立即回 202        │         │  → reclaim (stale pending) │
│                      │         │  → db queue sweeper        │
│  不註冊 MA 消費 jobs  │         │  → weekly closed loop      │
└──────────┬───────────┘         └──────────┬────────────────┘
           │                                 │
           └────────── PostgreSQL ───────────┘
              （score events / worker events / dead letters）
```

### 4.2 角色開關：`SERVICE_ROLE`

`core/config.py` 新增：

```
SERVICE_ROLE = web | worker | all   # 預設 all
```

- **`all`（預設）**：行為同現況（單機開發、未設定任何環境變數時零改動），評分在同 process 消化，靠 Wave 1 的 to_thread 保護不卡 loop。
- **`web`**：
  - `core/startup.py` 不註冊 MA 相關 scheduler jobs（`ma_queue_sweeper`、`ma_redis_stream_consumer`、`ma_redis_stream_reclaim`、`ma_weekly_closed_loop`）。
  - `queue_host.get_active_host()` 強制回 `redis_stream`（Redis 不可用時回 `database_queue`，由 worker 的 sweeper 撿）；**停用 `local_async` fallback 與 apscheduler dispatch**，web 端 enqueue 永遠只做 `xadd` / 寫 DB 排队，不在本 process 執行評分。
  - 觀察匯入 job 一併搬離：`router.py:403` 匯入端點改為只呼叫 `queue_observed_facebook_ad_import`（寫入狀態 + enqueue 一筆 `observation_import` stream 事件），不再用 `BackgroundTasks` 在 web process 跑 `run_observed_facebook_ad_import_job`。
- **`worker`**：
  - 新增入口 `backend/worker_main.py`：初始化 DB / Redis / scheduler，註冊上述 MA jobs，另掛極簡 `/healthz` HTTP endpoint（供 Zeabur 健康檢查），不掛業務 router。
  - stream consumer 擴充：目前 `consume_redis_stream_batch` 只認評分事件，需支援 `event_type=observation_import` 的訊息分流到 `run_observed_facebook_ad_import_job`。

### 4.3 訊息與降級路徑

| 情境 | 行為 |
|---|---|
| Redis 正常 | web `xadd` → worker stream consumer 消費；consumer crash 未 ack 的訊息由 `reclaim_redis_stream_pending`（`xautoclaim`）撿回 |
| Redis 不可用 | web 落 `database_queue`（score event status=queued 已入 DB）；worker 的 `sweep_meta_andromeda_queue` 每輪掃 queued 事件補派工 |
| worker 全掛 | 事件安全堆積在 stream/DB，web 不受影響；匯入狀態顯示 queued，worker 恢復後繼續消化（`import_status_store` TTL 1hr 內狀態可查） |
| 單機開發（`SERVICE_ROLE=all`、無 Redis） | 完全維持現況行為，Wave 1 的 to_thread 保證不卡 loop |

跨 process 並發限制不需要新工作：`DistributedSemaphore`（`concurrency.py`）本來就是 Redis token bucket，worker 多副本時評分並發依然全域收斂在 `META_ANDROMEDA_SCORE_MAX_CONCURRENCY`。

### 4.4 部署（Zeabur）

- 既有 service 保持不變，環境變數加 `SERVICE_ROLE=web`。
- 新增一個 service，同一個 repo/image，啟動命令改 `python worker_main.py`（或 `uvicorn worker_main:app`，若 healthz 走 ASGI），環境變數 `SERVICE_ROLE=worker`，共用 `DATABASE_URL`、`REDIS_URI`、`OPENROUTER_API_KEY` 等。
- worker service 記憶體配額建議 ≥ web（ffmpeg 抽幀 + 大檔 base64 的峰值都在這裡）。
- `META_ANDROMEDA_QUEUE_HOST` 兩邊都設 `redis_stream`。

## 5. 實作步驟

### Wave 1：止血 — 消除 event loop 阻塞（先行，獨立可上線）

| # | 任務 | 檔案 | 內容 |
|---|---|---|---|
| 1.1 | 資產準備區塊整段離開 loop | `runtime.py:1286-1373` | 把 `generate_score_result` 內「DB 查 asset/user/API key + 讀檔 + base64 + S3 下載 + keyframe 抽取」抽成同步函式 `_prepare_asset_context(score_payload)`，以單一 `await asyncio.to_thread(...)` 呼叫（順帶解決該函式 130 行過長的問題） |
| 1.2 | ffmpeg 抽幀非阻塞 | `video_utils.py` | 因 1.1 已整段丟 thread，維持 `subprocess.run` 即可；補上單元測試驗證逾時/失敗降級行為不變 |
| 1.3 | 評分狀態機 DB 段離開 loop | `service.py:1169-1286` | `process_score_event` 內三段 `SessionLocal()` + repository 呼叫各自抽成同步函式並 `asyncio.to_thread` 包裝 |
| 1.4 | 匯入 job DB/Redis 段離開 loop | `service.py:799-857`、`import_status_store.py` | `run_observed_facebook_ad_import_job` 內的 repository 與 `set_import_status`（同步 Redis）呼叫以 `asyncio.to_thread` 包裝；`import_observed_facebook_ad` 內的同步段比照處理 |
| 1.5 | 迴歸測試 | `backend/tests/test_meta_andromeda_module.py` | 新增「loop 心跳測試」：monkeypatch 資產準備為 `time.sleep(2)` 的假阻塞，在評分執行期間以 `asyncio` 定時器驗證 loop 延遲 < 100ms；既有測試全綠 |

驗收標準：本機以 heuristic/openrouter 任一 provider 批次匯入 10 筆素材（含至少 2 支影片），期間連續呼叫 `/api/permissions/me/module/meta_andromeda`，P95 回應時間 < 500ms，評分結果與 Wave 1 前一致。

### Wave 2：長期方案 — worker process 拆分

| # | 任務 | 檔案 | 內容 |
|---|---|---|---|
| 2.1 | `SERVICE_ROLE` 設定 | `core/config.py` | 新增 `SERVICE_ROLE` property（`web`/`worker`/`all`，預設 `all`） |
| 2.2 | scheduler 註冊按角色分流 | `core/startup.py`、`core/scheduler.py` | `SERVICE_ROLE=web` 時不註冊 4 個 MA jobs；`worker` 時只註冊 MA jobs（週報等其他 jobs 歸屬需盤點確認，預設留在 web） |
| 2.3 | web 端 dispatch 收斂 | `queue_host.py` | `get_active_host()` 支援角色感知：`web` 角色下只回 `redis_stream`/`database_queue`，永不回 `apscheduler`/`local_async` |
| 2.4 | 匯入 job 走 queue | `router.py:403-421`、`queue_host.py`、`service.py` | stream 訊息加 `event_type` 欄位；匯入端點在 `web` 角色下改 enqueue `observation_import` 事件；consumer 依 `event_type` 分流到匯入 job 或評分 job；`all` 角色維持 `BackgroundTasks` 現況 |
| 2.5 | worker 入口 | `backend/worker_main.py`（新檔） | 初始化 + 註冊 jobs + `/healthz`；優雅關閉（收 SIGTERM 後停止收新訊息、等待 in-flight 評分完成或到達逾時） |
| 2.6 | 測試 | `backend/tests/` | 角色分流單元測試（各角色註冊的 jobs 清單、dispatch 路徑）；`observation_import` 事件端對端測試（enqueue → consumer 分流 → 匯入完成 → 自動評分入列） |
| 2.7 | 部署文件 | `docs/06_部署指南.md` 或 `docs/10` | 補 Zeabur 雙 service 拓撲、環境變數矩陣、worker 資源建議 |

驗收標準：staging 以 `web` + `worker` 雙 service 部署，批次匯入期間 web 的 CPU/記憶體無評分負載痕跡，權限 API 回應不受影響；手動 kill worker 驗證事件堆積與恢復消化；`xautoclaim` reclaim 路徑以人工中斷 consumer 驗證。

### Wave 3：前端防禦 + 問題二清理

| # | 任務 | 檔案 | 內容 |
|---|---|---|---|
| 3.1 | 模組權限 sessionStorage 快取 | `frontend/src/hooks/usePermission.jsx` | `useModuleAccess` 比照 `useUserModules` 既有 pattern：先讀 sessionStorage 快取立即渲染，背景 revalidate 更新；權限被撤銷時最多一個 session 的顯示延遲（後端 API 仍會 403，僅影響 UI gate） |
| 3.2 | 權限請求逾時 | `frontend/src/hooks/usePermission.jsx` | `fetchWithRetry` 加 `AbortSignal.timeout`（例如 10s），逾時顯示可重試的錯誤狀態而非永久轉圈 |
| 3.3 | 問題二 P1 清理 | 見第 6 節 | 四項小修，一個 commit 內完成 |

## 6. 問題二：模組優化盤點清單

### P1 — 健壯性（納入 Wave 3.3 一併處理）

| 項目 | 位置 | 問題 | 修法 |
|---|---|---|---|
| typo 產生的死碼 | `runtime.py:1404` | `META_ANDROMENS_SCORING_ALLOW_FALLBACK` 拼錯 + `hasattr` 三元式，實際永遠走正確設定，但可讀性極差 | 直接改為 `if not settings.META_ANDROMEDA_SCORING_ALLOW_FALLBACK: raise` |
| 殘留 debug 碼 | `modules/fb_ads/analytics_service.py:231-235` | 每次報表請求同步 append 寫 `debug_fields.log`，在高頻路徑上 | 移除（或改 `logger.debug`） |
| log level 不當 | `runtime.py:1378` | 每次評分都以 `logger.warning` 印 API key 長度等常態資訊 | 降為 `logger.debug` |
| 無意義延遲 | `runtime.py:1283` | `generate_score_result` 開頭 `await asyncio.sleep(0.05)` 無明顯用途 | 刪除（若有節流意圖，應以註解說明並移至 dispatch 層） |

### P2 — 效能與體驗（獨立立案，不阻塞本計劃）

| 項目 | 位置 | 問題 | 建議 |
|---|---|---|---|
| 大檔記憶體壓力 | `runtime.py:1320-1339` | 圖片/影片整包讀進記憶體再 base64（膨脹 33%）塞進 prompt payload；本地上傳資產無大小上限檢查（觀察匯入下載有 `OBSERVED_DOWNLOAD_MAX_BYTES`，上傳路徑沒有對應 gate） | 上傳路徑加大小上限；超大圖先縮圖再 base64；Wave 2 後峰值隔離在 worker，風險已降 |
| 匯入 fallback 逐筆打 FB API | `importers/facebook_ads_importer.py:130-142` | 批次匯入大量「不在整包報告前 500 名」的素材時，每筆各打一次單 ad 查詢 | 批次收集 miss 的 ad_id 後合併查詢，或提高整包報告 limit |
| 檔案過大 | `repository.py`（2692 行）、`runtime.py`（1415 行） | 單檔混雜多層職責，改動風險逐次升高 | 不專案性重構；下次觸碰時順勢拆分（Wave 1.1 抽出 `_prepare_asset_context` 即是第一步） |

### P3 — 既有記錄殘項

| 項目 | 來源 | 狀態 |
|---|---|---|
| `is_promoted` per-base-profile（P2-7） | docs/19+20 審查 | 未做，維持既有排程，與本計劃無相依 |

## 7. 風險與緩解

| 風險 | 緩解 |
|---|---|
| to_thread 化後執行順序/交易邊界改變引入 race | Wave 1 保持「一段同步函式 = 一個 Session 生命週期」原封搬移，不重排邏輯；跨 process 限流已由 `DistributedSemaphore` 收斂 |
| threadpool 耗盡（大量並發評分各佔一個 thread） | 評分並發已被 semaphore 限制在 2、匯入 5，遠低於預設 threadpool 上限；不需自訂 executor |
| `web` 角色誤部署但沒跑 worker → 評分永遠 queued | worker 心跳寫入 Redis/DB，web 的 `/api/meta-andromeda` 佇列頁顯示 worker 存活狀態警示；文件寫明環境變數矩陣 |
| stream 訊息格式加 `event_type` 的相容性 | consumer 對缺 `event_type` 的舊訊息預設當評分事件處理（向後相容） |
| 前端權限快取造成撤權顯示延遲 | 僅快取 UI gate，後端 API 權限檢查不變；快取 key 含 team_id，切團隊即失效 |

## 8. 里程碑

| 波次 | 內容 | 預估 | 可獨立上線 |
|---|---|---|---|
| Wave 1 | to_thread 止血 + 迴歸測試 | 0.5–1 天 | ✅（上線後症狀即消失） |
| Wave 2 | SERVICE_ROLE + worker_main + 匯入走 queue + 部署 | 2–3 天 | ✅（需 Zeabur 加開 worker service） |
| Wave 3 | 前端快取/逾時 + P1 清理 | 0.5 天 | ✅ |

依賴關係：Wave 1 → Wave 2（1.1–1.4 的包裝在 worker 內同樣必要）；Wave 3 與 Wave 2 無相依，可並行。
