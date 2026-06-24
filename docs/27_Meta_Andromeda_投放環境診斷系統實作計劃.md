# 27. Meta Andromeda 投放環境診斷系統實作計劃

## 背景與動機

Meta Andromeda 模組原始設計目標是對廣告素材進行 AI 創意品質評分，並透過預估偏差（Drift）檢查判斷評分模型是否仍具預測力。

在 2026-06 的實際運用中，發現了一個更深層的洞察：

> **Spearman ρ（創意品質排名 vs 實際 ROAS 排名的相關係數）本身就是「創意品質在當前市場環境中的影響力指標」，而非只是模型準確性的評估依據。**

具體觀察：
- H2 2025（ROAS 均值 3.68）：ρ = 0.346 → 創意品質是 ROAS 的關鍵差異因子
- H1 2026（ROAS 均值 4.91）：ρ = 0.121 → 整體 ROAS 被非創意因素拉高，創意品質影響力降低

這代表模組可以從「創意評分工具」延伸為「廣告投放環境診斷系統」，在不需要額外資料來源的情況下，從現有數據推算出每個投放區間的主要績效驅動因子，並提供對應的操作建議。

---

## 核心概念：投放狀態四象限

以 **Spearman ρ** 和 **ROAS 整體水準** 為兩個軸，將每個投放區間分類為四種狀態：

```
                     ROAS 高
                        │
          象限 B        │        象限 A
    市場/定向在撐       │   創意 + 市場環境雙重有利
    創意只是保底        │   可安心維持並擴量
                        │
ρ 低 ───────────────────┼─────────────────────── ρ 高
（創意影響力弱）        │                    （創意影響力強）
          象限 D        │        象限 C
    根本問題待解        │   創意是唯一差異因子
    產品/定向/出價      │   市場難打，需靠創意突圍
    需全面檢視          │
                        │
                     ROAS 低
```

### 各象限說明與行動建議

| 象限 | 狀態名稱 | ρ | ROAS | 主要驅動因子 | 建議行動 |
|---|---|---|---|---|---|
| A | **雙重有利** | ≥ 0.30 | ≥ P50 | 創意品質 + 市場順風 | 維持現有創意策略，擴大預算規模 |
| B | **市場護航** | < 0.30 | ≥ P50 | 受眾定向 / 競價策略 / 季節需求 | 勿把成績歸功創意，優先鞏固定向與競價優勢；創意達標即可 |
| C | **創意突圍** | ≥ 0.30 | < P50 | 創意品質（市場環境困難） | 重點投資創意優化，高分素材要積極擴量；低分素材盡快汰換 |
| D | **全面檢視** | < 0.30 | < P50 | 不明 / 多因素失調 | 需系統性檢視：產品競爭力、受眾定向、出價策略、素材是否疲乏 |

### ρ 門檻定義（與現有 Drift 系統一致）

| ρ | 創意影響力 |
|---|---|
| ≥ 0.30 | 強（创意品質顯著影響 ROAS 排名） |
| 0.10–0.30 | 弱（有相關但不顯著） |
| < 0.10 | 無（創意品質無法解釋 ROAS 差異） |

ROAS 高低以**當期 P50（中位數）** 為基準，動態判定。

---

## 現有資料基礎（不需新資料來源）

每次 Drift 檢查執行後，以下數據已可取得：

| 數據 | 來源 | 用途 |
|---|---|---|
| `spearman_r` | Drift report | ρ 值，象限分類主軸 |
| `roas_band_thresholds` | Drift report | P33/P67，用於推算 P50 基準 |
| `overall_score` | ScoreEvent | 創意品質分布分析 |
| `real_roas` | matched_pairs | ROAS 分布分析 |
| `accuracy`, `mae` | Drift report | 輔助指標 |
| `total_matched`, `calibration_candidate_total` | Drift report | 資料量與誤判狀況 |

可從現有資料額外計算：

- **ρ²（可決係數）**：創意品質解釋的 ROAS 變異比例（例：ρ=0.346 → ρ²=0.12，即創意解釋約 12% 的 ROAS 變異）
- **ROAS P50（中位數）**：判斷整體水準高低
- **ROAS 標準差**：衡量該期間廣告績效分散程度
- **overall_score 標準差**：衡量創意品質分散程度

---

## 實作計劃

### Phase 1：Drift Report 加入投放狀態診斷（後端）

**檔案：** `backend/modules/meta_andromeda/repository.py`

在 `create_drift_report` 計算 Spearman ρ 之後，新增：

```python
def _classify_period_state(roas_median: float, roas_p50_baseline: float, spearman_r: float) -> dict:
    roas_is_high = roas_median >= roas_p50_baseline
    creative_is_effective = spearman_r >= 0.30

    if roas_is_high and creative_is_effective:
        state = "dual_advantage"
        label = "雙重有利"
        recommendation = "創意品質與市場環境同步有利，維持現有創意策略並考慮擴大投放預算。"
    elif roas_is_high and not creative_is_effective:
        state = "market_driven"
        label = "市場護航"
        recommendation = "整體 ROAS 由市場/定向/競價因素拉高，創意品質影響力偏弱。優先鞏固受眾定向與競價策略；創意達標即可，勿過度投資創意優化。"
    elif not roas_is_high and creative_is_effective:
        state = "creative_critical"
        label = "創意突圍"
        recommendation = "市場環境困難，創意品質是主要差異因子。積極擴量高分素材，快速汰換低分素材，創意優化投資報酬率最高。"
    else:
        state = "needs_review"
        label = "全面檢視"
        recommendation = "創意品質與整體 ROAS 同步偏弱，需系統性檢視：產品競爭力、受眾定向精準度、出價策略、素材是否已疲乏。"

    return {
        "state": state,
        "label": label,
        "roas_is_high": roas_is_high,
        "creative_is_effective": creative_is_effective,
        "creative_explained_variance": round(spearman_r ** 2, 4),
        "recommendation": recommendation,
    }
```

#### Spearman ρ 改用 objective 主指標（跨產業支援）

現有實作寫死使用 `real_roas`，導致 lead gen 等非 ROAS 帳戶計算結果無意義。
改為從 `matched_pairs` 的 `primary_metric` / `primary_metric_value` 欄位取值，
以**同一主指標最多筆的那組**計算 ρ，其餘指標群組標注於報告中。

`matched_pairs` 新增欄位（從 `label_detail` 取得，`_resolve_observed_band` 已回傳）：
```python
matched_pairs.append({
    ...
    "primary_metric":        label_detail["metric"],   # "roas" / "cvr" / "cpa" / "cpl"
    "primary_metric_value":  label_detail["value"],    # 實際數值，用於 ρ 計算
    "real_roas": real_roas,                            # 保留供前端顯示
})
```

ρ 計算邏輯改為：
```python
from collections import Counter

dominant_metric = Counter(
    p["primary_metric"] for p in matched_pairs
    if p.get("primary_metric") and p.get("primary_metric_value") is not None
).most_common(1)
dominant_metric = dominant_metric[0][0] if dominant_metric else "roas"

_scores = [float(p["overall_score"])        for p in matched_pairs
           if p.get("primary_metric") == dominant_metric and p.get("overall_score") is not None]
_perf   = [float(p["primary_metric_value"]) for p in matched_pairs
           if p.get("primary_metric") == dominant_metric and p.get("overall_score") is not None]
spearman_r = _spearman_r(_scores, _perf) if len(_scores) >= 3 else 0.0
```

`report_payload` 新增 `dominant_metric` 與各指標筆數，供前端顯示依據說明：
```python
"dominant_metric": dominant_metric,
"metric_distribution": dict(Counter(p["primary_metric"] for p in matched_pairs
                                    if p.get("primary_metric"))),
```

**各帳戶類型對應：**

| 帳戶類型 | objective | ρ 計算用指標 | 需手動設定 |
|---|---|---|---|
| 電商 | purchase | ROAS | 否 |
| 潛客 | lead / cpl | CVR 或 CPL | 否 |
| 品牌 / App | 其他 | CPA | 否 |
| 混合目標 | 多種 | 最多筆的指標為主，其餘標注 | 否 |

---

#### 投放狀態分類與 P50 基準

計算主指標 P50 並分類象限：

```python
_perf_all = sorted(
    float(p["primary_metric_value"]) for p in matched_pairs
    if p.get("primary_metric") == dominant_metric and p.get("primary_metric_value") is not None
)
perf_median = _perf_all[len(_perf_all) // 2] if _perf_all else 0.0
period_diagnosis = _classify_period_state(perf_median, perf_median, spearman_r, dominant_metric)
```

`_classify_period_state` 加入 `dominant_metric` 參數，讓建議文字能夠對應正確指標名稱（例如 lead gen 帳戶建議文字改為「CVR」而非「ROAS」）。

**注意**：P50 基準線設計有兩種選擇：
- 以**當期自身 P50** 為基準（相對判定，Phase 1 採用）
- 以**歷史跨期 P50 均值** 為基準（絕對判定，Phase 4 引入）

`report_payload` 新增欄位：
```python
"period_diagnosis": period_diagnosis,
"perf_median": round(perf_median, 4),
"perf_std": round(statistics.stdev(_perf_all), 4) if len(_perf_all) >= 2 else 0.0,
"dominant_metric": dominant_metric,
"metric_distribution": dict(Counter(p["primary_metric"] for p in matched_pairs if p.get("primary_metric"))),
```

---

### Phase 2：監控工作台加入投放狀態區塊（前端）

**檔案：** `frontend/src/pages/MetaAndromedaMonitoring.jsx`

在每張 Drift 報告卡片的 summary 文字下方，加入投放狀態診斷卡：

```
┌─────────────────────────────────────────┐
│ 投放狀態診斷                            │
│                                         │
│  [市場護航]  ρ² = 1.5%                 │
│  整體 ROAS 由市場/定向因素拉高          │
│                                         │
│  建議：優先鞏固受眾定向與競價策略...    │
└─────────────────────────────────────────┘
```

狀態 badge 顏色對應：
- `dual_advantage` → 綠色
- `market_driven` → 藍色
- `creative_critical` → 橙色
- `needs_review` → 紅色

---

### Phase 3：版本總覽頁加入投放狀態摘要（前端）

**檔案：** `frontend/src/pages/MetaAndromedaRelease.jsx`

在「線上實測對照證據」面板的指標格下方，加入當期投放狀態與建議，讓模型發佈決策有更完整的上下文。

---

### Phase 4：跨期趨勢追蹤（後端 + 前端）

將歷史各期 Drift 報告的關鍵指標整合為趨勢圖：

| 欄位 | 說明 |
|---|---|
| `period` | 報告時間窗口 |
| `spearman_r` | 創意影響力 |
| `roas_median` | ROAS 中位數 |
| `period_state` | 象限分類 |
| `creative_explained_variance` | ρ² |

**API：** 新增 `GET /monitoring/drift-trend`，回傳歷史 Drift 報告摘要列表。

**前端：** 監控工作台新增「投放趨勢」section，顯示各期象限變化時間軸。

---

### Phase 5：象限切換自動告警（後端）

當最新 Drift 報告的象限與前一筆不同時，寫入 `active_alerts`，提醒操作者投放環境已發生結構性變化。

例：從「市場護航（B）」切換到「創意突圍（C）」→ 告警「市場順風期結束，創意品質重新成為關鍵，建議調整投放策略。」

---

## 不需要的資料（澄清邊界）

以下資料**不在本計劃範圍內**，不需要串接新資料來源：

- CTR / 互動率（需從 FB Ads API 另外拉取）
- 受眾重疊分析（需額外 API 權限）
- 素材疲乏偵測（需投放天數追蹤）
- 競價策略資料（Meta 廣告管理員後台資料）

這些可在未來的 Phase 6+ 評估引入，但不是本計劃的前提條件。

---

## 改動檔案清單

| Phase | 類型 | 檔案 |
|---|---|---|
| 1 | 後端修改 | `backend/modules/meta_andromeda/repository.py` |
| 2 | 前端修改 | `frontend/src/pages/MetaAndromedaMonitoring.jsx` |
| 3 | 前端修改 | `frontend/src/pages/MetaAndromedaRelease.jsx` |
| 4 | 後端新增 | `backend/modules/meta_andromeda/router.py`（新增 drift-trend endpoint） |
| 4 | 前端修改 | `frontend/src/pages/MetaAndromedaMonitoring.jsx`（趨勢 section） |
| 4 | 前端修改 | `frontend/src/services/metaAndromedaMonitoringService.js`（新增 API call） |
| 5 | 後端修改 | `backend/modules/meta_andromeda/repository.py`（告警邏輯） |

---

## 實作優先順序

```
Phase 1（後端診斷邏輯）
    → Phase 2（監控頁顯示）
        → Phase 3（版本總覽整合）
            → Phase 4（趨勢追蹤）
                → Phase 5（告警機制）
```

Phase 1–3 可在單次迭代內完成，Phase 4–5 為獨立迭代。

---

## 預期效益

1. **決策支援**：操作者在看偏差報告時，直接得到「這個時期應該優先優化什麼」的建議，不需要自行解讀數字
2. **策略調整依據**：季度切換時，系統自動提示投放環境是否發生結構性變化
3. **模組價值升級**：Andromeda 從「模型評估工具」升級為「投放智慧診斷系統」，提供創意優化以外的策略層建議
4. **零新資料成本**：完全基於現有 Drift 檢查流程，不需要新的資料來源或 API 串接
