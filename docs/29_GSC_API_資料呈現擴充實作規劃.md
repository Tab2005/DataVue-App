# GSC API 資料呈現擴充實作規劃

> 建立日期：2026-07-13  
> 狀態：規劃中，尚未實作；**其中第 1 項「Search Appearance 成效」已於 2026-07-17 透過 `docs/35_GSC_AI_Overview_生成式AI搜尋數據擴充實作規劃.md` 實作完成**，其餘項目（Search Type、裝置/國家交叉分析、Fresh Data、Sitemap、URL Inspection）仍待實作。
> 範圍：Google Search Console 模組新增可呈現資料面向，包含 Search Analytics 進階維度、Sitemaps 與 URL Inspection。

## 背景

目前系統的 GSC 模組已能呈現搜尋成效核心資料：

- 網站清單：`siteUrl`、`permissionLevel`
- Search Analytics 指標：`clicks`、`impressions`、`ctr`、`position`
- 已使用維度：`date`、`query`、`page`、`country`、`device`、`page,query`
- 已有衍生功能：頁面標題、頁面關鍵字、頁面趨勢、AI 搜尋意圖、內容缺口分析

Google Search Console API 仍有多個可直接提升 SEO 判讀價值的資料面向尚未呈現。這份文件規劃 1 至 7 項建議新增資料，先定義資料來源、後端端點、前端呈現與實作順序，不進行程式碼修改。

## 目標

1. 擴充 GSC Search Analytics 的可分析維度，讓使用者能看出搜尋外觀、搜尋類型、裝置與地區交叉差異。
2. 新增 Sitemap 健康狀態，補足技術 SEO 檢查入口。
3. 新增 URL Inspection 頁面診斷，讓 Top Pages 或低成效頁面能快速確認索引與結構化資料問題。
4. 保持現有 `/api/gsc/analytics` 相容，避免一次性重構 `GSCStats.jsx` 造成風險。

## 非目標

- 不在本階段建立長期資料倉儲或每日排程快照。
- 不批量自動檢查所有 URL Inspection，避免 API 配額與延遲風險。
- 不改動 OAuth scope，現有 `webmasters.readonly` 已足以支援本規劃的讀取資料。
- 不新增非官方 SEO 指標，例如第三方關鍵字量、難度分數或外鏈資料。

## 現況限制

後端目前 `GSCService.get_analytics()` 只支援：

- `startDate`
- `endDate`
- `dimensions`
- `dimensionFilterGroups`
- `rowLimit`
- `startRow`

尚未支援：

- `type`
- `aggregationType`
- `dataState`
- 回傳 `responseAggregationType`
- 回傳 `metadata`
- Sitemaps API
- URL Inspection API

前端目前主要集中在 `frontend/src/components/GSCStats.jsx`，功能已較大。新增功能時應優先拆成小型子元件，避免單檔繼續膨脹。

## 建議新增項目

### 1. Search Appearance 成效 — 已實作（見 `docs/35`）

> 2026-07-17：此項目已實作，端點為 `GET /api/gsc/search-appearance-summary`，前端為 `frontend/src/components/GSC/SearchAppearanceTab.jsx`（🎨 搜尋外觀分頁）。實作內容與本節規劃略有差異（例如占比分母改用 `dimensions=["date"]` 加總而非直接加總 searchAppearance 各列，避免重複計算），並額外加入 AI 相關關鍵字提示旗標。
>
> **重要澄清**：`searchAppearance` 維度不包含、也不會包含 AI Overview / 生成式 AI 曝光數據——Google 於 2026-06-03 推出的「生成式 AI 效能報表」目前僅限 GSC 後台 UI 查看，尚未透過任何 API 開放（詳見 `docs/35` 的「⚠️ 2026-07-17 重大結論更新」）。此分頁呈現的是既有 Rich Result／AMP／Merchant Listing 等真實搜尋外觀數據，與生成式 AI 報表是兩個互不相干的資料來源。
>
> 以下原規劃內容保留作為歷史記錄，實際規格請見 `docs/35_GSC_AI_Overview_生成式AI搜尋數據擴充實作規劃.md`。

**資料來源**

- Search Analytics `dimensions=["searchAppearance"]`
- 可搭配 `type=web` 或其他搜尋類型
- 可再用 `dimensionFilterGroups` 篩選特定 `searchAppearance`

**可呈現資料**

- 各搜尋外觀的 `clicks`、`impressions`、`ctr`、`position`
- 搜尋外觀流量占比
- CTR 高但曝光低的搜尋外觀
- 曝光高但 CTR 低的搜尋外觀

**前端呈現**

- 在 GSC 頁面新增 Tab：`搜尋外觀`
- 上方 KPI：
  - 搜尋外觀類型數
  - Rich result 點擊占比
  - 最高 CTR 搜尋外觀
  - 最大曝光搜尋外觀
- 主視覺：
  - 橫向長條圖：依點擊排序
  - 表格欄位：`搜尋外觀`、`點擊`、`曝光`、`CTR`、`平均排名`、`占比`
- 互動：
  - 點擊某個搜尋外觀後，下方顯示 `page + searchAppearance` 明細
  - 提供 CSV 匯出

**注意事項**

- Google 已公告 FAQ rich results 不再出現在搜尋結果，API 支援也將移除；UI 不應硬編碼 FAQ 類型，應以 API 回傳值動態呈現。

### 2. Search Type 成效

**資料來源**

- Search Analytics request body 的 `type`
- 可用值包含：`web`、`image`、`video`、`news`、`googleNews`、`discover`

**可呈現資料**

- 不同搜尋類型的總點擊、曝光、CTR、排名
- 各搜尋類型的頁面與關鍵字排行
- 圖片或影片搜尋是否有可開發流量

**前端呈現**

- 在日期篩選列旁新增 `搜尋類型` selector：
  - 預設：`Web`
  - 選項：`Web`、`Image`、`Video`、`News`、`Google News`、`Discover`
- 加入一個比較視圖：`搜尋類型比較`
  - 卡片式排列每個 type 的核心 KPI
  - 點擊任一 type 後套用到既有 Daily / Query / Page tabs
- 表格與圖表沿用現有 `analytics` 資料結構，降低改動。

**後端建議**

- 擴充 `/api/gsc/analytics` query params：
  - `search_type: Optional[str] = "web"`
- 對應到 Search Analytics request body 的 `type`。
- cache key 必須包含 `search_type`。

### 3. Page/Query + Device 交叉分析

**資料來源**

- `dimensions=["page","device"]`
- `dimensions=["query","device"]`

**可呈現資料**

- 同一頁面在 Mobile / Desktop / Tablet 的 CTR 與排名差異
- 同一關鍵字在不同裝置的排名差異
- 手機表現落後的頁面清單

**前端呈現**

- 在 `裝置分佈` tab 增加子頁籤：
  - `總覽`
  - `頁面 x 裝置`
  - `關鍵字 x 裝置`
- 新增診斷表格：
  - `頁面/關鍵字`
  - `Mobile 點擊`
  - `Desktop 點擊`
  - `Mobile CTR`
  - `Desktop CTR`
  - `Mobile 平均排名`
  - `Desktop 平均排名`
  - `差異標籤`
- 差異標籤規則：
  - `Mobile CTR 落後`
  - `Mobile 排名落後`
  - `Desktop 優勢`
  - `樣本不足`
- 提供快速篩選：
  - 只看 Mobile 落後
  - 只看曝光大於指定門檻
  - 只看排名 4-20 的可優化機會

**後端建議**

- 可先沿用 `/api/gsc/analytics?dimensions=page,device`
- 前端負責 pivot。
- 若資料量過大，再新增專用 endpoint 做 server-side aggregate。

### 4. Page/Query + Country 交叉分析

**資料來源**

- `dimensions=["page","country"]`
- `dimensions=["query","country"]`

**可呈現資料**

- 頁面在不同國家的曝光與點擊
- 關鍵字在哪些市場有需求
- 可在地化或翻譯的內容機會

**前端呈現**

- 在 `地區分佈` tab 增加子頁籤：
  - `總覽`
  - `頁面 x 國家`
  - `關鍵字 x 國家`
- 主視覺：
  - 世界/區域流量列表先沿用現有 country mapping，不強制做地圖
  - 表格以國家為欄位 pivot Top 5 國家
- 表格欄位：
  - `頁面/關鍵字`
  - `Top Country`
  - `Top Country Clicks`
  - `Top Country CTR`
  - `第二市場`
  - `在地化機會`
- 在地化機會規則：
  - 曝光高、CTR 低：標記 `需優化標題/摘要`
  - 曝光高、排名 8-20：標記 `內容在地化機會`
  - 多國都有曝光：標記 `多語系擴展候選`

**後端建議**

- 初期沿用現有 `/api/gsc/analytics`。
- cache key 包含 dimensions 即可。
- 若後續加入國家名稱標準化，應在前端 `COUNTRY_NAMES` 之外抽成共用常數。

### 5. Fresh Data / Hourly Data

**資料來源**

- Search Analytics `dataState="all"`
- 小時資料：`dataState="hourly_all"` + `dimensions=["hour"]` 或 `["date","hour"]`
- 回傳 metadata：
  - `first_incomplete_date`
  - `first_incomplete_hour`

**可呈現資料**

- 最近資料是否尚未 finalized
- 今日或昨日小時級走勢
- 暫定資料和正式資料的視覺區隔

**前端呈現**

- 日期選擇器旁新增 `資料狀態` toggle：
  - `正式資料`
  - `包含最新暫定資料`
- Daily tab 中：
  - 對 incomplete date 之後的資料點加上虛線或淡色
  - KPI 卡加上 `暫定` badge
- 新增 `小時趨勢`子區塊：
  - 折線圖：按 hour 顯示 clicks/impressions
  - 表格：`小時`、`點擊`、`曝光`、`CTR`
- 顯示提示：
  - `此區間含尚未完成處理的 Search Console 資料，數值可能變動。`

**後端建議**

- 擴充 `/api/gsc/analytics`：
  - `data_state: Optional[str] = "final"`
  - `include_metadata: bool = False`
- 回傳格式需從目前純 rows 調整為可選 envelope：

```json
{
  "rows": [],
  "responseAggregationType": "auto",
  "metadata": {
    "first_incomplete_date": "2026-07-12"
  }
}
```

**相容策略**

- 預設仍回傳純 rows，避免破壞既有前端。
- 只有 `include_metadata=true` 時回傳 envelope。

### 6. Sitemap 健康狀態

**資料來源**

- Search Console Sitemaps API
- `sitemaps().list(siteUrl=...)`
- `sitemaps().get(siteUrl=..., feedpath=...)`

**可呈現資料**

- `path`
- `lastSubmitted`
- `lastDownloaded`
- `isPending`
- `isSitemapsIndex`
- `type`
- `warnings`
- `errors`
- `contents[].type`
- `contents[].submitted`

**前端呈現**

- 新增 Tab：`Sitemap 健康`
- 上方 KPI：
  - Sitemap 數量
  - 錯誤數總和
  - 警告數總和
  - 最近下載時間
  - Pending 數量
- 主表格：
  - `Sitemap URL`
  - `類型`
  - `提交時間`
  - `最後下載`
  - `狀態`
  - `錯誤`
  - `警告`
  - `提交 URL 數`
- 狀態 badge：
  - `正常`
  - `待處理`
  - `有警告`
  - `有錯誤`
- 點開 Sitemap row：
  - 顯示 contents 類型明細，例如 web/image/video/news 的 submitted 數量。

**後端建議**

- 新增 endpoint：
  - `GET /api/gsc/sitemaps?site_url=...`
  - `GET /api/gsc/sitemaps/detail?site_url=...&sitemap_url=...`
- 只做讀取，不提供 submit/delete，避免誤操作。
- cache TTL 可較長，建議 30-60 分鐘。

### 7. URL Inspection 頁面診斷

**資料來源**

- URL Inspection API
- `POST https://searchconsole.googleapis.com/v1/urlInspection/index:inspect`

**可呈現資料**

- `inspectionResultLink`
- `indexStatusResult.verdict`
- `coverageState`
- `robotsTxtState`
- `indexingState`
- `lastCrawlTime`
- `pageFetchState`
- `googleCanonical`
- `userCanonical`
- `crawledAs`
- `sitemap[]`
- `referringUrls[]`
- `ampResult`
- `richResultsResult`

**前端呈現**

- 不建議新增全站批量頁面，先做成 `頁面分析` tab 的 row action：
  - 按鈕：`檢查索引`
  - 開啟右側 drawer 或 modal
- Drawer 區塊：
  - `索引總覽`
  - `抓取與 robots`
  - `Canonical`
  - `Sitemap / Referring URLs`
  - `AMP`
  - `Rich Results`
- 狀態顯示：
  - `PASS` → 綠色
  - `FAIL` → 紅色
  - `NEUTRAL` → 灰色
  - `UNKNOWN` → 黃色
- 在 Page table 可加一欄 `索引狀態`，但只顯示已查過且有快取的 URL，避免自動大量請求。

**後端建議**

- 新增 endpoint：
  - `POST /api/gsc/url-inspection`
- Request：

```json
{
  "site_url": "sc-domain:example.com",
  "inspection_url": "https://www.example.com/page",
  "language_code": "zh-TW"
}
```

- Response：

```json
{
  "inspectionResult": {
    "inspectionResultLink": "...",
    "indexStatusResult": {},
    "ampResult": {},
    "richResultsResult": {}
  },
  "cached": false,
  "fetched_at": "2026-07-13T00:00:00Z"
}
```

**配額與風險控制**

- 必須由使用者點擊觸發，不自動批量檢查。
- 加入短期快取，建議 12-24 小時。
- 同一 user/site/url 應有 rate limit。
- 查詢失敗時保留錯誤訊息，不影響 GSC 主表格。

## 後端 API 整體規劃

### A. 擴充現有 Analytics Endpoint

現有：

```http
GET /api/gsc/analytics
```

新增 query params：

- `search_type`: `web | image | video | news | googleNews | discover`
- `data_state`: `final | all | hourly_all`
- `aggregation_type`: `auto | byPage | byProperty`
- `include_metadata`: `boolean`

相容原則：

- 未傳新參數時，維持目前行為。
- 預設仍只回傳 rows。
- `include_metadata=true` 時才回傳 envelope。
- cache key 必須包含所有新增參數。

### B. 新增 Sitemaps Endpoint

```http
GET /api/gsc/sitemaps?site_url={site_url}
GET /api/gsc/sitemaps/detail?site_url={site_url}&sitemap_url={sitemap_url}
```

只讀取，不做 submit/delete。

### C. 新增 URL Inspection Endpoint

```http
POST /api/gsc/url-inspection
```

只允許檢查 `inspection_url` 屬於 `site_url` property 下的 URL。

## 前端架構規劃

目前 `GSCStats.jsx` 已承載過多功能。新增 1-7 項時，建議先拆出以下元件，再逐步接入：

- `GSCDateControls.jsx`：日期、比較、搜尋類型、資料狀態控制。
- `GSCTabNav.jsx`：tab 切換。
- `GSCSearchAppearanceTab.jsx`：搜尋外觀。
- `GSCSearchTypeComparison.jsx`：搜尋類型比較。
- `GSCDeviceCrossTab.jsx`：page/query + device。
- `GSCCountryCrossTab.jsx`：page/query + country。
- `GSCHourlyTrend.jsx`：fresh/hourly data。
- `GSCSitemapHealthTab.jsx`：Sitemap 健康。
- `GSCUrlInspectionDrawer.jsx`：URL Inspection drawer。

### 建議新增 Tabs

- `搜尋外觀`
- `搜尋類型`
- `Sitemap 健康`

### 建議擴充既有 Tabs

- `每日成效`
  - 加入 fresh data / hourly data 呈現。
- `頁面分析`
  - 加入 `檢查索引` row action。
  - 顯示已查過的索引狀態 badge。
- `地區分佈`
  - 加入 `頁面 x 國家`、`關鍵字 x 國家` 子頁籤。
- `裝置分佈`
  - 加入 `頁面 x 裝置`、`關鍵字 x 裝置` 子頁籤。

## 實作階段

### Phase 1：低風險 Search Analytics 擴充

範圍：

- `search_type`
- `searchAppearance`
- `page/query + device`
- `page/query + country`

原因：

- 都可沿用 Search Analytics API。
- 不需新增 OAuth scope。
- 可重用現有 cache、pagination、table rendering。

驗收：

- 可切換搜尋類型。
- 可看到搜尋外觀排行。
- 裝置交叉表能找出 Mobile 落後頁面。
- 國家交叉表能找出在地化機會。

### Phase 2：Fresh / Hourly Data

範圍：

- `dataState=all`
- `dataState=hourly_all`
- metadata 顯示

原因：

- 需要調整 response shape，需謹慎保持相容。
- UI 必須清楚標示暫定資料。

驗收：

- 使用者能切換正式資料/暫定資料。
- incomplete date/hour 被明確標記。
- 小時級資料正常顯示。

### Phase 3：Sitemap 健康

範圍：

- Sitemaps list/detail endpoint。
- Sitemap 健康 tab。

原因：

- 技術 SEO 價值高。
- 與 Search Analytics 資料結構不同，應獨立實作。

驗收：

- 顯示 sitemap 錯誤、警告、最後下載、提交 URL 數。
- 有錯誤或 pending 的 sitemap 被清楚標記。

### Phase 4：URL Inspection

範圍：

- URL inspection endpoint。
- Page tab row action。
- Inspection drawer。

原因：

- 高價值但配額與延遲風險最高。
- 必須設計成使用者手動觸發。

驗收：

- 使用者可針對單一頁面檢查索引狀態。
- Drawer 顯示索引、canonical、robots、rich results。
- 查詢結果有快取，重複打開不重打 API。

## 風險與對策

| 風險 | 影響 | 對策 |
|---|---|---|
| `GSCStats.jsx` 繼續膨脹 | 維護成本升高 | 新功能先拆元件 |
| GSC API 回傳資料列上限 | 部分長尾資料不可得 | 使用 pagination，但 UI 標示 top rows 限制 |
| URL Inspection 配額限制 | 批量檢查可能失敗 | 僅手動觸發 + 快取 + rate limit |
| Fresh data 尚未 finalized | 使用者誤判成正式結果 | 明確顯示暫定 badge 與說明 |
| `include_metadata` 改變 response shape | 破壞既有前端 | 預設維持純 rows |
| Search Appearance 類型變動 | UI 顯示錯誤 | 不硬編碼類型，動態呈現 API 回傳值 |

## 測試規劃

### 後端

- `GET /api/gsc/analytics` 未傳新參數時維持原本 rows response。
- `search_type` 會正確映射到 API request body `type`。
- `data_state` 會正確映射到 API request body `dataState`。
- `include_metadata=true` 時回傳 envelope。
- cache key 包含 `search_type`、`data_state`、`aggregation_type`。
- Sitemaps endpoint 在無資料、有 warning、有 error 時皆能正確回傳。
- URL Inspection endpoint 驗證 URL 屬於指定 property。

### 前端

- 搜尋類型切換後，所有既有 tab 重新抓取對應 type 資料。
- 搜尋外觀 tab 在空資料時顯示 empty state。
- 裝置/國家交叉表可排序、篩選、匯出。
- Fresh data 顯示暫定標記。
- Sitemap tab 顯示錯誤/警告 badge。
- URL Inspection drawer loading、success、error、cached 狀態皆正常。

## 文件與產品文案

新增功能完成後應同步更新：

- `docs/05_API_參考手冊.md`
- `docs/01_專案概覽.md`
- GSC 頁面上的 tooltip 與 empty state 文案

建議 tooltip 文案：

- `搜尋外觀：Google 搜尋結果中不同呈現形式的成效，例如影片、圖片、結構化資料或其他搜尋功能。`
- `暫定資料：Google 尚未完成處理的近期資料，數值可能變動。`
- `URL Inspection：檢查 Google 索引中目前已知的頁面狀態，非即時 live test。`

## 官方參考

- Search Analytics API: `https://developers.google.com/webmaster-tools/v1/searchanalytics/query`
- Sitemaps API: `https://developers.google.com/webmaster-tools/v1/sitemaps`
- URL Inspection API: `https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect`
- URL Inspection Result: `https://developers.google.com/webmaster-tools/v1/urlInspection.index/UrlInspectionResult`
