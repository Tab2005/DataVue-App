# Facebook Graph API: All Available Metrics (v24.0)

**Total Metrics Listed**: 85

## Cost & Spend (13)

| Metric Key | Used in System? | 中文備註 |
| :--- | :---: | :--- |
| `spend` | ✅ | 花費金額 |
| `cpm` | ✅ | 每千次曝光成本 |
| `cpc` | ✅ | 單次點擊成本 (全部) |
| `cpp` | ❌ | 每千人觸及成本 |
| `ctr` | ✅ | 點擊率 (全部) |
| `cost_per_unique_click` | ❌ | 單次不重複點擊成本 |
| `cost_per_inline_link_click` | ❌ | 單次連結點擊成本 |
| `cost_per_outbound_click` | ❌ | 單次外連點擊成本 |
| `cost_per_action_type` | ❌ | 單次動作成本 (依類型) |
| `cost_per_ad_click` | ❌ | 單次廣告點擊成本 |
| `cost_per_conversion` | ❌ | 單次轉換成本 |
| `cost_per_unique_conversion` | ❌ | 單次不重複轉換成本 |
| `social_spend` | ❌ | 社交互動花費 |

## Video (12)

| Metric Key | Used in System? | 中文備註 |
| :--- | :---: | :--- |
| `video_views` | ✅ | 影片觀看次數 (3秒) |
| `video_p25_watched_actions` | ❌ | 影片觀看至 25% |
| `video_p50_watched_actions` | ❌ | 影片觀看至 50% |
| `video_p75_watched_actions` | ❌ | 影片觀看至 75% |
| `video_p95_watched_actions` | ❌ | 影片觀看至 95% |
| `video_p100_watched_actions` | ❌ | 影片觀看至 100% |
| `video_avg_time_watched_actions` | ❌ | 影片平均觀看時間 |
| `video_30_sec_watched_actions` | ❌ | 影片觀看 30 秒 |
| `video_thruplay_watched_actions` | ❌ | ThruPlay (完整觀看或15秒) |
| `cost_per_thruplay` | ✅ | 單次 ThruPlay 成本 |
| `cost_per_2_sec_continuous_video_view` | ❌ | 單次 2 秒持續觀看成本 |
| `cost_per_15s_video_view` | ❌ | 單次 15 秒觀看成本 |

## Engagement (Post/Page) (11)

| Metric Key | Used in System? | 中文備註 |
| :--- | :---: | :--- |
| `post_engagement` | ✅ | 貼文互動 |
| `post_reactions` | ✅ | 貼文心情 |
| `post_comments` | ✅ | 貼文留言 |
| `post_shares` | ✅ | 貼文分享 |
| `page_likes` | ✅ | 粉專按讚 |
| `page_engagement` | ❌ | 粉專互動 |
| `checkin` | ❌ | 打卡次數 |
| `page_mention` | ❌ | 粉專提及 |
| `photo_view` | ❌ | 照片瀏覽 |
| `social_impressions` | ❌ | 社交曝光 (有好友互動) |
| `social_reach` | ❌ | 社交觸及 |

## Clicks & CTR (9)

| Metric Key | Used in System? | 中文備註 |
| :--- | :---: | :--- |
| `clicks` | ✅ | 所有點擊 |
| `unique_clicks` | ✅ | 不重複點擊 |
| `inline_link_clicks` | ✅ | 連結點擊 (站內) |
| `outbound_clicks` | ❌ | 外連點擊 (導外) |
| `unique_ctr` | ❌ | 不重複點擊率 |
| `inline_link_click_ctr` | ❌ | 連結點擊率 |
| `outbound_clicks_ctr` | ❌ | 外連點擊率 |
| `instant_experience_clicks_to_open` | ❌ | 即時體驗開啟點擊 |
| `instant_experience_clicks_to_start` | ❌ | 即時體驗開始點擊 |

## Conversions & App (15)

| Metric Key | Used in System? | 中文備註 |
| :--- | :---: | :--- |
| `purchase` | ✅ | 購買 |
| `add_to_cart` | ✅ | 加入購物車 |
| `initiate_checkout` | ✅ | 開始結帳 |
| `add_payment_info` | ✅ | 新增付款資訊 |
| `view_content` | ✅ | 查看內容 |
| `lead` | ❌ | 潛在客戶 (名單) |
| `contact` | ❌ | 聯絡 |
| `search` | ❌ | 搜尋 |
| `start_trial` | ❌ | 開始試用 |
| `subscribe` | ❌ | 訂閱 |
| `mobile_app_install` | ❌ | App 安裝 |
| `mobile_app_purchase_roas` | ❌ | App 購買 ROAS |
| `cost_per_mobile_app_install` | ❌ | 單次 App 安裝成本 |
| `app_use` | ❌ | App 使用 |
| `credit_spent` | ❌ | 應用程式內點數花費 |

## Dimensions (Age, Gender, Location) (10)

| Metric Key | Used in System? | 中文備註 |
| :--- | :---: | :--- |
| `date_start` | ✅ | 開始日期 |
| `date_stop` | ✅ | 結束日期 |
| `age` | ❌ | 年齡 (維度) |
| `gender` | ❌ | 性別 (維度) |
| `country` | ❌ | 國家 (維度) |
| `region` | ❌ | 地區 (維度) |
| `dma` | ❌ | DMA 市場 (維度) - **僅限美國** |
| `impression_device` | ❌ | 曝光裝置 (維度) |
| `platform_position` | ❌ | 版位 (維度) |
| `publisher_platform` | ❌ | 發佈平台 (FB/IG/Audience Network) |

## Quality & Diagnostics (6)

| Metric Key | Used in System? | 中文備註 |
| :--- | :---: | :--- |
| `quality_ranking` | ✅ | 品質排名 |
| `engagement_rate_ranking` | ✅ | 互動率排名 |
| `conversion_rate_ranking` | ✅ | 轉換率排名 |
| `quality_score` | ❌ | 品質分數 |
| `estimated_ad_recall_rate` | ❌ | 估計廣告回想率 |
| `estimated_ad_recallers` | ❌ | 估計廣告回想人數 |

## Settings & ID (9)

| Metric Key | Used in System? | 中文備註 |
| :--- | :---: | :--- |
| `account_id` | ✅ | 帳號 ID |
| `campaign_id` | ✅ | 行銷活動 ID |
| `adset_id` | ✅ | 廣告組合 ID |
| `ad_id` | ✅ | 廣告 ID |
| `objective` | ✅ | 行銷目標 |
| `buying_type` | ✅ | 購買類型 |
| `attribution_setting` | ❌ | 歸因設定 |
| `auction_bid` | ⛔ | 競價金額 (**已棄用** - API 無回傳, 測試於 2024-12-23) |
| `auction_competitiveness` | ⛔ | 競價競爭力 (**已棄用** - API 無回傳, 測試於 2024-12-23) |

---

## 🧮 Calculated Metrics (後端計算指標)

以下指標是由系統根據原生資料**計算**產生的，不是直接從 Facebook API 取得。

計算邏輯位於: `backend/service_modules/metrics.py`

### 成本相關

| 指標 Key | 中文名稱 | 計算公式 |
| :--- | :--- | :--- |
| `cpc` | 單次點擊成本 | `spend / link_clicks` |
| `cpm` | 千次曝光成本 | `(spend / impressions) * 1000` |
| `cpa` | 單次購買成本 | `spend / purchases` |
| `cost_per_atc` | 加購成本 | `spend / add_to_cart` |

### 效率相關

| 指標 Key | 中文名稱 | 計算公式 |
| :--- | :--- | :--- |
| `ctr` | 點擊率 | `(link_clicks / impressions) * 100` |
| `roas` | 廣告投報率 | `purchase_value / spend` |
| `aov` | 客單價 | `purchase_value / purchases` |

### 漏斗轉換率

| 指標 Key | 中文名稱 | 計算公式 |
| :--- | :--- | :--- |
| `view_to_cart_rate` | 瀏覽加購率 | `(add_to_cart / view_content) * 100` |
| `cart_to_purchase_rate` | 購物車購買率 | `(purchases / add_to_cart) * 100` |
| `cart_value_realization_rate` | 購物車價值實現率 | `(purchase_value / atc_value) * 100` |
| `cvr` | 購買轉換率 | `(purchases / link_clicks) * 100` |
| `cart_dropoff` | 購物車流失率 | `1 - (purchases / add_to_cart)` |

> **備註**: 上述計算指標在前端 `Analytics.jsx` 的 `calculateSummary()` 函數中也有重複計算，用於 KPI 卡片的即時彙總。
