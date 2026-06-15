# 13 FB Ads 導入 Meta Andromeda 實作計劃

## 目的

本文件依 [12_FB_Ads_導入_Meta_Andromeda_整合規格.md](C:\Users\BWM2\Documents\python\DataVue-App\docs\12_FB_Ads_導入_Meta_Andromeda_整合規格.md) 拆解第一階段實作工作。

修正後的實作目標不是：

- 把 `FB Ads` ad row 直接導入既有 `score pipeline`

而是：

- 建立 `FB Ads observed data -> Meta Andromeda evaluation pipeline` 的第一階段基礎

## 第一階段範圍

第一階段只做：

1. observed creative 匯入契約
2. Facebook ad observed data importer
3. 素材轉存
4. observed creative record 建立
5. lineage 與 performance snapshot 保存
6. 權限與基本驗證

第一階段不做：

1. observed creative 自動重跑 `/scores`
2. 觀測結果與既有 pre-score 自動配對
3. release / drift 自動計算
4. 完整 observed diagnostics UI

## 架構決策

- 既有 `/api/meta-andromeda/scores` 維持 pre-score 語義
- observed data 匯入走獨立 endpoint
- observed record 與 `score_event` 不混用同一主鍵語義
- importer 封裝 Facebook 專屬欄位邏輯
- 後端負責素材下載與 storage 轉存

## 實作階段

### Phase 1. observed import 契約與 endpoint 骨架

目標：

- 建立 observed import API，而不是 score import API

任務：

- 在 `meta_andromeda/schemas.py` 新增：
  - `FacebookAdObservedImportRequest`
  - `FacebookAdObservedImportResponse`
- 在 `meta_andromeda/router.py` 新增：
  - `POST /api/meta-andromeda/evaluations/import/facebook-ads`
- 在 `meta_andromeda/service.py` 新增：
  - `import_observed_facebook_ad(...)`

驗收：

- endpoint 存在
- request / response schema 固定
- 測試可驗證基本 validation 與錯誤語義

### Checkpoint A

- API 契約穩定
- 已與既有 `/scores` 流程語義切開

### Phase 2. Facebook observed importer

目標：

- 從既有 FB Ads ad row 與 creative metadata 產生 observed candidate

任務：

- 新增 `backend/modules/meta_andromeda/importers/facebook_ads_importer.py`
- importer 需負責：
  - 讀取 ad row
  - 補足 creative metadata
  - 取得 observed performance snapshot
  - 正規化成 `ObservedCreativeCandidate`
- 明確規則：
  - 先只支援 `image`
  - 若缺少可用 media_url，回 `422`

驗收：

- importer 可獨立測試
- 缺素材、找不到 ad、缺關鍵欄位時有穩定錯誤

### Checkpoint B

- Facebook 專屬資料映射已收斂到 importer
- observed candidate 結構固定

### Phase 3. 素材轉存與 observed record 建立

目標：

- 將 observed creative 轉成 Meta Andromeda 可追蹤素材與紀錄

任務：

- 下載遠端 `image_url`
- 呼叫 Meta Andromeda storage adapter 轉存素材
- 建立 observed creative record
- 保存：
  - `asset_uri`
  - `asset_id`
  - `source_platform`
  - `source_account_id`
  - `campaign_id`
  - `adset_id`
  - `ad_id`
  - `performance_snapshot`

驗收：

- 匯入完成後能回傳 `observed_creative_id`
- 資料可追溯來源與成效快照

### Checkpoint C

- 後端已可完成完整 observed import
- 尚未做 UI 也可驗證 end-to-end backend flow

### Phase 4. 權限與 team-aware 行為

目標：

- 將 observed import 接到既有權限系統

任務：

- 檢查：
  - `fb_ads` module access
  - `fb_ads:analytics:view`
  - `meta_andromeda` module access
  - `meta_andromeda:operate`
- 支援 `X-Team-ID`
- 補 allow / deny 測試

驗收：

- 權限不足時回 `403`
- `viewer` 不可匯入
- `team_admin / team_owner` 可匯入

### Checkpoint D

- observed import 已正確接入 shared permission model

### Phase 5. 前端入口

目標：

- 在 `FB Ads Analytics` 提供 observed import 入口

任務：

- 在 ad row 增加：
  - `送至 Meta Andromeda 評估`
- 呼叫 observed import endpoint
- 顯示：
  - 匯入成功
  - `observed_creative_id`
  - 後續可查看的位置

驗收：

- 使用者可從現有 FB Ads 畫面完成 observed import
- 前端不自行處理素材下載與 storage

### Checkpoint E

- 使用者可操作完整 observed import flow

### Phase 6. 文件與後續掛點

目標：

- 文件與現況一致
- 為第二階段 diagnostics / calibration 保留掛點

任務：

- 更新規格文件
- 更新 Meta Andromeda 模組說明
- 在文件明確標註：
  - 第二階段才會討論 evaluation summary / diagnostics / drift linkage

驗收：

- 文件狀態與實作一致

## 任務清單

- [ ] Task 1: 建立 observed import schema 與 endpoint 骨架
  - Acceptance: `/api/meta-andromeda/evaluations/import/facebook-ads` 存在
  - Verify: backend schema / router 測試

- [ ] Task 2: 建立 `facebook_ads_importer`
  - Acceptance: 可產生 `ObservedCreativeCandidate`
  - Verify: importer 單元測試

- [ ] Task 3: 完成素材轉存與 observed record 建立
  - Acceptance: 匯入成功後有 `observed_creative_id` 與 `asset_uri`
  - Verify: backend 整合測試

- [ ] Task 4: 補齊權限與 team-aware 測試
  - Acceptance: 權限 allow / deny 行為正確
  - Verify: 權限測試

- [ ] Task 5: 在 FB Ads 畫面加 observed import 按鈕
  - Acceptance: 前端可觸發 observed import
  - Verify: `npm run build`

- [ ] Task 6: 更新文件並標定第二階段掛點
  - Acceptance: 文件與實作同步
  - Verify: docs review

## 驗證指令

```powershell
cd backend
.\.venv311\Scripts\python.exe -m pytest tests\test_meta_andromeda_module.py -q
.\.venv311\Scripts\python.exe -m pytest tests\test_permissions.py -q

cd ..\frontend
npm run build
```

## 風險與對策

### 1. observed import 與 score import 混淆

風險：

- 後續實作者又把 observed import 接回 `/scores`

對策：

- 在 schema / router / docs 明確使用 `evaluation` / `observed` 命名

### 2. Facebook creative 欄位不完整

風險：

- 文案與素材欄位有缺漏

對策：

- 第一階段允許 copy fields 空值
- 只要求可匯入素材與核心 observed metrics

### 3. observed record 結構定太死

風險：

- 第二階段 diagnostics / calibration 擴充困難

對策：

- 以 lineage + performance snapshot + asset metadata 為第一階段最小閉環
- 不過早設計完整 evaluation 結果表

## Open Questions

1. 第一階段 observed import 是否只支援 `image`？
2. observed creative detail 是否延後到第二階段？
3. observed import 完成後，前端是顯示 toast 即可，還是要先提供 detail link？
4. 第二階段是否需要把 observed data 與既有 pre-score record 做 matching？
