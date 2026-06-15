# 13 FB Ads 導入 Meta Andromeda 實作計劃

## 目的

本文件依 [12_FB_Ads_導入_Meta_Andromeda_整合規格.md](C:\Users\BWM2\Documents\python\DataVue-App\docs\12_FB_Ads_導入_Meta_Andromeda_整合規格.md) 拆解第一階段的落地實作。

本計劃的目標是：

- 建立 `Observation` 路徑
- 為未來 `Learning` 路徑保留資料結構與擴充點

不是：

- 把 `FB Ads` 直接接進既有 `Prediction` score submit

## 第一階段範圍

第一階段只做：

1. observed import API 契約
2. facebook observed importer
3. observed creative 素材轉存
4. observed creative record 建立
5. lineage 與 performance snapshot 保存
6. observation window 標準化
7. 權限與 team-aware 驗證

第一階段不做：

1. observed creative 自動重跑 prediction
2. 完整 feature engineering pipeline
3. 完整 calibration / drift product flow
4. 完整 observed diagnostics UI
5. `last_14d` 與 `custom` observation window

## 實作原則

- `Prediction` 與 `Observation` 契約分開
- importer 負責 Facebook 專屬邏輯
- storage 轉存由後端負責
- 第一階段先建立 observation 事實層
- 第二階段再在 observation 之上建立 learning / calibration

## 實作階段

### Phase 1. Observation import 契約與 endpoint 骨架

目標：

- 建立 observation import API

任務：

- 在 `schemas.py` 新增：
  - `FacebookAdObservedImportRequest`
  - `FacebookAdObservedImportResponse`
- 在 `router.py` 新增：
  - `POST /api/meta-andromeda/evaluations/import/facebook-ads`
- 在 `service.py` 新增：
  - `import_observed_facebook_ad(...)`
- 固定第一階段 observation window contract：
  - `last_7d`
  - `last_30d`
  - `lifetime`

驗收：

- endpoint 存在
- request / response schema 固定
- 錯誤語義明確
- 不接受第一階段未開放的 window kind

### Checkpoint A

- observation API 已與既有 `/scores` 切開

### Phase 2. Facebook observed importer

目標：

- 從 `FB Ads` ad row 產生 `ObservedCreativeCandidate`

任務：

- 新增 `backend/modules/meta_andromeda/importers/facebook_ads_importer.py`
- 由 importer 負責：
  - 讀取 ad row
  - 讀取 creative metadata
  - 取得 observed performance snapshot
  - 正規化欄位
  - 判斷 media type

驗收：

- importer 可獨立測試
- 缺素材 / 找不到 ad / 缺 observed metrics 可穩定報錯

### Checkpoint B

- Facebook 專屬資料映射收斂到 importer

### Phase 3. 素材轉存與 observed creative record

目標：

- 將 observed creative 轉成 Meta Andromeda 內部可追溯素材

任務：

- 下載 `media_url`
- 呼叫 storage adapter 寫入素材
- 建立 observed creative record
- 保存：
  - `asset_uri`
  - `asset_id`
  - `source_platform`
  - `source_account_id`
  - `campaign_id`
  - `adset_id`
  - `ad_id`
  - `observation_window_kind`
  - `observation_window_start`
  - `observation_window_end`
  - `performance_snapshot`

驗收：

- 匯入後回傳 `observed_creative_id`
- 資料可追溯來源與 observed metrics

### Checkpoint C

- 後端已完成完整 observation import flow

### Phase 4. 權限與 team-aware 驗證

目標：

- 將 observation import 接上 DataVue 共用權限系統

任務：

- 檢查：
  - `fb_ads` module access
  - `fb_ads:analytics:view`
  - `meta_andromeda` module access
- 支援 `X-Team-ID`
- 補 allow / deny 測試

驗收：

- 權限不足時回 `403`
- `viewer` 不可匯入
- `team_admin / team_owner` 可匯入

### Checkpoint D

- observation import 已正確接入 team-aware permission

### Phase 5. 前端入口

目標：

- 在 `FB Ads Analytics` 提供 observation import 入口

任務：

- 在 ad row 增加：
  - `送至 Meta Andromeda 評估`
- 呼叫 observation import endpoint
- 顯示：
  - 匯入成功
  - `observed_creative_id`
  - 後續可查看位置

驗收：

- 使用者可從現有 `FB Ads` 畫面完成 observation import

### Checkpoint E

- 使用者可完成 observed creative 匯入

### Phase 6. 第二階段掛點整理

目標：

- 為 learning 路徑留下清楚的下一步

任務：

- 在文件中標註第二階段要接的能力：
  - prediction vs observed matching
  - calibration data generation
  - drift signal generation
  - evaluation summary

驗收：

- 文件可清楚銜接第二階段

## 任務清單

- [ ] Task 1: 建立 observation import schema 與 endpoint 骨架
  - Acceptance: `/api/meta-andromeda/evaluations/import/facebook-ads` 存在
  - Acceptance: 第一階段僅接受 `last_7d / last_30d / lifetime`
  - Verify: backend schema / router 測試

- [ ] Task 2: 建立 `facebook_ads_importer`
  - Acceptance: 可產生 `ObservedCreativeCandidate`
  - Verify: importer 單元測試

- [ ] Task 3: 完成素材轉存與 observed creative record 建立
  - Acceptance: 匯入後可取得 `observed_creative_id` 與 `asset_uri`
  - Verify: backend 整合測試

- [ ] Task 4: 補齊權限與 team-aware 測試
  - Acceptance: 權限 allow / deny 行為正確
  - Verify: 權限測試

- [ ] Task 5: 在 `FB Ads` 畫面加 observed import 按鈕
  - Acceptance: 前端可觸發 observation import
  - Verify: `npm run build`

- [ ] Task 6: 更新文件並整理第二階段掛點
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

### 1. Observation 又被當成 Prediction

風險：

- 開發時又把 observed import 接回 `/scores`

對策：

- API / schema / 文件全部使用 `observation` / `evaluation` 命名

### 2. Facebook creative 欄位不完整

風險：

- 缺少文案或素材欄位

對策：

- 第一階段允許 copy fields 空值
- 先以素材與 observed performance snapshot 為核心

### 3. 直接做 learning 過早複雜化

風險：

- 第一階段若直接做特徵訓練與 model update，會讓範圍爆炸

對策：

- 第一階段先建立 observation fact layer
- 第二階段再做 learning / calibration

## 第二階段預留

第二階段可在本計劃之後承接：

1. observed creative 與既有 pre-score record matching
2. 預估 vs 真實 outcome 對照
3. calibration feature / label 生成
4. drift evidence 聚合
5. evaluation summary 與 reviewer/operator 工作流

## Open Questions

1. 第一階段是否只支援 `image`？
2. observed detail 是否延後到第二階段？
3. 匯入成功後前端先顯示 toast，還是直接提供 detail link？
4. 第二階段要先做 calibration，還是先做 observed diagnostics？
