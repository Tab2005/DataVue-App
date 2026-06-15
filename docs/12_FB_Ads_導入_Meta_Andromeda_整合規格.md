# 12 FB Ads 導入 Meta Andromeda 整合規格

## 文件目的

本文件定義 `DataVue-App` 內既有 `FB Ads` 數據流，如何安全且可維護地導入 `Meta Andromeda` 供創意評分、審核與後續工作流程使用。

本文件是開發前規格文件。目的是先確認資料流、模組邊界、API 契約、權限模型與驗收條件，再進入實作。

## 適用範圍

本規格只處理下列整合情境：

- 從既有 `FB Ads` 分析資料中，選取單筆廣告創意
- 將該創意正規化後導入 `Meta Andromeda`
- 建立可追蹤的 `score_event`
- 保留來源 lineage，讓後續 `review queue / monitoring / release` 可追溯

本規格不處理：

- 新的 Facebook API 抓取器重寫
- Meta Andromeda 模型邏輯改版
- 跨平台素材來源整合（如 TikTok / Google Ads）
- 批次匯入與批次評分排程

## 目前現況

### FB Ads 已有能力

既有 `FB Ads` 模組已可從 Facebook Ads API 抓回分析列資料，主要入口位於：

- [backend/routers/facebook.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\routers\facebook.py)
- [backend/modules/fb_ads/analytics_service.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\fb_ads\analytics_service.py)

目前 `analytics-data` 已能回傳：

- `campaign_id`
- `adset_id`
- `ad_id`
- `name`
- `objective`
- `image_url`
- `status`
- spend / clicks / roas / purchases 等成效欄位

### Meta Andromeda 目前吃的資料契約

目前 `Meta Andromeda` 的評分送單入口為：

- `POST /api/meta-andromeda/assets:upload`
- `POST /api/meta-andromeda/scores`

相關 schema 位於：

- [backend/modules/meta_andromeda/schemas.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\schemas.py)

目前 `ScoreSubmitRequest` 需要的核心欄位是：

- `asset_uri`
- `asset_type`
- `asset_id`
- `request_mode`
- `objective`
- `placement_family`
- `market`
- `primary_text`
- `headline`
- `cta`

### 現況缺口

目前缺少一層穩定的匯入邊界：

- `FB Ads` 回來的是報表列資料，不是 `Meta Andromeda` 可直接評分的標準素材請求
- `Meta Andromeda` 需要 `asset_uri`，但 `FB Ads` 目前主要提供的是 `image_url`
- `FB Ads` 報表列不保證完整提供 `headline / primary_text / cta`
- 若讓前端直接把 `FB Ads row` 硬組成 `/scores` payload，會導致模組耦合與介面失控

## 目標

建立一條正式的整合路徑，使使用者能從 `FB Ads` 現有資料列中，將單筆廣告創意導入 `Meta Andromeda`，並符合以下條件：

1. `Meta Andromeda` 不直接依賴 Facebook 原始 API 回應格式
2. `FB Ads` 與 `Meta Andromeda` 之間存在明確的正規化層
3. 產生的 `score_event` 保留來源追蹤資訊
4. 權限檢查同時涵蓋：
   - `fb_ads` 可讀
   - `meta_andromeda` 可操作
5. 未來可沿用相同模式支援其他廣告來源

## 整體流程圖

以下流程描述第一階段預計實作的單筆創意導入路徑。

```text
[使用者在 FB Ads Analytics 畫面選取一筆 ad row]
  |
  v
[前端顯示「送至 Meta Andromeda」操作]
  |
  v
[前端送出 POST /api/meta-andromeda/import/facebook-ads]
  |
  | request:
  | - account_id
  | - ad_id
  | - since / until
  | - market / placement_family / request_mode
  | - optional primary_text / headline / cta
  v
[Meta Andromeda import endpoint]
  |
  +--> [檢查權限]
  |      - fb_ads module access
  |      - meta_andromeda module access
  |      - meta_andromeda:operate
  |
  +--> [讀取 X-Team-ID]
  |
  +--> [呼叫 Facebook Ads importer]
           |
           +--> [從 FB Ads service 取得 ad row / creative metadata]
           |
           +--> [正規化成 CreativeCandidate]
                    - source_platform
                    - account_id / campaign_id / adset_id / ad_id
                    - objective
                    - media_url / media_type
                    - optional copy fields
                    - performance_snapshot
  |
  v
[素材處理]
  |
  +--> [驗證是否有可評分 media_url]
  |
  +--> [下載遠端素材]
  |
  +--> [寫入 Meta Andromeda storage]
  |
  +--> [取得 asset_uri / asset_id / asset_type]
  v
[Meta Andromeda score request 組裝]
  |
  +--> [建立標準 ScoreSubmitRequest]
           - asset_uri
           - asset_type
           - asset_id
           - objective
           - placement_family
           - market
           - primary_text / headline / cta
  |
  v
[Meta Andromeda 既有流程]
  |
  +--> create_score_event
  +--> assign_score_runtime_job
  +--> enqueue_score_event
  |
  v
[回傳 import response]
  |
  | response:
  | - score_event_id
  | - status=queued
  | - runtime_job_id
  | - asset_uri
  | - source lineage
  v
[前端提示成功並導向 Review Queue / Score Detail]
```

### 流程分層

為避免模組耦合失控，流程責任應明確分層：

1. `FB Ads` 模組

- 提供 ad row / creative metadata 的來源能力
- 不負責 Meta Andromeda 的 storage 與 score event 建立

2. `facebook_ads_importer`

- 將 Facebook 專屬資料正規化為 `CreativeCandidate`
- 封裝欄位對應與素材型別判斷

3. `Meta Andromeda import service`

- 驗證權限
- 下載與轉存素材
- 組裝標準 `ScoreSubmitRequest`
- 建立 `score_event`

4. 前端

- 只負責觸發匯入與顯示結果
- 不負責素材下載、storage 寫入或 lineage 拼裝

## 核心設計決策

### 1. 不直接重用 `/api/meta-andromeda/scores` 作為 FB Ads 原始匯入接口

原因：

- `/scores` 的契約是「已準備好可評分素材」的內部標準格式
- `FB Ads` 現有資料並不天然符合該契約
- 若直接讓前端轉型，會讓前端承擔 storage、素材類型判定、lineage 拼裝等責任

結論：

- 保留既有 `/scores` 作為標準評分入口
- 新增一條 import 型 API，專責把 `FB Ads` 創意轉成 Meta Andromeda 可接受的請求

### 2. 新增中介模型 `CreativeCandidate`

`CreativeCandidate` 是匯入層的內部標準模型，用來承接不同平台素材來源。

建議欄位：

```json
{
  "source_platform": "facebook_ads",
  "source_account_id": "act_123456789",
  "campaign_id": "120000000000010",
  "adset_id": "120000000000011",
  "ad_id": "120000000000012",
  "ad_name": "Summer Promo Ad 01",
  "objective": "OUTCOME_SALES",
  "placement_family": "feed",
  "market": "TW",
  "primary_text": null,
  "headline": null,
  "cta": null,
  "media_url": "https://...",
  "media_type": "image",
  "thumbnail_url": "https://...",
  "performance_snapshot": {
    "spend": 1200.5,
    "impressions": 18234,
    "clicks": 321,
    "purchases": 14,
    "roas": 2.85
  },
  "source_fetched_at": "2026-06-15T12:00:00Z"
}
```

設計原則：

- 這是匯入層模型，不直接暴露給前端作為長期 public contract
- 可作為後續 TikTok / Google Ads 導入的共用格式

### 3. 匯入流程要由後端負責，不由前端拼裝

正確流程：

1. 前端從 `FB Ads` 畫面送出 `account_id + ad_id + context`
2. 後端用該資訊補抓或重建 creative candidate
3. 後端驗證是否有可用素材 URL
4. 後端下載或轉存素材到 `Meta Andromeda` storage
5. 後端取得標準 `asset_uri`
6. 後端組裝既有 `ScoreSubmitRequest`
7. 後端呼叫 Meta Andromeda 既有 service 建立 `score_event`

## 建議 API 設計

### 新增 Endpoint

`POST /api/meta-andromeda/import/facebook-ads`

用途：

- 從既有 Facebook Ads 資料導入一筆創意到 Meta Andromeda

### Request

```json
{
  "account_id": "act_123456789",
  "ad_id": "120000000000012",
  "since": "2026-06-01",
  "until": "2026-06-15",
  "market": "TW",
  "placement_family": "feed",
  "request_mode": "auto",
  "primary_text": null,
  "headline": null,
  "cta": null
}
```

說明：

- `account_id` 與 `ad_id` 為必要欄位
- `since/until` 用於補抓或確認該筆 ad 的對應分析資料快照
- `market / placement_family / request_mode` 可先由前端或預設值帶入
- `primary_text / headline / cta` 若現有 FB Ads 資料抓不到，可讓前端補填或維持空值

### Response

```json
{
  "score_event_id": "ma_evt_20260615_001",
  "status": "queued",
  "runtime_job_id": "meta_andromeda_score_ma_evt_20260615_001",
  "asset_uri": "storage://meta-andromeda/uploads/2026/06/creative_001.png",
  "asset_type": "image",
  "asset_id": "fb_ad_120000000000012",
  "source": {
    "platform": "facebook_ads",
    "account_id": "act_123456789",
    "ad_id": "120000000000012"
  }
}
```

### 錯誤語義

- `400`: 缺少必要欄位或 payload 不合法
- `403`: 沒有 `fb_ads` 或 `meta_andromeda` 對應權限
- `404`: 找不到對應 ad 或素材
- `409`: 該 ad 在指定時間區間內不可匯入
- `422`: ad 可找到，但缺少可評分素材
- `500`: 匯入過程發生非預期錯誤

## 後端模組邊界

### 建議新增職責

#### A. Import schema

建議新增：

- `FacebookAdImportRequest`
- `FacebookAdImportResponse`

位置：

- `backend/modules/meta_andromeda/schemas.py`

#### B. Import service

建議新增 service function：

- `MetaAndromedaService.import_from_facebook_ad(...)`

內部責任：

1. 驗證 request
2. 讀取 FB Ads creative / analytics 資料
3. 建立 `CreativeCandidate`
4. 將遠端素材轉成 Meta Andromeda storage asset
5. 呼叫既有 `create_score_event / assign_score_runtime_job / enqueue_score_event`
6. 回傳標準 response

#### C. FB Ads adapter / normalizer

不建議把 Facebook 特定邏輯直接散落在 `MetaAndromedaService` 裡。

建議新增一個 adapter：

- `backend/modules/meta_andromeda/importers/facebook_ads_importer.py`

職責：

- 將 FB Ads 現有資料列正規化成 `CreativeCandidate`
- 封裝 Facebook 專屬欄位對應與 media 判定

## 素材處理策略

### 基本原則

`Meta Andromeda` 應只吃自身 storage 可追蹤的 `asset_uri`，不直接長期依賴第三方 URL。

### 建議流程

1. 從 FB Ads 拿到 `image_url` 或可替代 thumbnail/source
2. 後端下載素材
3. 呼叫 `storage_adapter.store_asset(...)`
4. 取得：
   - `asset_uri`
   - `asset_id`
   - `storage_key`
   - `checksum`
5. 再送入既有 `/scores` 流程

### 原因

- 避免 Facebook URL 過期或權限失效
- 讓 Meta Andromeda 的 `review queue / score detail / monitoring` 可穩定預覽
- 讓後續 audit / retry / replay 有固定素材來源

## Lineage 設計

匯入後的 `score_event` 應保留來源追蹤資訊。

最低要求：

```json
{
  "source_platform": "facebook_ads",
  "source_account_id": "act_123456789",
  "source_campaign_id": "120000000000010",
  "source_adset_id": "120000000000011",
  "source_ad_id": "120000000000012"
}
```

建議保留位置：

- `score_event` 資料表欄位延伸，或
- `lineage` JSON 欄位擴充

目標：

- review queue 可回查來源
- monitoring / timeline 可追溯哪一支廣告導入
- 未來支援從 FB Ads 頁面回跳到 Meta Andromeda 詳情

## 權限模型

此整合涉及兩個模組，不應只檢查單一模組權限。

### 必要條件

使用者必須同時具備：

1. `fb_ads` module access
2. `meta_andromeda` module access
3. `meta_andromeda:operate`

### 額外建議

若匯入流程會主動讀取較深層 FB Ads 資料，建議額外要求：

- `fb_ads:analytics:view`

### 權限判定原則

- 由後端做最終權限判定
- 必須支援 `X-Team-ID`
- 前端可用權限控制按鈕是否顯示，但不可取代後端驗證

## 前端整合建議

### 第一階段

先在 `FB Ads Analytics` 列表增加單筆操作：

- `送至 Meta Andromeda`

觸發後：

- 帶入 `account_id + ad_id + context`
- 呼叫新 API `/api/meta-andromeda/import/facebook-ads`
- 成功後顯示：
  - `score_event_id`
  - `queued` 狀態
  - 可跳轉到 `review queue` 或 `score detail`

### 不建議做法

不要在前端直接做以下事情：

- 下載 Facebook 圖片再上傳
- 自行判斷 `asset_type`
- 自行拼裝完整 `/scores` payload
- 自行決定 lineage 結構

這些都應留在後端匯入層。

## Commands

後續實作與驗證預計使用：

```powershell
cd backend
.\.venv311\Scripts\python.exe -m pytest tests\test_meta_andromeda_module.py -q
.\.venv311\Scripts\python.exe -m pytest tests\test_permissions.py -q

cd ..\frontend
npm run build
```

## 相關檔案

### 既有檔案

- [backend/routers/facebook.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\routers\facebook.py)
- [backend/modules/fb_ads/analytics_service.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\fb_ads\analytics_service.py)
- [backend/modules/meta_andromeda/router.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\router.py)
- [backend/modules/meta_andromeda/service.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\service.py)
- [backend/modules/meta_andromeda/schemas.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\schemas.py)
- [frontend/src/pages/Analytics.jsx](C:\Users\BWM2\Documents\python\DataVue-App\frontend\src\pages\Analytics.jsx)
- [frontend/src/pages/MetaAndromedaScoreLab.jsx](C:\Users\BWM2\Documents\python\DataVue-App\frontend\src\pages\MetaAndromedaScoreLab.jsx)

### 建議新增檔案

- `backend/modules/meta_andromeda/importers/facebook_ads_importer.py`
- `backend/tests/test_meta_andromeda_facebook_import.py`
- 視情況新增前端 service method

## 驗收條件

### API 層

- 可用 `account_id + ad_id` 成功建立一筆 Meta Andromeda `score_event`
- 匯入 response 會回 `score_event_id`、`status`、`asset_uri`
- 缺少素材時回 `422`
- 權限不足時回 `403`

### 資料層

- 匯入後 `score_event` 可追溯 `facebook_ads` 來源
- 匯入素材已轉存為 Meta Andromeda 自有 storage asset

### 權限層

- 只有具備 `fb_ads` 可讀 + `meta_andromeda:operate` 的使用者可匯入
- `viewer` 不可匯入
- `team_member` 若無 `operate` 不可匯入
- `team_admin` / `team_owner` 可匯入

### UI 層

- 在 FB Ads 相關畫面可看到「送至 Meta Andromeda」操作
- 成功匯入後可導向 review queue 或 score detail

## 風險與注意事項

### 1. Facebook creative 素材欄位不穩定

不同 ad type 可能只有：

- `image_url`
- `thumbnail_url`
- 無法直接取到原始可評分媒體

因此 importer 必須容錯，必要時拒絕匯入並回 `422`。

### 2. 文案欄位不一定拿得到

若現有資料流無法穩定提供：

- `primary_text`
- `headline`
- `cta`

可先允許空值，或在 UI 匯入前補填。

### 3. 匯入不應影響既有 FB Ads 分析流程

本整合必須是 additive，不可破壞既有：

- `/api/analytics-data`
- `/api/dashboard-data`
- `/api/analytics-trend`

### 4. 後續可能需要去重策略

同一個 `ad_id` 可能被多次導入。

第一階段建議：

- 允許重複導入
- 先透過 lineage 記錄來源

第二階段再決定是否加：

- 「同 ad 同期間避免重複匯入」
- 或「提示該 ad 已匯入過」

## 成功定義

本規格完成後，代表後續實作應達成：

1. 使用者可從 `FB Ads` 現有資料列一鍵送入 `Meta Andromeda`
2. `Meta Andromeda` 內部仍維持自己的標準 score contract
3. 匯入流程對使用者透明，不需手動下載再上傳素材
4. 權限、素材存放、來源追蹤都落在後端穩定邊界內

## Open Questions

以下事項在進入實作前最好先確認：

1. `FB Ads` 現有資料流是否已能穩定取到 creative 文案欄位？
2. 影片型素材是否納入第一階段，還是先只做 `image`？
3. 匯入後 UI 要直接跳轉到：
   - `Score Lab`
   - `Review Queue`
   - 還是未來新增的 `Score Detail` 頁？
4. 是否需要在第一階段就加入「避免重複匯入」策略？
