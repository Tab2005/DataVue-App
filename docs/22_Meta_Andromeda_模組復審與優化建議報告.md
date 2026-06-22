# 22 Meta Andromeda 模組復審與優化建議報告

## 基本資訊

- 審查日期：2026-06-18
- 審查範圍：`backend/modules/meta_andromeda`、Meta Andromeda ORM / Alembic migration、scheduler queue flow、frontend Meta Andromeda pages/services、既有模組文件與測試
- 審查目標：確認 `Meta Andromeda` 目前功能完整度、找出需要優化的實作風險，並提出模型與資料閉環調整方向
- 驗證狀態：已嘗試執行 `python -m pytest tests/test_meta_andromeda_module.py -q`，但目前預設 Python 環境缺少 `pytest`，測試未能執行

## 總結判定

`Meta Andromeda` 已具備完整的模組骨架：score lab、review queue、monitoring、release console、asset storage、queue host、external worker callback、FB Ads observed import、drift report 與 calibration sync 都有對應程式碼。

但目前仍不應視為 production-ready。主要原因不是 API 是否存在，而是資料治理與模型閉環仍有高風險實作：

| 優先級 | 結論 |
| --- | --- |
| P0 | `MetaAndromedaObservedCreative` ORM 已存在，但 Alembic migration 未建立 `meta_andromeda_observed_creatives` 表，正式環境 schema 可能漂移。 |
| P0 | drift report 在缺少 prediction 時會隨機建立並持久化 mock `ScoreEvent`，會污染模型評估與正式資料。 |
| P0 | 多個讀取 API 會自動寫入 seed/demo data，正式資料庫可能被 demo score、feedback、release record 污染。 |
| P1 | 前端仍用已廢棄的 `meta_andromeda:operate` / `meta_andromeda:release` feature permission 鎖住操作，與 module-only 權限策略不一致。 |
| P1 | queue / worker 狀態轉換缺少原子 claim 與 callback 冪等性，重複 job 或延遲 callback 可能覆蓋終態。 |
| P1 | scoring runtime 未讀取實際圖片/影片內容，模型輸入不足，難以支撐「創意素材預估」定位。 |

## 目前功能盤點

| 模組能力 | 已有實作 | 目前評估 |
| --- | --- | --- |
| Pre-launch prediction | `/assets:upload`、`/scores`、queued scoring、Score Lab | 可用，但模型主要看文字與 asset type，未分析素材內容。 |
| Review workflow | `/review-queue`、feedback timeline、Review Queue page | 基本可用。 |
| Queue / worker | APScheduler、database_queue、external_webhook、redis_stream、retry、dead-letter | 功能面完整，但狀態 claim 與冪等性不足。 |
| Runtime health | `/runtime/health`、`/health` Meta Andromeda checks | 可用，但部分 readiness 只檢查設定，不驗證端到端。 |
| Observation import | `/evaluations/import/facebook-ads`、`MetaAndromedaObservedCreative` model | 程式碼存在，但 migration 缺口與 media download 風險需先補。 |
| Learning / drift | `/drift:trigger`、`/calibration/sync` | 現階段仍偏示範，會用 mock/random 補資料，不可作正式模型決策依據。 |
| Release console | release overview / approve / reject / rollback | UI 與 API 可用，但 release record 是 seed/static 為主，尚未接真實 evaluation dataset。 |

## 主要發現

### P0. ObservedCreative 缺少 Alembic migration

證據：

- ORM model 存在於 `backend/database/models/meta_andromeda.py:30`，table name 為 `meta_andromeda_observed_creatives`。
- `backend/alembic/versions/20260608_meta_andromeda_workflow_tables.py:18` 只建立 assets、score_events、feedback_events、release_records、release_events。
- `backend/alembic/versions/20260611_meta_andromeda_drift_reports.py:18` 只建立 drift_reports。
- 搜尋 migration 未找到 `meta_andromeda_observed_creatives` 建表語句。

影響：

- 在嚴格 Alembic 管理的正式資料庫中，FB Ads observed import、drift report、calibration sync 會因缺表失敗。
- `backend/database/__init__.py:123` 的 production safety check 會在缺表時 emergency `Base.metadata.create_all()`，短期可能掩蓋問題，但會讓 schema 繞過 Alembic 版本控管，造成不同環境 schema 不一致。

建議：

- 新增 Alembic migration，明確建立 `meta_andromeda_observed_creatives`。
- 補上索引：`source_platform`、`source_account_id`、`ad_id`、`asset_uri`、`observation_window_kind`、`campaign_id`、`adset_id`。
- 建議加唯一約束或去重索引：`source_platform + source_account_id + ad_id + observation_window_kind + observation_window_start + observation_window_end`。
- 測試需加入「從 Alembic upgrade 建出的 DB schema」驗證，而不是只依賴 SQLAlchemy `create_all()`。

### P0. Drift report 會隨機建立 mock ScoreEvent 並持久化

證據：

- `backend/modules/meta_andromeda/repository.py:604` 至 `640`：當 observed data 大於等於 5 筆且找不到對應 prediction 時，程式會用 `random` 建立 `ma_evt_mock_*` completed score event，並 `db.commit()`。

影響：

- drift accuracy / MAE 會混入隨機模擬資料，結果不可重現。
- mock score event 會寫入正式表，污染 review queue、monitoring、release evidence。
- 模型 drift 本應暴露「prediction coverage 不足」，現在反而被假資料掩蓋。

建議：

- 立即移除正式路徑中的 mock prediction 持久化。
- 若需要 demo 行為，改成 `META_ANDROMEDA_DEMO_MODE=true` 才允許，且只回傳 transient result，不寫入 production tables。
- drift report 應明確輸出 `matched_count`、`unmatched_observed_count`、`coverage_ratio`，coverage 不足時直接標示 `insufficient_prediction_coverage`。

### P0. 讀取 API 會自動 seed demo data

證據：

- `backend/modules/meta_andromeda/repository.py:286` 至 `324`：`ensure_seed_data()` 會在資料表為空時寫入 demo score、feedback、release、drift records。
- `list_review_queue()`、`get_review_queue_detail()`、`get_monitoring_summary()` 等讀取方法會呼叫 `ensure_seed_data()`，例如 `repository.py:417`、`435`、`442`。

影響：

- 第一次讀 API 就可能改寫正式資料庫。
- seed 內含 queued score event，可能被 scheduler 補排並實際處理。
- release history 與 monitoring 會混入 demo record，讓營運人員誤判模型狀態。

建議：

- 移除 runtime read path 中的 `ensure_seed_data()`。
- 改為明確的 dev seed script 或 migration seed，並由環境變數控制，例如 `META_ANDROMEDA_ENABLE_DEMO_SEED=false` 預設關閉。
- production health/read API 不應有資料寫入 side effect。

### P1. 前端權限 gate 與 module-only 策略不一致

證據：

- 後端 `backend/modules/meta_andromeda/dependencies.py:18` 至 `21` 已將 operate / feedback / release alias 指向 module access。
- seed 設定中 `backend/seeds/permission_seeds.py:30` 顯示 `meta_andromeda` feature permission 為空。
- 前端仍用 `usePermission('meta_andromeda:operate')`：`frontend/src/pages/MetaAndromedaMonitoring.jsx:32`。
- 前端仍用 `usePermission('meta_andromeda:release')`：`frontend/src/pages/MetaAndromedaRelease.jsx:21`。
- UI 文案仍提示需要舊 feature permission：`MetaAndromedaMonitoring.jsx:462`、`MetaAndromedaRelease.jsx:414`。

影響：

- 有 `meta_andromeda` module access 的使用者，API 可以操作，但 UI 可能隱藏 Drift / Calibration / Release 按鈕。
- 權限文件、後端、前端出現三方不一致，後續維護容易回歸到錯誤模型。

建議：

- Frontend 操作用 `useModuleAccess('meta_andromeda')` 或直接依 route-level `ProtectedModule` 判定，不再查 `meta_andromeda:*` feature permission。
- 移除 UI 文案中的舊權限名。
- 補前端測試：模擬 module access 為 true、feature permission 為 false 時，Drift / Calibration / Release 操作仍可見。

### P1. Queue / worker 缺少原子 claim 與 callback 冪等性

證據：

- `repository.mark_score_processing()` 在 `backend/modules/meta_andromeda/repository.py:935` 至 `946` 直接讀取 row 後改 status 並遞增 attempt，沒有 `WHERE status='queued'` 類型的原子 claim。
- `repository.mark_score_completed()` 在 `repository.py:948` 至 `972` 會覆寫 score event 狀態，不檢查目前是否仍為 processing。
- `service.handle_external_worker_callback()` 在 `backend/modules/meta_andromeda/service.py:514` 至 `639` 接受 callback 後直接更新狀態，缺少 receipt/callback id 去重與終態保護。
- Redis stream consumer 在 `backend/modules/meta_andromeda/queue_host.py:80` 至 `107` 排入 APScheduler 後立即 ack/delete stream message。

影響：

- 重複排程、worker 重啟、Redis reclaim、外部 worker 延遲 callback 都可能讓同一 score event 被處理多次。
- stale `completed` callback 可能覆蓋已 failed/dead-lettered 的終態。
- attempt_count 可能被重複增加，retry/dead-letter 判定失真。

建議：

- 將 `mark_score_processing` 改成原子 update，例如只允許 `queued` 或可 reclaim 的 `processing` 被 claim。
- 增加 `processing_lease_until` / `claimed_by` / `claim_token` 欄位，worker callback 必須帶 claim token。
- worker event 增加 `receipt_id` 或 `callback_event_id` 唯一約束，重複 callback 回 200 但不重複改狀態。
- `mark_score_completed` / `mark_score_failed` 需拒絕覆寫 terminal 狀態，除非有明確 rollback/reprocess command。
- Redis stream 訊息最好在 score event 完成或 DB claim 成功後再 ack，或至少保留 DB lease-based recovery。

### P1. Scoring runtime 沒有分析實際素材內容

證據：

- OpenRouter prompt 在 `backend/modules/meta_andromeda/runtime.py:68` 至 `84` 只包含 asset type、objective、placement、market、headline、primary text、CTA。
- heuristic scoring 在 `runtime.py:175` 至 `273` 主要依 asset type、文案是否存在、placement 做固定加分。
- `storage.py` 已保存檔案，但 runtime 沒有讀取 image/video bytes、OCR、frame sampling、object/logo/text density 等素材特徵。

影響：

- 模組定位是 creative intelligence，但目前模型無法判斷真正的創意畫面、構圖、產品露出、影片節奏、字幕密度、品牌元素。
- 分數容易反映「表單填得完整」而不是素材品質。
- 與投放後成效做 calibration 時，特徵不足會限制模型可學習性。

建議：

- 加入 multimodal feature extraction：圖片 OCR、產品/人物/品牌/logo 偵測、主色/對比、文字密度、safe area、CTA 可見性。
- 影片需抽樣 key frames，至少取前 1 秒、3 秒、hook frame、end card，並保存 feature manifest。
- 如果暫時只用 LLM，改用支援 image/video input 的 provider 或先建立 vision-feature service，再把 structured features 送入 scoring model。
- 將 confidence 從固定值改為基於資料完整度、provider quality、歷史 calibration error 的校準信心。

### P1. Calibration sync 還不是實際訓練資料集

證據：

- `backend/modules/meta_andromeda/repository.py:1135` 至 `1208` 的 `sync_calibration_dataset()` 只把 `lineage["calibration"]` 寫回 observed creative，沒有建立 dataset table、dataset item table 或 downstream training/evaluation job。
- Release records 仍主要由 seed/static data 驅動，沒有與 calibration dataset 或 holdout evaluation 形成可追溯關係。

影響：

- API 回傳 `queued_for_calibration`，但實際沒有 queue、dataset artifact、模型版本產物。
- release gate 無法證明候選模型真的基於新資料改善。

建議：

- 新增 `meta_andromeda_calibration_datasets`、`meta_andromeda_calibration_items`、`meta_andromeda_model_evaluations`。
- 每次 sync 建立 immutable dataset snapshot，記錄 included/excluded observed IDs、label policy、feature manifest、產生者與時間。
- release candidate 必須引用 evaluation ID，promotion gate 由 evaluation metrics 產生，不再手動 seed。

### P2. Upload / storage 邊界不足

證據：

- `frontend/src/pages/MetaAndromedaScoreLab.jsx:192` 只用 accept 限制副檔名。
- `backend/modules/meta_andromeda/router.py:214` 直接 `await file.read()`，會把整個檔案讀入記憶體。
- `backend/modules/meta_andromeda/storage.py:106` 至 `135` 未檢查檔案大小、MIME sniff、內容類型白名單。

影響：

- 大檔案可能造成 API worker 記憶體壓力。
- 只靠前端 accept 無法防止非圖片/影片內容上傳。
- 若 `public_url` 對外暴露，可能衍生內容安全與濫用風險。

建議：

- 後端加入 max file size，例如 image 10 MB、video 100 MB，並在讀取前後都驗證。
- 使用 streaming upload 到 object storage，避免整檔進記憶體。
- 用 magic bytes / MIME sniff 驗證內容，不只看 extension 或 client-provided content type。
- 若要公開素材，加上 signed URL、短效權限或 CDN private bucket policy。

### P2. FB Ads observed import 的輸入驗證與 media download 邊界不足

證據：

- schema 允許 `observation_window_kind='custom'`，但 `facebook_ads_importer.resolve_observation_window()` 只支援 last_7d、last_30d、lifetime；若 custom 沒帶 since/until，會拋 `ValueError`。
- `MetaAndromedaService._download_observed_asset_snapshot()` 在 `backend/modules/meta_andromeda/service.py:296` 直接 GET `media_url`，沒有 domain allowlist、size cap、content length check。
- importer 只從 `row.get("image_url")` 推出 image，影片素材仍會變成 `unknown`。

影響：

- custom window 缺欄位可能變成 500，而不是清楚的 422 validation error。
- media_url 若來源資料異常，存在 SSRF 與大檔下載風險。
- video creative observation 無法完整保存素材快照。

建議：

- Pydantic schema 對 custom window 加 `since` / `until` 必填驗證，並檢查日期順序。
- media download 加 domain allowlist、`Content-Length` 上限、content type 白名單與 timeout。
- FB Ads importer 補 video thumbnail / video source URL 欄位處理。

### P2. Monitoring 指標與查詢效能仍偏示範

證據：

- `backend/modules/meta_andromeda/repository.py:486` 的 latency metrics 是固定值。
- score event model 只有 `runtime_job_id` index，常用查詢會依 `status`、`created_at`、`roas_band`、`asset_uri` 過濾或排序。

影響：

- monitoring latency 無法反映真實 runtime / queue health。
- 資料量增加後 review queue、summary count、drift matching 會變慢。

建議：

- latency 從 `queued_at`、`started_at`、`completed_at` 計算 avg / p95 / max。
- 補索引：`status + created_at`、`reviewed + created_at`、`asset_uri + status`、`roas_band`。
- 大型 summary count 可用 materialized stats 或週期性聚合表。

### P2. 文件與 API 契約有漂移

證據：

- `docs/10_Meta_Andromeda_模組說明.md` 列出 `/release:approve`、`/release:reject`、`/release:rollback`，但後端實際是 `/release/approve`、`/release/reject`、`/release/rollback`。
- `backend/modules/meta_andromeda/README.md` 描述「有 `GOOGLE_AI_API_KEY` 時走 Gemini」，但 `backend/core/config.py:169` 至 `178` 與 `runtime.py` 實作是 OpenRouter。
- 既有 `docs/21_Meta_Andromeda_模組完整度審計報告.md` 判定 100% production-ready，與本次程式碼審查結果不一致。

影響：

- 新開發者或代理會依過期文件呼叫錯誤路由或設定錯誤 provider。
- 上線判斷可能低估資料治理風險。

建議：

- 更新 `docs/10` 與 README 的 API path、provider 設定、production readiness 狀態。
- `docs/21` 建議標註為歷史快照，並引用本報告作為 2026-06-18 復審結論。

## 模型調整建議

### 1. 輸入特徵升級

目前模型輸入應從「文字欄位為主」升級為「素材特徵 + 文案 + 投放 context」：

| 類別 | 建議特徵 |
| --- | --- |
| Image | OCR 文字密度、產品/人物/logo 偵測、主體位置、色彩對比、CTA 可見性、safe area、品牌一致性。 |
| Video | 前 1 秒 hook frame、3 秒 retention cue、字幕密度、節奏切換、end card、產品露出時間。 |
| Copy | headline、primary text、CTA、語氣、優惠強度、localization、違規風險。 |
| Context | objective、placement、market、受眾、歷史 account baseline、campaign type。 |
| Outcome | spend、impressions、clicks、purchase_value、ROAS、CPA、CTR、CVR、learning phase。 |

### 2. 預測目標重新定義

目前固定用 ROAS band 門檻 `low < 1.5`、`mid < 3.5`、`high >= 3.5`。建議改為分層 label policy：

- 依 objective 區分目標：purchase 看 ROAS / CPA，lead 看 CPL / CVR，traffic 看 CTR / CPC。
- 依 market / account baseline 做相對分位數，例如 top 25% / middle 50% / bottom 25%。
- 保存 label policy version，避免不同時期的 drift report 使用不同標準卻不可追溯。

### 3. 分數與信心校準

- 將 `overall_score` 與 `roas_band` 拆開治理，避免單一分數掩蓋 label uncertainty。
- confidence 不應固定 0.72 / 0.61，應基於資料完整度、模型版本、相似樣本數、historical calibration error。
- 加入 ECE、Brier score、coverage、confusion matrix、per-segment MAE。

### 4. Fallback 策略調整

目前 provider 失敗會回 heuristic 並標記 `provider_fallback`。建議：

- production scoring 若走 fallback，預設狀態應為 `completed_with_fallback` 或 `needs_review`，不要與正常 AI score 混為同一類 completed。
- release / drift evaluation 應可排除 fallback scoring，或獨立評估 fallback cohort。
- fallback 分數不要進入 model promotion metrics，除非明確標記並分組。

### 5. Release gate 由真實 evaluation 驅動

- 每個 candidate model version 必須有 evaluation artifact。
- promotion gate 應來自 holdout set、recent observed set、per-market / per-objective segment。
- release action 應保存：dataset_id、evaluation_id、metrics snapshot、approver、rollback plan。

## 建議修復路線

| 優先級 | 建議工作 | 驗收標準 |
| --- | --- | --- |
| P0 | 補 `meta_andromeda_observed_creatives` Alembic migration | 全新 DB 執行 `alembic upgrade head` 後存在 observed table 與索引。 |
| P0 | 移除 read path seed 與 drift mock score 持久化 | 所有 GET/read API 無寫入 side effect；drift 不再建立 `ma_evt_mock_*`。 |
| P1 | 前端改成 module-only 權限 gate | 只有 `meta_andromeda` module access 時，Monitoring / Release 操作按鈕可見。 |
| P1 | worker claim / callback 冪等化 | 重複 job、重複 callback、stale callback 不會覆蓋 terminal status。 |
| P1 | 模型輸出 schema 驗證 | provider 回傳不合法 roas_band、overall_score、risk_tags 時能被拒絕或降級處理。 |
| P2 | 上傳與 media download 安全邊界 | 大檔、錯誤 MIME、非允許來源 URL 被拒絕且回 4xx。 |
| P2 | 真實 monitoring metrics 與索引 | latency 從 timestamps 計算，review queue / summary 在大量資料下可接受。 |
| P2 | calibration dataset 實體化 | 每次 sync 建立 dataset 與 items，release candidate 可追溯到 evaluation。 |
| P3 | 更新文件與舊審計報告狀態 | README、docs/10、docs/21 與程式實作一致。 |

## 需要補的測試

| 類型 | 建議測試 |
| --- | --- |
| Migration | 從空 DB 跑 Alembic head，驗證所有 Meta Andromeda tables 存在，不依賴 `create_all()`。 |
| Data hygiene | 呼叫 overview / review queue / monitoring 不會新增 seed records。 |
| Drift | 沒有 prediction match 時不建立 mock score，只回 coverage insufficient。 |
| Permission | module access true、feature permission false 時，前端操作仍可見；後端仍通過。 |
| Worker | 同一 score event 被兩個 worker 同時 claim 時只能一個成功。 |
| Callback | 重複 completed callback 不重複寫 event；stale completed 不覆蓋 failed/dead-lettered。 |
| Upload | 超大檔、錯誤 MIME、副檔名偽裝、空檔案皆被拒絕。 |
| Model schema | provider 回傳 invalid JSON、invalid band、非數字分數時有明確 fallback 或 422/failed 狀態。 |

## 結論

本模組目前適合作為功能原型與內部驗證基礎，但若要作為正式 creative intelligence / model release workflow，需要先處理 P0/P1 項目。

最高優先級不是增加更多 UI，而是先保證三件事：

1. Schema 由 Alembic 完整控管。
2. 正式資料不被 seed/mock/random 資料污染。
3. Worker 與模型評估結果具備冪等、可追溯、可重現的治理能力。

完成上述後，再投入 multimodal feature extraction、calibration dataset 與真實 release evaluation，模型調整才會有可靠基礎。
