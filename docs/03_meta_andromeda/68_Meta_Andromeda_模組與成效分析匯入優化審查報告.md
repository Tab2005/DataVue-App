# 68. Meta Andromeda 模組與成效分析匯入優化審查報告

## 完成狀態（2026-08-07 追記）

本報告列出的 P0/P1/P2 項目已全數實作完成並合併至 main；P3 中 A8、B7 依文件本身建議維持不做；B2 只做了文件建議的「第一層」（前端併發化），後端批次端點（第二層）尚未做。逐項對照：

| 項目 | 狀態 | 備註 |
|---|---|---|
| A1 評分重用改 checksum 匹配 | ✅ 已完成 | |
| A2 資產 checksum 去重 | ✅ 已完成 | |
| A3 `enqueue_score_event` 分支合併 + `dispatch_accepted` | ✅ 已完成 | |
| A4 per-user OpenRouter 金鑰解析邏輯統一 | ✅ 已完成 | |
| A5 `VALID_ROAS_BANDS` 重複定義清理 | ✅ 已完成 | |
| A6 路徑穿越檢查改用 `is_relative_to()` | ✅ 已完成 | |
| A7 structured output 429 backoff | ✅ 已完成 | |
| A8 圖片改傳 URL 而非一律 base64 | 維持不做 | 文件本身標「評估項，非必改」，需要外部驗證 OpenRouter 端能否存取 public_url，未驗證前不動 |
| B1 前端匯入狀態輪詢 | ✅ 已完成 | |
| B2 批次匯入效率 | ⚠️ 部分完成 | 只做第一層：前端改有限併發（`BATCH_IMPORT_CONCURRENCY`）。第二層「後端批次端點」未做 |
| B3 影片廣告匯入支援 | ✅ 已完成 | |
| B4 媒體下載改串流限制大小 | ✅ 已完成 | |
| B5 匯入端點冪等去重 | ✅ 已完成 | |
| B6 import status TTL 拉長 | ✅ 已完成 | TTL 從 1 小時拉長到 4 小時（採文件建議的較簡單選項，未做「semaphore 等待期間定期 touch」） |
| B7 匯入 payload 市場/版位寫死 | 維持不動 | 文件本身標「暫不動，記錄在案即可」 |

## 基本資訊

- 審查日期：2026-08-07
- 審查範圍：
  1. Meta Andromeda 模組整體（評分管線、runtime、queue host、儲存、repository）
  2. 「成效分析 → Meta Andromeda 觀測匯入」全路徑（前端 Analytics 頁 → 後端 observation_import → 資產儲存 → 自動評分）
- 審查方式：靜態程式碼審閱（未跑線上流量驗證），交叉比對 docs/18、19、20、23、24、28、30、32 既有審查與立案，本報告只列**尚未立案**的新發現。
- 版本基準：main @ `3977fae`

## 總結判定

模組經 docs/24（event loop 阻塞修復）、docs/28（Option D 集中化儲存）兩輪整改後，架構面（web/worker 分離、to_thread 化、分散式 semaphore、Redis stream 派工）已相當穩健。本次審查最重要的新發現是：

> **觀測匯入的「評分重用」機制實際上永遠不會命中**（A1）。每次匯入都會產生全新的 `asset_uri`，而重用查詢用 `asset_uri` 精確比對，因此同一素材在多個觀測窗口匯入時，每個窗口都會重新呼叫一次 AI 評分——與程式碼註解宣稱的設計意圖（「只要該素材已有評分就重用，不必每個窗口重評」）相反。連帶地資產儲存也無 checksum 去重（A2），同素材反覆匯入會持續累積重複的二進位副本。

其次是前端匯入後**只查一次狀態、無後續輪詢**（B1），使用者看到的匯入/評分徽章會永遠停在「排隊中」，需手動重新整理才知道結果。

---

## 第一部分：Meta Andromeda 模組整體優化

### A1.（P0，成本）評分重用比對條件錯誤，跨窗口匯入 100% 重複呼叫 AI

- 位置：`backend/modules/meta_andromeda/service/observation_import.py:291-309`（`_prepare_score_event_for_observation_sync`）
- 現況：重用查詢條件為 `MetaAndromedaScoreEvent.asset_uri == asset_uri`。但 `asset_uri` 來自本次匯入剛存好的資產（`storage.py:113-115`，`asset_{uuid4}` 隨機生成、逐次不同），所以：
  - 同一廣告在 last_7d / last_30d / lifetime 三個窗口各匯入一次 → 三個全新 `asset_uri` → 查詢永遠找不到既有 completed 評分 → AI 評分呼叫 3 次。
  - 先前在 ScoreLab 手動評過的同一素材，從成效分析匯入時也不會被重用。
- 佐證：模組內已有正確做法——`labeling.py:41-78` 的 `match_observed_to_prediction()` 明確寫著「checksum 匹配優先於 asset_uri 精確匹配，因為重新下載的資產會拿到全新的隨機 asset_uri、但 checksum 不變」。drift 配對與校準集建置都用這套，唯獨匯入自動評分的重用沒用。
- 建議：改為兩段式查詢——先以本次資產的 `checksum_sha256` 找出 sibling asset ids，再查 `asset_id.in_(siblings) AND status='completed' AND scoring_mode='ai'` 的最新事件；找不到才建新評分事件。直接重用 `match_observed_to_prediction` 的查詢邏輯即可。
- 效益：三窗口工作流的 AI 呼叫成本直接砍到 1/3；同時讓 `linked_observation_ids` 多對一關聯真正開始運作。

### A2.（P1，儲存成本）資產儲存無 checksum 去重，重複匯入持續累積副本

- 位置：`backend/modules/meta_andromeda/storage.py:106-135`（`store_asset`）、`repository/observations.py:313-330`（`create_uploaded_asset`）
- 現況：`store_asset` 已計算 `checksum_sha256`，但存檔前不查重——每次匯入（不同窗口、不同日期、或使用者重按一次）都完整寫入一份新的二進位副本與新的 asset row。docs/28 遷移時已有 4,544 個歷史檔案，這個增長模式會持續放大集中儲存的體積。
- 建議：`_store_observed_asset_sync` 在呼叫 `store_asset` 前，先查 `MetaAndromedaAsset.checksum_sha256 == sha256(file_bytes)` 且 `upload_status='stored'` 的既有資產；命中就直接回傳既有 asset（不寫檔、不建新 row，或建新 row 但共用 storage_key）。注意 ScoreLab 手動上傳路徑可维持現狀，先只改觀測匯入路徑，風險最小。
- 效益：與 A1 相乘——checksum 命中既有資產時，連下載 CDN 圖檔的 30 秒 httpx 請求都可以跳過（先抓 header 比對已知 media_url 的既有觀測即可短路）。

### A3.（P2，程式碼品質）`enqueue_score_event` 兩個分支回傳完全相同，且派工失敗無狀態標記

- 位置：`backend/modules/meta_andromeda/service/scoring.py:42-44`
- 現況：`if dispatch["accepted"]: return repository.get_review_queue_detail(...)` 與 else 分支回傳一模一樣；`get_review_queue_detail` 在同函式內被呼叫兩次（開頭一次、結尾一次）。派工失敗時只在 worker event 記 `dispatch_failed`，score event 本身停留在 `queued`，完全依賴 sweeper 補派。
- 建議：合併回傳；`accepted=False` 時考慮直接把事件標記為 `dispatch_failed` 或至少在回傳值帶出 `dispatch_accepted` 讓呼叫端可感知。

### A4.（P2，程式碼品質）per-user OpenRouter 金鑰解析邏輯重複實作兩份

- 位置：`backend/modules/meta_andromeda/runtime.py:108-139`（`resolve_openrouter_api_key_for_asset`）與 `runtime.py:414-431`（`_prepare_asset_context` 內嵌同款 asset→uploader→TokenManager 查詢）
- 現況：兩段程式碼做同一件事（asset_id → uploaded_by → google_id → TokenManager.get_ai_api_key），docs 註解還特別警告過繞過統一入口的事故（2026-07-03 回測 0/22）。
- 建議：`_prepare_asset_context` 改呼叫 `resolve_openrouter_api_key_for_asset`（已持有 db_session，可直接傳入），維持單一真相。

### A5.（P3，清理）`VALID_ROAS_BANDS` 匯入後又重複定義

- 位置：`backend/modules/meta_andromeda/runtime.py:16-23`（從 `confidence` import）與 `runtime.py:38`（重新定義同值常數）
- 建議：刪除 line 38 的重定義。

### A6.（P2，穩健性）路徑穿越防護用法錯誤：`relative_to()` 不回傳 False 而是拋例外

- 位置：`backend/modules/meta_andromeda/runtime.py:446`、`runtime.py:482`
- 現況：`if safe_path.relative_to(storage_root.resolve()) and safe_path.exists():` ——當路徑在 root 之外時 `relative_to` 拋 `ValueError`，不會走 `if` 的 False 分支，而是被外層籠統的 `except Exception` 吃掉記成 base64/keyframe 失敗。防護「碰巧有效」但語意錯誤且錯誤訊息誤導。
- 建議：改用 `safe_path.is_relative_to(storage_root.resolve())`（Python 3.9+），語意正確且不用靠例外流程。

### A7.（P3，成本）結構化輸出嘗試失敗後不分類原因，429 時多打一發

- 位置：`backend/modules/meta_andromeda/runtime.py:224-243`（`_call_provider_once`）
- 現況：structured output 前置嘗試（docs/20 P2-2）任何失敗都立即 fallback 到 regex 路徑重打。若失敗原因本來就是 429 限流，等於在被限流的當下立刻再送一個完整請求，加劇限流。
- 建議：structured 嘗試的 except 內做與下方相同的 429 判別，是限流就先 backoff 再進 fallback 迴圈（或直接把 structured 嘗試併入既有 retry 迴圈的第一輪）。

### A8.（P3，評估項）圖片一律以 base64 data URI 內嵌，可評估改傳 URL

- 位置：`backend/modules/meta_andromeda/runtime.py:437-466`
- 現況：filesystem 與 S3 後端都把整張圖讀進記憶體、base64 後塞進 request payload。S3 後端在設定了 `META_ANDROMEDA_STORAGE_PUBLIC_BASE_URL` 時其實已有 `public_url`。
- 建議：若 public_url 可被 OpenRouter 端存取（需驗證），優先傳 URL、退回 base64。可省 worker 記憶體與 33% 的 payload 膨脹。屬評估項，非必改。

### A9. 既有已立案、尚未執行的項目（本報告不重複展開）

| 項目 | 出處 | 狀態 |
|---|---|---|
| 評分模型真實準確率改善五波計劃（排序準確率 0.4446 差於隨機） | docs/30 + docs/32 | 已立案，待啟動 |
| `is_promoted` per-base-profile（P2-7） | docs/19+20 | 未做 |
| worker 架構重整 | docs/25 | 待議 |

---

## 第二部分：成效分析 → Meta Andromeda 匯入優化

### B1.（P1，UX）匯入送出後只查一次狀態、無後續輪詢，徽章永遠停在「排隊中」

- 位置：`frontend/src/hooks/useAnalyticsObservationImport.js:78-105`
- 現況：POST 拿到 202 後立即 GET 一次 status——此時背景 job 幾乎必然還在 `queued`，之後**再也不查**。`AnalyticsDataTable` 的 Obs/Score 雙徽章（`AnalyticsDataTable.jsx:452-487`）因此長期顯示排隊中；匯入按鈕也因 `['loading','accepted','polling']` 判斷持續 disabled。使用者只能重新整理頁面，而重新整理後 `observationImportState` 是 in-memory state，直接歸零、什麼都看不到。
- 建議：對狀態非終態（completed/failed）的列啟動輪詢——例如 5 秒間隔、上限 2 分鐘（後端 status 端點已同時融合 Redis 進度與 DB 事實，輪詢成本低）；批次情境用單一 interval 掃所有 in-flight 列，避免 N 個 timer。終態後停止並更新徽章。
- 效益：這是匯入功能「感覺沒在動」的最大來源；後端其實都做完了，只是前端不知道。

### B2.（P2，效率）批次匯入嚴格逐筆序列送出，N 筆 = N 次串行往返

- 位置：`frontend/src/hooks/useAnalyticsObservationImport.js:161-168`（`for...await`）
- 現況：批次送出對每列 `await submitObservationRow(row)`——每筆是「POST（202 快速返回）+ 立即 GET status」兩次往返全部串行。後端這個 POST 只做 enqueue（`router/observation_import.py:25-43`），真正工作在 worker，前端串行純粹是浪費等待。50 筆選取在 200ms RTT 下要等 20 秒才顯示「批次送出完成」。
- 建議（兩層，可只做第一層）：
  1. 前端改小併發（3–5 個 in-flight，`Promise.allSettled` 分批），並把 B1 的單次 status GET 從 submit 路徑移除（交給輪詢）。
  2. 後端加批次端點 `POST /evaluations/import/facebook-ads/batch` 收 `ad_ids[]`——一次抓整包報告、逐筆展開 enqueue，把每筆各自 `get_custom_report`＋線性掃描 500 列的重工（`facebook_ads_importer.py:119-142`）也一併消除（目前靠 analytics cache 緩解，但 cache miss 時批次首筆會重打 FB API）。

### B3.（P1，功能缺口）影片廣告永遠無法從成效分析匯入評分

- 位置：`backend/modules/meta_andromeda/importers/facebook_ads_importer.py:47-48`
- 現況：`media_url = row.get("image_url")`；影片廣告的 insights row 沒有 image_url（或只有縮圖），`media_type` 落到 `"unknown"` → 匯入後 `score_status = skipped_no_asset`，整條自動評分不啟動。但 runtime 端明明已支援影片 keyframe 抽取評分（`runtime.py:473-496`，docs/23 補完的能力）。等於：模組能評影片，匯入管道卻送不進影片。
- 建議：importer 補影片來源解析——經 ad creative API 取 `video_id`/`source` 或至少 `thumbnail_url`；影片抓不到時退回以縮圖當 image 評分（並在 lineage 標記 degraded），讓影片素材不再整批漏出評分閉環。
- 效益：對以影片為主的帳號，這是目前評分覆蓋率的最大缺口；也直接影響 docs/30 準確率樣本的代表性（樣本全是圖片）。

### B4.（P2，資源）媒體下載全量落地後才檢查大小上限

- 位置：`backend/modules/meta_andromeda/service/observation_import.py:90-96`
- 現況：`await client.get(media_url)` 把整個 body 讀進記憶體，之後才比對 `META_ANDROMEDA_OBSERVED_DOWNLOAD_MAX_BYTES` 丟 413。超大檔案（或惡意 URL）會先吃滿頻寬與記憶體才被拒絕；批次匯入時多個併發 job 疊加。
- 建議：改 `client.stream("GET", ...)`——先看 `Content-Length` header 超限即斷；無 header 則邊讀邊累計、超限即中止連線。

### B5.（P2，冪等）匯入端點無 in-flight 去重，重複觸發會排出重複 job

- 位置：`backend/modules/meta_andromeda/router/observation_import.py:25-43`、`service/observation_import.py:42-56`
- 現況：同一 `observed_creative_id`（同廣告+同窗口+同日）重複送出時，`queue_observed_facebook_ad_import` 只是覆寫 status store 再排一個新 job——兩個 job 都會完整執行：各自下載媒體、各存一份資產（A2 放大）、各建一個 score event（A1 放大成兩次 AI 呼叫）。前端 disabled 判斷只防單列連點，不防「批次送出後又對同列單獨匯入」或多分頁操作。
- 建議：`queue_observed_facebook_ad_import` 先讀 status store——若該 id 已是 `queued`/`processing` 就直接回傳現況（`status: "already_queued"`），不再派工。Redis TTL 1 小時內天然冪等，成本極低。

### B6.（P3，狀態可靠性）import status TTL 1 小時，長批次尾端狀態可能提前蒸發

- 位置：`backend/modules/meta_andromeda/import_status_store.py:17`（`IMPORT_STATUS_TTL_SECONDS = 3600`）
- 現況：狀態每次更新都重設 TTL，正常情況夠用；但佇列壅塞（semaphore 限流 + 大批次）時，排在尾端的 job 若超過 1 小時未輪到，最後一次 `queued` 寫入的 TTL 到期後，status 端點會回 `not_found`——而此時 DB 還沒有 observed row，前端（做了 B1 輪詢後）會顯示「找不到匯入」。
- 建議：`run_observed_facebook_ad_import_job` 在 semaphore 等待期間定期 touch 狀態（或把 TTL 提到 4 小時）；屬 B1 落地後才會浮現的邊角，先記錄。

### B7.（P3，彈性）前端匯入 payload 寫死 `market: 'TW'`、`placement_family: 'all'`

- 位置：`frontend/src/hooks/useAnalyticsObservationImport.js:56-57`
- 現況：所有從成效分析匯入的觀測一律 TW/all。目前業務單一市場沒問題，但 prompt profile 與 objective routing 都以 market/placement 為輸入，未來多市場帳號會全部被標錯。
- 建議：暫不動；在匯入 UI 加欄位前先確認是否有多市場需求。記錄在案即可。

---

## 建議執行順序

| 優先 | 項目 | 主要效益 | 預估規模 |
|---|---|---|---|
| P0 | A1 評分重用改 checksum 匹配 | AI 成本 ↓（三窗口流程約 -66%） | 小：單函式改查詢 + 測試 |
| P1 | B1 前端狀態輪詢 | 匯入功能可感知、可用性 | 小：單 hook + 測試 |
| P1 | B3 影片匯入支援 | 評分覆蓋率、樣本代表性 | 中：importer + creative API |
| P1 | A2 資產 checksum 去重 | 儲存成本、下載頻寬 | 小-中：匯入路徑先行 |
| P2 | B5 匯入冪等去重 | 防重複成本 | 小 |
| P2 | B2 批次送出併發化/批次端點 | 批次體感速度 | 小（前端層）/中（後端端點） |
| P2 | B4 串流下載限長 | 記憶體/頻寬防護 | 小 |
| P2 | A3、A4、A6 程式碼品質三項 | 可維護性 | 各為小 |
| P3 | A5、A7、A8、B6、B7 | 清理與評估項 | 視情況搭車處理 |

相依提醒：A1 與 A2 一起做效益最大（checksum 命中 → 既不重存也不重評）；B1 是 B6 的前置；B2 的後端批次端點若做，B5 的冪等檢查應內建其中。

## 測試建議

- A1：`tests/meta_andromeda/test_observation_import.py` 加「同素材第二窗口匯入 → 不建新 score event、linked_observation_ids 增長」案例（整個評分重用路徑目前零測試覆蓋——`linked_observation_ids` 在測試中完全沒出現，這正是 bug 存活至今的原因）。
- A2：同 checksum 二次匯入 → 資產表不增列（或增列但 storage_key 相同）。
- B1：前端 hook 測試加 fake timer 輪詢至 completed / 逾時兩情境。
- B5：同 id 二次 queue → 第二次回 `already_queued` 且 stream 只收到一則訊息。
