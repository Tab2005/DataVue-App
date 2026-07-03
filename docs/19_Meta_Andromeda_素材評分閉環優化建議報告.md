# 19. Meta Andromeda 素材評分機制與閉環優化建議報告

- **日期**：2026-07-03
- **性質**：純分析報告，未修改任何程式碼
- **範圍**：`backend/modules/meta_andromeda`（runtime / model_registry / calibration_pipeline / repository / service / importers）、`backend/core/scheduler.py` 相關 job、`backend/database/models/meta_andromeda.py`
- **相關前文**：docs/15（Prompt 自適應校準計畫）、docs/16（廣告目標分類與指標路由計畫）、docs/17（Phase 3 學習閉環實作成果）、docs/18（模組功能審查與優化報告）

---

## 一、現況架構總覽

### 1.1 模型機制（預測端）

```
Score Lab 上傳 / 觀測匯入
        │
        ▼
ScoreEvent (queued) ──► 佇列 (apscheduler / db_queue / redis_stream / external_webhook)
        │
        ▼
MetaAndromedaRuntimeAdapter.generate_score_result()   runtime.py:965
        │
        ├─ model_registry.get_entry()                 model_registry.py:71（程式碼寫死的 5 個版本 + env 覆寫）
        ├─ _load_scoring_profile()                    runtime.py:261（DB is_promoted profile → 具名 profile → 寫死 fallback prompt）
        ├─ _resolve_objective_group()                 runtime.py:52（objective → conversion/lead/traffic/awareness/video/engagement）
        ├─ _resolve_active_profile()                  runtime.py:316（DB objective_profiles → 寫死 _DEFAULT_OBJECTIVE_PROFILES → base）
        │
        ├─ OpenRouterScoringProvider.score()          runtime.py:641
        │     · prompt = template + calibration_guidance + few-shot
        │     · 多模態：image 以 public URL 或 base64 data URI 附上（video 不附任何內容）
        │     · temperature 0.2、max_tokens 8192、重試 3 次、regex 修復 JSON
        │     · 輸出：overall_score(0-100)、roas_band(high/mid/low/null)、
        │       diagnostic_breakdown(4 項文字)、drivers、risk_tags、summary
        │
        └─ 失敗 → HeuristicScoringProvider fallback   runtime.py:736（規則加減分，score 24–88）
```

### 1.2 閉環機制（回饋端）

```
(1) FB Ads 觀測匯入        importers/facebook_ads_importer.py
      ad-level insights → performance_snapshot{spend, impressions, clicks,
      purchases, purchase_value, roas, ctr, cpc} → ObservedCreative
      └─ 有素材 → 優先 link 既有 Score Lab 預評，否則自動補評分  service.py:691

(2) Drift Report（手動觸發） repository.create_drift_report()  repository.py:1051
      ObservedCreative ↔ ScoreEvent 配對（checksum → asset_uri）
      → 動態 P33/P67 門檻算 observed_band → accuracy / MAE / Spearman ρ
      → 象限診斷（市場護航/創意突圍/雙重有利/全面檢視）

(3) 校準資料集（手動觸發）  repository.sync_calibration_dataset()  repository.py:1888
      配對後取「band 有偏差」的項目 → CalibrationDataset/Items
      → synced_count ≥ 10 自動排 calibration job                 service.py:1444

(4) 校準管線                calibration_pipeline.generate_calibrated_profile()
      偏差方向分析（over/under/mixed）→ 產生新 ScoringProfile
      （base prompt + calibration_guidance + 3 筆 worst few-shot）

(5) 人工採納                POST /monitoring/scoring-profiles/{name}/promote
      is_promoted=True → runtime 下次評分全域改用該 profile

(6) 人工回饋                POST /scores/{id}/feedback（approve/revise/reject + reason_codes）

(7) Release 工作台          approve / reject / rollback（只改 DB 記錄）
```

---

## 二、閉環斷點盤點（P0：不修，閉環實際上不成立）

### P0-1. 自動校準管線因參數錯誤「從未真正執行」

- `service.py:1448` 把 **模型版本** `settings.META_ANDROMEDA_SCORING_MODEL_VERSION`（預設 `cand_v2026_06_05_a`）當成 `base_profile_name` 傳給校準 job。
- `calibration_pipeline.py:139-149` 卻用它去查 `MetaAndromedaScoringProfile.profile_name`。模型版本（`cand_v2026_06_05_a`）與 profile 名稱（`creative_scoring_v2`）是兩個不同命名空間。
- 更根本的：**資料庫沒有任何 seed 的基礎 ScoringProfile**——profile 只會由校準管線本身建立（雞生蛋）。因此 `base_profile is None` → 永遠 `return None`，只在 log 留一行 warning。
- **結果**：Drift → 校準資料集 → 自動產生校準 Profile 這條主閉環，目前實際產出恆為零。前面步驟（資料集、偏差分析）都在做工，最後一步靜默失敗。

**建議**：
1. 建立 migration / 啟動 seed：把 `runtime.py` 的 `_FALLBACK_USER_PROMPT_TEMPLATE`、`_FALLBACK_SYSTEM_PROMPT` 與 `_DEFAULT_OBJECTIVE_PROFILES` 寫入 DB 成為 `creative_scoring_v1` 基礎 profile（single source of truth 移到 DB，程式碼保留為最後 fallback）。
2. `sync_calibration_dataset` 改傳 `model_registry.get_entry().scoring_profile`（或目前 promoted profile 的名稱），不要傳模型版本。
3. 校準 job 失敗/跳過時把狀態寫回 `CalibrationDataset.status`（如 `calibration_failed:base_profile_missing`），讓前端看得到，不要只留 log。

### P0-2. Drift 與校準兩套標籤政策不一致（同一筆資料兩種 observed_band）

- Drift report 用**動態 P33/P67 門檻**（ROAS 排除流量廣告、CTR/CPC 只看流量廣告；`repository.py:1088-1135`）。
- `sync_calibration_dataset` 呼叫 `_resolve_observed_band(obs.objective, obs.performance_snapshot)`（`repository.py:1942`）**不傳任何門檻** → 走固定 fallback（ROAS 3.0/6.0；流量廣告因無 CTR/CPC 門檻一律標 `low`）。
- 兩處都標 `LABEL_POLICY_VERSION = "ma_label_policy_v1"`，版本號無法區分實際不同的標籤規則。
- 配對邏輯也不一致：drift 先用 `asset.checksum_sha256` 再退 `asset_uri`（`repository.py:1141-1170`），校準只用 `asset_uri`（`repository.py:1928-1936`）→ 校準資料集配對率必然低於 drift report，且兩邊樣本集合不同。

**建議**：
1. 抽出共用的 `match_observed_to_prediction()` 與 `label_observed_band()`，drift 與校準走同一條路。
2. 門檻不要每批重算後即丟：把每次計算出的 P33/P67 門檻**持久化為 account-level label policy**（含生效區間與樣本數），校準與 drift 引用同一份；門檻變更時 bump `LABEL_POLICY_VERSION`。
3. 校準項目寫入時記錄使用的門檻值（drift 已在 `report_payload.roas_band_thresholds` 記了，校準項沒有）。

### P0-3. Lead 廣告的觀測標籤整條是死碼，一律標 low

- `_resolve_observed_band` 對 lead objective 依序找 `cvr` → `cpl`（`repository.py:154-170`），找不到再走 ROAS/CPA。
- 但 FB importer 的 `performance_snapshot` 只有 `spend / impressions / clicks / purchases / purchase_value / roas / ctr / cpc`（`facebook_ads_importer.py:50-59`）——**沒有 leads、cvr、cpl、cpa 任何一個欄位**。
- 結果：lead 廣告的 CVR/CPL 分支永遠 miss，落到 ROAS 分支；lead 廣告 ROAS 通常為 0 → **observed_band 恆為 low**。模型對 lead 素材再準也會被判「高估」，這類樣本進校準資料集後會把 prompt 越校越保守。
- CPA 分支（`repository.py:208-215`）同樣是死碼。CPL 門檻 150/350 也寫死且無幣別概念。

**建議**：
1. importer 補抓 `actions`（lead / onsite_conversion.lead_grouped）、算 `cvr = leads/clicks`、`cpl = spend/leads`、`cpa = spend/purchases`，寫入 snapshot。
2. lead 的門檻同樣改為 account-level 動態分位數（與 P0-2 統一），幣別敏感的 CPL/CPA 不應使用全域固定值。
3. 在 drift report payload 增加「各 objective_group 的標籤指標覆蓋率」（多少筆 lead 廣告實際有 cvr/cpl 可用），讓死碼問題以後能在監控面板直接暴露。

### P0-4. 兩套 objective 路由規則不一致，OUTCOME_LEADS 會被拆成兩半

- Runtime 端：`_OBJECTIVE_GROUP_MAP` 精確比對（`runtime.py:21-55`），**缺 `outcome_leads`、`outcome_app_promotion`**，未命中一律歸 `conversion`。
- Repository 端：`_TRAFFIC_OBJECTIVE_TOKENS` 用**子字串**比對（`repository.py:42-52`），lead 判斷用 `"lead" in objective_key`（`repository.py:154`），`outcome_leads` 會命中。
- 結果：FB 標準 objective `OUTCOME_LEADS` 的廣告——**評分時用轉換（ROAS）prompt 打分與出 band，貼標籤時卻用 lead（CVR/CPL）邏輯**（又因 P0-3 退化成 ROAS→low）。同一筆資料在預測端與觀測端被當成兩種廣告。
- 子字串比對本身也有誤傷風險（任何含 "reach"、"video" 的自訂命名都會被吸進流量組）。

**建議**：
1. 收斂成**單一** `resolve_objective_group()`（放 shared util），runtime 與 repository 共用；用精確比對 + 明確的別名表，未知值記 log 並歸入 `unknown` 而非默默歸 conversion。
2. 補齊 `outcome_leads → lead`、`outcome_app_promotion →`（建議新增 `app` 群組或先歸 conversion 但要有 log）。
3. 匯入時就把解析後的 `objective_group` 存進 ObservedCreative 與 ScoreEvent.lineage，之後所有統計用存下來的群組，不再重新解析（避免規則演進造成歷史資料重新分組）。

### P0-5. 非轉換廣告的 band 比對無意義，卻在污染 accuracy/MAE 與校準集

- 流量/互動/知名度/影片組的 prompt 明確要求 `roas_band = null`（正確設計），但 drift 與校準把 `pred.roas_band or "low"` 當預測值（`repository.py:1185`、`repository.py:1944`）。
- 結果：模型**正確地**不出 band 的廣告，被記成「預測 low」，再跟 CTR/CPC 動態 band 比對 → accuracy/MAE 失真；err>0 的會進校準資料集、甚至被選為 few-shot「錯例」教材。

**建議**：
1. 對 `roas_band_eligible = False` 的觀測項，band 比對應改用 **overall_score 的分位數推導預測 band**（例如同批 AI 分數的 P33/P67 切三段），或干脆排除出 band accuracy，只納入 Spearman 排名評估。
2. 校準資料集同步時排除「pred_band 缺失」的項目，或以獨立的 `band_source: score_derived` 標記。

### P0-6. Release 機制與 runtime 完全脫鉤（目前是展示品）

- `perform_release_action`（`repository.py:1810-1886`）approve/rollback 只是在三筆 DB 記錄間搬字串；**runtime 實際用哪個模型由 env `META_ANDROMEDA_SCORING_MODEL_VERSION` + 寫死在程式碼的 `model_registry` 決定**（`model_registry.py:22-69`），release 動作對評分行為零影響。
- Release records 的 `pairwise_ranking_accuracy`、`mean_band_error` 是 seed 假資料（`repository.py:386-441`），promotion gate summary 也是寫死的，系統從未計算過這些指標。

**建議**：
1. Model registry 落地到 DB（表已有 release records 可擴充），`get_entry()` 讀 DB 的 current_production；approve 後 runtime 真正切換。env 覆寫保留為 ops escape hatch。
2. 以 drift report 的配對資料**實算** pairwise ranking accuracy 與 mean band error，寫回 release record，promotion gate 由真實數字驅動（詳見 P1-6）。
3. 若短期不打算做真切換，建議在 UI 明確標示「示範資料」，避免營運誤讀。

---

## 三、預測準確率優化（P1：提升評分與觀測的對齊品質）

### P1-1. 兩段式評分：LLM 當特徵抽取器 + 統計校準層（最大槓桿）

現況是「LLM 一次到位直接輸出 band + 0-100 整數分」，準確率天花板受限於：LLM 對特定帳戶/市場的成效分布沒有先驗、輸出分數聚集在少數整數、prompt 校準只能靠文字指令間接影響。

建議演進為兩段式：

1. **LLM 只負責可觀察的創意特徵**：把 `diagnostic_breakdown` 從四段中文評語改成**數值子分數**（如 visual_appeal / copywriting / cta_clarity / relevance 各 0-100 + 一句理由），並保留 risk_tags。
2. **band 預測交給輕量統計模型**：用既有 CalibrationItem（prediction 子分數 × observed_band）訓練 per-account（資料不足時 global）的 ordinal logistic / isotonic 校準層，輸出 band 與**經驗校準的機率**。
3. 好處：
   - 校準從「改 prompt 求 LLM 聽話」變成「直接擬合資料」，收斂快且可量化（AUC / ranking accuracy 可直接回歸測試）。
   - `confidence` 不再是手寫公式（現況 `runtime.py:511-527` 的 0.42/0.58 base + completeness 加權），而是有統計意義的機率。
   - LLM prompt 的角色簡化，對 P0-1 的 prompt 校準依賴度下降。

### P1-2. 評估與校準樣本的「純度」控制

目前 drift/校準配對時對 ScoreEvent 只過濾 `status == "completed"`，不看：

- `lineage.scoring_mode`：heuristic fallback 的分數（規則加減分）與 AI 分數混在同一池被評估與校準。
- `lineage.registry_model_version` / prompt profile：不同模型版本、不同 prompt 版本的分數混算，校準前後根本無法歸因。
- `request_context.origin`：Score Lab「投放前預測」與觀測匯入後的「事後補評」混在一起。事後補評的素材已在投放（雖然模型看不到成效數據），嚴格說不是預測。

**建議**：
1. 配對時預設過濾 `scoring_mode == "ai"`；drift payload 分開統計 fallback 占比（本身就是重要健康指標）。
2. **在 lineage 記錄實際使用的 prompt profile row id/name**。現況 `runtime.py:617/901` 只記 `registry_entry.scoring_profile`，但 `_load_scoring_profile`（`runtime.py:270-278`）會被 is_promoted profile 全域覆蓋——記錄與實際用的 prompt 可能不同，這會讓「校準 profile 上線前後 ρ 有沒有變好」永遠算不清。
3. drift report 增加 `origin` 維度切片：投放前預測 vs 事後補評的 accuracy 分開看，前者才是產品宣稱的能力。

### P1-3. 標籤穩健性：最低樣本門檻與觀測窗口去重

- 現況只排除 `spend <= 0`；spend 1 元、impressions 50 的廣告與 spend 十萬的廣告同權重。小曝光量的 ROAS/CTR 噪音極大。
- 同一 ad 可以在 last_7d / last_30d / lifetime 三種窗口各存在一筆 ObservedCreative（`build_observed_creative_id` 含窗口種類與匯入日期，`service.py:473-475`），custom 窗口的 drift report 用區間重疊撈取（`repository.py:1062-1068`）會把同一素材算多次。

**建議**：
1. 標籤納入門檻：`impressions ≥ 1000` 或 `spend ≥ account 日均 spend 的 x%`（可設定），不足者標 `insufficient_delivery` 排除於 accuracy，但保留展示。
2. 加入**觀測成熟度**概念：投放未滿 N 天（學習期）的觀測標記為 immature，不進校準集。
3. 同一 `ad_id` 在同一份 drift report 內去重（取窗口最長或 spend 最大的一筆），或以 spend 加權統計。
4. Spearman 考慮 spend 加權版本，讓大預算素材的排序對齊更重要。

### P1-4. 統計方法修正

- `_spearman_r`（`repository.py:55-71`）**沒有 tie 處理**：排序位置直接當 rank。LLM 分數大量同分（65/70/75 聚集）時，同分項的 rank 由排序穩定性隨機決定，ρ 會系統性失真——而 ρ 是 drift 判定（healthy/warning/drifted）的主判據。→ 改用 average rank（或 scipy 的 spearmanr 演算法）。
- 分位數 `int(len*0.33)` 是有偏索引，樣本 ≥5 就啟用動態門檻太激進（5 筆資料的 P33/P67 幾乎是隨機數）。→ 使用線性插值分位數，門檻樣本下修建議至 ≥20，不足時沿用上一期已持久化的門檻（配合 P0-2）。
- `perf_is_high = median >= mean`（`repository.py:1246`）只是分布偏態的指標，**與「表現好不好」無關**（右偏分布永遠判 False），而象限診斷（市場護航/創意突圍等，`repository.py:100-140`）整個建立在它上面。→ 改為與可解釋的基準比較：上一期同帳戶中位數、帳戶目標 ROAS、或近 90 天 rolling baseline。
- ρ 門檻 0.30/0.10 無檢定：n=6 時 ρ=0.35 毫無意義。→ 附 permutation p-value 或最少樣本要求（如 n≥15 才允許判 drifted）。

### P1-5. 校準 few-shot 與 guidance 品質

現況（`calibration_pipeline.py:109-124`）：
- few-shot 只有 headline 文字 + band 對錯，**沒有圖像**——但模型主要靠圖像評分，教材缺主要證據。
- Lesson 一律是 "Be more careful when evaluating similar creatives"，無資訊量。
- 只取 error 最大 3 筆（全是錯例、可能全是同方向），不分 objective_group；guidance 是三選一的全域模板（`_BIAS_GUIDANCE`）。

**建議**：
1. few-shot 附上素材縮圖（多模態 few-shot：以 data URI 塞入 messages），並帶「模型當時的分項評語 vs 實際成效指標值」。
2. 錯例與**對例**混合（校準不只是修正，也要固定住做對的判斷）；per objective_group 分開挑選與注入（runtime 已有 objective_profiles 結構可放）。
3. guidance 由模板升級為依 confusion matrix 生成的具體規則（例如「high→mid 的錯誤集中在『多人物、文字覆蓋率高』的素材」），可用一次 LLM 呼叫做 error clustering 摘要。
4. `MIN_ITEMS_FOR_CALIBRATION = 10` 偏低，且這 10 筆全是「錯例」（sync 只收 err>0）。建議資料集同時收錄配對正確的項目（`error=0`）供對照組與回測使用（現況正確項完全不入庫，P1-6 的回測就沒有 holdout 可用）。

### P1-6. 校準 profile 的回測 gate 與自動 rollback（閉環的「驗證」環節目前缺席）

現況：校準 profile 產生後，`promote_scoring_profile`（`repository.py:2095-2121`）一鍵全域生效，**沒有任何前置評估**；promote 後也沒有機制驗證新 prompt 是否真的變好。

**建議**：
1. **Promote 前**：自動用新 profile 重評 holdout 集（校準資料集中保留 20-30% 不進 few-shot 的項目 + error=0 的對照項），比較新舊 profile 的 band accuracy / ranking accuracy，達標（如 accuracy 提升且不劣化 ρ）才開放 promote 按鈕；結果寫入 profile 的 `bias_summary`。
2. **Promote 後**：下一期 drift report 自動與 promote 前基線比較，連續 2 期劣化自動降級（un-promote）並通知。
3. 這組數字同時回填 release record 的 `pairwise_ranking_accuracy` / `mean_band_error`，讓 P0-6 的 release gate 有真資料可用。

---

## 四、模型機制強化（P1~P2）

### P2-1. 影片素材目前是「盲評」

`_build_multimodal_user_content`（`runtime.py:489-493`)只在 `asset_type == "image"` 時附視覺內容；video 組的 prompt 要求評 hook/pacing，但模型只看得到 headline/primary_text。→ 建議抽 keyframes（如 0s/2s/5s 三幀）以多圖傳入；未實作前，video 評分應在結果標記 `video_content_not_inspected` risk tag，confidence 顯著下調（現況 completeness 的 `image_signal` 對 video 永遠是 0，但只降 ~0.03-0.06，遠不足以反映「沒看過內容」）。

### P2-2. 輸出穩定性：structured outputs 與 self-consistency

- JSON 目前靠 regex 抽取 + 截斷修復（`runtime.py:391-447`），行為脆弱。OpenRouter 支援 `response_format: json_schema`（多數模型），建議優先使用，失敗再退 regex。
- 單次取樣 temperature 0.2 仍有 run-to-run 方差；對高價值請求（觀測補評、回測）可用 3 次取樣取中位數（self-consistency），對互動式 Score Lab 保持單次以控成本。
- 分數聚集問題：可要求「先各分項 0-25 再加總」或輸出兩位小數，展開分布、改善排名解析度（直接受益於 Spearman 與 P1-1 校準層）。

### P2-3. 模型選型分層

Registry 目前所有 AI 版本都指向 `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`（`model_registry.py`）：免費層有嚴格限流（現有 429 重試邏輯即為此而生）、視覺理解能力有限、reasoning 模型輸出還需剝 `<think>`。建議：
1. Registry 落 DB 後，按情境分層：互動評分用快而便宜的多模態模型，回測/校準基準用較強模型並比較兩者與實際成效的 ρ，數據說話。
2. 至少將 provider_model 與其實測 ρ/accuracy 綁定展示在 Release 工作台，選型有依據。

### P2-4. Confidence 經驗校準

現況公式（base 0.58 + completeness*0.24 + multimodal 0.06，`runtime.py:511-527`）輸出的 0.7 不代表 70% 正確率。有了配對資料後，定期按 confidence 分桶計算實際 band 命中率，擬合簡單的 calibration mapping（或直接由 P1-1 的統計層輸出機率取代）。前端顯示的 confidence 應該「說到做到」。

---

## 五、閉環流程完善（P2）

### P2-5. 人工回饋（feedback）目前是死水

`submit_feedback`（`repository.py:1781-1808`）存下 approve/revise/reject 與 reason_codes 後，沒有任何下游使用。建議：
1. reason_codes 納入 drift/偏差分析（reviewer 說 hook_soft 的素材是否真的表現差？→ 驗證 reviewer 與模型誰準）。
2. reject + 高分（或 approve + 低分）的分歧樣本自動進校準候選（人工弱標籤），與成效標籤並行但分開權重。
3. 在 review queue 顯示該素材事後的 observed_band，讓 reviewer 回饋形成「人 vs 模型 vs 市場」三方對照。

### P2-6. 閉環自動化排程

Drift report 與 calibration sync 目前全靠手動 API 觸發（`router.py:248/389`）。建議每帳戶每週排程：自動產 drift report → `drift_status != healthy` 時自動 sync 校準資料集 → 校準管線（P0-1 修復後）→ 產出 profile 待人工（或 gate 通過後自動）promote。人只需要看儀表板與按 promote，閉環頻率從「有人想到才轉」變成穩定節拍。

### P2-7. 多進程 prompt cache 失效

`invalidate_prompt_cache`（`runtime.py:368-375`）只清本進程記憶體快取；multi-worker 部署下 promote 後其他 worker 仍用舊 prompt 直到重啟（專案剛把 import 併發移到 Redis，方向一致）。建議：cache 加 TTL（如 5 分鐘）作為底線 + promote 時發 Redis pub/sub 失效通知。另外 `_load_scoring_profile` 的「is_promoted 優先於具名 profile」是全域覆蓋設計，若未來 registry 有多個 profile 並存，會互相踩踏——promoted 狀態應該 per base-profile 而非全域唯一。

### P2-8. 同素材跨窗口重複補評

`create_and_enqueue_score_event_for_observation`（`service.py:704-733`）只 link `observed_creative_id IS NULL` 的既有評分；同一素材第二個觀測窗口匯入時會再建一筆新評分（成本 + 同素材多分數影響配對）。建議 link 條件放寬為「同 asset、AI 模式、completed 的最新評分」，以 lineage 陣列記錄多個 observation 關聯。

---

## 六、建議實施順序

| 階段 | 項目 | 內容 | 效益 |
|------|------|------|------|
| **第 1 波（修斷點）** | P0-1 | seed 基礎 profile + 修 base_profile_name 傳參 | 自動校準閉環開始真正運轉 |
| | P0-2 | 統一配對與標籤函式、門檻持久化 | drift 與校準看同一份事實 |
| | P0-3 | importer 補 leads/cvr/cpl/cpa | lead 廣告標籤從恆 low 變可用 |
| | P0-4 | 單一 objective 路由 + 補 outcome_leads | 預測端與觀測端同一分組 |
| | P0-5 | 非轉換廣告改 score 分位數推 band 或排除 | accuracy/校準集去污染 |
| **第 2 波（提準確率）** | P1-2 | lineage 記實際 prompt profile、過濾 heuristic | 校準效果可歸因 |
| | P1-4 | Spearman tie 修正、門檻樣本數、perf 基準 | drift 判定可信 |
| | P1-3 | 曝光門檻、窗口去重、成熟度 | 標籤降噪 |
| | P1-5 | 多模態 few-shot、正例對照、分 objective | prompt 校準有效性 |
| | P1-6 | 校準回測 gate + promote 後追蹤 | 閉環有「驗證」環節 |
| **第 3 波（結構升級）** | P1-1 | 數值化 breakdown + 統計校準層 | 準確率最大單一槓桿 |
| | P0-6 | registry 落 DB、release 實算指標 | 發佈治理閉環 |
| | P2-1~P2-8 | 影片 keyframes、structured output、feedback 活用、排程化、cache 失效 | 穩健性與自動化 |

---

## 七、關鍵檔案索引

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
