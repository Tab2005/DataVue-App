# 10 Meta Andromeda 模組說明

## 文件目的

本文件描述 `Meta Andromeda` 在 `DataVue-App` 內的目前整合狀態，作為 DataVue 宿主專案內部的維運、部署、驗收與後續開發依據。

`meta-andromeda` 原始專案中的 `13~20` 系列文件仍保留整合歷程與驗收紀錄；本文件則以 `DataVue-App` 目前實際程式與部署狀態為準。

## 模組範圍

`Meta Andromeda` 目前提供下列能力：

- 模組總覽 `overview`
- 創意評分提交 `score submit`
- 評分結果讀取 `score detail`
- 審核佇列 `review queue`
- reviewer feedback 時間線
- 監控總覽 `monitoring summary`
- 單筆事件時間線 `score event timeline`
- drift trigger
- release overview / approve / reject / rollback
- shared runtime health

## 前端路由

前端路由定義於 [frontend/src/App.jsx](C:\Users\BWM2\Documents\python\DataVue-App\frontend\src\App.jsx)。

- `/meta-andromeda`
- `/meta-andromeda/review-queue`
- `/meta-andromeda/monitoring`
- `/meta-andromeda/release`
- `/meta-andromeda/score-lab`

左側選單定義於 [frontend/src/components/Sidebar.jsx](C:\Users\BWM2\Documents\python\DataVue-App\frontend\src\components\Sidebar.jsx)，目前以 `Meta Andromeda` 父層模組群組呈現，子選單包含：

- 模組總覽
- 審核佇列
- 監控總覽
- 版本總覽
- 評分工作台

## 後端 API

後端 router 位於 [backend/modules/meta_andromeda/router.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\router.py)。

主要端點如下：

- `GET /api/meta-andromeda/ping`
- `GET /api/meta-andromeda/overview`
- `GET /api/meta-andromeda/runtime/health`
- `GET /api/meta-andromeda/review-queue`
- `GET /api/meta-andromeda/review-queue/{score_event_id}`
- `GET /api/meta-andromeda/monitoring/summary`
- `GET /api/meta-andromeda/monitoring/score-events/{score_event_id}/timeline`
- `POST /api/meta-andromeda/drift:trigger`
- `GET /api/meta-andromeda/release/overview`
- `POST /api/meta-andromeda/assets:upload`
- `POST /api/meta-andromeda/scores`
- `GET /api/meta-andromeda/scores/{score_event_id}`
- `GET /api/meta-andromeda/scores/{score_event_id}/feedback`
- `POST /api/meta-andromeda/scores/{score_event_id}/feedback`
- `POST /api/meta-andromeda/release:approve`
- `POST /api/meta-andromeda/release:reject`
- `POST /api/meta-andromeda/release:rollback`
- `POST /api/meta-andromeda/worker/score-events/{score_event_id}/callbacks`

## 權限模型

模組權限依賴 DataVue 既有 Google 登入與後端 permission mapping，不存在獨立帳密登入。

目前使用的權限點：

- `meta_andromeda:module`
- `meta_andromeda:operate`
- `meta_andromeda:feedback`
- `meta_andromeda:release`

相關邏輯位於：

- [backend/modules/meta_andromeda/dependencies.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\dependencies.py)
- [backend/services/permission_service.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\services\permission_service.py)
- [backend/seeds/permission_seeds.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\seeds\permission_seeds.py)

說明：

- 目前共享環境 smoke 已使用 Google `Bearer token` 驗證通過。
- 若使用 super-admin token，只能證明功能與整合可用，不能代表 reviewer / operator 權限隔離已完成。

## Shared Runtime 組成

### Storage

儲存 adapter 位於 [backend/modules/meta_andromeda/storage.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\storage.py)。

目前支援：

- `filesystem`
- `s3_compatible`

核心設定在 [backend/core/config.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\core\config.py) 與 [backend/.env.example](C:\Users\BWM2\Documents\python\DataVue-App\backend\.env.example)。

### Queue Host

queue host adapter 位於 [backend/modules/meta_andromeda/queue_host.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\queue_host.py)。

目前支援：

- `apscheduler`
- `local_async`
- `database_queue`
- `external_webhook`
- `redis_stream`

### Runtime

scoring runtime 位於：

- [backend/modules/meta_andromeda/runtime.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\runtime.py)
- [backend/modules/meta_andromeda/model_registry.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\model_registry.py)

目前採用：

- model registry + provider runtime 結構
- 若可用 `GOOGLE_AI_API_KEY`，可走 provider 路徑
- 否則回退 deterministic heuristic provider

## 資料庫與 Migration

Meta Andromeda 相關 migration：

- `20260608_meta_andromeda_workflow_tables.py`
- `20260609_meta_andromeda_worker_observability.py`
- `20260611_meta_andromeda_drift_reports.py`

目前 deploy-time migration 由 [backend/run_migration.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\run_migration.py) 自動處理，並已加入：

- legacy DataVue DB baseline stamp
- `alembic_version.version_num` 長度自動擴充

backend 啟動配置位於 [backend/Dockerfile](C:\Users\BWM2\Documents\python\DataVue-App\backend\Dockerfile)。

目前啟動策略：

1. 先執行 `python run_migration.py`
2. 設定 `DATAVUE_SKIP_STARTUP_MIGRATIONS=1`
3. 再啟動 `python main.py`

此設計的目的是讓 migration 問題在 deploy 階段直接 fail-fast，而不是讓容器啟動後以半可用狀態提供服務。

## Health 與 Smoke

健康檢查入口：

- `GET /health`
- `GET /api/meta-andromeda/runtime/health`

shared-environment smoke script 位於：

- [backend/scripts/meta_andromeda_shared_runtime_smoke.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\scripts\meta_andromeda_shared_runtime_smoke.py)

目前已驗證共享環境：

- backend API domain：`https://datavue-dev-saas-bk.sitetegy.com`
- smoke 結果：`7/7 PASS`

注意：

- smoke 的 `BASE_URL` 必須填 backend API domain
- 不可填 frontend SPA domain，否則 `/health` 與 `/api/*` 會回前端 HTML

## 目前已確認可用

- backend migration 與啟動已修正到可在 Zeabur 既有 PostgreSQL 上升級
- shared runtime smoke 已通過
- review queue / monitoring / release overview 在共享環境可讀
- frontend 側欄已改為 `Meta Andromeda` 子選單群組

## 尚未完成的交付項

目前尚未完成的主項目不是功能開發，而是共享環境驗收：

- reviewer UAT
- operator UAT
- rollback drill
- 權限隔離驗證
- 最終 sign-off

這些驗收紀錄目前仍維護於 `meta-andromeda` 專案的交付文件中。

## 相關文件

- [06_部署指南.md](C:\Users\BWM2\Documents\python\DataVue-App\docs\06_部署指南.md)
- [zeabur_deployment_guide.md](C:\Users\BWM2\Documents\python\DataVue-App\docs\zeabur_deployment_guide.md)
- [backend/modules/meta_andromeda/README.md](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\README.md)

