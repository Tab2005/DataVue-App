# Facebook Ads 數據指標對照表 (v24.0)

本文件列出系統支援的所有 Facebook 廣告指標，並區分數據來源、系統狀態與計算邏輯。

---

## 📋 指標定義說明

### 指標來源 (Source Types)
| 來源類型 | 說明 |
| :--- | :--- |
| **原生 (Native)** | 直接從 Facebook API 欄位取得的基礎數據 (e.g. `spend`, `impressions`)。 |
| **動作 (Action)** | 從 Facebook `actions` 或 `action_values` 陣列中解析出來的特定事件 (e.g. `purchases`, `atc`)。 |
| **計算 (Calculated)** | 由系統後端根據基礎數據二次計算產生 (e.g. `roas`, `cpa`, `ctr`)。 |

### 系統狀態 (System Status)
*   ✅ **已啟動**: 系統已實作此指標且可在報表/圖卡中使用。
*   ❌ **未開通**: Facebook API 支援但系統暫未實作（作為參考）。
*   ⛔ **已棄用**: Facebook 已停止支援或 API 無法回傳數據。

---

## 📊 數據指標清單

### 1. 成本與點擊 (Cost & Clicks)

| 指標 Key | 來源類型 | 中文備註 | 系統啟動? | 備註 / 邏輯 |
| :--- | :--- | :--- | :---: | :--- |
| `spend` | 原生 | 花費金額 | ✅ | 廣告帳號幣別 |
| `impressions` | 原生 | 曝光次數 | ✅ | |
| `reach` | 原生 | 觸及人數 | ✅ | |
| `clicks` | 原生 | 所有點擊次數 | ✅ | 包含讚、留言、分享等所有點擊 |
| `link_clicks` | 原生 | 連結點擊次數 | ✅ | 指標代號: `inline_link_clicks` |
| `unique_clicks` | 原生 | 不重複點擊次數 | ✅ | |
| `cpm` | 計算 | 千次曝光成本 | ✅ | `(spend / impressions) * 1000` |
| `cpc` | 計算 | 單次點擊成本 | ✅ | `spend / link_clicks` |
| `ctr` | 計算 | 連結點擊率 | ✅ | `(link_clicks / impressions) * 100` |
| `cpp` | 計算 | 每千人觸及成本 | ✅ | `(spend / reach) * 1000` |
| `unique_ctr` | 計算 | 不重複點擊率 | ✅ | `(unique_clicks / reach) * 100` |
| `cost_per_unique_click`| 計算 | 單次不重複點擊成本 | ✅ | |
| `cost_per_inline_link_click`| 計算 | 單次連結點擊成本 | ✅ | |
| `cost_per_outbound_click`| 計算 | 單次外連點擊成本 | ✅ | |
| `cost_per_conversion`| 計算 | 單次轉換成本 | ✅ | |
| `cost_per_action_type` | 原生 | 單次動作成本 | ❌ | |
| `cost_per_ad_click` | 原生 | 單次廣告點擊成本 | ❌ | |
| `social_spend` | 原生 | 社交互動花費 | ❌ | |

### 2. 轉化與漏斗 (Conversions & Funnel)

| 指標 Key | 來源類型 | 中文備註 | 系統啟動? | 備註 / 邏輯 |
| :--- | :--- | :--- | :---: | :--- |
| `purchases` | 動作 | 購買次數 | ✅ | `action_type: purchase` |
| `purchase_value` | 動作 | 購買轉換價值 | ✅ | `action_value: purchase` |
| `roas` | 計算 | 廣告投報率 | ✅ | `purchase_value / spend` |
| `cpa` | 計算 | 單次購買成本 | ✅ | `spend / purchases` |
| `add_to_cart` | 動作 | 加入購物車次數 | ✅ | `action_type: add_to_cart` |
| `atc_value` | 動作 | 加購轉換價值 | ✅ | `action_value: add_to_cart` |
| `cost_per_atc` | 計算 | 加入購物車成本 | ✅ | `spend / add_to_cart` |
| `view_content` | 動作 | 查看內容 | ✅ | |
| `initiate_checkout` | 動作 | 開始結帳 | ✅ | |
| `add_payment_info` | 動作 | 新增付款資訊 | ✅ | |
| `cvr` | 計算 | 購買轉換率 | ✅ | `(purchases / link_clicks) * 100` |
| `view_to_cart` | 計算 | 瀏覽加購率 | ✅ | `(add_to_cart / view_content) * 100` |
| `cart_conversion` | 計算 | 購物車購買率 | ✅ | `(purchases / add_to_cart) * 100` |
| `contact` | 動作 | 聯絡 | ❌ | |
| `search` | 動作 | 搜尋 | ❌ | |
| `start_trial` | 動作 | 開始試用 | ❌ | |
| `subscribe` | 動作 | 訂閱 | ❌ | |

### 3. 影音指標 (Video)

| 指標 Key | 來源類型 | 中文備註 | 系統啟動? | 備註 / 邏輯 |
| :--- | :--- | :--- | :---: | :--- |
| `video_views` | 動作 | 影片觀看 (3秒) | ✅ | |
| `video_thruplay` | 動作 | ThruPlay | ✅ | 完整觀看或15秒 |
| `cost_per_thruplay` | 計算 | 每次 ThruPlay 成本 | ✅ | `spend / thruplay` |
| `video_p100_watched` | 原生 | 影片觀看 100% | ✅ | |
| `video_avg_time_watched`| 原生 | 平均觀看時間 | ✅ | |
| `video_p25_watched` | 原生 | 影片觀看 25% | ❌ | |
| `video_p50_watched` | 原生 | 影片觀看 50% | ❌ | |
| `video_p75_watched` | 原生 | 影片觀看 75% | ❌ | |

### 4. 互動與品質 (Engagement & Quality)

| 指標 Key | 來源類型 | 中文備註 | 系統啟動? | 備註 / 邏輯 |
| :--- | :--- | :--- | :---: | :--- |
| `post_engagement` | 動作 | 貼文互動 | ✅ | |
| `post_reactions` | 動作 | 貼文心情 | ✅ | |
| `post_comments` | 動作 | 貼文留言 | ✅ | |
| `post_shares` | 動作 | 貼文分享 | ✅ | |
| `post_saves` | 動作 | 貼文儲存 | ✅ | |
| `page_likes` | 動作 | 粉專按讚 | ✅ | |
| `quality_ranking` | 原生 | 品質排名 | ✅ | 僅限 Ad 層級 |
| `engagement_rate_ranking`| 原生 | 互動率排名 | ✅ | 僅限 Ad 層級 |
| `conversion_rate_ranking`| 原生 | 轉換率排名 | ✅ | 僅限 Ad 層級 |
| `page_engagement` | 原生 | 粉專互動 | ❌ | |
| `photo_view` | 原生 | 照片瀏覽 | ❌ | |
| `social_reach` | 原生 | 社交觸及 | ❌ | |

### 5. 即時體驗與訊息 (IE & Messaging)

| 指標 Key | 來源類型 | 中文備註 | 系統啟動? | 備註 / 邏輯 |
| :--- | :--- | :--- | :---: | :--- |
| `instant_experience_open` | 原生 | 即時體驗開啟 | ✅ | |
| `instant_experience_start`| 原生 | 即時體驗開始 | ✅ | |
| `messaging_first_reply` | 動作 | 首次訊息回覆 | ✅ | |
| `messaging_conversation_started`| 動作 | 開始對話 | ✅ | |
| `cost_per_message` | 計算 | 每則訊息成本 | ✅ | |

---

## 🧮 標準化計算規則 (Standardized Rules)

### 1. 彙整重算邏輯 (Sum-of-Sums)
在 **KPI 儀表板圖卡** 與 **表格總計列** 中，率值或平均值指標採用權重加總計算，將該期間的所有分子加總後除以分母加總。
> **公式**: `Result = Sum(Numerator) / Sum(Denominator)`

### 2. 零分母保護 (Zero-Division Protection)
所有計算指標在分母為 0 時，結果均會回傳 `0` 而非錯誤或空值。
> **代碼實作**: `(num / den) if den > 0 else 0.0`

### 3. 多層級過濾保護
品質排名指標僅於 `Level=Ad` 時請求，系統會自動根據層級過濾 API 欄位以防止 400 錯誤。

---

## 🛠️ 開發參考
*   **後端註冊表**: `backend/async_services.py` -> `METRICS_REGISTRY`
*   **KPI 計算邏輯**: `backend/services/facebook_service.py` -> `_format_kpi`
