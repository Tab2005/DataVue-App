# Facebook Ads 數據指標對照表 (v24.0)

本文件列出系統支援的所有 Facebook 廣告指標，並區分數據來源與計算邏輯。

---

## 📋 指標來源定義 (Source Types)

| 來源類型 | 說明 |
| :--- | :--- |
| **原生 (Native)** | 直接從 Facebook API 欄位取得的基礎數據 (e.g. `spend`, `impressions`)。 |
| **動作 (Action)** | 從 Facebook `actions` 或 `action_values` 陣列中解析出來的特定事件 (e.g. `purchases`, `atc`)。 |
| **計算 (Calculated)** | 由系統後端根據基礎數據二次計算產生 (e.g. `roas`, `cpa`, `ctr`)。 |

---

## 📊 核心指標清單 (Core Metrics)

### 1. 成本與點擊 (Cost & Clicks)

| 指標 Key | 來源類型 | 中文備註 | 備註 / 邏輯 |
| :--- | :---: | :--- | :--- |
| `spend` | 原生 | 花費金額 | 廣告帳號幣別 |
| `impressions` | 原生 | 曝光次數 | |
| `reach` | 原生 | 觸及人數 | |
| `clicks` | 原生 | 所有點擊次數 | 包含讚、留言、分享等所有點擊 |
| `link_clicks` | 原生 | 連結點擊次數 | 指標代號: `inline_link_clicks` |
| `unique_clicks` | 原生 | 不重複點擊次數 | |
| `cpm` | 計算 | 千次曝光成本 | `(spend / impressions) * 1000` |
| `cpc` | 計算 | 單次點擊成本 | `spend / link_clicks` |
| `ctr` | 計算 | 連結點擊率 | `(link_clicks / impressions) * 100` |
| `cpp` | 計算 | 每千人觸及成本 | `(spend / reach) * 1000` |
| `unique_ctr` | 計算 | 不重複點擊率 | `(unique_clicks / reach) * 100` |

### 2. 點擊與轉化率 (CTR & Funnel)

| 指標 Key | 來源類型 | 中文備註 | 備註 / 邏輯 |
| :--- | :---: | :--- | :--- |
| `inline_link_click_ctr` | 計算 | 連結點擊率 | `(inline_link_clicks / impressions) * 100` |
| `outbound_clicks` | 原生 | 外連點擊次數 | 導向站外的點擊 |
| `outbound_clicks_ctr` | 計算 | 外連點擊率 | `(outbound_clicks / impressions) * 100` |
| `unique_ctr` | 計算 | 不重複點擊率 | `(unique_clicks / reach) * 100` |
| `cvr` | 計算 | 購買轉換率 | `(purchases / link_clicks) * 100` |
| `view_to_cart` | 計算 | 瀏覽加購率 | `(add_to_cart / view_content) * 100` |
| `cart_conversion` | 計算 | 購物車購買率 | `(purchases / add_to_cart) * 100` |

### 3. 電商與轉化 (E-commerce)

| 指標 Key | 來源類型 | 中文備註 | 備註 / 邏輯 |
| :--- | :---: | :--- | :--- |
| `purchases` | 動作 | 購買次數 | `action_type: purchase` |
| `purchase_value` | 動作 | 購買轉換價值 | `action_value: purchase` |
| `roas` | 計算 | 廣告投報率 | `purchase_value / spend` |
| `cpa` | 計算 | 單次購買成本 | `spend / purchases` |
| `add_to_cart` | 動作 | 加入購物車次數 | `action_type: add_to_cart` |
| `atc_value` | 動作 | 加購轉換價值 | `action_value: add_to_cart` |
| `cost_per_atc` | 計算 | 加入購物車成本 | `spend / add_to_cart` |

### 4. 影音與其他 (Video & Others)

| 指標 Key | 來源類型 | 中文備註 | 備註 / 邏輯 |
| :--- | :---: | :--- | :--- |
| `video_views` | 動作 | 影片觀看 (3秒) | `action_type: video_view` |
| `video_thruplay` | 動作 | ThruPlay | `action_type: video_view` (特定模式解析) |
| `cost_per_thruplay` | 計算 | 每次 ThruPlay 成本 | `spend / thruplay` |
| `instant_experience_open` | 原生 | 全螢幕體驗開啟 | `instant_experience_clicks_to_open` |
| `instant_experience_start` | 原生 | 全螢幕體驗開始 | `instant_experience_clicks_to_start` |

---

## 🧮 標準化計算規則 (Standardized Rules)

為了確保數據在不同視圖下的一致性，系統遵循以下計算規範：

### 1. 彙整重算邏輯 (Sum-of-Sums)
在 **KPI 儀表板圖卡** 與 **表格總計列** 中，率值或平均值指標**不採用**平均值，而是將該期間的所有分子加總後除以分母加總。
> **公式**: `Result = Sum(Numerator) / Sum(Denominator)`
> *   *範例*: CTR = `Sum(連結點擊) / Sum(總曝光)`

### 2. 零分母保護 (Zero-Division Protection)
所有計算指標在分母為 0 時，結果均會回傳 `0` 而非錯誤或空值。
> **代碼實作**: `(num / den) if den > 0 else 0.0`

### 3. 多層級過濾保護
部分指標（如 `quality_ranking`）僅在 `Level=Ad` 時有效。系統後端會根據請求層級自動調整 API Fields，避免 400 錯誤。

### 4. 幣別與百分比格式化
*   **成本/價值**: 預設顯示 `$0` (Currency)。
*   **率值**: 預設顯示 `0.00%` (Percent)。
*   **次數**: 預設顯示 `0` (Number, 含千分位)。

---

## 🛠️ 開發參考
*   **後端註冊表**: `backend/async_services.py` -> `METRICS_REGISTRY`
*   **前端註冊表**: `frontend/src/constants/metricsRegistry.js`
*   **KPI 計算邏輯**: `backend/services/facebook_service.py` -> `_format_kpi`
