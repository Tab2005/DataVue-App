# 32. Meta Andromeda 評分模型準確率改善實作計劃

- 建立日期:2026-07-13
- 狀態:待啟動
- 依據:docs/30(真實準確率分析與改善建議)
- 關聯:docs/19、docs/20(release 機制)、docs/22、docs/28(Worker 集中化)

---

## 零、問題總覽與波次對映

docs/30 揭露:現任 production 版本 cand_v2026_06_05_a 的真實成對排序準確率 **0.4446**(差於隨機)、平均級距誤差 **0.8218**(近一整級),與 drift report 嚴重預估偏差(ρ=-0.461、31%)互相印證。628 筆評分全部出自單一免費 nano 模型,無對照組;無法直接判定是「模型能力不足」還是「rubric 與成效預測本質錯位」。

| 波次 | 對應 docs/30 建議 | 目標 | 性質 |
|---|---|---|---|
| 第 1 波 | 4.1.1 人工抽樣歸因 | 提供高分低效/低分高效配對明細的匯出能力,支撐人工歸因 | 純新增,低風險 |
| 第 2 波 | 4.1.2 換模型回測 | 候選模型批次回測 + 準確率對照表 | 新增 job,中等複雜度 |
| 第 3 波 | 4.1.3 refresh-metrics 例行化 | 指標自動更新,不再依賴手動呼叫 | 小改動 |
| 第 4 波 | 4.2.6 上線門檻 | 核准流程加 0.55 排序準確率硬門檻 | 小改動,行為變更 |
| 第 5 波(選配,另行細化) | 4.2.4/4.2.5 rubric 重設計、級距與排序分離 | 依第 1 波歸因結論決定方向後再展開 | 待議 |

執行相依:第 1 波結論決定第 5 波方向;第 2 波產出決定是否換模型;第 3、4 波獨立,可隨時插入。

---

## 一、第 1 波:配對明細匯出(歸因抽樣支援)

### 任務 1.1 — 後端:drift 配對明細端點

**問題**:`repository.compute_release_metrics()` 與 drift report 內部都有「觀測素材 × 評分事件」的配對邏輯(`match_observed_to_prediction`),但配對明細不對外暴露,人工歸因無資料可看,只能拿到聚合後的準確率數字。

**變更檔案**:`backend/modules/meta_andromeda/repository.py`、`backend/modules/meta_andromeda/router.py`、`backend/modules/meta_andromeda/schemas.py`、`backend/tests/test_meta_andromeda_module.py`

**實作步驟**:
1. repository 新增 `list_release_metric_pairs(db, model_version, *, sort="mismatch") -> dict`:重用 `compute_release_metrics` 的配對迴圈(建議抽出共用私有函式,避免兩份邏輯漂移),每筆配對輸出:`observed_creative_id`、`ad_name`、`asset_uri`(供縮圖)、`objective`、`observation_window_kind`、`overall_score`、`pred_band`、`real_band`、`label_value`(實際成效值)、`band_gap`(|pred-real| 級距差)、`spend`。
2. 排序模式:`mismatch`(預設,band_gap 大→小,再按 overall_score 高→低,讓「高分低效」浮最上面)與 `score_vs_perf`(overall_score 降冪,附實際成效排名,方便看反相關)。
3. router 新增 `GET /api/meta-andromeda/release/{model_version}/metric-pairs`,權限沿用 `require_meta_andromeda_release`;支援 `?limit=`(預設 50)。
4. 測試:配對輸出欄位完整性、mismatch 排序正確(構造 高分低band/低分高band 假資料)、無配對時回空陣列 + `sample_count: 0`。

**驗收標準**:對 cand_v2026_06_05_a 呼叫可拿到 331 筆(與 refresh-metrics 的 sample_count 一致);排序模式行為正確;既有測試無回歸。

**風險/回滾**:純讀取端點,無狀態變更;單獨回滾。

### 任務 1.2 — 前端:版本總覽配對明細區塊 + CSV 匯出

**問題**:歸因抽樣的實際操作者(營運)需要在 UI 上看素材縮圖對照分數與實際成效,不可能人人跑 API。

**變更檔案**:`frontend/src/pages/MetaAndromedaRelease.jsx`、`frontend/src/services/metaAndromedaMonitoringService.js`(或對應 release service)

**實作步驟**:
1. 版本總覽「線上實測對照證據」下方新增可折疊「配對明細」區塊:表格欄位=縮圖(沿用評估紀錄的 preview 邏輯,含 media_url fallback)、廣告名稱、objective、模型總分、預測級距、實際級距、級距差、花費;預設 mismatch 排序,前 50 筆。
2. 「匯出 CSV」按鈕:前端把已載入資料組成 CSV 下載(不必後端另做匯出端點)。
3. 注意 apiClient 不支援 `{ params }`(既知陷阱,見監控頁 validate-candidate 修法),query string 要拼在路徑上。

**驗收標準**:UI 能看到配對明細與縮圖;CSV 開啟欄位正確;高分低效案例排最前。

**風險/回滾**:純前端新增區塊;單檔回滾。

**第 1 波完成後的人工動作(非程式任務)**:營運從明細中抽「高分低效」「低分高效」各 15 筆人工歸因,結論寫回 docs/30 §3(判定假設 1 模型能力 vs 假設 2 rubric 錯位),決定第 5 波方向。

---

## 二、第 2 波:候選模型批次回測

### 任務 2.1 — 回測批次 job(worker 執行)

**問題**:628 筆評分全出自 nemotron-3-nano(free),沒有第二個模型的對照數據,「換模型會不會更準」目前只能猜。需要能對既有 355 筆觀測素材,用指定候選模型重新評分並計算同口徑準確率。

**變更檔案**:`backend/modules/meta_andromeda/service.py`、`backend/modules/meta_andromeda/repository.py`、`backend/modules/meta_andromeda/router.py`、`backend/core/scheduler.py`(如走排程派工)、`backend/tests/test_meta_andromeda_module.py`

**實作步驟**:
1. 新增「回測執行」端點 `POST /api/meta-andromeda/backtest/runs`,payload:`provider_model`(必填)、`sample_limit`(預設全量觀測素材)、`note`。啟動前先用 `model_catalog.validate_candidate_model()` 驗證模型存在且支援 image input,不合格直接 422。
2. 回測 job 在 worker 上執行(SERVICE_ROLE 判斷,比照觀測匯入的 queue 派工路徑):逐筆對觀測素材呼叫評分管線,`model_registry.get_entry(purpose="backtest")` 路徑指定 provider_model(backtest purpose 已設計為不吃 `META_ANDROMEDA_SCORING_MODEL` env 覆寫,避免被運維逃生門干擾)。
3. 回測產生的評分事件必須與線上事件隔離:`lineage.scoring_purpose = "backtest"` + `lineage.backtest_run_id`,並確認**評估紀錄列表、監控統計、drift report、compute_release_metrics(針對線上版本)全部排除 backtest 事件**——這是本任務最大的正確性風險,測試要逐一覆蓋。
4. 併發與成本控制:沿用 `_score_event_semaphore`(併發 2)節流;免費模型另加保守間隔(可設 env `META_ANDROMEDA_BACKTEST_INTERVAL_SECONDS`,預設 2s)防限速;job 進度寫 Redis(比照 import_status_store 模式),`GET /backtest/runs/{id}` 可查進度/失敗數。
5. 回測完成後自動以 `compute_release_metrics` 同邏輯(改為過濾 `backtest_run_id`)計算該 run 的 `pairwise_ranking_accuracy` / `mean_band_error` / `sample_count`,存入 run 紀錄。

**驗收標準**:對一個小樣本(`sample_limit=10`)端到端跑通;線上評估紀錄/監控/drift 數字在回測前後完全不變(隔離驗證);run 完成後有準確率結果;中途失敗可重跑(冪等:同 run 已評分素材跳過)。

**風險/回滾**:新增流程,不觸線上評分路徑;隔離過濾若有漏,線上統計會被污染——以測試把關;整波可獨立回滾。

### 任務 2.2 — 回測對照表 UI

**問題**:回測結果需要與現任版本並排比較,才能做「是否換模型」決策。

**變更檔案**:`frontend/src/pages/MetaAndromedaRelease.jsx`(或監控頁,擇一集中)、對應 service

**實作步驟**:
1. 版本總覽新增「回測對照」區塊:發起回測(輸入 provider_model,前置呼叫既有 validate-candidate 查詢功能確認可用)、run 列表(模型、進度、sample_count、排序準確率、級距誤差、狀態)。
2. 對照表首列固定顯示現任 production 的真實指標(0.4446 / 0.8218)作為 baseline,超過 baseline 且 ≥ 0.55 的 run 標綠。

**驗收標準**:能從 UI 發起回測、看進度、比較結果;顏色標示正確。

**風險/回滾**:純前端;單檔回滾。

---

## 三、第 3 波:refresh-metrics 例行化

### 任務 3.1 — 排程自動刷新現任版本指標

**問題**:refresh-metrics 目前需手動呼叫(2026-07-13 首次即為手動),之後新評分/新觀測進來,版本總覽數字會逐漸過期,且 `is_demo_data` 旗標依賴人工記得刷。

**變更檔案**:`backend/core/scheduler.py`、`backend/modules/meta_andromeda/service.py`、`backend/tests/`(對應排程測試檔)

**實作步驟**:
1. worker 排程新增每日一次(建議 UTC 02:00,錯開週報與其他 job)`refresh_meta_andromeda_release_metrics`:查現任 production 版本 → 呼叫 `MetaAndromedaService.refresh_release_metrics`;`insufficient_data` 視為正常結果記 info,不告警。
2. 比照既有 job 慣例:註冊於 SERVICE_ROLE=worker,單例防重入,失敗記 warning 不中斷其他 job。
3. 前一版卡片數字若仍為 seed(`is_demo_data=true`),前端在該卡片角落補一個小標「示範資料」(per-record 旗標已存在,純顯示)——修正 docs/30 §6 提到的「前一版 0.74/0.19 仍是假數字」閱讀誤導。

**驗收標準**:排程觸發後 DB 指標更新、`updated_at` 變化;前一版卡片有示範資料小標;現任卡片無。

**風險/回滾**:每日一次的輕量 job(331 筆配對計算 < 數秒);移除排程即回滾。

---

## 四、第 4 波:核准上線門檻

### 任務 4.1 — approve 動作加排序準確率硬門檻

**問題**:docs/30 §4.2.6 — 現行核准流程不看任何準確率,cand_v2026_06_05_a 就是這樣帶著 seed 假數字上線的。需防止「上線後才發現不如隨機」重演。

**變更檔案**:`backend/modules/meta_andromeda/repository.py`(release action)、`backend/modules/meta_andromeda/router.py`、`backend/modules/meta_andromeda/schemas.py`、前端 release 頁、測試

**實作步驟**:
1. approve 動作前置檢查:目標版本 `metrics_source == "computed"` 且 `pairwise_ranking_accuracy >= 0.55`(門檻設 env `META_ANDROMEDA_RELEASE_MIN_PAIRWISE_ACCURACY`,預設 0.55),不滿足回 422 與明確訊息(「未回測」vs「回測未達標」分開講)。
2. 保留逃生門:payload 加 `force: true` + 必填 `note`,可越過門檻但 release event 記錄 `forced: true`(稽核用)。rollback 不設門檻(回滾是止血動作)。
3. 前端:核准按鈕在不達標時顯示原因;force 走二次確認對話框。

**驗收標準**:未回測版本核准被擋;達標版本正常核准;force 可越過且 history 有 forced 標記;rollback 不受影響。

**風險/回滾**:行為變更(核准變嚴),但有 force 逃生門;單波回滾。

---

## 五、第 5 波(選配,待第 1 波歸因結論):rubric / 級距機制重設計

**先決條件**:第 1 波人工歸因得出結論後,擇一路線細化(本波僅佔位,不預先展開任務):

- 路線 A(歸因結論=假設 1 模型能力不足):以第 2 波回測結果直接換模型,走既有 create_candidate → backtest → approve(過第 4 波門檻)流程,本波即完成,不需改 rubric。
- 路線 B(歸因結論=假設 2 rubric 錯位):評分 prompt 從「素材品質」轉向「同帳戶歷史高效素材特徵對齊」,objective/受眾/價格帶入 context;級距預測與排序分離(級距改由歷史統計產生,LLM 只做相對排序)。屆時另立實作計劃(預計為 docs/33)。

---

## 六、建議執行順序與相依

1. **第 1 波**(1.1 → 1.2):先做,產出歸因所需資料;人工歸因與後續波次並行。
2. **第 3 波**:小改動,可與第 1 波同批部署。
3. **第 2 波**(2.1 → 2.2):第 1 波部署後即可開工,不必等歸因結論(對照數據早晚要有)。
4. **第 4 波**:第 2 波可用後部署(門檻要有回測數據才有意義;先上會把所有候選版本全擋住)。
5. **第 5 波**:等第 1 波歸因結論。

## 七、明確不做(記錄在案)

- 不回溯修改既有 628 筆線上評分事件與其 lineage(歷史數據保持原樣,僅供分析)。
- 不做多模型同時線上 A/B 評分(成本與複雜度不符現階段需求;回測對照已足夠決策)。
- prod_v2026_05_28 不補算指標(無評分事件掛載,無資料可算,只做 UI 示範資料標示)。
- 級距統計模型(路線 B 的一部分)不在本計劃展開,若走該路線另立 docs/33。
