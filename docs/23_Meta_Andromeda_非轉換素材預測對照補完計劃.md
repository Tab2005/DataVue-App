# Meta Andromeda 非轉換素材（曝光/流量）預測對照補完計劃

日期：2026-07-07
狀態：規劃完成，待核准後實作

## 1. 問題確認

已對照程式碼驗證：**曝光（awareness）、流量（traffic）、影片觀看（video）、互動（engagement）四類目標的素材，目前無法在「已評估素材」明細頁做「預測 vs 實際」的詳細成效對照，只有轉換（conversion）與名單（lead）兩類可以。**

根因鏈：

1. `backend/modules/meta_andromeda/runtime.py` 的 `_DEFAULT_OBJECTIVE_PROFILES`，對 `traffic`/`awareness`/`video`/`engagement` 四組的 prompt 明確要求「Set roas_band to null」，且 `"roas_band_eligible": False`（第 160/178、190/209、221/239、251/269 行）。這是**刻意設計**（docs/19 第 121 行記載「正確設計」）——這四類目標本來就不該用 ROAS 邏輯評分，模型只輸出 `overall_score`，不輸出任何 high/mid/low 的可比對預測。
2. 觀測（實際成效）端反而做得完整：`labeling.py` 的 `compute_label_thresholds`/`label_observed_band` 對這四組會用 CTR/CPC 算動態 P33/P67 門檻，產出真正的 `observed_band`。這部分沒問題，不需要改。
3. 比對環節（`repository.py:951-990` `get_review_queue_detail`，對應前端 `MetaAndromedaReviewQueue.jsx:571-626` 的「✅ 實際成效對照」卡片）：因為預測端 `roas_band` 恆為 `null`，`prediction_band = None`、`error = None`。詳情頁顯示「預測：--」「實際：high/mid/low」「誤差：--」，看得到實際成效，但沒有對應預測可以比對準確度。
4. 同樣的 gate 也擋在 `sync_calibration_dataset`（`repository.py:2349-2354`，`if not pred_roas_eligible or pred.roas_band is None: skipped_not_band_eligible += 1; continue`）與 `create_drift_report` 的 accuracy/MAE 計算（`repository.py:1294-1298`）——這四組素材完全不會進入校準集、few-shot 教材、holdout backtest。

這不是三波修復（docs/19+20）遺漏的 bug——原本 P0-5 問題是「null 預測被誤當成 low 硬比對，污染 accuracy/MAE」，wave 1 已修正為「不比對、直接排除」，這是當時正確的修法。但修完後的結果就是：曝光/流量素材在**個別素材層級**架構上就是沒有可比對的預測，只有整批次的 Spearman 相關性分析（`repository.py:1369-1387`，overall_score vs CTR/CPC 觀測值）還能看整體趨勢。

## 2. 目標

讓 `traffic`/`awareness`/`video`/`engagement` 四類目標的素材，也能在素材評估明細頁看到「預測 vs 實際」的逐筆成效對照，並自動享有既有的校準集、few-shot 教材、holdout backtest、drift accuracy/MAE 等下游機制（這些機制本身已是通用邏輯，不需要重寫）。

## 3. 方案評估

### 方案 A（建議）：讓模型對這四類目標也輸出一個真正可比對的預測 band

比照 `lead` 目標既有的作法——`lead` 組本來就複用 `roas_band` 欄位語意，改稱「LEAD QUALITY BAND」（`runtime.py:130-133`）。同樣手法套用到其餘四組：

- `traffic` → CTR 潛力 band
- `awareness` → 品牌記憶度/觸及效率 band
- `video` → VTR（觀看完成度）潛力 band
- `engagement` → 互動率潛力 band

**優點**：
- 是真正的模型判斷，不是事後湊出來的代理指標。
- 沿用 `lead` 的既有設計模式，risk 可控，審查者容易理解。
- 下游 pipeline（`repository.py`/`labeling.py`/`calibration_pipeline.py`）的 gate 全部是通用判斷式（`if pred_band is None: skip`），一旦這四組也產生非 null 的 `roas_band`，會**自動**被納入 accuracy/MAE、校準集、few-shot、holdout backtest，完全不用改這些檔案的邏輯。
- 不需要新增資料庫欄位或 migration——沿用既有的 `roas_band`（string, nullable）、`CalibrationItem.prediction_band`/`observed_band`（既有欄位）即可。

**缺點/風險**：
- 這四類目標本來就沒有像 ROAS 一樣自然连续的量化尺度（CTR 潛力、品牌記憶度都是較主觀的判斷），模型輸出的 band 品質需要之後用真實資料驗證準確度，可能不如 conversion/lead 準。
- 需要小心修改 prompt 措辭，避免舊有「不要求 CTA/不評估購買意圖」的既有正確設計被破壞（例如 awareness 組 prompt 明確說「missing CTA 不扣分」，這條規則要保留，只是額外加一條「輸出可比對的 band」）。

### 方案 B：用 `overall_score` 固定切點反推代理 band（例如 ≥70 high、40-69 mid、<40 low）

**優點**：完全不用改 prompt，不多花 LLM token，零風險上線。

**缺點**：`overall_score` 的 0-100 尺度是「素材品質分」，從來沒有針對 CTR/CPC 或品牌記憶度做過校準，拿來反推「預測是否會有高 CTR」在統計上沒有正當性，容易做出一個看起來有對照、實際上很不準的假象指標，之後还要花力氣去 debunk。

**建議：採方案 A**。理由：這才是解決使用者實際訴求（讓評估紀錄本身具備和 conversion/lead 對等的預測能力），而且已有 `lead` 的成功先例可以照抄設計模式與既有 pipeline 相容性，工程風險主要集中在 prompt 文字設計與後續準確度驗證，而非架構重構。

## 4. 影響範圍分析

### 4.1 需要修改

| 檔案 | 修改內容 |
|---|---|
| `backend/modules/meta_andromeda/runtime.py` | `_DEFAULT_OBJECTIVE_PROFILES` 中 `traffic`/`awareness`/`video`/`engagement` 四組：`"roas_band_eligible"` 改為 `True`；`user_prompt_template` 移除「Set roas_band to null」指示，改為比照 `lead` 組寫法，要求輸出「XX潛力 BAND: high/mid/low」，並保留原本「不評估購買意圖/CTA 不扣分」等既有正確規則 |
| `backend/modules/meta_andromeda/objective_routing.py` | 新增 `is_predicted_band_eligible()`（回傳 True，語意涵蓋所有已知 group，供 heuristic fallback 與文件標記使用）；**不動** `NON_ROAS_GROUPS`／`is_roas_band_eligible()` 現有定義，因為 `labeling.py` 靠它判斷「觀測端該用 CTR/CPC 還是 ROAS/CPA」，這條路由邏輯本身是對的，不能因為預測端要改就連動改掉 |
| `backend/modules/meta_andromeda/repository.py` | `_score_to_detail`/`_score_to_list_item` 新增 `objective_group` 頂層欄位（`resolve_objective_group(score.objective)`，純函式呼叫，非新欄位存值），方便前端動態顯示對應標籤，不需要 migration |
| `frontend/src/pages/MetaAndromedaReviewQueue.jsx` | 第 539 行寫死的「Predicted ROAS / 預測 ROAS」標籤，改為依 `detail.objective_group` 動態顯示（例如 traffic → 「Predicted CTR Potential / 預測 CTR 潛力」） |
| `frontend/src/utils/metaAndromedaLabels.js` | 新增 `PREDICTED_BAND_LABELS_ZH`（objective_group → 顯示標籤對照表）與 `getPredictedBandLabel(objectiveGroup, lang)` |
| `backend/tests/test_meta_andromeda_module.py` | 新增 traffic/awareness/video/engagement 四組的 `_validate_provider_result`/`label_observed_band`/`sync_calibration_dataset`/`create_drift_report` 端對端測試（目前完全沒有針對這四組的既有測試覆蓋，這次一併補齊） |

### 4.2 確認不需要修改（現有邏輯已是通用設計）

- `backend/modules/meta_andromeda/labeling.py`：`label_observed_band`/`compute_label_thresholds` 的 CTR/CPC 觀測邏輯不變。
- `backend/modules/meta_andromeda/repository.py` 的 `sync_calibration_dataset`（2271 行起）、`create_drift_report`（1272 行起）、`get_review_queue_detail`（935 行起）：判斷式都是通用的 `if pred_band is None: skip`，一旦 `pred.roas_band` 非 null 自動納入，不用改程式碼。
- `backend/modules/meta_andromeda/calibration_pipeline.py`：`analyze_dataset_bias` 的 few-shot 分組（115-117 行）已經是依 `objective_group` 通用分組，無特殊排除四組的邏輯。
- 資料庫 schema／migration：`MetaAndromedaScoreEvent.roas_band`、`MetaAndromedaCalibrationItem.prediction_band`/`observed_band` 都已是可用欄位，語意從「純 ROAS」擴展為「該目標類型的可比對評級」與 `lead` 當初的做法一致，不需要新增欄位或改 nullable 設定。

### 4.3 待確認事項（需要产品判斷，非技術問題）

1. **Heuristic fallback（`build_heuristic_score_result`，AI 不可用時的規則引擎）要不要也給這四組一個 band？**
   目前建議：**不給**。Heuristic 分數只是簡單加減分規則，不是真的「模型判斷 CTR 潛力」，硬湊一個 band 出來意義不大，且會讓「這筆是真 AI 判斷還是規則引擎湊的」更難分辨。維持 heuristic 分數在這四組時 `roas_band=None`，明確標示為降級模式、無法對照。
2. **這四組 band 的實際準確度未知**，需要上線後累積真實 CTR/CPC 資料才能驗證 Spearman/accuracy 是否有意義（可能會發現模型對「品牌記憶度」的判斷比 CTR 潛力準確度更差）。建議上線後观察至少 2-3 期 drift report 再決定要不要調整 prompt 措辭或砍掉表現最差的子項。
3. 是否要把 `roas_band` 這個歷史命名做一次全面重新命名（例如改成語意中立的 `predicted_band`）？**這次不做**，範圍太大、風險與本次目標無關；本次只在 API 回傳與前端顯示層做語意包裝（`objective_group` + 顯示標籤對照表），底層欄位名稱維持不變，行為與 `lead` 現況一致。

## 5. 實作步驟（單一波次，無需像 docs/20 分三波，範圍集中在 prompt + 顯示層）

1. `objective_routing.py`：新增 `is_predicted_band_eligible()`。
2. `runtime.py`：修改 `traffic`/`awareness`/`video`/`engagement` 四組的 `user_prompt_template`（新增可比對 band 輸出要求，保留既有「不評估購買意圖」等規則）與 `roas_band_eligible: True`。
3. `repository.py`：`_score_to_detail`/`_score_to_list_item` 加 `objective_group` 欄位。
4. 前端：`metaAndromedaLabels.js` 加標籤對照表；`MetaAndromedaReviewQueue.jsx` 第 539 行與其餘寫死「ROAS」文字處改為動態標籤（含清單頁徽章、篩選器文案如需要）。
5. 補測試：針對四組各寫至少一組「AI 回傳 band → `_validate_provider_result` 正確落地 → `label_observed_band` 產生 observed_band → `sync_calibration_dataset`/`create_drift_report` 正確納入 accuracy 計算」的端對端合成資料測試。
6. 全程用 mock/injected scorer 驗證，不觸發真實 OpenRouter API 呼叫（比照三波修復的既有驗證慣例）。
7. 跑 `tests/test_meta_andromeda_module.py` 全量，確認既有測試無新增回歸。

## 6. 驗收標準

- 曝光/流量/影片/互動四類目標的素材，在成效分析批次匯入後，「已評估素材」明細頁的「✅ 實際成效對照」卡片能顯示非 `--` 的「預測」欄位與對應誤差。
- Drift report 與校準集 summary 中，這四組素材的樣本數（`matched_count`/`synced_count`）從 0 變為有實際數字。
- 既有 conversion/lead 的行為與顯示完全不受影響（純新增邏輯分支，不改動這兩組的 prompt/eligibility）。
- 前端不再對 traffic/awareness/video/engagement 素材顯示「Predicted ROAS」字樣（語意錯誤），改顯示對應目標的正確指標名稱。
