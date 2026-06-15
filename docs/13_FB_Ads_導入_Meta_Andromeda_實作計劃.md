# 13 FB Ads 導入 Meta Andromeda 實作計劃

## 目的

本文件依 [12_FB_Ads_導入_Meta_Andromeda_整合規格.md](C:\Users\BWM2\Documents\python\DataVue-App\docs\12_FB_Ads_導入_Meta_Andromeda_整合規格.md) 拆解實作順序、任務切分、驗收方式與風險控制。

此文件的用途是：

- 作為開發前的執行計劃
- 控制 `FB Ads -> Meta Andromeda` 整合的實作範圍
- 確保每一階段都能獨立驗證

## 總覽

本次實作要達成的核心成果：

1. 建立 `facebook_ads_importer`
2. 新增 `POST /api/meta-andromeda/import/facebook-ads`
3. 讓後端可把 Facebook creative 轉存到 Meta Andromeda storage
4. 重用既有 Meta Andromeda score event 流程
5. 在 `FB Ads Analytics` UI 上提供單筆導入入口
6. 補齊權限、錯誤、lineage 與測試

## 架構決策

- 既有 `POST /api/meta-andromeda/scores` 不改為 FB Ads 匯入入口
- 新增 import 型 endpoint，避免前端負責資料轉型與素材下載
- Facebook 專屬欄位映射收斂到 importer，不散落在 router / page / service 多處
- `Meta Andromeda` 只吃標準化後的 request，不直接依賴 Facebook 回應格式
- 權限必須同時檢查 `fb_ads` 與 `meta_andromeda`

## 實作階段

### Phase 1. 契約與匯入骨架

目標：

- 把 import API 契約與 service 骨架建立起來
- 不先碰前端

任務：

- 在 `meta_andromeda/schemas.py` 新增：
  - `FacebookAdImportRequest`
  - `FacebookAdImportResponse`
- 在 `meta_andromeda/service.py` 新增：
  - `import_from_facebook_ad(...)`
- 在 `meta_andromeda/router.py` 新增：
  - `POST /api/meta-andromeda/import/facebook-ads`
- 明確定義錯誤語義：
  - `403` 權限不足
  - `404` ad 不存在
  - `422` 無可評分素材

驗收：

- API endpoint 可被呼叫
- payload 驗證正常
- 尚未接完整 importer 前，可先回固定 stub 或明確未完成錯誤

主要檔案：

- [backend/modules/meta_andromeda/schemas.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\schemas.py)
- [backend/modules/meta_andromeda/router.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\router.py)
- [backend/modules/meta_andromeda/service.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\service.py)

### Checkpoint A

- API 契約已固定
- 不需動前端即可用測試驗證 request / response shape

### Phase 2. Facebook importer 與資料正規化

目標：

- 從既有 FB Ads service 抓出單筆 ad 可用素材與欄位
- 正規化為 `CreativeCandidate`

任務：

- 新增 `backend/modules/meta_andromeda/importers/facebook_ads_importer.py`
- 定義 importer 內部職責：
  - 依 `account_id + ad_id + since + until` 抓取資料
  - 從 ad row 與 creative metadata 整理：
    - `campaign_id`
    - `adset_id`
    - `ad_id`
    - `objective`
    - `media_url`
    - `media_type`
    - `performance_snapshot`
  - 產出 `CreativeCandidate`
- 明確規則：
  - `image_url` 可用時視為 `image`
  - 若只有 `thumbnail_url`，定義是否接受
  - 無法判定可評分素材時回 `422`

驗收：

- importer 可獨立測試
- 對 ad row 缺欄位與缺素材時有穩定錯誤

主要檔案：

- `backend/modules/meta_andromeda/importers/facebook_ads_importer.py`
- [backend/modules/fb_ads/analytics_service.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\fb_ads\analytics_service.py)
- 視需要新增 importer 專用測試檔

### Checkpoint B

- `CreativeCandidate` 轉換規則固定
- Facebook 專屬邏輯已封裝，不外漏到 router / 前端

### Phase 3. 素材轉存與 score event 建立

目標：

- 將 Facebook 遠端素材變成 Meta Andromeda 自有 asset
- 導入既有 `score_event` 流程

任務：

- 在 import service 中新增：
  - 遠端素材下載
  - `asset_type` 判定
  - `storage_adapter.store_asset(...)`
- 取得：
  - `asset_uri`
  - `asset_id`
  - `storage_key`
- 將 importer 產出的 candidate 轉為標準 `ScoreSubmitRequest`
- 呼叫既有：
  - `create_score_event`
  - `assign_score_runtime_job`
  - `enqueue_score_event`

驗收：

- 匯入一筆 Facebook ad 後，能得到 `queued` 的 `score_event`
- Meta Andromeda review queue 可查到新資料

主要檔案：

- [backend/modules/meta_andromeda/service.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\service.py)
- [backend/modules/meta_andromeda/storage.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\storage.py)
- 視需要擴充 repository / lineage 欄位

### Checkpoint C

- 後端單獨已能完成完整匯入
- 前端尚未接按鈕也不影響 end-to-end API 驗證

### Phase 4. 權限與 lineage

目標：

- 把匯入流程納入 team-aware 權限模型
- 保留來源追溯能力

任務：

- 在 import endpoint 中檢查：
  - `fb_ads` module access
  - `meta_andromeda` module access
  - `meta_andromeda:operate`
- 視需要補：
  - `fb_ads:analytics:view`
- 在 score event 或 lineage 結構中保留：
  - `source_platform`
  - `source_account_id`
  - `source_campaign_id`
  - `source_adset_id`
  - `source_ad_id`

驗收：

- `viewer` 不可導入
- `member` 無 operate 不可導入
- `admin/owner` 可導入
- review queue / detail 可回查來源

主要檔案：

- [backend/modules/meta_andromeda/router.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\router.py)
- [backend/modules/meta_andromeda/service.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\service.py)
- repository / schema / tests

### Checkpoint D

- 匯入功能與既有權限系統整合完成
- 權限 allow / deny 行為可測

### Phase 5. 前端入口整合

目標：

- 在 `FB Ads Analytics` 畫面新增單筆導入入口

任務：

- 在 `Analytics.jsx` 或對應 row component 加入：
  - `送至 Meta Andromeda`
- 點擊後呼叫：
  - `POST /api/meta-andromeda/import/facebook-ads`
- 成功後顯示：
  - `score_event_id`
  - `queued`
  - 導向 review queue 或 detail 的入口
- 沒有權限時不顯示，或顯示 disabled 狀態與提示

驗收：

- 使用者可從 ad row 成功觸發導入
- UI 不需手動下載或重新上傳素材

主要檔案：

- [frontend/src/pages/Analytics.jsx](C:\Users\BWM2\Documents\python\DataVue-App\frontend\src\pages\Analytics.jsx)
- 前端 service 檔案
- 視需要新增 toast / modal / action button component

### Checkpoint E

- 使用者端流程完整
- 可從 FB Ads 直接進入 Meta Andromeda 工作流

### Phase 6. 測試與文件回填

目標：

- 補齊後端與前端的核心驗證
- 更新相關文件

任務：

- 後端測試：
  - request validation
  - 權限 allow / deny
  - importer 成功 / 缺素材 / 找不到 ad
  - score event 建立成功
- 前端測試：
  - button 顯示條件
  - 成功匯入的 action flow
- 文件更新：
  - 規格文件
  - Meta Andromeda 模組說明
  - 權限調整紀錄

驗收：

- 測試通過
- 文件狀態與實作一致

## 任務清單

- [ ] Task 1: 建立 import API schema 與 router 骨架
  - Acceptance: 新 endpoint 存在，request / response schema 固定
  - Verify: `backend\\.venv311\\Scripts\\python.exe -m pytest tests\\test_meta_andromeda_module.py -q`
  - Files: `schemas.py`, `router.py`, `service.py`

- [ ] Task 2: 建立 `facebook_ads_importer`
  - Acceptance: 可將 Facebook ad 資料轉為 `CreativeCandidate`
  - Verify: importer 單元測試通過
  - Files: `importers/facebook_ads_importer.py`, 測試檔

- [ ] Task 3: 完成遠端素材轉存與 score event 建立
  - Acceptance: 匯入後可得到 `queued` 的 `score_event`
  - Verify: 後端整合測試通過
  - Files: `service.py`, `storage.py`, tests

- [ ] Task 4: 補齊匯入權限與 lineage
  - Acceptance: 權限與來源追溯都能驗證
  - Verify: 權限測試與 detail 檢查通過
  - Files: `router.py`, `service.py`, repository/tests

- [ ] Task 5: 在 FB Ads 畫面加「送至 Meta Andromeda」
  - Acceptance: 前端可觸發匯入並顯示成功結果
  - Verify: `npm run build`
  - Files: `Analytics.jsx`, frontend service

- [ ] Task 6: 補測試與文件回填
  - Acceptance: 測試與文件同步完成
  - Verify: pytest + frontend build + docs 更新
  - Files: tests + docs

## 驗證指令

```powershell
cd backend
.\.venv311\Scripts\python.exe -m pytest tests\test_meta_andromeda_module.py -q
.\.venv311\Scripts\python.exe -m pytest tests\test_permissions.py -q

cd ..\frontend
npm run build
```

## 風險與對策

### 1. Facebook 資料欄位不足

風險：

- 現有 ad row 未必有完整 copy fields

對策：

- 第一階段允許 `primary_text / headline / cta` 為空
- importer 只保證素材與核心識別欄位

### 2. 素材 URL 失效或不可下載

風險：

- Facebook 回傳的 URL 可能有時效性或權限限制

對策：

- 將下載失敗定義為明確的 import failure
- 先支援 image，影片延後

### 3. 匯入入口過早綁死 UI

風險：

- 若先做畫面按鈕，後端契約尚未穩定，會反覆修改

對策：

- 先完成 Phase 1~4 再接前端

## Open Questions

1. 第一階段是否只支援 `image`，暫不支援 `video`？
2. 匯入成功後預設導向：
   - `review queue`
   - `score detail`
   - 還是留在原頁顯示 toast？
3. 是否要在第一階段做「同 ad 避免重複匯入」？
4. 若 `headline / primary_text / cta` 缺失，是否需要前端先補填再送？
