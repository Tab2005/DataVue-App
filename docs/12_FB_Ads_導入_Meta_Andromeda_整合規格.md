# 12 FB Ads 導入 Meta Andromeda 整合規格

## 文件目的

本文件定義 `FB Ads` 與 `Meta Andromeda` 的整合規格，但整合目標不是把 `FB Ads` 現有資料直接送入既有 `score submit`。

本次整合的正確目標是：

- 讓 `FB Ads` 已投放素材與真實成效，成為 `Meta Andromeda` 的 `Observation` 輸入
- 讓 observation 資料能服務：
  - reviewer / operator 判讀
  - diagnostics
  - calibration
  - drift
  - release evidence
  - 強化未來 `Prediction` 能力

## 背景

### 原始 MVP 路徑

`Meta Andromeda` 原始 MVP 路徑是：

- 上傳素材
- 補充上下文欄位
- 送入 `/api/meta-andromeda/scores`
- 取得預估分數與診斷

這條路線的本質是：

- 在沒有真實投放數據時，先做預估

### DataVue 串接後的新現實

`DataVue` 既有 `FB Ads` 模組已經有真實投放資料：

- `campaign_id`
- `adset_id`
- `ad_id`
- `objective`
- `image_url`
- `spend`
- `impressions`
- `clicks`
- `purchases`
- `roas`

這代表：

- 有些素材在進入 `Meta Andromeda` 時，不再是「未知樣本」
- 而是「已投放、已有 observed outcome 的樣本」

因此：

- 這類樣本不能再直接當成既有 `Prediction` 流程的同義輸入

## 模組內的新角色分工

本整合完成後，`Meta Andromeda` 內部應區分三條語義：

### 1. Prediction

用途：

- 對尚未投放或無數據素材做預估

輸入：

- `asset_uri`
- `asset_type`
- `objective`
- `placement_family`
- `market`
- optional copy fields

輸出：

- score
- risk tags
- diagnostics

### 2. Observation

用途：

- 對已投放素材保存真實資料與上下文

輸入：

- creative asset
- source lineage
- performance snapshot

輸出：

- observed creative record
- observed performance snapshot
- reviewer / operator 可檢視資料

### 3. Learning

用途：

- 用 observed data 反饋 prediction 能力

第一階段不要求完整訓練系統，但 observation 資料結構必須足以支援：

- calibration
- drift
- release decision support
- 特徵回饋

## 第一階段整合目標

第一階段只做：

- `FB Ads -> Meta Andromeda Observation`

不做：

- `FB Ads -> 直接進 /scores`
- observed data 匯入後自動重跑 prediction
- 完整 model retraining pipeline

## 功能邊界

### 本次要做

1. 從 `FB Ads` 匯入單筆已投放 creative
2. 取得素材與 observed performance snapshot
3. 轉存素材到 Meta Andromeda storage
4. 建立 observed creative record
5. 保存 lineage
6. 為第二階段 diagnostics / calibration 預留掛點

### 本次不做

1. observed creative 自動生成新的 `score_event`
2. observed creative 自動寫回既有 review queue
3. 完整訓練模型與特徵工程 pipeline
4. release / drift 的完整 product UI

## 建議資料模型

### ObservedCreativeCandidate

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
  "performance_snapshot": {
    "spend": 1200.5,
    "impressions": 18234,
    "clicks": 321,
    "purchases": 14,
    "purchase_value": 4800,
    "roas": 2.85,
    "ctr": 1.76,
    "cpc": 3.74
  },
  "source_fetched_at": "2026-06-15T12:00:00Z"
}
```

### 設計原則

- 這是 observation 模型，不是 `ScoreSubmitRequest`
- 它的用途是保存觀測事實，不是直接表示預估請求

## 整體流程圖

```text
[使用者在 FB Ads Analytics 選一筆已投放 ad row]
  |
  v
[前端顯示「送至 Meta Andromeda 評估」]
  |
  v
[POST /api/meta-andromeda/evaluations/import/facebook-ads]
  |
  +--> 檢查權限
  |     - fb_ads module access
  |     - fb_ads:analytics:view
  |     - meta_andromeda module access
  |
  +--> 讀取 X-Team-ID
  |
  +--> 呼叫 facebook_ads_importer
  |      - 讀取 ad row
  |      - 讀取 creative metadata
  |      - 整理 observed performance snapshot
  |      - 正規化成 ObservedCreativeCandidate
  |
  +--> 驗證 media_url 是否可轉存
  |
  +--> 下載並轉存素材到 Meta Andromeda storage
  |
  +--> 建立 observed creative record
  |      - asset_uri
  |      - lineage
  |      - performance_snapshot
  |
  +--> 回傳 observed_creative_id
  |
  v
[前端提示成功，導向 observed detail 或後續 evaluation 工作區]
```

## 建議 API 契約

### Endpoint

`POST /api/meta-andromeda/evaluations/import/facebook-ads`

### Request

```json
{
  "account_id": "act_123456789",
  "ad_id": "120000000000012",
  "since": "2026-06-01",
  "until": "2026-06-15",
  "market": "TW",
  "placement_family": "feed",
  "primary_text": null,
  "headline": null,
  "cta": null
}
```

### Response

```json
{
  "observed_creative_id": "ma_obs_20260615_001",
  "status": "imported",
  "asset_uri": "storage://meta-andromeda/uploads/2026/06/fb_ad_120000000000012.png",
  "source": {
    "platform": "facebook_ads",
    "account_id": "act_123456789",
    "ad_id": "120000000000012"
  },
  "performance_snapshot": {
    "spend": 1200.5,
    "roas": 2.85,
    "purchases": 14
  }
}
```

### 錯誤語義

- `400`: payload 不合法
- `403`: 權限不足
- `404`: ad 不存在
- `422`: ad 找得到，但缺少可匯入素材或必要觀測欄位
- `500`: 匯入流程非預期錯誤

## 權限模型

觀測資料匯入時，使用者應同時具備：

1. `fb_ads` module access
2. `fb_ads:analytics:view`
3. `meta_andromeda` module access

原則：

- 前端只做顯示控制
- 後端做最終 team-aware 判定

## 與既有 Prediction 流程的關係

### 保留分流

- `/api/meta-andromeda/scores`
  - 仍然只用於 prediction

- `/api/meta-andromeda/evaluations/import/facebook-ads`
  - 用於 observation import

### Observation 對 Prediction 的價值

第一階段 observation import 的目的不是馬上替代 prediction，而是為 prediction 提供未來強化基礎：

- 哪些特徵與真實表現更相關
- 哪些診斷規則需要修正
- 哪些素材型別在實際投放中與預估有偏差

## 第一階段成功定義

1. 使用者可從 `FB Ads` 匯入單筆已投放素材
2. 匯入資料包含：
   - 素材
   - lineage
   - observed performance snapshot
3. 匯入流程與既有 `/scores` 語義清楚分離
4. 第二階段可在此基礎上擴充 diagnostics / calibration / drift

## 第二階段建議方向

在第一階段 observation import 建立後，再討論：

1. observed creative 是否產生 evaluation summary
2. 是否與既有 pre-score record 做 matching
3. 是否納入 release / drift evidence
4. 是否建立 observed detail / evaluation queue UI

## Open Questions

1. 第一階段是否只支援 `image`？
2. observed detail 頁面是否延後到第二階段？
3. 若缺少 `primary_text / headline / cta`，是否允許空值匯入？
4. 第二階段是否要建立 prediction vs observed 對照規則？
