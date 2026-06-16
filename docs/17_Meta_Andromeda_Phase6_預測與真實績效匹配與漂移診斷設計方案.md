# 17 Meta Andromeda Phase 6 預測與真實績效匹配與漂移診斷設計方案

## 目的

本方案依據 [13_FB_Ads_導入_Meta_Andromeda_實作計劃.md](file:///C:/Users/BWM2/Documents/python/DataVue-App/docs/13_FB_Ads_%E5%B0%8E%E5%85%A5_Meta_Andromeda_%E5%AF%A6%E4%BD%9C%E8%A8%88%E5%8A%83.md) 之 `Phase 6` 規劃，旨在將 Meta Andromeda 原先僅具備骨架/偽實現（Mock）的「模型漂移診斷報告（Drift Report）」升級為**基於真實預估與觀測數據匹配**的診斷分析。

透過此方案，系統將能自動關聯 `預估 ROAS 區間 (Prediction)` 與 `真實觀測 ROAS 績效 (Observation)`，計算模型預測準確率與偏差，並在準確度下降時觸發漂移警報（Drift Status: drifted / warning / healthy），為未來的資料校準（Calibration）與模型自我調整奠定基礎。

---

## 核心設計概念

### 1. 預測與觀測匹配機制 (Prediction-Observation Matching)
為了評估預測的準確度，我們需要將 `MetaAndromedaObservedCreative` (真實觀測) 與 `MetaAndromedaScoreEvent` (模型預測) 進行 1-to-1 的匹配對照。

* **關聯鍵值**：使用唯一素材識別碼 `asset_uri` 進行關聯。
* **匹配篩選條件**：
  * 只匹配預估狀態為成功完成的事件：`MetaAndromedaScoreEvent.status == "completed"`。
  * 若同一個 `asset_uri` 存在多次預估，系統將選擇**預估時間最接近且早於觀測開始時間**的那一次預測記錄，若無，則預設採用該 `asset_uri` 最新的成功預測記錄。

---

### 2. 真實 ROAS 分類映射 (ROAS Band Mapping)
模型預估產出的 ROAS 指標是以分類區間 `roas_band`（`low` / `mid` / `high`）呈現。為此，我們需要將觀測所得的實體浮點數 ROAS 轉換為同等區間，才能進行交叉比對。

#### 轉換對照表 (預設切分閥值)：
* **低回報 (Low)**：`ROAS < 1.5`
* **中回報 (Mid)**：`1.5 <= ROAS < 3.5`
* **高回報 (High)**：`ROAS >= 3.5`

> [!NOTE]
> 此閥值未來可根據市場別 (`market`) 或廣告目標 (`objective`) 進行動態配置，第一階段先採用標準化預設值。

---

### 3. 模型漂移與偏差評估指標 (Metrics)

當觸發漂移檢查時，系統會計算以下三大指標：

#### A. 匹配總數 (Matched Pair Count)
* **定義**：當前觀測窗口內成功關聯到預測記錄的 Observed Creative 數量。
* **公式**：$N = \text{Count}(\text{Pairs})$。如果匹配數過少（例如 $N < 5$），系統將標記為 `insufficient_data`，不輕易宣告模型漂移。

#### B. 預測準確率 (Prediction Accuracy)
* **定義**：預估的 ROAS Band 與實際轉化後的 ROAS Band 完全吻合的比例。
* **公式**：
  $$\text{Accuracy} = \frac{\sum_{i=1}^{N} [Band_{pred\_i} == Band_{obs\_i}]}{N}$$

#### C. 平均絕對偏差 (Mean Absolute Band Error - MAE)
* **定義**：衡量預測偏離實際的嚴重程度。將區間數值化：`low = 1, mid = 2, high = 3`。
* **公式**：
  $$\text{MAE} = \frac{\sum_{i=1}^{N} |Score_{pred\_i} - Score_{obs\_i}|}{N}$$
  * *範例*：若模型預估為 `high` (3)，而實際為 `low` (1)，則單筆誤差值為 2。偏差值越高表示模型偏離越嚴重。

---

### 4. 漂移狀態判定門檻 (Drift Thresholds)

系統將綜合上述指標，判定當前模型的健康狀態：

| 狀態 (Drift Status) | 準確率 (Accuracy) 門檻 | 平均絕對偏差 (MAE) 門檻 | 說明 |
| :--- | :--- | :--- | :--- |
| **`healthy` (健康)** | $\ge 75\%$ | $\le 0.35$ | 模型預估精準，無須調整。 |
| **`warning` (警告)** | $60\% \le \text{Accuracy} < 75\%$ | $0.35 < \text{MAE} \le 0.50$ | 預測能力輕微下滑，建議觀察。 |
| **`drifted` (漂移)** | $< 60\%$ | $> 0.50$ | 模型已出現顯著偏差，應評估重新訓練或資料校準。 |

---

## 後端實作修改藍圖

### 1. 調整 `repository.py` 的 `create_drift_report`
我們將重寫 `create_drift_report`，取代原本的 mock 計算。

```python
def create_drift_report(
    self,
    db: Session,
    window_kind: str,
    triggered_by: str | None = None,
    note: str | None = None,
):
    # 1. 撈取目前的所有 Observed Creative
    observed_list = (
        db.query(MetaAndromedaObservedCreative)
        .filter(MetaAndromedaObservedCreative.observation_window_kind == window_kind)
        .all()
    )
    
    matched_pairs = []
    correct_count = 0
    total_error = 0.0
    
    # 區間映射字典
    band_score = {"low": 1, "mid": 2, "high": 3}
    
    # 2. 逐筆進行 Prediction 匹配與比對
    for obs in observed_list:
        # 尋找對應的 Completed ScoreEvent
        pred = (
            db.query(MetaAndromedaScoreEvent)
            .filter(
                MetaAndromedaScoreEvent.asset_uri == obs.asset_uri,
                MetaAndromedaScoreEvent.status == "completed"
            )
            .order_by(MetaAndromedaScoreEvent.completed_at.desc())
            .first()
        )
        
        if not pred:
            continue
            
        # 提取真實 ROAS
        real_roas = obs.performance_snapshot.get("roas", 0.0)
        
        # 真實 ROAS 轉成 Band
        if real_roas < 1.5:
            real_band = "low"
        elif real_roas < 3.5:
            real_band = "mid"
        else:
            real_band = "high"
            
        pred_band = pred.roas_band or "low"
        
        is_match = (pred_band == real_band)
        if is_match:
            correct_count += 1
            
        # 計算 MAE 誤差
        err = abs(band_score.get(pred_band, 1) - band_score.get(real_band, 1))
        total_error += err
        
        matched_pairs.append({
            "ad_id": obs.ad_id,
            "ad_name": obs.ad_name,
            "prediction_band": pred_band,
            "observed_band": real_band,
            "real_roas": real_roas,
            "error": err
        })
        
    # 3. 計算統計指標
    total_matched = len(matched_pairs)
    accuracy = correct_count / total_matched if total_matched > 0 else 0.0
    mae = total_error / total_matched if total_matched > 0 else 0.0
    
    # 4. 判定漂移健康度
    if total_matched < 5:
        drift_status = "insufficient_data"
        severity = "info"
        summary = f"數據量不足 (僅匹配 {total_matched} 筆)，無法評估模型漂移狀態。"
    elif accuracy >= 0.75 and mae <= 0.35:
        drift_status = "healthy"
        severity = "info"
        summary = f"模型表現穩定 (Accuracy: {accuracy:.1%}, MAE: {mae:.2f})，無顯著漂移。"
    elif accuracy >= 0.60 and mae <= 0.50:
        drift_status = "warning"
        severity = "medium"
        summary = f"模型出現輕微偏差 (Accuracy: {accuracy:.1%}, MAE: {mae:.2f})，請密切關注。"
    else:
        drift_status = "drifted"
        severity = "high"
        summary = f"模型預估已出現顯著漂移！(Accuracy: {accuracy:.1%}, MAE: {mae:.2f})，建議重新校準。"

    # 5. 寫入資料庫
    report = MetaAndromedaDriftReport(
        window_kind=window_kind,
        drift_status=drift_status,
        summary=summary,
        severity=severity,
        triggered_by=triggered_by,
        note=note,
        report_payload={
            "total_observed": len(observed_list),
            "total_matched": total_matched,
            "accuracy": round(accuracy, 4),
            "mae": round(mae, 4),
            "matched_details": matched_pairs
        }
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return self._drift_report_to_dict(report)
```

---

## 驗收計畫 (Verification Plan)

### 1. 單元測試驗證
在 `backend/tests/test_meta_andromeda_module.py` 中新增 Drift 核心算法測試：
* **情境 A**：建立預測為 `high`、真實 ROAS 為 4.2 (對應 `high`) 的配對，驗證準確率為 100% 且狀態為 `healthy`。
* **情境 B**：建立預測為 `high`、真實 ROAS 為 0.8 (對應 `low`) 的配對，驗證準確率為 0% 且觸發 `drifted` 警報。
* **情境 C**：無匹配數據時，回傳 `insufficient_data`。

### 2. 生產整合測試
* 於 Zeabur 部署新後端後，由前端 UI 點擊「Trigger Drift Check」，驗證產生的 Drift 報告內之 `report_payload` 具有真實的廣告配對明細。
