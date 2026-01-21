# GA4 可用指標與維度（對照 GA4 Data API 名稱）

下列為常用指標與維度，右側為 GA4 Data API 中的「正式 name」。如需完整清單或自訂維度／指標，請使用 Metadata API（properties.getMetadata）。來源：Google Analytics Data API 官方文件。

## 使用者
- 活躍使用者：`activeUsers`
- 使用者總數：`totalUsers`
- 新使用者：`newUsers`

## 工作階段 / 參與度
- 工作階段：`sessions`
- 互動工作階段：`engagedSessions`
- 參與度（互動率）：`engagementRate`
- 平均工作階段持續時間（秒）：`averageSessionDuration`
- 觀看次數（頁面/畫面）：`screenPageViews`

## 事件與轉換
- 事件計數：`eventCount`
- 事件名稱（維度）：`eventName`
- 事件價值：`eventValue`

## 網頁 / 內容
- 網頁路徑（path）：`pagePath`
- 網頁標題：`pageTitle`
- 網頁完整位置（URL）：`pageLocation`

## 流量 / 廣告活動
- 來源（source）：`source`
- 媒介（medium）：`medium`
- 廣告活動（campaign）：`campaign`
- 預設管道群組（工作階段）：`sessionDefaultChannelGroup` 或 `defaultChannelGroup`
- 來源/媒介（合併）：`sourceMedium`

## 電子商務 / 獲利
- 購買收益：`purchaseRevenue`
- 電子商務購買次數：`ecommercePurchases`
- 交易（含購買事件計數）：`transactions`
- 商品收益：`itemRevenue`
- 已購買的商品數：`itemsPurchased`

## 裝置 / 技術
- 裝置類別：`deviceCategory`
- 裝置型號：`deviceModel`
- 作業系統：`operatingSystem`
- 平台：`platform`

## 地理
- 國家/地區：`country`
- 區域（region）：`region`
- 城市：`city`

## 時間
- 日期（YYYYMMDD）：`date`
- 小時：`hour`
- 日期+小時：`dateHour`
- 年月合併：`yearMonth`

## 使用者屬性（內建 / 範例）
- 年齡區間：`userAgeBracket`
- 性別：`userGender`
- 最初工作階段日期：`firstSessionDate`

## 其他有用欄位
- 畫面/頁面檢視（每工作階段）：`screenPageViewsPerSession`
- 每位使用者事件數：`eventCountPerUser`
- 跳出率：`bounceRate`
- 總收益：`totalRevenue`

---
註：
- 此檔列出常見且在實務中常用的 API 欄位名稱；GA4 Data API 的完整維度與指標表極為詳細（含廣告、Search Console、廣告平台整合欄位與大量商品層級維度），如需完整清單或動態查詢某個 property 的自訂欄位，請使用 Metadata API：

- Metadata API 範例：`GET https://analyticsdata.googleapis.com/v1beta/properties/{propertyId}:getMetadata`

### FAQ — Metadata API 與權限

- 問：有 GA4 Data API 權限就能呼叫 Metadata API 嗎？
- 答：是的。Metadata API 屬於 Google Analytics Data API 生態系的一部分，通常使用相同的 OAuth scope（例如 `https://www.googleapis.com/auth/analytics.readonly`）。只要你的 OAuth token 有讀取 Analytics 的權限，且該帳號/服務帳號可以存取目標 property，就能呼叫 `properties:getMetadata` 來取得該 property 可用的維度與指標（含自訂欄位）。

- 注意事項：
	- Metadata 回傳的是該 property 支援的欄位清單與欄位細節，但並不會回傳實際的報表資料（報表資料仍由 Data API 回傳）。
	- 某些自訂維度/指標或重要事件的字串必須依照 Metadata 提供的格式使用（例如 `customEvent:parameter_name[event_name]`）。
	- 若你的帳號沒有對該 property 的存取權，Metadata API 也會因授權錯誤而失敗；管理員層級通常不是必要，但 property 的讀取權限必須存在。

需要我把這份對照轉成 JSON（供前端下拉選單使用）或把某些常用組合加入到後端預設範本嗎？
