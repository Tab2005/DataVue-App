# Meta Andromeda 廣告目標分類與指標路由計畫

> **文件編號：** 29
> **建立日期：** 2026-06-24
> **狀態：** 部分完成（Phase 1 已實作，Phase 2-3 待實作）

---

## 背景與問題

Meta Andromeda 診斷系統目前只用 ROAS 來評估廣告成效。但實務上廣告有多種類型：

- **轉換廣告**（OUTCOME_SALES）：目標是購買，ROAS 有意義
- **潛在客戶廣告**（OUTCOME_LEADS）：目標是表單填寫，用 CVR / CPL 評估
- **流量廣告**（OUTCOME_TRAFFIC）：目標是連結點擊，ROAS 不適用，用 CTR / CPC
- **互動廣告**（OUTCOME_ENGAGEMENT）：目標是貼文互動/追蹤/按讚，ROAS 不適用
- **知名度廣告**（OUTCOME_AWARENESS）：目標是觸及/曝光，ROAS 不適用

流量/互動/知名度廣告因為沒有設計成帶來購買轉換，ROAS 永遠是 0。若將這些廣告納入診斷，會造成：

| 影響點 | 說明 |
|---|---|
| 偏差診斷準確率失真 | 流量廣告 AI 預估 Low、實際也 Low（ROAS=0），準確率虛高 |
| Spearman ρ 被拖低 | 大量 ROAS=0 拉低相關係數，投放環境診斷失真 |
| 校準集偏誤 | 若 AI 預估 Mid/High 但實際 ROAS=0，進入校準後讓模型以為自己高估 |

---

## Facebook API 的廣告目標欄位

Facebook Insights API 提供 `objective` 欄位，可在查詢時帶入。回傳值為英文代碼：

| API 值 | 中文說明 | 評估指標 |
|---|---|---|
| `OUTCOME_SALES` | 銷售/購買/轉換 | ROAS |
| `OUTCOME_LEADS` | 潛在客戶 | CVR / CPL（已支援） |
| `OUTCOME_TRAFFIC` | 流量（連結點擊） | CTR / CPC |
| `OUTCOME_ENGAGEMENT` | 互動（貼文互動、追蹤、按讚） | CTR / CPC |
| `OUTCOME_AWARENESS` | 品牌知名度/觸及 | CTR / CPC |
| `OUTCOME_APP_PROMOTION` | 應用程式推廣 | 安裝數（暫不處理） |

舊帳號可能仍使用舊代碼（`CONVERSIONS`、`LINK_CLICKS`、`POST_ENGAGEMENT`、`REACH` 等），需一併納入判斷。

### 關於 `objective` vs `optimization_goal` 的區別

- `objective`：**廣告活動層級**的大類目，可在 Insights API 直接取得 → 本計畫採用
- `optimization_goal`：**廣告組層級**的優化目標（更細），可區分「貼文互動」vs「追蹤按讚」，但需額外查詢 adsets API

對診斷系統來說，`objective` 的精細度已足夠（流量/互動/知名度都走 CTR/CPC 路線，不需再細分）。

---

## 現有程式碼狀態

### 管線已存在，只差 API 未請求

```
FB API ──→ analytics_service.py (_process_flat_row)
            └─ "objective": row.get("objective", "-")   ← 有提取邏輯
                  ↓
           normalize_facebook_ad_row
            └─ objective=row.get("objective")           ← 有傳遞
                  ↓
           ObservedCreativeCandidate.objective           ← Schema 欄位存在
                  ↓
           MetaAndromedaObservedCreative.objective       ← DB 欄位存在
                  ↓
           _resolve_observed_band(objective, ...)        ← 有 objective 參數
```

### `_resolve_observed_band` 現有邏輯

```python
objective_key = _objective_key(objective)  # lowercase strip

if any(token in objective_key for token in ("lead", "cpl")):
    # 用 CVR 或 CPL 評估
    ...

roas = snapshot.get("roas")
if roas is not None:
    # 用 ROAS 評估（幾乎所有 objective 都落到這裡）
    ...

cpa = snapshot.get("cpa")
if cpa is not None:
    # 用 CPA 評估
    ...

return "low", {"metric": "fallback", "value": None}
```

**問題**：`objective` 即使是 `OUTCOME_TRAFFIC`，因為 `roas` 不是 `None`（normalize 時設為 `0.0`），仍會走 ROAS 分支，永遠回傳 "low"。

---

## 實作計畫

### Phase 1：取得 `objective` 欄位（已完成 ✓）

**檔案：** `backend/modules/fb_ads/analytics_service.py`

在 `api_fields` 字串加入 `"objective,"` → FB API 開始回傳廣告目標值。

```python
api_fields = (
    "campaign_id,adset_id,ad_id,"
    "campaign_name,adset_name,ad_name,"
    "objective,"   # ← 已加入
    "spend,impressions,..."
)
```

**部署後操作**：成效分析頁面重新批次匯入廣告 → `MetaAndromedaObservedCreative.objective` 從 `"-"` 更新為真實值。

---

### Phase 2：擴充 `_resolve_observed_band` 支援流量/互動指標

**檔案：** `backend/modules/meta_andromeda/repository.py`

#### 2-1 新增 objective 分類輔助函式

```python
_TRAFFIC_OBJECTIVE_TOKENS = (
    "traffic", "engagement", "awareness", "reach", "video",
    "outcome_traffic", "outcome_engagement", "outcome_awareness",
    # 舊代碼
    "link_clicks", "post_engagement", "page_likes",
    "brand_awareness", "video_views",
)

def _is_traffic_objective(objective_key: str) -> bool:
    return any(token in objective_key for token in _TRAFFIC_OBJECTIVE_TOKENS)
```

#### 2-2 擴充 `_resolve_observed_band` 函式簽名

```python
def _resolve_observed_band(
    objective: str | None,
    performance_snapshot: dict | None,
    roas_thresholds: tuple[float, float] | None = None,
    ctr_thresholds: tuple[float, float] | None = None,   # 新增
    cpc_thresholds: tuple[float, float] | None = None,   # 新增
) -> tuple[str, dict]:
```

#### 2-3 在函式內加入流量/互動分支

```python
# 流量 / 互動 / 知名度廣告：用 CTR 或 CPC 評估
if _is_traffic_objective(objective_key):
    ctr = snapshot.get("ctr")
    if ctr is not None and ctr_thresholds:
        value = float(ctr)
        low_t, high_t = ctr_thresholds
        if value >= high_t:
            return "high", {"metric": "ctr", "value": value}
        if value >= low_t:
            return "mid", {"metric": "ctr", "value": value}
        return "low", {"metric": "ctr", "value": value}

    cpc = snapshot.get("cpc")
    if cpc is not None and cpc_thresholds and float(cpc) > 0:
        value = float(cpc)
        low_t, high_t = cpc_thresholds   # CPC 反向：low_t 是「貴」的門檻
        if value <= high_t:              # CPC 夠低 → High
            return "high", {"metric": "cpc", "value": value}
        if value <= low_t:
            return "mid", {"metric": "cpc", "value": value}
        return "low", {"metric": "cpc", "value": value}

    return "low", {"metric": "fallback_traffic", "value": None}
```

---

### Phase 3：動態計算 CTR / CPC 門檻

**檔案：** `backend/modules/meta_andromeda/repository.py`（`create_drift_report`）

與 ROAS 使用 P33/P67 的邏輯完全相同，但只對流量/互動廣告的資料集計算：

```python
# 分群計算門檻
_traffic_obs = [
    obs for obs in observed_list
    if _is_traffic_objective(_objective_key(obs.objective))
]

ctr_thresholds: tuple[float, float] | None = None
cpc_thresholds: tuple[float, float] | None = None

_ctr_values = sorted(
    float(obs.performance_snapshot["ctr"])
    for obs in _traffic_obs
    if obs.performance_snapshot and obs.performance_snapshot.get("ctr")
)
if len(_ctr_values) >= 5:
    ctr_thresholds = (
        _ctr_values[int(len(_ctr_values) * 0.33)],   # P33 → Low/Mid 邊界
        _ctr_values[int(len(_ctr_values) * 0.67)],   # P67 → Mid/High 邊界
    )

_cpc_values = sorted(
    float(obs.performance_snapshot["cpc"])
    for obs in _traffic_obs
    if obs.performance_snapshot and obs.performance_snapshot.get("cpc")
    and float(obs.performance_snapshot["cpc"]) > 0
)
if len(_cpc_values) >= 5:
    # CPC 越低越好，P33 是「便宜」那側 → High
    cpc_thresholds = (
        _cpc_values[int(len(_cpc_values) * 0.67)],   # P67 → Low/Mid 邊界（貴的那側）
        _cpc_values[int(len(_cpc_values) * 0.33)],   # P33 → Mid/High 邊界（便宜的那側）
    )
```

然後在呼叫 `_resolve_observed_band` 時帶入：

```python
real_band, label_detail = _resolve_observed_band(
    obs.objective,
    obs.performance_snapshot,
    roas_thresholds,
    ctr_thresholds=ctr_thresholds,
    cpc_thresholds=cpc_thresholds,
)
```

---

### Phase 4：校準集過濾（選擇性）

流量/互動廣告進入校準集時，其 `label_metric` 會是 `"ctr"` 或 `"cpc"` 而非 `"roas"`，在後續 `analyze_dataset_bias` 可依此分群分析，避免混用不同指標的偏差。

目前校準集的 `sync_calibration_dataset` 不需要修改，因為它依賴 `_resolve_observed_band` 的結果，Phase 2-3 完成後自然受益。

---

## 前置條件與執行順序

```
Phase 1 完成（✓）
  └─ 重新部署
       └─ 成效分析頁面批次重新匯入廣告
            └─ 確認 MetaAndromedaObservedCreative.objective 有正確值
                 └─ 開始實作 Phase 2-3
                      └─ 重新跑偏差診斷
                           └─ 驗證流量廣告以 CTR/CPC 評估
```

---

## 修改檔案清單

| 類型 | 路徑 | Phase |
|---|---|---|
| 已修改 | `backend/modules/fb_ads/analytics_service.py` | Phase 1 ✓ |
| 待修改 | `backend/modules/meta_andromeda/repository.py` | Phase 2-3 |

---

## 暫緩事項

- **`optimization_goal` 細分**：區分「貼文互動」vs「追蹤按讚」，需額外查詢 adsets API，目前 `objective` 精細度已足夠
- **APP 廣告（OUTCOME_APP_PROMOTION）**：需用安裝數/安裝成本評估，暫不處理
- **樣本數不足時的 fallback**：流量廣告 < 5 筆時無法計算 P33/P67，目前設計為回傳 `"low"` + `"fallback_traffic"`，可考慮完全跳過不進入診斷
