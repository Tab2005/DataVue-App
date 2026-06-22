# 10 Meta Andromeda 模組說明

## 文件目的

本文件重新定義 `Meta Andromeda` 在 `DataVue-App` 內的模組定位、能力邊界與後續演進方向。

`Meta Andromeda` 不再只是一個「上傳素材後預估成效」的獨立 MVP，而是 DataVue 內負責創意預估、投放後觀測、與學習閉環的模組。

本文件應作為：

- 模組定位說明
- 前後端功能邊界依據
- 權限、部署、驗收與後續開發的上位文件

## 模組定位

`Meta Andromeda` 的目標是建立一條完整的 creative intelligence 閉環：

```text
素材輸入
  -> 預估評分
  -> 投放觀測
  -> 真實數據回收
  -> 特徵校準 / drift / release evaluation
  -> 反饋下一輪預估能力
```

換句話說，`Meta Andromeda` 應同時承擔三層能力：

1. `Prediction`

- 在沒有投放數據時，根據素材、文案、目標與版位預估表現
- 這是原本 MVP 的核心能力

2. `Observation`

- 在素材實際投放後，保存真實表現、素材快照、來源 lineage 與 reviewer/operator 判讀依據

3. `Learning`

- 用投放後真實數據校準預估能力
- 建立 calibration、drift、release decision 所需的資料基礎

## 模組功能地圖

### A. Pre-launch Prediction

用途：

- 創意尚未投放
- 或資料不足，仍需先做預估判斷

典型輸入：

- `asset_uri`
- `asset_type`
- `objective`
- `placement_family`
- `market`
- `primary_text / headline / cta`

典型輸出：

- `overall_score`
- `roas_band`
- `risk_tags`
- `diagnostic_breakdown`
- `top_positive_drivers / top_negative_drivers`

### B. Post-launch Observation

用途：

- 創意已投放
- 已具備 `FB Ads` 真實數據

典型輸入：

- creative 素材
- 廣告來源識別
- observed performance snapshot
- reviewer/operator 回饋

典型輸出：

- observed creative record
- source lineage
- 真實表現快照
- 後續 diagnostics / calibration 掛點

### C. Learning / Calibration

用途：

- 將真實投放結果回灌模型能力

第一階段不要求完整訓練系統，但應為下列能力保留結構：

- prediction vs observed outcome 比對
- calibration data accumulation
- drift signal accumulation
- release gate decision support

## 當前與目標的關係

### 目前已存在的部分

在 `DataVue-App` 目前已存在的是：

- 模組總覽 `overview`
- 評分工作台 `score lab`
- `score_event` 提交與讀取
- review queue
- feedback timeline
- monitoring summary / timeline
- release overview / actions
- runtime health

這些能力主要屬於：

- `Pre-launch Prediction`
- 與 prediction 相關的 workflow / monitoring / release 支援

### 目前缺少的部分

目前尚未完整建立的是：

- 從 `FB Ads` 導入已投放素材的 `Observation` 路徑
- observed creative record 與 performance snapshot
- prediction 與 observed outcome 的關聯
- 用 observed data 強化 prediction 的 `Learning` 路徑

## 前端路由

前端路由定義於 [frontend/src/App.jsx](C:\Users\BWM2\Documents\python\DataVue-App\frontend\src\App.jsx)。

目前已存在：

- `/meta-andromeda`
- `/meta-andromeda/review-queue`
- `/meta-andromeda/monitoring`
- `/meta-andromeda/release`
- `/meta-andromeda/score-lab`

目前這些路由主要對應 prediction 與其 workflow。

後續若 observation / learning 擴充成熟，可新增：

- observed creative detail
- evaluation queue
- calibration / drift workspace

## 後端 API

後端 router 位於 [backend/modules/meta_andromeda/router.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\router.py)。

目前已存在的 API 以 prediction workflow 為主：

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
- `POST /api/meta-andromeda/release/approve`
- `POST /api/meta-andromeda/release/reject`
- `POST /api/meta-andromeda/release/rollback`
- `POST /api/meta-andromeda/worker/score-events/{score_event_id}/callbacks`

後續 observation 第一階段建議新增一條獨立入口：

- `POST /api/meta-andromeda/evaluations/import/facebook-ads`

注意：

- observed import 不應直接重用既有 `/scores` 契約
- `/scores` 應維持 pre-launch prediction 的語義

## 運作架構

### 1. Intake

來源可以分成兩種：

- 手動上傳素材
- 從 `FB Ads` 匯入已投放素材與 observed data

### 2. Scoring Runtime

目前 scoring runtime 位於：

- [backend/modules/meta_andromeda/runtime.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\runtime.py)
- [backend/modules/meta_andromeda/model_registry.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\model_registry.py)

目前採用：

- registry-backed runtime
- Gemini provider
- deterministic heuristic fallback

說明：

- 這條 runtime 目前主要服務 prediction flow
- 未來 learning 不是取代它，而是逐步校準它

### 3. Storage

儲存 adapter 位於 [backend/modules/meta_andromeda/storage.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\storage.py)。

目前支援：

- `filesystem`
- `s3_compatible`

此層不只服務素材上傳，也應服務 observed creative 轉存。

### 4. Queue Host

queue host adapter 位於 [backend/modules/meta_andromeda/queue_host.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\queue_host.py)。

目前支援：

- `apscheduler`
- `local_async`
- `database_queue`
- `external_webhook`
- `redis_stream`

### 5. Monitoring / Release

目前 monitoring 與 release 主要追蹤 prediction workflow 的執行狀態。

後續若 observation / learning 完整納入，release gate 的依據應逐步包含：

- observed performance evidence
- calibration 結果
- drift signal

## 權限模型

模組權限依賴 DataVue 既有 Google 登入與 permission mapping，不存在獨立帳密登入。

### 目前權限策略

`Meta Andromeda` 目前已收斂為單一模組權限模型：

- module key：`meta_andromeda`
- 用途：控制模組是否可見、是否可進入 `/meta-andromeda*`、以及是否可使用模組內所有功能

說明：

- 目前不再區分 `view / feedback / operate / release` 的 feature-level gate
- 只要使用者在當前工作區具備 `meta_andromeda` module access，即可使用模組內功能
- 前端與後端的實際授權檢查都應以 `require_module("meta_andromeda")` 為準

### 與 FB Ads 匯入的聯動

若從 `FB Ads` 導入 observed data，後端應檢查：

- `fb_ads` module access
- `fb_ads:analytics:view`
- `meta_andromeda` module access

## 模組演進路線

### Phase 0. MVP

- 手動上傳素材
- 直接做預估與診斷

### Phase 1. Prediction Workflow in DataVue

- review queue
- monitoring
- release
- runtime health

### Phase 2. Observed Creative Import

- 從 `FB Ads` 匯入已投放素材
- 建立 observed creative record
- 保存 performance snapshot 與 lineage

### Phase 3. Learning Loop

- prediction vs observed 對照
- calibration
- drift
- release evidence 強化

## 目前已確認可用

- backend migration 與啟動已修正到可在 Zeabur 既有 PostgreSQL 上升級
- shared runtime smoke 已通過
- review queue / monitoring / release overview 在共享環境可讀
- frontend 側欄已改為 `Meta Andromeda` 子選單群組
- 權限模型已接到 DataVue 共用 permission system

## 尚未完成的主項目

模組當前最大的未完成項，不再只是 UAT，而是模組能力本身尚未補齊第二條與第三條路線：

- `FB Ads observed data import`
- observed creative record
- prediction vs observed 關聯
- calibration / learning 基礎
- reviewer / operator 真實流程驗收
- rollback drill / final sign-off

## 相關文件

- [11_Meta_Andromeda_權限完善調整紀錄.md](C:\Users\BWM2\Documents\python\DataVue-App\docs\11_Meta_Andromeda_權限完善調整紀錄.md)
- [12_FB_Ads_導入_Meta_Andromeda_整合規格.md](C:\Users\BWM2\Documents\python\DataVue-App\docs\12_FB_Ads_導入_Meta_Andromeda_整合規格.md)
- [13_FB_Ads_導入_Meta_Andromeda_實作計劃.md](C:\Users\BWM2\Documents\python\DataVue-App\docs\13_FB_Ads_導入_Meta_Andromeda_實作計劃.md)
- [06_部署指南.md](C:\Users\BWM2\Documents\python\DataVue-App\docs\06_部署指南.md)
- [backend/modules/meta_andromeda/README.md](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\README.md)
