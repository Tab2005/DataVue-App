# 12 FB Ads 導入 Meta Andromeda 整合規格

## 文件目的

本文件重新定義 `FB Ads` 與 `Meta Andromeda` 的整合方向，避免把兩種不同語義的流程混在一起：

- `Pre-score pipeline`
  - 上傳素材
  - 預估素材表現
  - 適用於尚未投放或資料不足的創意

- `Post-launch evaluation pipeline`
  - 匯入已投放素材與真實成效
  - 做事後分析、校準、drift 檢查與 reviewer/operator 判讀
  - 適用於已經有 `FB Ads` 真實數據的創意

本規格的第一階段只處理第二條：

- `FB Ads observed data -> Meta Andromeda evaluation / feedback loop`

不處理：

- 把已投放素材直接送進既有 `Meta Andromeda score submit` 當成同一條流程

## 問題釐清

### Meta Andromeda 原始用途

目前 `Meta Andromeda` 既有主流程是：

- 上傳素材
- 補充 `objective / placement / market / copy`
- 呼叫 `POST /api/meta-andromeda/scores`
- 取得預估分數與診斷

這條流程的本質是：

- 預測
- 上線前評估
- 低資料或無資料情境下的判斷輔助

### FB Ads 現有資料的性質

`FB Ads` 模組現有抓回來的資料則是：

- 素材已經投放過
- 已經有 `spend / impressions / clicks / purchases / roas`
- 屬於真實觀測結果，不是預估輸入

因此，若把這些資料直接送進現在的 `/scores`，會出現語義衝突：

1. 這支素材已經有真實結果，不再只是「待預估樣本」
2. `/scores` 產出的東西目前定義為預估或診斷結果
3. 已投放資料更適合成為：
   - calibration data
   - drift data
   - post-launch diagnostic sample

## 本次修正後的整合方向

### 核心結論

`FB Ads` 現有數據不應在第一階段直接導入既有 `score submit` 流程。

第一階段正確方向應是：

- 將已投放素材與真實成效導入 `Meta Andromeda evaluation pipeline`
- 用來做：
  - 事後診斷
  - reviewer/operator 判讀
  - 預估結果驗證
  - drift / release / calibration 依據

### 功能邊界

#### A. Pre-score pipeline

用途：

- 預估尚未投放素材的可能表現

輸入：

- `asset_uri`
- `asset_type`
- `objective`
- `placement_family`
- `market`
- optional `primary_text / headline / cta`

輸出：

- 預估分數
- 風險標籤
- 說明摘要

現況：

- 已存在
- 不在本次整合範圍內改動主語義

#### B. Post-launch evaluation pipeline

用途：

- 對已投放素材做事後分析
- 比對真實表現與模型預估
- 累積 calibration 與 drift 訊號

輸入：

- creative 素材識別
- 真實成效快照
- 來源 lineage

輸出：

- observed creative record
- evaluation summary
- reviewer/operator 可用的事後診斷結果
- calibration / drift 訊號

現況：

- 本次整合第一階段應優先定義與建立

## 第一階段要做什麼

第一階段不是「一鍵把 FB Ads ad row 送去 score」。

第一階段要做的是：

1. 定義 observed creative 匯入模型
2. 定義 observed performance 匯入 API
3. 建立可追溯的素材與成效快照紀錄
4. 保留未來接上：
   - 診斷
   - calibration
   - drift
   - release evaluation

## 建議資料模型

### ObservedCreativeCandidate

建議先引入一個中介模型，專門描述已投放素材樣本：

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

- 這個模型代表「已觀測樣本」
- 不是既有 `ScoreSubmitRequest`
- 不應直接假裝自己是 pre-score request

## 整體流程圖

```text
[使用者在 FB Ads Analytics 畫面選取一筆已投放 ad row]
  |
  v
[前端顯示「送至 Meta Andromeda 評估」操作]
  |
  v
[前端送出 POST /api/meta-andromeda/evaluations/import/facebook-ads]
  |
  +--> [檢查權限]
  |      - fb_ads module access
  |      - meta_andromeda module access
  |      - meta_andromeda:operate
  |
  +--> [讀取 X-Team-ID]
  |
  +--> [呼叫 facebook_ads_importer]
           |
           +--> [讀取 ad row / creative metadata / observed metrics]
           |
           +--> [正規化為 ObservedCreativeCandidate]
  |
  +--> [素材轉存到 Meta Andromeda storage]
  |
  +--> [建立 observed creative record]
  |
  +--> [保存 lineage + performance snapshot]
  |
  +--> [回傳 observed record id / evaluation status]
  |
  v
[前端提示成功並導向 observed creative detail / evaluation queue]
```

## 建議 API 方向

### 第一階段建議 Endpoint

`POST /api/meta-andromeda/evaluations/import/facebook-ads`

用途：

- 從既有 `FB Ads` 匯入一筆已投放創意樣本
- 作為 observed creative / evaluation / calibration 的輸入

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
- `422`: 找得到 ad，但缺少可匯入素材或必要成效欄位
- `500`: 匯入流程非預期錯誤

## 權限模型

第一階段匯入 observed data 時，使用者應同時具備：

1. `fb_ads` module access
2. `fb_ads:analytics:view`
3. `meta_andromeda` module access
4. `meta_andromeda:operate`

原則：

- 前端只做顯示控制
- 後端做最終 team-aware 判定

## 與既有 score pipeline 的關係

### 明確分流

第一階段要明確保留以下界線：

- `/api/meta-andromeda/scores`
  - 仍然只用於 pre-score / prediction flow

- `/api/meta-andromeda/evaluations/import/facebook-ads`
  - 用於 post-launch observed data import

### 暫不做的事情

以下不在第一階段範圍：

1. 匯入 observed data 後立即重跑同一套 `/scores`
2. 用 observed ad 自動覆蓋既有 pre-score record
3. 混用 `score_event_id` 與 observed record id

## 第一階段成功定義

若第一階段完成，應達成：

1. 使用者可從 `FB Ads` 現有 ad row 匯入一筆 observed creative
2. 匯入資料會帶入真實成效快照，而不是只帶素材
3. 匯入資料與既有 `/scores` 流程語義分離
4. 後續可在此基礎上延伸：
   - calibration
   - drift
   - post-launch diagnostics

## 第二階段可能延伸

在 observed data import 建立後，才適合討論：

1. observed creative 是否要觸發事後診斷
2. observed result 是否要和舊有 pre-score 結果做比對
3. observed data 是否要納入 release gate / drift report
4. 是否建立 evaluation queue / observed detail UI

## Open Questions

1. 第一階段 observed import 是否只支援 `image`？
2. observed creative detail 要獨立頁面，還是先只做後端匯入？
3. 若缺少 `primary_text / headline / cta`，是否允許空值直接匯入？
4. observed import 完成後，是否需要立刻產生基本診斷摘要？
