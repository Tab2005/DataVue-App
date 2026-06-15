# Meta Andromeda Module

DataVue 內的 Meta Andromeda 模組整合入口。

## 目前已掛載範圍

- `/api/meta-andromeda/ping`
- `/api/meta-andromeda/overview`
- `/api/meta-andromeda/review-queue`
- `/api/meta-andromeda/review-queue/{score_event_id}`
- `/api/meta-andromeda/scores/{score_event_id}/feedback`
- `/api/meta-andromeda/monitoring/summary`
- `/api/meta-andromeda/monitoring/score-events/{score_event_id}/timeline`
- `/api/meta-andromeda/drift:trigger`
- `/api/meta-andromeda/runtime/health`
- `/api/meta-andromeda/release/overview`
- 前端 `/meta-andromeda*` 路由入口

## 目前狀態

- 已接 DataVue 現有 auth / module permission
- `Meta Andromeda` 目前採 module-only access：只要具備 `meta_andromeda` module access，即可使用模組內功能
- read / write workflow 已落到 DataVue DB
- asset upload 已支援 `filesystem` 與 `s3_compatible` storage backend；可落檔到 `META_ANDROMEDA_STORAGE_ROOT`，或寫入 shared object storage bucket
- score submit 已改成 APScheduler-backed queued processing
- score runtime 已改成 registry-backed provider flow，預設 `auto` 模式會在有 `GOOGLE_AI_API_KEY` 時走 Gemini，否則回退到 deterministic heuristic provider
- score worker 已補 timeout / retry policy，受 `META_ANDROMEDA_SCORE_TIMEOUT_SECONDS`、`META_ANDROMEDA_SCORE_MAX_ATTEMPTS`、`META_ANDROMEDA_SCORE_RETRY_DELAY_SECONDS` 控制
- 初次 submit 與 retry 都走 `queue_host.py`，目前可切到 `apscheduler`、`local_async`、`database_queue`、`external_webhook`、`redis_stream`
- `database_queue` 模式下，web host 只寫入 queued record，worker host 由 scheduler sweeper 依 `META_ANDROMEDA_QUEUE_SWEEP_INTERVAL_SECONDS` 掃描並派工
- `external_webhook` 模式下，DataVue 會將 score dispatch POST 到 `META_ANDROMEDA_EXTERNAL_QUEUE_ENDPOINT`，並附上 `request_id`、可選 `Authorization`、可選 HMAC signature
- 外部 worker 可透過 `/api/meta-andromeda/worker/score-events/{score_event_id}/callbacks` 回報 `accepted / processing / completed / failed`
- callback 可使用 `META_ANDROMEDA_EXTERNAL_WORKER_SHARED_SECRET` 的 HMAC signature，或 `META_ANDROMEDA_EXTERNAL_WORKER_TOKEN` 驗證
- callback `failed` 事件可依 `retryable / retry_delay_seconds` 接回既有 retry / dead-letter 規則
- `redis_stream` 模式下，DataVue 會直接將 score dispatch 寫入 `META_ANDROMEDA_REDIS_STREAM_KEY`
- worker host 啟動後會註冊 Redis stream consumer，使用 `META_ANDROMEDA_REDIS_STREAM_GROUP` / `META_ANDROMEDA_REDIS_STREAM_CONSUMER` 讀取、ack、刪除已接受訊息
- worker host 也會執行 stale pending reclaim，使用 `META_ANDROMEDA_REDIS_STREAM_RECLAIM_IDLE_MS` / `META_ANDROMEDA_REDIS_STREAM_RECLAIM_BATCH_SIZE` 重新 claim 長時間卡住的訊息
- worker audit / dead-letter observability 已持久化到 DataVue DB
- monitoring 已支援依 `score_event_id` 查看 worker timeline 與 dead-letter detail
- drift trigger 已落地，前端 monitoring 頁可直接送出 drift 檢查
- 若 scheduler 關閉，可依 `META_ANDROMEDA_SCORE_LOCAL_ASYNC_FALLBACK` 決定是否使用同程序 async fallback
- release overview 與 score lineage 會帶出 registry 來源、provider、provider model、feature manifest
- `/health` 現在會附帶 `checks.meta_andromeda`，可查看 queue host、storage backend、registry、external worker readiness
- `/api/meta-andromeda/runtime/health` 可提供更細的 shared-runtime readiness 摘要
- `backend/scripts/meta_andromeda_shared_runtime_smoke.py` 可對共享環境執行最小 API smoke
- frontend 已補頁面自動化測試：Monitoring / ScoreLab / ReviewQueue / Release
- 權限檢查已收斂為 `meta_andromeda` module access，不再對模組內 action 使用額外 feature gate
- 已支援 shared object storage adapter，但尚未完成目標環境 bucket / credentials 的實際驗證紀錄
- 已補外部 worker callback contract，但尚未完成共享環境 smoke / UAT / rollback 的實際執行紀錄

## 下一步

- 在共享環境執行 smoke / UAT / rollback，並回填 execution sheet / sign-off
