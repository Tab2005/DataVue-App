# 20. Meta Andromeda 素材評分閉環優化實作計劃

- **日期**：2026-07-03
- **性質**：實作計劃（依 docs/19 分析報告展開為可執行任務）
- **依據**：docs/19_Meta_Andromeda_素材評分閉環優化建議報告.md
- **範圍**：`backend/modules/meta_andromeda`（runtime / model_registry / calibration_pipeline / repository / service / importers）、`backend/core/scheduler.py`、`backend/database/models/meta_andromeda.py`
- **執行原則**：每個任務獨立可測、可回滾；第 1 波全部完成前不進入第 2 波（P0 斷點會污染第 2 波要修的統計量）。

---

## 零、總覽與波次對應

| 波次 | 目標 | 對應 docs/19 章節 | 前置條件 |
|------|------|------|------|
| 第 1 波 | 修復閉環斷點，讓自動校準真正跑起來 | 二、P0-1~P0-6 | 無 |
| 第 2 波 | 提升評估與校準樣本品質，讓準確率數字可信 | 三、P1-1~P1-6 | 第 1 波 P0-1~P0-5 完成 |
| 第 3 波 | 結構升級與自動化 | 四、五、P2-1~P2-8 | 第 2 波完成 |

每個任務區塊包含：**問題**（引用報告結論）、**變更檔案**、**實作步驟**、**驗收標準**、**風險/回滾**。

---

## 第 1 波：修斷點（P0）

### 任務 1.1 — 修復自動校準管線參數錯誤 + 基礎 Profile Seed（P0-1）

**問題**：`service.py:1448` 把模型版本字串當 `base_profile_name` 傳給 `calibration_pipeline.generate_calibrated_profile()`，但該函式用它去查 `MetaAndromedaScoringProfile.profile_name`（`calibration_pipeline.py:141`）。資料庫目前沒有任何基礎 profile，`base_profile is None` 時整條校準管線 `return None`，只留 log，閉環最後一步恆為零產出。

**變更檔案**：
- `backend/database/models/meta_andromeda.py`（新增 migration 或確認既有欄位可承載 seed）
- `backend/alembic/versions/`（新增 migration：seed 一筆 `creative_scoring_v1` 基礎 profile）
- `backend/modules/meta_andromeda/service.py`（`sync_calibration_dataset` 附近，約 1444-1450 行）
- `backend/modules/meta_andromeda/calibration_pipeline.py`（若 base_profile 查無時的錯誤處理，約 139-149 行）

**實作步驟**：
1. 撰寫 Alembic migration：將 `runtime.py` 的 `_FALLBACK_USER_PROMPT_TEMPLATE`、`_FALLBACK_SYSTEM_PROMPT`、`_DEFAULT_OBJECTIVE_PROFILES` 寫入 `MetaAndromedaScoringProfile` 表，profile_name 固定為 `creative_scoring_v1`，`is_promoted=True`（作為初始全域基準）。
2. 修改 `service.py`：校準 job 觸發時改傳目前生效的 profile 名稱（優先讀 `is_promoted=True` 的 profile；查無則退 `model_registry.get_entry().scoring_profile`），不再傳 `META_ANDROMEDA_SCORING_MODEL_VERSION`。
3. 修改 `calibration_pipeline.generate_calibrated_profile()`：`base_profile is None` 時，把失敗原因寫回 `CalibrationDataset.status`（例如 `calibration_failed:base_profile_missing`），而非只留 log。
4. 確認 runtime 的 `_load_scoring_profile()`（`runtime.py:261`）在 DB 有 seed profile 後行為不變（DB profile 優先於寫死 fallback，邏輯本來就支援）。

**驗收標準**：
- 本地/測試環境跑一次 migration 後，DB 存在 `creative_scoring_v1`。
- 模擬一批 `synced_count >= 10` 的校準資料集，觸發 job 後產生新的 `xxx_cal_xxxxx` profile，非 `None`。
- 刻意讓 base_profile 查無（改錯名稱）時，`CalibrationDataset.status` 能看到明確失敗原因，而非僅 log。

**風險/回滾**：新 migration 為新增資料，不影響既有資料；若 seed 內容有誤，可用新 migration 修正 profile 內容，不需回滾整條鏈路。

---

### 任務 1.2 — 統一配對與標籤政策（P0-2）

**問題**：Drift report 用動態 P33/P67 門檻（`repository.py:1088-1135`），`sync_calibration_dataset` 呼叫 `_resolve_observed_band()` 卻不傳門檻，走固定 fallback（`repository.py:1942`）。兩處 `LABEL_POLICY_VERSION` 相同但規則不同；配對邏輯也不同（drift 用 checksum→asset_uri，校準只用 asset_uri）。

**變更檔案**：
- `backend/modules/meta_andromeda/repository.py`（抽出共用函式；drift 約 1051-1170 行，校準約 1888-1950 行）
- 新增 `backend/database/models/meta_andromeda.py` 的 `LabelPolicy`（或等效）表，或在既有表加欄位持久化門檻

**實作步驟**：
1. 抽出 `match_observed_to_prediction()`：統一配對邏輯（checksum 優先、asset_uri 次之），drift 與校準都呼叫此函式。
2. 抽出 `label_observed_band()`：統一標籤規則，接受門檻參數（不再有「傳/不傳門檻」兩條路徑）。
3. 新增門檻持久化：每次計算出 P33/P67 門檻後寫入 account-level 記錄（含生效區間、樣本數、`LABEL_POLICY_VERSION`）；校準與 drift 都讀同一份最新有效門檻，而非各自即算即丟。
4. 門檻規則變更時 bump `LABEL_POLICY_VERSION`，讓歷史資料可追溯用的是哪個政策版本。
5. 校準項目寫入時比照 drift 的 `report_payload.roas_band_thresholds`，記錄實際使用的門檻值。

**驗收標準**：
- 同一批 ObservedCreative，drift report 與校準資料集算出的 `observed_band` 完全一致（相同輸入、相同輸出）。
- 校準項目資料結構新增門檻欄位，可查得到當次使用的 P33/P67 值。

**風險/回滾**：屬於邏輯重構，需以既有測試資料跑 diff 驗證新舊配對/標籤結果差異範圍；建議先在 staging 跑一次 drift report 對比新舊結果再上線。

---

### 任務 1.3 — 修復 Lead 廣告觀測標籤死碼（P0-3）

**問題**：`_resolve_observed_band()` 對 lead objective 找 `cvr`/`cpl`（`repository.py:154-170`），但 FB importer 的 `performance_snapshot`（`facebook_ads_importer.py:50-59`）完全沒有 `leads/cvr/cpl/cpa` 欄位，恆 miss 落到 ROAS 分支 → lead 廣告 `observed_band` 恆為 `low`，還會把 prompt 越校越保守。

**變更檔案**：
- `backend/modules/meta_andromeda/importers/facebook_ads_importer.py`
- `backend/modules/meta_andromeda/repository.py`（`_resolve_observed_band` lead 分支，約 154-215 行）

**實作步驟**：
1. importer 補抓 FB `actions` 欄位中的 `lead` / `onsite_conversion.lead_grouped`，計算 `leads` 數。
2. 在 `performance_snapshot` 新增 `leads`、`cvr = leads/clicks`、`cpl = spend/leads`、`cpa = spend/purchases`（分母為 0 時處理為 None，不可除以零）。
3. lead 的 CVR/CPL 判斷門檻改為 account-level 動態分位數（依賴任務 1.2 的統一門檻機制），移除寫死的 150/350 CPL 門檻與無幣別假設。
4. drift report payload 新增「各 objective_group 標籤指標覆蓋率」欄位（例如多少筆 lead 廣告實際有 cvr/cpl 可用），供監控面板使用。

**驗收標準**：
- 匯入含 lead 廣告的測試資料後，`performance_snapshot` 可見 `leads/cvr/cpl/cpa` 欄位。
- lead 廣告的 `observed_band` 不再恆為 `low`，能依實際 CVR/CPL 分布出現 high/mid/low 分布。
- drift report payload 可見 lead 覆蓋率指標。

**風險/回滾**：純新增欄位與判斷分支，不影響既有 ROAS-based objective 的行為；若 FB API 版本無 `actions` 欄位，需加防呆（欄位缺失時退回舊行為並記 warning，不 crash）。

---

### 任務 1.4 — 統一 Objective 路由規則，補齊 outcome_leads（P0-4）

**問題**：Runtime 端 `_OBJECTIVE_GROUP_MAP`（`runtime.py:21-55`）精確比對且缺 `outcome_leads`/`outcome_app_promotion`，未命中歸 `conversion`；Repository 端用子字串比對（`repository.py:42-52`, `repository.py:154`），`outcome_leads` 會命中 lead 分支。同一筆 `OUTCOME_LEADS` 廣告在預測端用轉換 prompt、觀測端用 lead 邏輯評分。

**變更檔案**：
- 新增共用模組（建議 `backend/modules/meta_andromeda/objective_routing.py` 或放入既有 `shared`/`utils`）
- `backend/modules/meta_andromeda/runtime.py`（移除本地 `_OBJECTIVE_GROUP_MAP`，改呼叫共用函式）
- `backend/modules/meta_andromeda/repository.py`（移除子字串比對，改呼叫共用函式）
- `backend/database/models/meta_andromeda.py`（`ObservedCreative`/`ScoreEvent.lineage` 新增 `objective_group` 欄位，若尚無）

**實作步驟**：
1. 建立單一 `resolve_objective_group(objective: str) -> str`：精確比對 + 明確別名表（含 `outcome_leads → lead`、`outcome_app_promotion` 明確歸類或獨立 `app` 群組），未知值記 log 並回傳 `unknown`（不再默默歸 conversion）。
2. runtime.py 與 repository.py 都改呼叫此共用函式，移除各自的路由邏輯。
3. 匯入資料時，把解析後的 `objective_group` 存進 `ObservedCreative` 與 `ScoreEvent.lineage`，後續統計一律讀存下來的值，不再即時重新解析（避免規則演進導致歷史資料重新分組、破壞可比較性）。

**驗收標準**：
- `OUTCOME_LEADS` 廣告的評分 prompt 與觀測標籤邏輯一致（都走 lead 分組）。
- 單元測試涵蓋 `resolve_objective_group()` 的所有已知 objective 值 + 一個未知值（應回傳 `unknown` 並記 log）。
- 既有 ObservedCreative 記錄的 `objective_group` 為匯入當下解析結果，不受後續規則變更影響。

**風險/回滾**：屬於路由邏輯集中化重構，需搭配任務 1.3 一起驗證 lead 相關資料流；建議先跑歷史資料的 diff 報告（新舊分組結果差異筆數），評估是否需要一次性回填。

---

### 任務 1.5 — 非轉換廣告排除/修正 Band 比對污染（P0-5）

**問題**：流量/互動/知名度/影片組的 prompt 明確要求 `roas_band = null`（正確設計），但 drift 與校準把 `pred.roas_band or "low"` 當預測值（`repository.py:1185`, `repository.py:1944`），導致模型「正確不出 band」被誤記為「預測 low」，污染 accuracy/MAE，甚至被選為校準 few-shot 錯例。

**變更檔案**：
- `backend/modules/meta_andromeda/repository.py`（drift band 比對約 1185 行，校準同步約 1944 行）

**實作步驟**：
1. 對 `roas_band_eligible = False` 的觀測項，band 比對改用同批 AI `overall_score` 的分位數（P33/P67）推導預測 band，或直接排除出 band accuracy 計算，只納入 Spearman 排名評估（二擇一，建議先採「排除 + 只算 Spearman」，實作成本低且語意正確）。
2. 校準資料集同步時排除「`pred_band` 缺失」的項目；若採用分位數推導方案，則標記 `band_source: score_derived` 以與真正的 roas_band 區分。

**驗收標準**：
- 流量/互動/知名度/影片組廣告不再出現在 band accuracy/MAE 的分母中（或明確標記為 `score_derived` 來源）。
- 校準資料集中不再出現「模型正確不出 band 卻被當錯例」的項目。

**風險/回滾**：純過濾/標記邏輯，不影響轉換類廣告既有行為；上線後對比新舊 accuracy 數字（預期轉換組不變、非轉換組樣本數下降）。

---

### 任務 1.6 — Release 機制與 Runtime 串接（P0-6，可視情況併入第 3 波）

**問題**：`perform_release_action`（`repository.py:1810-1886`）只操作 DB 記錄，實際 runtime 用哪個模型由 env `META_ANDROMEDA_SCORING_MODEL_VERSION` 決定，release 動作對評分行為零影響；`pairwise_ranking_accuracy`/`mean_band_error` 是 seed 假資料。

**變更檐案**：
- `backend/modules/meta_andromeda/model_registry.py`
- `backend/modules/meta_andromeda/repository.py`（release records 相關，約 386-441、1810-1886 行）

**實作步驟（本波先做最小可行版本，完整版見任務 1.6b／第 3 波）**：
1. 短期（本波）：在 UI／API 回傳中明確標示 release 工作台數字為「示範資料」，避免營運誤讀（對應報告建議 3）。
2. 完整落地（model registry 落 DB、`get_entry()` 讀 DB current_production、promote 後 runtime 真正切換、實算 pairwise ranking accuracy）排入第 3 波任務 3.2，因其依賴任務 1.2（統一配對）與任務 2.5（回測 gate）的資料基礎。

**驗收標準（本波）**：
- Release 工作台 UI/API 對假資料有清楚標示。

---

## 第 2 波：提升準確率（P1）

> 前置：第 1 波 P0-1~P0-5 完成，確保資料流乾淨後再進行統計層面優化。

### 任務 2.1 — Lineage 記錄實際使用的 Prompt Profile + 過濾 Heuristic Fallback（P1-2）

**問題**：`_load_scoring_profile()`（`runtime.py:270-278`）可能被 is_promoted profile 全域覆蓋，但 lineage 只記 `registry_entry.scoring_profile`（`runtime.py:617/901`），記錄與實際使用的 prompt 可能不同，導致「校準前後 ρ 有無變好」無法歸因。配對時也未過濾 `lineage.scoring_mode`（heuristic fallback 分數與 AI 分數混算）。

**變更檔案**：
- `backend/modules/meta_andromeda/runtime.py`（617、901 行附近，記錄 lineage 處）
- `backend/modules/meta_andromeda/repository.py`（drift/校準配對過濾條件）

**實作步驟**：
1. `runtime.py` 記錄 lineage 時，改記 `_load_scoring_profile()` 實際解析後使用的 profile row id/name（而非 registry 設定值）。
2. drift/校準配對預設過濾 `lineage.scoring_mode == "ai"`；drift payload 分開統計 heuristic fallback 占比（作為健康指標）。
3. drift report 增加 `origin` 維度切片（投放前預測 vs 事後補評），accuracy 分開呈現。

**驗收標準**：
- 觸發一次 is_promoted profile 覆蓋情境，lineage 記錄的 profile 與實際生成 prompt 所用的 profile 一致（可用測試斷言）。
- drift report 可見 heuristic fallback 占比與 origin 切片後的 accuracy。

---

### 任務 2.2 — 統計方法修正（P1-4）

**問題**：`_spearman_r()`（`repository.py:55-71`）無 tie 處理；分位數門檻樣本數下限過低（≥5 即啟用）且用有偏索引；`perf_is_high = median >= mean`（`repository.py:1246`）只反映分布偏態，與「表現好不好」無關，卻是象限診斷的基礎；ρ 門檻 0.30/0.10 無檢定支撐。

**變更檔案**：
- `backend/modules/meta_andromeda/repository.py`（`_spearman_r` 約 55-71 行；分位數計算；`perf_is_high` 約 1246 行；象限診斷約 100-140 行）

**實作步驟**：
1. `_spearman_r()` 改用 average rank 處理 tie（或直接採用 `scipy.stats.spearmanr` 若專案允許新增依賴）。
2. 分位數改用線性插值；動態門檻樣本下限由 5 上修至 20；不足時沿用上一期已持久化的門檻（依賴任務 1.2 的門檻持久化機制）。
3. `perf_is_high` 改為與可解釋基準比較：上一期同帳戶中位數 / 帳戶目標 ROAS / 近 90 天 rolling baseline（三選一或可設定，建議先做「上一期同帳戶中位數」，資料需求最低）。
4. drift 判定（healthy/warning/drifted）的 ρ 門檻附加最少樣本要求（如 n≥15 才允許判定為 drifted），樣本不足時標記為 `insufficient_sample`。

**驗收標準**：
- 單元測試：含大量同分項的資料集，`_spearman_r()` 結果與 scipy 的 `spearmanr`（忽略 p-value）一致。
- n<15 的帳戶不再出現 `drifted` 判定，改為 `insufficient_sample`。

---

### 任務 2.3 — 標籤穩健性：曝光門檻與窗口去重（P1-3）

**問題**：現況只排除 `spend <= 0`，小曝光廣告與大預算廣告同權重；同一 ad 可能在多個觀測窗口各存一筆 ObservedCreative，custom 窗口的區間重疊撈取會重複計算。

**變更檔案**：
- `backend/modules/meta_andromeda/repository.py`（drift 撈取與統計邏輯）
- `backend/modules/meta_andromeda/service.py`（`build_observed_creative_id` 相關，約 473-475 行）

**實作步驟**：
1. 標籤納入最低門檻：`impressions >= 1000` 或 `spend >= account 日均 spend 的 x%`（可設定），不足者標記 `insufficient_delivery`，排除於 accuracy 計算但保留展示。
2. 加入觀測成熟度概念：投放未滿 N 天的觀測標記 `immature`，不進校準集。
3. 同一 `ad_id` 在同一份 drift report 內去重（取窗口最長或 spend 最大的一筆），或改為 spend 加權統計。
4. Spearman 計算加入 spend 加權版本（可作為額外指標，不取代原始 ρ）。

**驗收標準**：
- 模擬同一 ad 有 last_7d/last_30d/lifetime 三筆觀測的情境，drift report 統計結果不重複計入該 ad。
- 低曝光（如 impressions=50）廣告在 accuracy 計算中被排除或明確標記。

---

### 任務 2.4 — 校準 Few-shot 與 Guidance 品質提升（P1-5）

**問題**：few-shot 只有 headline 文字 + band 對錯（`calibration_pipeline.py:109-124`），無圖像佐證；lesson 固定文案無資訊量；只取 error 最大 3 筆、不分 objective_group；`MIN_ITEMS_FOR_CALIBRATION = 10` 全為錯例，無對照組。

**變更檔案**：
- `backend/modules/meta_andromeda/calibration_pipeline.py`
- `backend/modules/meta_andromeda/repository.py`（`sync_calibration_dataset`，收錄範圍調整）

**實作步驟**：
1. few-shot 訊息附上素材縮圖（data URI 多模態 few-shot），並帶模型當時分項評語 vs 實際成效指標值。
2. 錯例與對例混合，per objective_group 分開挑選與注入（沿用 runtime 既有 objective_profiles 結構）。
3. guidance 由固定模板升級為依 confusion matrix 生成的具體規則（可用一次 LLM 呼叫做 error clustering 摘要，取代 `_BIAS_GUIDANCE` 三選一模板）。
4. `sync_calibration_dataset` 同時收錄 `error=0` 的正確配對項目（作為對照組/回測 holdout），不再只收 `err>0`。

**驗收標準**：
- 校準資料集中同時存在錯例與對例，且依 objective_group 分類可查詢。
- few-shot payload 中可見圖像 data URI 與具體錯誤模式描述（非固定文案）。

---

### 任務 2.5 — 校準 Profile 回測 Gate 與 Promote 後追蹤（P1-6）

**問題**：`promote_scoring_profile()`（`repository.py:2095-2121`）一鍵全域生效，無前置評估，promote 後也無驗證機制。此任務依賴任務 2.4 的對照組資料才可執行。

**變更檔案**：
- `backend/modules/meta_andromeda/repository.py`（`promote_scoring_profile` 及周邊）
- `backend/modules/meta_andromeda/calibration_pipeline.py`
- `backend/core/scheduler.py`（若追蹤機制需排程）

**實作步驟**：
1. Promote 前：自動用新 profile 重評 holdout 集（校準資料集中保留 20-30% 不進 few-shot 的項目 + `error=0` 對照項），比較新舊 profile 的 band accuracy / ranking accuracy；達標（accuracy 提升且 ρ 不劣化）才開放 promote 按鈕；結果寫入 profile 的 `bias_summary`。
2. Promote 後：下一期 drift report 自動與 promote 前基線比較，連續 2 期劣化自動降級（un-promote）並通知（通知管道沿用既有機制，如有）。
3. 這組實測數字回填 release record 的 `pairwise_ranking_accuracy` / `mean_band_error`，供任務 1.6 完整版（第 3 波）使用。

**驗收標準**：
- 新 profile 未通過 holdout 回測時，promote API 拒絕或需明確覆寫旗標。
- 連續 2 期劣化情境下，系統自動 un-promote 並可在記錄中查到原因。

---

## 第 3 波：結構升級與自動化（P2、含 P1-1、P0-6 完整版）

> 前置：第 2 波完成，統計層面可信後再投入結構性升級（工作量較大，建議依序而非併行）。

### 任務 3.1 — 兩段式評分：數值化 Breakdown + 統計校準層（P1-1，最大槓桿）

**變更檔案**：`runtime.py`（prompt 與輸出 schema）、新增校準統計模型模組、`calibration_pipeline.py`

**實作步驟**：
1. 把 `diagnostic_breakdown` 從四段中文評語改為數值子分數（visual_appeal / copywriting / cta_clarity / relevance 各 0-100 + 一句理由），保留 risk_tags。
2. 用既有 CalibrationItem（子分數 × observed_band）訓練 per-account（不足時 global）的 ordinal logistic / isotonic 校準層，輸出 band 與經驗校準機率。
3. `confidence` 改由統計層輸出機率，取代現況 `runtime.py:511-527` 手寫公式。

**驗收標準**：band accuracy / ranking accuracy 可用回歸測試量化追蹤；confidence 分桶後的實際命中率接近其宣稱值（誤差 < 10 個百分點）。

### 任務 3.2 — Model Registry 落 DB + Release 實算指標（P0-6 完整版）

**實作步驟**：
1. Model registry 落地到 DB（擴充既有 release records 表），`get_entry()` 讀 DB current_production；approve 後 runtime 真正切換模型；env 覆寫保留為 ops escape hatch。
2. 以 drift report 配對資料實算 pairwise ranking accuracy 與 mean band error，寫回 release record，promotion gate 由真實數字驅動。

### 任務 3.3 — 其餘 P2 項目（可獨立排期，依優先序）

| 項目 | 摘要 | 主要檔案 |
|------|------|------|
| P2-1 | 影片素材抽 keyframes 多圖傳入；未實作前標記 `video_content_not_inspected` 並顯著調降 confidence | `runtime.py` |
| P2-2 | 改用 `response_format: json_schema`；高價值請求 self-consistency（3 次取樣取中位數） | `runtime.py` |
| P2-3 | Registry 落 DB 後按情境分層選模型（互動用快模型、回測用強模型），provider_model 綁定實測 ρ/accuracy 展示 | `model_registry.py` |
| P2-4 | Confidence 經驗校準：定期按分桶計算實際命中率，擬合 calibration mapping | `runtime.py` |
| P2-5 | 人工回饋 reason_codes 納入偏差分析；分歧樣本自動進校準候選；review queue 顯示事後 observed_band | `repository.py` |
| P2-6 | 每帳戶每週排程：drift report → 校準資料集 sync → 校準管線 → 待 promote | `scheduler.py` |
| P2-7 | prompt cache 加 TTL + promote 時 Redis pub/sub 失效通知；is_promoted 改為 per base-profile 而非全域唯一 | `runtime.py` |
| P2-8 | 同素材跨窗口重複補評：link 條件放寬為「同 asset、AI 模式、completed 最新評分」 | `service.py` |

---

## 附錄：關鍵檔案索引（沿用 docs/19）

| 檔案 | 角色 |
|------|------|
| `backend/modules/meta_andromeda/runtime.py` | 評分 runtime：prompt 組裝、多模態、confidence、fallback |
| `backend/modules/meta_andromeda/model_registry.py` | 寫死的模型註冊表 + env 覆寫 |
| `backend/modules/meta_andromeda/calibration_pipeline.py` | 偏差分析與校準 profile 生成 |
| `backend/modules/meta_andromeda/repository.py` | 配對、標籤（`_resolve_observed_band`）、drift report、校準集同步、release |
| `backend/modules/meta_andromeda/service.py` | 觀測匯入、自動補評、校準 job 觸發（`sync_calibration_dataset`） |
| `backend/modules/meta_andromeda/importers/facebook_ads_importer.py` | FB 成效快照欄位定義 |
| `backend/core/scheduler.py` | 評分 job、校準 job（`run_meta_andromeda_calibration_pipeline`） |
| `backend/database/models/meta_andromeda.py` | ScoreEvent / ObservedCreative / CalibrationDataset / ScoringProfile 等 ORM |
