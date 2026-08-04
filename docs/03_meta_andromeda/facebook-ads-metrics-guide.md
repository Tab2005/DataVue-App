# Facebook Ads 指標完整說明

> 本文件說明 DataVue 系統中所有 Facebook Ads 指標的定義、計算方式和應用場景

## 📊 目錄

- [通用指標](#通用指標)
- [電商指標](#電商指標)
- [漏斗指標](#漏斗指標)
- [互動指標](#互動指標)
- [影音指標](#影音指標)
- [訊息指標](#訊息指標)
- [名稱優化建議](#名稱優化建議)

---

## 通用指標

### 基礎數據

#### 花費金額 (Spend)
- **欄位**: `spend`
- **格式**: 貨幣
- **說明**: 廣告實際花費的總金額
- **應用**: 預算管理、ROI 計算

#### 曝光次數 (Impressions)
- **欄位**: `impressions`
- **格式**: 數字
- **說明**: 廣告被展示的總次數(包含重複)
- **應用**: 觸及規模評估

#### 觸及人數 (Reach)
- **欄位**: `reach`
- **格式**: 數字
- **說明**: 看過廣告的不重複用戶數
- **應用**: 實際受眾規模

#### 頻率 (Frequency)
- **欄位**: `frequency`
- **格式**: 小數
- **計算**: 曝光次數 ÷ 觸及人數
- **說明**: 平均每位用戶看到廣告的次數
- **應用**: 避免廣告疲勞(建議 < 3)

---

### 點擊相關指標 (關鍵!)

#### ⭐ CTR - 點擊率 (All Clicks)
- **欄位**: `ctr`
- **格式**: 百分比
- **計算**: (所有點擊 ÷ 曝光次數) × 100%
- **包含點擊類型**:
  - 讚、愛心、哈哈等所有反應
  - 留言、分享
  - 個人資料點擊
  - 相片/影片查看
  - **連結點擊**
  - 其他所有互動
- **應用**: 
  - ✅ 品牌曝光型廣告
  - ✅ 貼文互動型廣告
  - ❌ 不適合電商導流廣告

#### ⭐⭐⭐ 連結點擊率 (Link Click CTR) - 重要!
- **欄位**: `inline_link_click_ctr`
- **格式**: 百分比
- **計算**: (連結點擊 ÷ 曝光次數) × 100%
- **只包含**: 
  - CTA 按鈕點擊(「立即購買」「了解更多」等)
  - 廣告中的網址連結點擊
  - **真正導向網站的點擊**
- **應用**:
  - ✅✅✅ 電商導流廣告(最重要)
  - ✅✅✅ 網站轉換型廣告
  - ✅ Landing Page 優化

#### 點擊次數 (全部) (All Clicks)
- **欄位**: `clicks`
- **格式**: 數字
- **說明**: 所有類型的點擊總數
- **應用**: 整體互動評估

#### 連結點擊次數 (Link Clicks)
- **欄位**: `link_clicks`
- **來源**: `inline_link_clicks`
- **格式**: 數字
- **說明**: 導向網站的連結點擊總數
- **應用**: 實際流量計算

#### 不重複點擊次數 (Unique Clicks)
- **欄位**: `unique_clicks`
- **格式**: 數字
- **說明**: 不重複用戶的點擊次數
- **應用**: 真實點擊用戶數

#### 不重複點擊率 (Unique CTR)
- **欄位**: `unique_ctr`
- **格式**: 百分比
- **計算**: (不重複點擊 ÷ 觸及人數) × 100%

#### 外連點擊次數 (Outbound Clicks)
- **欄位**: `outbound_clicks`
- **格式**: 數字
- **說明**: 離開 Facebook 平台的點擊
- **應用**: 站外流量追蹤

#### 外連點擊率 (Outbound CTR)
- **欄位**: `outbound_clicks_ctr`
- **格式**: 百分比
- **計算**: (外連點擊 ÷ 曝光次數) × 100%

---

### 成本指標

#### CPC (單次點擊成本)
- **欄位**: `cpc`
- **格式**: 貨幣
- **計算**: 花費 ÷ 點擊次數
- **說明**: 每次點擊的平均成本(所有點擊)
- **基準**: 依產業而異,台灣電商約 NT$5-15

#### CPM (千次曝光成本)
- **欄位**: `cpm`
- **格式**: 貨幣
- **計算**: (花費 ÷ 曝光次數) × 1000
- **說明**: 每 1000 次曝光的成本
- **基準**: 台灣市場約 NT$30-100

#### 單次連結點擊成本 (Cost per Link Click)
- **欄位**: `cost_per_inline_link_click`
- **格式**: 貨幣
- **計算**: 花費 ÷ 連結點擊次數
- **說明**: 每次真實導流的成本
- **應用**: 電商廣告最重要的成本指標

#### CPP (每千人觸及成本)
- **欄位**: `cpp`
- **格式**: 貨幣
- **計算**: (花費 ÷ 觸及人數) × 1000
- **應用**: 品牌曝光效率

---

## 電商指標

### 購買相關

#### 購買次數 (Purchases)
- **欄位**: `purchases`
- **來源**: `actions` (action_type: 'purchase')
- **格式**: 數字
- **說明**: 廣告帶來的購買轉換次數
- **歸因窗口**: 通常為 7 天點擊 + 1 天瀏覽

#### 購買轉換價值 (Purchase Value)
- **欄位**: `purchase_value`
- **來源**: `action_values` (action_type: 'purchase')
- **格式**: 貨幣
- **說明**: 廣告帶來的總購買金額

#### CPA (單次購買成本)
- **欄位**: `cpa`
- **格式**: 貨幣
- **計算**: 花費 ÷ 購買次數
- **說明**: 每筆訂單的廣告成本
- **應用**: 電商最重要的指標之一

#### 購買 ROAS (Return on Ad Spend)
- **欄位**: `roas`
- **格式**: 小數
- **計算**: 購買轉換價值 ÷ 花費
- **說明**: 廣告投資報酬率
- **基準**: 
  - ROAS > 3: 優秀
  - ROAS 2-3: 良好
  - ROAS < 2: 需優化

### 購物車相關

#### 加到購物車次數 (Add to Cart)
- **欄位**: `add_to_cart`
- **來源**: `actions` (action_type: 'add_to_cart')
- **格式**: 數字
- **說明**: 用戶將商品加入購物車的次數

#### 加到購物車的轉換值 (ATC Value)
- **欄位**: `atc_value`
- **來源**: `action_values` (action_type: 'add_to_cart')
- **格式**: 貨幣
- **說明**: 加入購物車商品的總價值

#### 加入購物車成本 (Cost per ATC)
- **欄位**: `cost_per_atc`
- **格式**: 貨幣
- **計算**: 花費 ÷ 加到購物車次數

#### 開始結帳次數 (Initiate Checkout)
- **欄位**: `initiate_checkout`
- **來源**: `actions` (action_type: 'initiate_checkout')
- **格式**: 數字
- **說明**: 用戶開始結帳流程的次數

#### 新增付款資訊次數 (Add Payment Info)
- **欄位**: `add_payment_info`
- **來源**: `actions` (action_type: 'add_payment_info')
- **格式**: 數字

#### 瀏覽內容次數 (View Content)
- **欄位**: `view_content`
- **來源**: `actions` (action_type: 'view_content')
- **格式**: 數字
- **說明**: 用戶查看商品頁面的次數

---

## 漏斗指標

#### 購買轉換率 (CVR)
- **欄位**: `cvr`
- **格式**: 百分比
- **計算**: (購買次數 ÷ 連結點擊次數) × 100%
- **說明**: 點擊進站後的購買轉換率
- **基準**: 2-5% 為正常範圍

#### 查看後購物車加入率 (View to Cart)
- **欄位**: `view_to_cart`
- **格式**: 百分比
- **計算**: (加購次數 ÷ 瀏覽內容次數) × 100%

#### 購物車購買率 (Cart Purchase Rate)
- **欄位**: `cart_conversion`
- **格式**: 百分比
- **計算**: (購買次數 ÷ 加購次數) × 100%
- **說明**: 加購後實際購買的比率

#### 廣告購物車流失率 (Cart Dropoff)
- **欄位**: `cart_dropoff`
- **格式**: 百分比
- **計算**: (1 - 購買次數 ÷ 加購次數) × 100%
- **應用**: 找出結帳流程問題

---

## 互動指標

#### 貼文留言 (Comments)
- **欄位**: `post_comments`
- **來源**: `actions` (action_type: 'comment')
- **格式**: 數字

#### 貼文儲存 (Saves)
- **欄位**: `post_saves`
- **來源**: `actions` (action_type: 'onsite_conversion.post_save')
- **格式**: 數字

#### 貼文分享 (Shares)
- **欄位**: `post_shares`
- **來源**: `actions` (action_type: 'post')
- **格式**: 數字

#### 貼文互動 (Post Engagement)
- **欄位**: `post_engagement`
- **來源**: `actions` (action_type: 'post_engagement')
- **格式**: 數字
- **說明**: 所有貼文互動的總和

#### 貼文心情 (Reactions)
- **欄位**: `post_reactions`
- **來源**: `actions` (action_type: 'post_reaction')
- **格式**: 數字
- **包含**: 讚、愛心、哈哈、哇、嗚、怒

#### 粉絲專頁按讚 (Page Likes)
- **欄位**: `page_likes`
- **來源**: `actions` (action_type: 'like')
- **格式**: 數字

---

## 影音指標

#### 影片觀看次數 (Video Views)
- **欄位**: `video_views`
- **來源**: `actions` (action_type: 'video_view')
- **格式**: 數字
- **定義**: 播放 3 秒以上

#### ThruPlay
- **欄位**: `video_thruplay`
- **格式**: 數字
- **定義**: 完整播放或播放至少 15 秒

#### 影片觀看進度
- **25%**: `video_p25_watched`
- **50%**: `video_p50_watched`
- **75%**: `video_p75_watched`
- **100%**: `video_p100_watched`

#### 平均觀看時間 (Avg Watch Time)
- **欄位**: `video_avg_time_watched`
- **格式**: 秒數

#### 每次 ThruPlay 成本
- **欄位**: `cost_per_thruplay`
- **格式**: 貨幣
- **計算**: 花費 ÷ ThruPlay 次數

---

## 訊息指標

#### 首次訊息回覆 (First Reply)
- **欄位**: `messaging_first_reply`
- **來源**: `actions` (action_type: 'onsite_conversion.messaging_first_reply')
- **格式**: 數字

#### 開始對話 (Conversation Started)
- **欄位**: `messaging_conversation_started`
- **格式**: 數字

#### 每則訊息成本 (Cost per Message)
- **欄位**: `cost_per_message`
- **格式**: 貨幣
- **計算**: 花費 ÷ 首次訊息回覆

---

## 名稱優化建議

### 問題
目前系統中有兩個名稱相似的 CTR 指標容易混淆:
- `ctr` - "CTR (連結點擊率)"
- `inline_link_click_ctr` - "連結點擊率"

### 建議優化方案

#### 方案 A: 明確區分用途 (推薦)
```
ctr                      → "CTR (全部點擊率)"
inline_link_click_ctr    → "連結點擊率" 或 "網站點擊率"
```

#### 方案 B: 突出電商導向
```
ctr                      → "互動點擊率 (CTR)"
inline_link_click_ctr    → "導流點擊率" 或 "轉換點擊率"
```

#### 方案 C: 英文縮寫區分
```
ctr                      → "CTR (All Clicks)"
inline_link_click_ctr    → "Link CTR" 或 "LCTR"
```

### 推薦方案
**方案 A** 最適合:
- **CTR (全部點擊率)** - 清楚說明包含所有互動
- **連結點擊率** - 簡潔明瞭,符合電商需求

---

## 📌 快速參考

### 電商廣告必看指標
1. ⭐⭐⭐ **連結點擊率** (`inline_link_click_ctr`)
2. ⭐⭐⭐ **購買 ROAS** (`roas`)
3. ⭐⭐⭐ **CPA** (`cpa`)
4. ⭐⭐ **購買轉換率** (`cvr`)
5. ⭐⭐ **單次連結點擊成本** (`cost_per_inline_link_click`)

### 品牌曝光廣告必看指標
1. ⭐⭐⭐ **觸及人數** (`reach`)
2. ⭐⭐⭐ **CPM** (`cpm`)
3. ⭐⭐ **CTR (全部點擊率)** (`ctr`)
4. ⭐⭐ **貼文互動** (`post_engagement`)
5. ⭐ **頻率** (`frequency`)

---

## 更新日誌

- **2026-02-05**: 初版建立,包含所有主要 Facebook Ads 指標定義
