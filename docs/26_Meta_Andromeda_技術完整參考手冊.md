# 26 Meta Andromeda 技術完整參考手冊

> 本文件依據 2026-06-23 當前程式碼庫實際狀態撰寫，涵蓋 Meta Andromeda 模組的資料庫模型、API 端點、評分引擎、佇列主機、儲存後端、前端頁面與維護機制，供開發、部署、稽核人員作為首要技術參考。

---

## 1. 模組定位總覽

Meta Andromeda 是 DataVue 中負責「廣告創意智慧評估」的核心模組，整合三個能力層：

| 層次 | 名稱 | 說明 |
|---|---|---|
| Pre-launch | **Prediction（預估）** | 廣告上線前，由 AI 或啟發式演算法對素材評分，預估 ROAS 區間與驅動因素 |
| Post-launch | **Observation（觀測）** | 廣告上線後，從 Facebook Graph API 抓取真實成效，存入觀察紀錄 |
| Feedback | **Learning（學習）** | 比對預估與實測，產生校準資料集、漂移報告，驅動模型迭代 |

---

## 2. 系統架構全覽

```
┌─────────────────────────────────────────────────────────┐
│                     前端 (React)                         │
│  MetaAndromeda  │  ScoreLab  │  ReviewQueue  │  Release  │
│  Monitoring     │  (Overview │  (審核佇列)    │  (版本控台)│
│                 │   總覽)    │               │           │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────┐
│              後端 FastAPI (/api/meta-andromeda)          │
│  router.py → service.py → repository.py                 │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ runtime.py  │  │ queue_host   │  │  storage.py    │  │
│  │ (AI/Heuristic│  │ .py          │  │ (filesystem /  │  │
│  │  評分引擎)   │  │ (佇列調度)   │  │  S3)           │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
│                                                          │
│  model_registry.py (版本登錄中心)                        │
└──────────────────────────┬──────────────────────────────┘
                           │ SQLAlchemy ORM
┌──────────────────────────▼──────────────────────────────┐
│                    PostgreSQL 資料庫                      │
│  11 個 meta_andromeda_* 資料表                           │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 資料庫模型（11 張資料表）

所有模型定義於 `backend/database/models/meta_andromeda.py`。

### 3.1 MetaAndromedaAsset（素材資料表）

**資料表名**：`meta_andromeda_assets`

| 欄位 | 類型 | 說明 |
|---|---|---|
| `id` | String PK | `asset_` 前綴，10 位 hex |
| `asset_uri` | String UNIQUE | 內部儲存協議 URI，格式 `storage://meta-andromeda/<key>` |
| `storage_backend` | String(50) | `filesystem` 或 `s3_compatible` |
| `storage_key` | String | 相對儲存路徑（或 S3 Key） |
| `asset_type` | String(20) | `image` 或 `video` |
| `source_filename` | String | 原始上傳檔名 |
| `checksum_sha256` | String(128) | SHA-256 校驗值 |
| `upload_status` | String(50) | 預設 `stored` |
| `file_size_bytes` | Integer | 檔案位元組大小 |
| `public_url` | String | 選填，S3 公開 URL |
| `uploaded_by` | String FK → `users.id` | 上傳者 User ID |
| `uploaded_at` | DateTime | 上傳時間戳 |

---

### 3.2 MetaAndromedaObservedCreative（線上廣告觀察紀錄）

**資料表名**：`meta_andromeda_observed_creatives`

記錄從 Facebook Ads 抓取的廣告實測結果，為 Post-launch 觀測層的主要來源。

| 欄位 | 類型 | 說明 |
|---|---|---|
| `id` | String PK | `ma_obs_` 前綴，12 位 hex |
| `asset_id` | String FK | 關聯素材（可為 Null） |
| `asset_uri` | String | 內部儲存協議 URI |
| `source_platform` | String(50) | 來源平台，目前為 `facebook_ads` |
| `source_account_id` | String(120) | 廣告帳戶 ID |
| `campaign_id` | String(120) | 廣告活動 ID |
| `adset_id` | String(120) | 廣告組 ID |
| `ad_id` | String(120) | 廣告 ID（必填） |
| `ad_name` | String | 廣告名稱 |
| `objective` | String(50) | 行銷目標（如 `purchase`、`lead`） |
| `placement_family` | String(50) | 版位系列（如 `feed`、`stories`） |
| `market` | String(20) | 目標市場（如 `TW`） |
| `primary_text` | Text | 廣告主要文字 |
| `headline` | Text | 廣告標題 |
| `cta` | String(100) | 行動呼籲按鈕 |
| `media_url` | String | 素材媒體 URL |
| `media_type` | String(20) | `image` 或 `video` |
| `performance_snapshot` | JSON | 實測成效快照（Spend, ROAS, CTR 等） |
| `observation_window_kind` | String(50) | 觀察時間窗口類型 |
| `observation_window_start/end` | String(40) | 觀察時間範圍 |
| `source_fetched_at` | String(40) | 從 Facebook API 抓取的時間戳 |
| `lineage` | JSON | 資料來源溯源記錄 |
| `created_at` | DateTime | 建立時間 |

---

### 3.3 MetaAndromedaScoreEvent（評分事件）

**資料表名**：`meta_andromeda_score_events`

系統最核心的資料表，每一次評分請求對應一筆記錄。

| 欄位 | 類型 | 說明 |
|---|---|---|
| `id` | String PK | `ma_evt_` 前綴，12 位 hex |
| `status` | String(50) | `queued` / `processing` / `completed` / `failed` |
| `runtime_job_id` | String(120) | 調度器任務 ID |
| `created_at` / `queued_at` | DateTime | 建立與排隊時間 |
| `started_at` / `completed_at` / `failed_at` | DateTime | 執行各階段時間戳 |
| `updated_at` | DateTime | 最後更新時間 |
| `asset_uri` | String | 素材內部 URI |
| `asset_type` | String(20) | `image` 或 `video` |
| `asset_id` | String FK | 關聯素材 |
| `preview_url` | String | 預覽 URL |
| `request_mode` | String(50) | `auto` / `diagnostic_only` |
| `objective` | String(50) | 行銷目標 |
| `placement_family` | String(50) | 版位系列 |
| `market` | String(20) | 目標市場 |
| `prediction_mode` | String(50) | `diagnostic_plus_roas` / `diagnostic_only` |
| `overall_score` | Integer | 0-100 整體評分 |
| `roas_band` | String(50) | `high` / `mid` / `low` |
| `model_version` | String(100) | 使用的模型版本 |
| `reviewed` | Boolean | 是否已人工審核 |
| `feedback_count` | Integer | 回饋次數 |
| `latest_feedback_decision` | String(50) | 最新回饋決定 |
| `feature_manifest_id` | String(100) | 特徵清單版本 ID |
| `error_message` | Text | 失敗原因 |
| `attempt_count` | Integer | 嘗試次數 |
| `diagnostic_breakdown` | JSON | 各維度評估結果 |
| `roas_prediction` | JSON | ROAS 預測詳細資訊（包含 confidence） |
| `risk_tags` | JSON | 風險標籤清單 |
| `top_positive_drivers` | JSON | 前三正向驅動因素 |
| `top_negative_drivers` | JSON | 前三負向驅動因素 |
| `explanations` | JSON | 完整解釋摘要 |
| `lineage` | JSON | 模型版本與提供者溯源 |
| `request_context` | JSON | 請求上下文（Headline, CTA, 等） |

---

### 3.4 MetaAndromedaFeedbackEvent（人工回饋事件）

**資料表名**：`meta_andromeda_feedback_events`

| 欄位 | 類型 | 說明 |
|---|---|---|
| `id` | String PK | `fb_evt_` 前綴 |
| `score_event_id` | String FK | 關聯評分事件 |
| `reviewer_id` | String | 審核者 ID（Email 或 User ID） |
| `decision` | String(50) | 回饋決定（`approve` / `reject` 等） |
| `reason_codes` | JSON | 原因代碼列表 |
| `comment` | Text | 自由文字說明 |
| `created_at` | DateTime | 建立時間 |

---

### 3.5 MetaAndromedaReleaseRecord（版本發佈記錄）

**資料表名**：`meta_andromeda_release_records`

| 欄位 | 類型 | 說明 |
|---|---|---|
| `id` | String PK | UUID |
| `record_kind` | String(50) | `current_production` / `previous_production` / `candidate` |
| `model_version` | String(100) | 模型版本標識符 |
| `release_status` | String(50) | 發佈狀態 |
| `approved_by` | String | 審核者 |
| `pairwise_ranking_accuracy` | Float | 配對排名準確率 |
| `mean_band_error` | Float | 平均帶誤差 |
| `promotion_gate_summary` | JSON | 發佈門檻摘要 |

---

### 3.6 MetaAndromedaReleaseEvent（版本操作事件日誌）

**資料表名**：`meta_andromeda_release_events`

記錄 `approve` / `reject` / `rollback` 等版本操作的稽核軌跡。

---

### 3.7 MetaAndromedaWorkerEvent（Worker 事件日誌）

**資料表名**：`meta_andromeda_worker_events`

追蹤每個評分任務從派送到完成的完整 Worker 生命週期，支援觀測性需求。

| 關鍵欄位 | 說明 |
|---|---|
| `event_type` | 事件類型，如 `dispatch_requested`、`processing_started`、`completed`、`failed` |
| `queue_host` | 調度主機標識，如 `apscheduler`、`redis_stream` |
| `attempt_count` | 當時嘗試次數 |
| `event_payload` | 完整事件 JSON 載荷 |

---

### 3.8 MetaAndromedaDeadLetter（死信佇列）

**資料表名**：`meta_andromeda_dead_letters`

超過最大重試次數後進入死信佇列，供人工排查。

---

### 3.9 MetaAndromedaDriftReport（漂移報告）

**資料表名**：`meta_andromeda_drift_reports`

| 欄位 | 說明 |
|---|---|
| `drift_status` | `drifted` / `stable` / `info` |
| `severity` | 嚴重程度：`info` / `warning` / `critical` |
| `window_kind` | 分析時間窗口類型 |
| `report_payload` | 完整漂移分析 JSON |

---

### 3.10 MetaAndromedaCalibrationDataset（校準資料集）

**資料表名**：`meta_andromeda_calibration_datasets`

儲存每次校準作業的元資訊，如時間窗口、標籤策略版本、同步數量等。

---

### 3.11 MetaAndromedaCalibrationItem（校準資料項目）

**資料表名**：`meta_andromeda_calibration_items`

每個校準項目連結「觀察紀錄」與「評分事件」，記錄預測帶（`prediction_band`）與實測帶（`observed_band`）的誤差。

---

## 4. API 端點參考

**Base Path**：`/api/meta-andromeda`  
**路由定義**：`backend/modules/meta_andromeda/router.py`

### 4.1 基礎端點

| Method | 路徑 | 權限 | 說明 |
|---|---|---|---|
| GET | `/ping` | `meta_andromeda` 模組 | 健康檢查 |
| GET | `/overview` | `meta_andromeda` 模組 | 模組總覽（功能狀態、整合進度） |
| GET | `/runtime/health` | `meta_andromeda` 模組 | 執行期健康狀態（DB、佇列、儲存、模型登錄） |

### 4.2 素材管理

| Method | 路徑 | 權限 | 說明 |
|---|---|---|---|
| POST | `/assets:upload` | `meta_andromeda_operate` | 上傳素材（圖片/影片），自動壓縮圖片 |
| GET | `/assets/preview?uri=` | 開放（路由層） | 代理預覽/下載素材，防路徑穿越攻擊 |

**素材上傳限制：**
- 圖片：`image/png`、`image/jpeg`、`image/webp`（副檔名 `.png`/`.jpg`/`.jpeg`/`.webp`）
- 影片：`video/mp4`、`video/quicktime`（副檔名 `.mp4`/`.mov`）
- 大小：由 `META_ANDROMEDA_UPLOAD_MAX_BYTES` 設定
- 圖片自動壓縮：超過 400KB 的圖片自動縮小至最長邊 1200px，JPEG/WebP 以 Quality 85 儲存

### 4.3 評分工作台

| Method | 路徑 | 權限 | 說明 |
|---|---|---|---|
| POST | `/scores` | `meta_andromeda_operate` | 建立評分事件並排入佇列 |
| GET | `/scores/{score_event_id}` | `meta_andromeda` 模組 | 取得單一評分事件詳情 |
| GET | `/scores/{score_event_id}/feedback` | `meta_andromeda` 模組 | 取得評分回饋清單 |
| POST | `/scores/{score_event_id}/feedback` | `meta_andromeda_feedback` | 提交評分回饋 |

**評分請求格式（`ScoreSubmitRequest`）：**
```json
{
  "asset_uri": "storage://meta-andromeda/...",
  "asset_type": "image",
  "asset_id": "asset_abc123",
  "request_mode": "auto",
  "objective": "purchase",
  "placement_family": "feed",
  "market": "TW",
  "headline": "廣告標題",
  "primary_text": "廣告主要文字",
  "cta": "立即購買"
}
```

### 4.4 審核佇列

| Method | 路徑 | 說明 |
|---|---|---|
| GET | `/review-queue` | 列出評分事件（支援 `status`、`reviewed`、`limit` 篩選） |
| GET | `/review-queue/{score_event_id}` | 取得單一評分事件詳情 |

### 4.5 監控

| Method | 路徑 | 說明 |
|---|---|---|
| GET | `/monitoring/summary` | 監控總覽（含 Worker 主機資訊） |
| GET | `/monitoring/score-events/{score_event_id}/timeline` | 評分事件完整 Worker 時間軸 |

### 4.6 版本管理（Release Console）

| Method | 路徑 | 說明 |
|---|---|---|
| GET | `/release/overview` | 取得版本總覽（production / candidate 清單） |
| POST | `/release/approve` | 核准候選版本 |
| POST | `/release/reject` | 拒絕候選版本 |
| POST | `/release/rollback` | 回滾至前一版本 |

### 4.7 FB Ads 觀察匯入

| Method | 路徑 | 說明 |
|---|---|---|
| POST | `/evaluations/import/facebook-ads` | 觸發 FB 廣告觀察匯入（非同步背景任務） |
| GET | `/evaluations/import/facebook-ads/{observed_creative_id}/status` | 查詢匯入進度 |

**額外權限要求**：同時需要 `fb_ads` 模組與 `fb_ads:analytics:view` 權限。

### 4.8 校準與漂移

| Method | 路徑 | 說明 |
|---|---|---|
| POST | `/calibration/sync` | 將觀察紀錄打包為校準資料集 |
| POST | `/drift:trigger` | 手動觸發漂移診斷報告 |

### 4.9 External Worker 回調

| Method | 路徑 | 說明 |
|---|---|---|
| POST | `/worker/score-events/{score_event_id}/callbacks` | 外部 Worker 回調端點（支援 HMAC 簽名驗證） |

**支援的 `event_type`**：`accepted` / `processing` / `completed` / `failed`

### 4.10 維護作業

| Method | 路徑 | 說明 |
|---|---|---|
| POST | `/maintenance/cleanup-stale-score-events` | 清理停滯的評分事件（支援手動/自動觸發） |

---

## 5. 評分引擎

**路徑**：`backend/modules/meta_andromeda/runtime.py`

### 5.1 評分流程

```
用戶送出評分請求
  → MetaAndromedaRuntimeAdapter.build_score_submission()  建立評分 payload
  → MetaAndromedaService.enqueue_score_event()           排入佇列
  → 佇列調度執行
  → MetaAndromedaRuntimeAdapter.generate_score_result()  選擇評分提供者並執行
  → 結果寫回 score_event（repository.mark_score_completed）
```

### 5.2 評分提供者（Scoring Providers）

#### AI 提供者：OpenRouterScoringProvider

- 透過 `OpenRouterClient` 呼叫 OpenAI-compatible API（當前模型：`nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`）
- 使用多模態輸入：文字 Prompt + 圖片 URL（Base64 Data URI 或公開 URL）
- System Prompt 強調：保守評分，繁體中文輸出
- 回傳結構需包含：`overall_score`（0-100）、`roas_band`（high/mid/low）、`top_positive_drivers`、`top_negative_drivers`、`risk_tags`、`diagnostic_breakdown`、`summary`
- **Rate Limit 處理**：偵測到 HTTP 429 時，自動以指數退避（2s, 4s, 8s）最多重試 3 次
- **Prompt 動態載入**：System Prompt 與 User Prompt Template 從 DB 的 `meta_andromeda_scoring_profiles` 表讀取，由 `_load_scoring_profile()` 快取後注入。`request_context`（headline / primary_text / cta）透過 `str.format_map()` 格式化至 template 中

#### 啟發式提供者：HeuristicScoringProvider

- 無需 AI API，純規則計算
- 基礎分：圖片 56 分、影片 52 分
- 加分項：有 Headline (+8)、有 Primary Text (+8)、有 CTA (+10)、purchase 目標 (+3)、適合版位 (+4)
- 分數範圍限制：24 ~ 88
- 適用情境：OpenRouter API 不可用、本地開發、Fallback

### 5.3 評分模式

| 模式 | 說明 |
|---|---|
| `auto` | 自動選擇 AI 或 Heuristic（依設定和 API 金鑰可用性） |
| `diagnostic_only` | 僅輸出診斷評分，不預測 ROAS 帶 |

### 5.4 信心分數計算（Confidence Score）

信心分數（0.18 ~ 0.92）基於：
- 信號完整度（Headline / Primary Text / CTA / 圖片 / objective / placement / market 共 7 項）
- 評分模式（AI：基礎 0.58；Heuristic：基礎 0.42）
- 是否使用多模態圖片輸入（+0.06）
- Fallback 啟用時（-0.12 懲罰）

### 5.5 API 金鑰優先級

```
1. 資料庫中素材上傳者的個人 OpenRouter API Key
2. 環境變數 OPENROUTER_API_KEY
3. 環境變數 ZEABUR_AI_HUB_API_KEY（備用）
4. 回退至 Heuristic
```

> **實作注意**：`generate_score_result` 中取得金鑰時必須使用 `settings.OPENROUTER_API_KEY`（property，自動合併 `OPENROUTER_API_KEY` 與 `ZEABUR_AI_HUB_API_KEY` 兩個環境變數），不可直接呼叫 `os.getenv("OPENROUTER_API_KEY")`，否則會漏掉 `ZEABUR_AI_HUB_API_KEY` 備用金鑰。

### 5.6 已知陷阱與除錯備忘

以下問題均曾在生產環境中導致 AI 評分靜默 fallback 至啟發式備用，且從 OpenRouter 後台觀察不到任何 API 請求（錯誤在送出請求前就已發生）：

#### 陷阱 A：`few_shot_examples` 型別錯誤（AttributeError 在 API 呼叫前觸發）

**症狀**：日誌出現 `'str' object has no attribute 'get'`，OpenRouter 後台無任何請求紀錄。

**原因**：Alembic migration 若使用 `json.dumps([])` 寫入 JSON 欄位，SQLAlchemy 讀回時可能返回字串 `'[]'` 而非 list。`'[]'` 為 truthy，進入 `_format_few_shot_block()` 後對字元迭代，`'['.get(...)` 拋出 AttributeError。

**修正**：
- migration 中 `few_shot_examples` 直接寫 `[]`（Python list），不用 `json.dumps([])`
- `_load_scoring_profile` 讀取後強制型別轉換：若為 str 則 `json.loads`，若非 list 則設為 `[]`
- `score()` 中加防護：`if few_shot_examples and isinstance(few_shot_examples, list):`

#### 陷阱 B：`request_context` 未傳入 score payload（Prompt 欄位空白）

**症狀**：AI 正常呼叫，但 Prompt 中 Headline、Primary text、CTA 均為空字串，評分依據不完整。

**原因**：`repository.py` 的 `_score_to_detail()` 曾缺少 `"request_context"` 欄位，導致 `score_payload` 裡沒有廣告文案資訊。

**修正**：`_score_to_detail` 加入 `"request_context": _safe_json_dict(score.request_context)`；`_safe_json_dict` 需能處理 DB JSON 欄位返回字串的情形。

#### 陷阱 C：推理模型 `max_tokens` 不足導致 JSON 截斷

**症狀**：日誌出現 `AI response JSON structure is broken. Extracted: { "overall_score": 85, "roas_band": "mid", "top_positive_drivers":`（JSON 在生成途中被切斷）。

**原因**：`nvidia/nemotron-*-reasoning` 等推理模型的 chain-of-thought 思考過程與實際輸出共享同一個 `max_tokens` 預算。prompt 包含真實廣告文案時，思考鏈變長，剩餘給 JSON 輸出的 token 不足。2048 在 prompt 有實際內容時不夠用。

**修正**：`runtime.py` 中 `generate_content` 呼叫的 `max_tokens` 參數設為 `4096`。

---

## 6. 模型登錄中心（Model Registry）

**路徑**：`backend/modules/meta_andromeda/model_registry.py`

### 6.1 已登錄版本

| 版本 ID | 提供者 | 模型 | 發佈頻道 |
|---|---|---|---|
| `prod_v2026_05_28` | openrouter | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | production |
| `prod_v2026_05_12` | heuristic | `heuristic://creative_scoring_v0` | superseded |
| `cand_v2026_06_05_a` | openrouter | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | candidate |
| `cand_v2026_06_04_b` | openrouter | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | candidate |
| `candidate_v0` | heuristic | `heuristic://creative_scoring_v0` | local_fallback |

### 6.2 版本解析優先級

```
環境變數 META_ANDROMEDA_SCORING_PROVIDER
  → "heuristic"：強制使用 candidate_v0 heuristic
  → "openrouter" + META_ANDROMEDA_SCORING_MODEL：使用指定模型覆蓋
  → "auto"：依登錄表中版本設定使用

META_ANDROMEDA_SCORING_MODEL_VERSION
  → 指定使用的登錄版本（預設 cand_v2026_06_05_a）
```

---

## 7. 佇列主機（Queue Host）

**路徑**：`backend/modules/meta_andromeda/queue_host.py`

### 7.1 支援的佇列模式

| 模式 | 環境變數值 | 說明 |
|---|---|---|
| **APScheduler** | `apscheduler` | 使用內建 APScheduler 調度評分任務（開發/小規模部署推薦） |
| **Redis Stream** | `redis_stream` | 寫入 Redis Stream，支援 Consumer Group 消費與失敗重認（xautoclaim） |
| **External Webhook** | `external_webhook` | POST 派送至外部 Worker，使用 HMAC 簽名，外部 Worker 回調結果 |
| **Local Async** | `local_async` | `asyncio.create_task()` 直接在主行程執行（測試用） |
| **Database Queue** | `database_queue` | 僅寫入資料庫記錄，由外部 Polling 機制觸發 |
| **Auto** | `auto` | 依序偵測 APScheduler → Local Async → Unavailable |

### 7.2 Redis Stream 設定

| 環境變數 | 說明 |
|---|---|
| `META_ANDROMEDA_REDIS_STREAM_KEY` | Stream 名稱 |
| `META_ANDROMEDA_REDIS_STREAM_GROUP` | Consumer Group 名稱 |
| `META_ANDROMEDA_REDIS_STREAM_CONSUMER` | 消費者名稱 |
| `META_ANDROMEDA_REDIS_STREAM_BATCH_SIZE` | 每批消費量 |
| `META_ANDROMEDA_REDIS_STREAM_RECLAIM_IDLE_MS` | 失敗訊息重認 idle 門檻（毫秒） |

### 7.3 External Webhook 設定

| 環境變數 | 說明 |
|---|---|
| `META_ANDROMEDA_EXTERNAL_QUEUE_ENDPOINT` | 外部 Worker 接收端 URL |
| `META_ANDROMEDA_EXTERNAL_QUEUE_TOKEN` | Bearer Token（Authorization Header） |
| `META_ANDROMEDA_EXTERNAL_QUEUE_SIGNING_SECRET` | HMAC 簽名密鑰（X-Meta-Andromeda-Signature） |
| `META_ANDROMEDA_EXTERNAL_WORKER_SHARED_SECRET` | 回調驗證密鑰 |
| `META_ANDROMEDA_EXTERNAL_WORKER_TOKEN` | 回調 Bearer Token |

---

## 8. 儲存後端（Storage）

**路徑**：`backend/modules/meta_andromeda/storage.py`

### 8.1 Filesystem（本機檔案系統）

- 設定：`META_ANDROMEDA_STORAGE_BACKEND=filesystem`
- 儲存根目錄：`META_ANDROMEDA_STORAGE_ROOT`
- 儲存路徑格式：`<ROOT>/<PREFIX>/uploads/<YYYY>/<MM>/<DD>/<asset_id>/<filename>`
- 素材 URI 格式：`storage://meta-andromeda/<storage_key>`

### 8.2 S3-Compatible（物件儲存）

- 設定：`META_ANDROMEDA_STORAGE_BACKEND=s3_compatible`
- 需要套件：`boto3`
- 相關設定：`META_ANDROMEDA_STORAGE_S3_BUCKET`、`META_ANDROMEDA_STORAGE_S3_REGION`、`META_ANDROMEDA_STORAGE_S3_ACCESS_KEY_ID`、`META_ANDROMEDA_STORAGE_S3_SECRET_ACCESS_KEY`
- 可選 endpoint：`META_ANDROMEDA_STORAGE_S3_ENDPOINT_URL`（支援 MinIO、Cloudflare R2 等相容服務）

### 8.3 素材預覽安全機制

- 路徑穿越防護：使用 `Path.resolve().relative_to()` 驗證
- 僅允許 HTTP（非 HTTPS）以外的 media URL Host（`META_ANDROMEDA_ALLOWED_MEDIA_HOSTS` 白名單）

---

## 9. Facebook Ads 觀察匯入流程

```
POST /evaluations/import/facebook-ads
  → 立即返回 202 Accepted（含 observed_creative_id）
  → 背景任務執行：
      1. 呼叫 Facebook Graph API 取得廣告成效與素材資訊
      2. 下載素材快照（若有 media_url 且為允許的 Host）
      3. 壓縮並儲存素材至 Storage Backend
      4. 建立 ObservedCreative 記錄
      5. 若素材成功儲存，自動建立評分事件並排入佇列（auto 模式）

GET /evaluations/import/facebook-ads/{observed_creative_id}/status
  → 合併 DB 記錄 + 記憶體內狀態（_observation_import_statuses）返回進度
```

**`observed_creative_id` 格式**：`ma_obs_<YYYYMMDD>_<ad_id後6位>_<window_kind>`

---

## 10. 維護機制（Maintenance）

**路徑**：`MetaAndromedaService.cleanup_stale_score_events()`

### 10.1 停滯評分事件清理

自動或手動清理長時間停留在 `queued` 或 `processing` 狀態的評分事件：

- 超時門檻：`META_ANDROMEDA_STALE_PROCESSING_MINUTES`（預設）或請求傳入值
- 清理行動：將狀態改為 `failed`，記錄 `maintenance_cancelled` Worker 事件
- 選項：`purge_worker_events`（刪除相關 Worker Events）、`purge_dead_letters`（刪除死信記錄）
- 同步移除 APScheduler 中的對應排程任務

### 10.2 自動排程清理

系統啟動時（`core/scheduler.py`）設有定期自動清理任務，定期喚醒並執行停滯評分事件的清理。

---

## 11. 前端頁面

**目錄**：`frontend/src/pages/`

| 頁面檔案 | 功能說明 |
|---|---|
| `MetaAndromeda.jsx` | 模組總覽頁，顯示整合狀態、功能能力列表與說明備註 |
| `MetaAndromedaScoreLab.jsx` | 評分工作台，上傳素材、設定參數、提交評分、查看結果 |
| `MetaAndromedaReviewQueue.jsx` | 審核佇列，列出評分事件，支援篩選與人工回饋 |
| `MetaAndromedaMonitoring.jsx` | 監控總覽，顯示評分任務狀態統計與 Worker 時間軸 |
| `MetaAndromedaRelease.jsx` | 版本控台，管理模型版本的核准/拒絕/回滾 |

**前端服務層**：`frontend/src/services/`

| 服務檔案 | 對應後端 |
|---|---|
| `metaAndromedaService.js` | `/ping`、`/overview` |
| `metaAndromedaReviewQueueService.js` | `/review-queue`、`/scores`、`/scores/*/feedback` |
| `metaAndromedaMonitoringService.js` | `/monitoring/*` |
| `metaAndromedaReleaseService.js` | `/release/*` |
| `metaAndromedaWorkflowService.js` | `/assets:upload`、`/evaluations/import/*`、`/calibration/*`、`/drift:trigger`、`/maintenance/*` |

---

## 12. 權限系統

**路徑**：`backend/modules/meta_andromeda/dependencies.py`

Meta Andromeda 採用「模組層級」統一存取控制，所有操作統一要求 `meta_andromeda` 模組存取權。

| 依賴函數 | 實際要求 |
|---|---|
| `require_meta_andromeda_module` | `meta_andromeda` 模組 |
| `require_meta_andromeda_operate` | 同上（模組等級） |
| `require_meta_andromeda_feedback` | 同上（模組等級） |
| `require_meta_andromeda_release` | 同上（模組等級） |
| `require_fb_ads_module` | `fb_ads` 模組（FB Ads 匯入時額外要求） |
| `require_fb_ads_analytics_view` | `fb_ads:analytics:view` 權限 |

---

## 13. 評分事件狀態機

```
       建立
        │
        ▼
    [queued]  ←─────────────────── 重試排隊
        │
        ▼
  [processing] ─── 超時/例外 ──→ [queued] 重試 (attempt_count < MAX)
        │                            │
        │                            └── 超過最大重試 ──→ [failed] → 死信佇列
        ▼
   [completed]
```

**相關設定**：
- `META_ANDROMEDA_SCORE_MAX_CONCURRENCY`：同時處理的最大評分任務數（Semaphore）
- `META_ANDROMEDA_SCORE_MAX_ATTEMPTS`：最大重試次數
- `META_ANDROMEDA_SCORE_TIMEOUT_SECONDS`：單次評分超時（秒）
- `META_ANDROMEDA_SCORE_RETRY_DELAY_SECONDS`：重試間隔（秒）

---

## 14. 學習閉環與漂移診斷

### 14.1 關聯一：漂移鎖定機制

- 定期比對「預估評分分帶」與「實測 ROAS 分帶」
- 若準確率低於設定門檻（`accuracy_gate`），漂移狀態標記為 `drifted`
- 漂移發生時，Release Console 的「發佈按鈕」自動鎖定，防止擴大誤差

### 14.2 關聯二：校準資料集（Calibration Dataset）

- `POST /calibration/sync`：將觀察紀錄與評分事件對齊，產生帶有 `prediction_band` vs `observed_band` 誤差的校準項目
- 校準項目可匯出作為 LLM Fine-tuning 資料集

### 14.3 關聯三：評估門檻動態調整

- 觀察紀錄中的實測 ROAS/CTR 數據提供市場基準線
- 未來可動態調整 Heuristic 計算參數，使評分更貼近當前市場趨勢

---

## 15. 關鍵環境變數摘要

| 環境變數 | 預設值 | 說明 |
|---|---|---|
| `META_ANDROMEDA_STORAGE_BACKEND` | `filesystem` | 儲存後端類型 |
| `META_ANDROMEDA_STORAGE_ROOT` | — | Filesystem 儲存根目錄 |
| `META_ANDROMEDA_STORAGE_KEY_PREFIX` | `""` | 儲存 Key 前綴 |
| `META_ANDROMEDA_SCORING_PROVIDER` | `auto` | 評分提供者：`auto` / `openrouter` / `heuristic` |
| `META_ANDROMEDA_SCORING_MODEL_VERSION` | `cand_v2026_06_05_a` | 模型登錄版本 |
| `META_ANDROMEDA_SCORING_MODEL` | — | 覆蓋 Provider Model 名稱 |
| `META_ANDROMEDA_SCORING_ALLOW_FALLBACK` | `true` | AI 失敗時是否 Fallback 至 Heuristic |
| `META_ANDROMEDA_QUEUE_HOST` | `auto` | 佇列主機模式 |
| `META_ANDROMEDA_SCORE_MAX_CONCURRENCY` | `3` | 最大並發評分數 |
| `META_ANDROMEDA_SCORE_MAX_ATTEMPTS` | `3` | 最大重試次數 |
| `META_ANDROMEDA_SCORE_TIMEOUT_SECONDS` | `90` | 評分超時秒數 |
| `META_ANDROMEDA_STALE_PROCESSING_MINUTES` | `30` | 停滯任務超時分鐘數 |
| `META_ANDROMEDA_UPLOAD_MAX_BYTES` | `20971520` | 素材上傳大小上限（20MB） |
| `META_ANDROMEDA_OBSERVED_DOWNLOAD_MAX_BYTES` | `15728640` | 觀察素材下載上限（15MB） |
| `OPENROUTER_API_KEY` | — | OpenRouter 全局 API 金鑰 |

---

## 16. 相關文件索引

| 文件 | 說明 |
|---|---|
| `docs/meta_andromeda_architecture_guide.md` | 系統架構與閉環流程圖說明 |
| `docs/10_Meta_Andromeda_模組說明.md` | 模組定位與能力邊界 |
| `docs/12_FB_Ads_導入_Meta_Andromeda_整合規格.md` | FB Ads 匯入整合規格 |
| `docs/15_Meta_Andromeda_儲存機制與持久化掛載實作計劃.md` | 儲存機制設計 |
| `docs/17_Meta_Andromeda_Phase6_預測與真實績效匹配與漂移診斷設計方案.md` | 漂移診斷設計方案 |
| `docs/25_Meta_Andromeda_AI評分準確性與Prompt優化方案.md` | AI Prompt 優化方案 |
| `docs/zeabur_deployment_guide.md` | Zeabur 部署指南（含 Meta Andromeda 環境變數） |
