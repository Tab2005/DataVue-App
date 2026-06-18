# 23 Meta Andromeda 模組功能審查與優化報告

## 基本資訊

- 審查日期：2026-06-18
- 審查範圍：`backend/modules/meta_andromeda`（service / runtime / repository / router / queue_host / storage / schemas / model_registry / importer / dependencies）、`backend/database/models/meta_andromeda.py`、Alembic migrations、`backend/core/scheduler.py`、`backend/services/ai/openrouter_client.py`、`backend/core/config.py`、前端 `frontend/src/pages/MetaAndromeda*.jsx` 與其 services / tests
- 審查目標：盤點功能完整度、找出可優化之處、評估模型是否有優化空間
- 對照基準：`docs/22_Meta_Andromeda_模組復審與優化建議報告.md`（同日稍早之復審，為 HEAD commit）
- 驗證方式：逐檔閱讀原始碼並以 `grep` / git log 交叉驗證問題是否仍存在；本次未執行 pytest（環境預設缺 pytest，與 doc 22 狀況相同）

## 總結判定

本次審查**確認 doc 22 所列的 P0／P1 問題截至 2026-06-18 全數仍未修復**（doc 22 為 HEAD 提交，其後無任何修復 commit），並**新增 5 項 doc 22 未提及的問題**（其中 1 項為 P0 級安全／權限缺口）。

模組功能骨架完整：score lab、review queue、monitoring、release console、asset storage、queue host（apscheduler / database_queue / external_webhook / redis_stream / local_async）、external worker callback、FB Ads observed import、drift report、calibration sync 皆有對應實作與前端頁面。但「功能存在」不等於「production-ready」——目前最關鍵的風險集中在**資料治理**與**模型治理**兩條線，而非 API 數量。

| 優先級 | 結論 |
| --- | --- |
| P0 | `meta_andromeda_observed_creatives` 表仍無 Alembic migration（doc 22 已列，已於 2026-06-18 修復）。 |
| P0 | drift report 仍在 read path 隨機建立並持久化 `ma_evt_mock_*` score event（doc 22 已列，已於 2026-06-18 修復）。 |
| P0 | 讀取 API 仍自動寫入 seed/demo data（doc 22 已列，已於 2026-06-18 修復）。 |
| **P0（新）** | `MetaAndromedaScoreLab.jsx` 完全沒有權限 gate，任何能進入頁面的使用者都能上傳素材並送評（已於 2026-06-18 修復）。 |
| P1 | 前端 Monitoring／Release 仍用已廢棄的 `meta_andromeda:operate`／`:release` feature permission（doc 22 已列，未修）。 |
| P1 | queue／worker 狀態轉換缺原子 claim 與 callback 冪等性（doc 22 已列，未修）。 |
| P1 | scoring runtime 不讀素材內容，模型輸入不足（doc 22 已列，未修）。 |
| **P1（新）** | `add_meta_andromeda_score_job` 不 gate `is_scheduler_enabled()`，scheduler 關閉時 Meta Andromeda job 仍會被排程。 |
| **P1（新）** | OpenRouter 評分 provider 不傳 multimodal／image 給模型，且 client 的 `timeout` 參數是 dead code。 |
| P2 | 上傳／media download 安全邊界不足（doc 22 已列，未修）。 |
| P2 | monitoring 指標仍為固定值、索引不足（doc 22 已列，未修）。 |
| P2 | calibration sync 未實體化為 dataset（doc 22 已列，未修）。 |
| **P2（新）** | confidence 寫死 0.72／0.61、overall_score 邏輯分數與 heuristic 偏高，模型輸出缺乏校準。 |
| **P2（新）** | README／doc 10／doc 21 文件漂移（doc 22 已部分提及，本次補強證據）。 |

## 功能盤點（現狀）

| 模組能力 | 已有實作 | 現狀評估 |
| --- | --- | --- |
| Pre-launch prediction | `/assets:upload`、`/scores`、queued scoring、Score Lab 頁 | 路徑通，但模型只看文字欄位與 asset type，不分析素材畫面。 |
| Review workflow | `/review-queue`、feedback timeline、Review Queue 頁（含縮圖預覽） | 基本可用，縮圖預覽為近期新增。 |
| Queue / worker | apscheduler / database_queue / external_webhook / redis_stream / local_async、retry、dead-letter、stream reclaim | 功能面完整，但 claim 與 callback 冪等性不足。 |
| Runtime health | `/runtime/health`、`/health` checks | 可用，但部分 readiness 只檢查設定不驗證端到端。 |
| Observation import | `/evaluations/import/facebook-ads`、`MetaAndromedaObservedCreative` ORM、雙層抓取（快取＋ad_id fallback） | 程式碼完整，但缺 migration、media download 邊界不足。 |
| Learning / drift | `/drift:trigger`（含 custom date range）、`/calibration/sync` | 仍偏示範，會用 mock／random 補資料，不可作正式決策。 |
| Release console | release overview / approve / reject / rollback | UI／API 可用，但 release record 以 seed／static 為主，未接真實 evaluation。 |

## doc 22 問題之修復狀態驗證

逐項以原始碼驗證，doc 22 列出的問題**全部仍存在**：

| doc 22 問題 | 驗證證據 | 狀態 |
| --- | --- | --- |
| P0 ObservedCreative 缺 migration | `backend/alembic/versions/20260618_meta_andromeda_observed_creatives.py` 已補 table 與索引，兼容既有 DB 補建索引 | **已修** |
| P0 drift mock score 持久化 | `repository.py` 已移除 `ma_evt_mock_*` 建立與 commit 邏輯，缺預測資料時直接略過 | **已修** |
| P0 read path seed | `repository.py` 已移除 read path `ensure_seed_data(db)` 呼叫；測試改為 fixture 顯式 seed | **已修** |
| P1 前端權限不一致 | `MetaAndromedaMonitoring.jsx:32` `usePermission('meta_andromeda:operate')`、`MetaAndromedaRelease.jsx:21` `usePermission('meta_andromeda:release')` | **未修** |
| P1 worker claim／callback 冪等 | `repository.py:935-946` mark_score_processing 無原子 claim；`service.py:514-639` callback 無 receipt 去重 | **未修** |
| P1 scoring 不讀素材 | `runtime.py:68-84` prompt 只含文字欄位；`runtime.py:175-273` heuristic 只看文案是否存在 | **未修** |
| P1 calibration 未實體化 | `repository.py:1135-1208` 只寫回 `lineage["calibration"]`，無 dataset table | **未修** |
| P2 上傳／download 邊界 | `router.py:214` `await file.read()` 整檔入記憶體；`storage.py:106-135` 無 size／MIME 驗證 | **未修** |
| P2 monitoring 固定值 | `repository.py:486` latency 為寫死 `{avg:1180, p95:2140, max:3410}` | **未修** |
| P2 文件漂移 | README:26 稱「有 GOOGLE_AI_API_KEY 走 Gemini」；`docs/10:173-175` 仍列 `/release:approve` 而非實際的 `/release/approve` | **未修** |

> 結論：doc 22 發布後無任何修復 commit。doc 22 應視為「待辦清單」而非「已完成事項」。本報告在其基礎上補充新發現，並重新彙整優先級。

## 本次新發現（doc 22 未提及）

### N1.（P0）ScoreLab 頁面完全沒有權限 gate

證據：

- `frontend/src/pages/MetaAndromedaScoreLab.jsx` 全文 `grep usePermission|useModuleAccess|hasPermission` **零命中**——該元件未 import 任何權限 hook。
- 對照其餘三個 Meta Andromeda 頁面（Monitoring / Release / ReviewQueue）皆有 `usePermission` 呼叫。
- 測試檔 `MetaAndromedaScoreLab.test.jsx` mock 了 `usePermission` 回傳 `true`，但因元件從未呼叫該 hook，此 mock 為 dead code，無保護效果。

影響：

- 後端 `POST /assets:upload` 與 `POST /scores` 雖有 `require_meta_andromeda_operate`（module access）保護，但前端 ScoreLab 頁面本身不檢查權限——任何能路由到該頁的使用者都能操作 UI。
- 若路由層未以 `ProtectedModule` 包裹 `/meta-andromeda/score-lab`，則形同無前端權限屏障。
- 與 doc 22 P1「前端權限不一致」同類但更嚴重：Monitoring／Release 至少還有（錯誤的）feature gate，ScoreLab 是**完全沒有 gate**。

建議：

- ScoreLab 改用 `useModuleAccess('meta_andromeda')` 或 route-level `ProtectedModule`，與後端 module-only 策略對齊。
- 補前端測試：module access 為 false 時，上傳與送評按鈕停用或頁面導向。

### N2.（P1）score job 排程不 gate scheduler 啟用狀態

證據：

- `backend/core/scheduler.py:450-466` `add_meta_andromeda_score_job` 直接 `scheduler.add_job`，**未呼叫** `is_scheduler_enabled()`。
- 對照同檔 `add_report_job`（~line 410）會先檢查 `is_scheduler_enabled()` 才排程。

影響：

- 當 `ENABLE_REPORT_SCHEDULER=false` 關閉排程器時，報表 job 不排，但 Meta Andromeda score job 仍會嘗試排程。
- 若 scheduler 未啟動（`scheduler.running` 為 False），`add_job` 行為依賴 APScheduler 內部狀態，可能靜默失敗或拋錯，導致 score event 永遠卡在 queued。
- `queue_host.get_active_host()` 雖會在 auto 模式判斷 `scheduler.running`，但 `enqueue_score_event` 在非 auto 顯式設定（如 `apscheduler`）時不會再檢查。

建議：

- `add_meta_andromeda_score_job` 開頭 gate `is_scheduler_enabled()`，與 report job 一致；關閉時退回 `local_async` 或回傳 `accepted=False`。
- 補測試：scheduler disabled 時 score submit 的派工行為可預期。

### N3.（P1）OpenRouter 評分不傳素材、且 timeout 參數為 dead code

證據：

- `backend/services/ai/openrouter_client.py:148-176` `generate_content` 把 prompt 組成 `{"role":"user","content": prompt}` 純字串，**未支援 multimodal content array**（無 `image_url` 等）。
- `runtime.py:95-102` 呼叫 `client.generate_content(prompt, model, system_prompt, 0.2, 600)`，prompt 內容只有 asset type、objective、placement、market、headline、primary text、CTA——已存檔的圖片／影片 bytes 從未傳入模型。
- `openrouter_client.py:154` `generate_content` 簽名含 `timeout` 參數，但 line 167 的 `chat.completions.create(...)` **未帶 `timeout=`**，該參數從未生效。
- `runtime.py:658` 外層有 `asyncio.wait_for(..., timeout=settings.META_ANDROMEDA_SCORE_TIMEOUT_SECONDS)` 兜底，但 OpenAI SDK 呼叫本身無 timeout，長尾請求會佔用 worker thread 直到外層 cancel。

影響：

- 強化 doc 22 P1「scoring runtime 不讀素材內容」的根因：即使 provider 改成支援 vision 的模型，現有 client 也無法傳圖。
- SDK 層無 timeout，外層 `asyncio.wait_for` cancel 時，blocked thread 可能不會立即釋放，累積下來拖垮 worker。
- OpenRouter client 的 API key fallback 鏈（`OPENROUTER_API_KEY` → `GOOGLE_API_KEY` → `ZEABUR_AI_HUB_API_KEY`）對一個 OpenRouter 專用 client 而言語意混亂，易誤導設定。

建議：

- 若要走視覺評分：OpenRouter client 支援 multimodal content（image_url/base64），runtime 改傳已存素材的存取 URL 或 base64；或改用支援 image input 的 provider model。
- `generate_content` 把 `timeout` 真正傳進 `chat.completions.create(timeout=...)`，或移除 dead param。
- 釐清 client 的 key fallback 鏈語意，避免 OpenRouter client 回退到 Google key。

### N4.（P2）模型輸出缺乏校準：confidence 寫死、分數邏輯偏高

證據：

- `runtime.py:145` OpenRouter 路徑 confidence 固定 `0.72`；`runtime.py:245` heuristic 路徑 confidence 固定 `0.61`，與實際樣本數／歷史誤差無關。
- `runtime.py:183-196` heuristic 起分 72（image）／67（video），叠加後 `max(48, min(score, 91))`——即使完全沒有 headline／primary_text／CTA，image 也有 72 分，偏樂觀。
- `repository.py:586` band 門檻寫死 `low<1.5 / mid<3.5 / high>=3.5`，未依 objective／market 區分。

影響：

- confidence 無法反映預測可信度，reviewer 無法據此決定是否信賴分數。
- heuristic 偏高分可能讓劣質素材通過 review，污染下游 calibration（calibration 只挑 `err>0` 的，但高分素材若實際 ROAS 低會被大量標記，放大資料偏差）。
- 單一 ROAS 門檻跨 objective 使用，lead／traffic 廣告的 ROAS 語意與 purchase 不同，label 品質不均。

建議：

- confidence 改為基於資料完整度、相似樣本數、歷史 calibration error 的計算值，並隨模型版本儲存。
- heuristic 起分下調或改為「缺欄位扣分」模型，避免空文案也得高分。
- label policy 版本化：依 objective 分目標（purchase 看 ROAS／CPA，lead 看 CPL／CVR），保存 policy version 以利 drift 可追溯。

### N5.（P2）文件漂移補強證據

doc 22 已提及文件與實作不一致，本次補充更具體證據：

- `backend/modules/meta_andromeda/README.md:26`：「score runtime … 預設 auto 模式會在有 `GOOGLE_AI_API_KEY` 時走 Gemini，否則回退到 deterministic heuristic provider」——但 `runtime.py` 實作是 OpenRouter（`OpenRouterScoringProvider`），`model_registry.py` 預設 provider 為 `openrouter`、model 為 `deepseek/deepseek-v4-flash`。README 描述與程式碼矛盾。
- `docs/10_Meta_Andromeda_模組說明.md:173-175` 仍列 `POST /api/meta-andromeda/release:approve`（冒號語法），但 `router.py:350` 實際是 `/release/approve`（斜線）。
- `docs/21_Meta_Andromeda_模組完整度審計報告.md` 判定 100% production-ready，與 doc 22 及本報告結論相反。

影響：

- 新開發者依 README 設定 `GOOGLE_AI_API_KEY` 期待走 Gemini，實際仍走 OpenRouter，金鑰可能無效卻不自知。
- 依 doc 10 呼叫 `/release:approve` 會 404。
- 依 doc 21 認為模組已 ready 而貿然上線，會踩 P0 資料污染風險。

建議：

- 更新 README:26 為 OpenRouter provider 描述，並標註 Gemini 已遷移為選用備援（commit `23847e6` 已做遷移但 README 未同步）。
- 更新 doc 10:173-175 為 `/release/approve` 等正確 path。
- doc 21 加註「歷史快照，2026-06-18 復審結論以 doc 22／doc 23 為準」。

## 模型優化空間（彙整並擴充 doc 22 模型章節）

### 1. 輸入特徵升級（最高優先）

現況：模型輸入僅 asset_type + 文字欄位 + 投放 context，**完全沒有素材視覺特徵**。

| 類別 | 建議特徵 |
| --- | --- |
| Image | OCR 文字密度、產品／人物／logo 偵測、主體位置、色彩對比、CTA 可見性、safe area、品牌一致性 |
| Video | 前 1 秒 hook frame、3 秒 retention cue、字幕密度、節奏切換、end card、產品露出時間 |
| Copy | headline、primary text、CTA、語氣、優惠強度、localization、違規風險 |
| Context | objective、placement、market、受眾、歷史 account baseline、campaign type |
| Outcome | spend、impressions、clicks、purchase_value、ROAS、CPA、CTR、CVR、learning phase |

實作路徑：先建 vision-feature service（OCR + 偵測 + frame sampling），把 structured features 送入 scoring model；或改用支援 image input 的 provider 並讓 OpenRouter client 傳 multimodal content（見 N3）。

### 2. 預測目標重新定義

現況：固定 ROAS band 門檻 `low<1.5 / mid<3.5 / high>=3.5`（`repository.py:586`、`repository.py:1177`）。

建議：

- 依 objective 區分目標：purchase 看 ROAS／CPA，lead 看 CPL／CVR，traffic 看 CTR／CPC。
- 依 market／account baseline 做相對分位數（top 25% / middle 50% / bottom 25%）。
- 保存 label policy version，避免不同時期 drift report 用不同標準卻不可追溯。

### 3. 分數與信心校準

- `overall_score` 與 `roas_band` 拆開治理，避免單一分數掩蓋 label uncertainty。
- confidence 不應固定 0.72／0.61（見 N4），應基於資料完整度、模型版本、相似樣本數、historical calibration error。
- 加入 ECE、Brier score、coverage、confusion matrix、per-segment MAE 等評估指標。

### 4. Fallback 策略調整

現況：provider 失敗回 heuristic 並標 `provider_fallback`（`runtime.py:382-390`），但分數仍以 `status=completed` 入庫。

建議：

- fallback scoring 預設狀態應為 `completed_with_fallback` 或 `needs_review`，不與正常 AI score 混為同類 completed。
- release／drift evaluation 應可排除 fallback scoring，或獨立評估 fallback cohort。
- fallback 分數不進入 model promotion metrics（除非明確標記並分組）。

### 5. Release gate 由真實 evaluation 驅動

現況：release record 以 seed／static data 驅動（`repository.py` SEED_RELEASE_RECORDS），promotion_gate_summary 為手動 seed。

建議：

- 每個 candidate model version 必須有 evaluation artifact（dataset_id、metrics snapshot）。
- promotion gate 來自 holdout set、recent observed set、per-market／per-objective segment。
- release action 保存：dataset_id、evaluation_id、metrics snapshot、approver、rollback plan。
- 需先實體化 calibration dataset（doc 22 P2：新增 `meta_andromeda_calibration_datasets`／`_items`／`model_evaluations` 表）。

## 建議修復路線（合併 doc 22 與本次新發現，重新排序）

| 優先級 | 建議工作 | 驗收標準 |
| --- | --- | --- |
| P0 | 補 `meta_andromeda_observed_creatives` Alembic migration＋索引 | 已完成；新增 `20260618_meta_andromeda_observed_creatives.py` |
| P0 | 移除 read path seed 與 drift mock score 持久化 | 已完成；read API 移除 side effect，drift 不再建立 `ma_evt_mock_*` |
| P0 | ScoreLab 頁面補權限 gate（本報告 N1） | 已完成；module access 為 false 時無法上傳／送評，前端測試已補 |

### 2026-06-18 P0 修復狀態補記

- 已完成三項 P0 修復：ObservedCreative migration、read path seed / drift mock 移除、ScoreLab module access gate。
- 驗證結果：
  - `frontend`: `npm test -- MetaAndromedaScoreLab.test.jsx` 通過（2/2）。
  - `backend`: `python -m py_compile backend/tests/test_meta_andromeda_module.py backend/alembic/versions/20260618_meta_andromeda_observed_creatives.py` 通過。
  - `backend pytest` 尚未執行，原因是目前環境缺少 `pytest` 套件（`No module named pytest`）。
| P1 | 前端 Monitoring／Release 改 module-only 權限 gate | 只有 `meta_andromeda` module access 時操作按鈕可見 |
| P1 | `add_meta_andromeda_score_job` gate `is_scheduler_enabled()`（N2） | scheduler disabled 時 score 派工行為可預期 |
| P1 | worker claim／callback 冪等化 | 重複 job、重複 callback、stale callback 不覆蓋 terminal status |
| P1 | OpenRouter client 支援 multimodal＋修通 timeout（N3） | 視覺素材能傳入模型；SDK 呼叫有實際 timeout |
| P1 | 模型輸出 schema 驗證 | provider 回傳不合法 band／score／risk_tags 時能被拒絕或降級 |
| P2 | 上傳與 media download 安全邊界 | 大檔、錯誤 MIME、非允許來源 URL 被拒絕且回 4xx |
| P2 | 真實 monitoring metrics 與索引 | latency 從 timestamps 計算；review queue／summary 大量資料下可接受 |
| P2 | confidence 校準化、heuristic 起分下調、label policy 版本化（N4） | confidence 非固定值；空文案不得高分；label policy 可追溯 |
| P2 | calibration dataset 實體化 | 每次 sync 建立 dataset 與 items，release candidate 可追溯到 evaluation |
| P3 | 更新文件（README、doc 10、doc 21）（N5） | 路由 path、provider 描述、readiness 狀態與程式一致 |

## 需要補的測試（合併 doc 22 與本次新發現）

| 類型 | 建議測試 |
| --- | --- |
| Migration | 從空 DB 跑 Alembic head，驗證所有 Meta Andromeda tables 存在，不依賴 `create_all()` |
| Data hygiene | 呼叫 overview／review queue／monitoring 不會新增 seed records |
| Drift | 沒有 prediction match 時不建立 mock score，只回 coverage insufficient |
| Permission（後端） | score submit endpoint 的權限拒絕測試（目前僅 observation import 與 overview 有） |
| Permission（前端） | module access true、feature permission false 時 Monitoring／Release／ScoreLab 操作可見；access false 時不可操作（**含 ScoreLab，目前零覆蓋**） |
| Worker | 同一 score event 被兩個 worker 同時 claim 時只能一個成功 |
| Callback | 重複 completed callback 不重複寫 event；stale completed 不覆蓋 failed／dead-lettered |
| Scheduler | `is_scheduler_enabled=false` 時 score job 不排程（N2） |
| Upload | 超大檔、錯誤 MIME、副檔名偽裝、空檔案皆被拒絕 |
| Model schema | provider 回傳 invalid JSON、invalid band、非數字分數時有明確 fallback 或 422／failed |
| Timeout | OpenRouter client 實際 timeout 生效（N3），不靠外層 asyncio 兜底 |

## 結論

本模組功能齊備，作為功能原型與內部驗證基礎已堪用，但距正式 creative intelligence／model release workflow 仍有明顯差距。doc 22（同日稍早復審）所列 P0／P1 問題至今全數未修，本報告再新增 5 項發現（含 1 項 P0：ScoreLab 無權限 gate）。

最高優先級不是增加更多 UI，而是先保證四件事：

1. **Schema 由 Alembic 完整控管**（observed_creatives migration）。
2. **正式資料不被 seed／mock／random 污染**（read path seed、drift mock）。
3. **權限一致性**（ScoreLab 補 gate、Monitoring／Release 改 module-only）。
4. **Worker 與模型評估結果具備冪等、可追溯、可重現的治理能力**（claim／callback 冪等、calibration dataset 實體化）。

完成上述後，再投入 multimodal feature extraction（含 OpenRouter client 支援視覺輸入）、confidence 校準、真實 release evaluation，模型優化才會有可靠基礎。模型本身的優化空間明確：從「文字欄位評分」升級為「素材視覺特徵 + 文案 + 投放 context + 成效 outcome」的多模態閉環，這也是模組「creative intelligence」定位能否成立的關鍵。

> 本報告與 `docs/22` 互補：doc 22 為首輪復審，本報告（doc 23）為同日第二輪，補驗證修復狀態並新增發現。兩份結論一致——模組尚未 production-ready，需先處理 P0／P1。
