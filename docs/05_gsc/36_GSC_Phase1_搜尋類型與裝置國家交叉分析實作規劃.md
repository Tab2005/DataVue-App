# GSC Phase 1：搜尋類型、裝置交叉、國家交叉 實作規劃

> 建立日期：2026-07-21
> 狀態：規劃中，尚未實作
> 範圍：`docs/29` 第 2-4 項（搜尋類型成效、Page/Query × Device 交叉、Page/Query × Country 交叉）的細部實作規劃，聚焦低風險、可沿用現有 Search Analytics API 與 `/api/gsc/analytics` 端點的擴充。
> 前置關聯：延伸自 [`docs/29_GSC_API_資料呈現擴充實作規劃.md`](./29_GSC_API_資料呈現擴充實作規劃.md) 的「Phase 1：低風險 Search Analytics 擴充」，本文件為該階段的落地實作規劃（含現況程式碼盤點與具體改動點），第 1 項「搜尋外觀」已於 `docs/35` 完成，不在本文件範圍內。

## 背景

`docs/29` 建立於 2026-07-13，規劃了 7 項 GSC 資料擴充，其中第 1 項已透過 `docs/35` 完成。第 2-4 項（搜尋類型、裝置交叉、國家交叉）被歸類為「Phase 1：低風險」，原因是三者都只需要 Search Analytics API 既有能力，不需新增 OAuth scope，也不需要新建 endpoint（沿用 `/api/gsc/analytics`）。本文件盤點目前實際程式碼現況，並將三項整理為可執行的實作步驟。

**現況程式碼盤點（2026-07-21 確認）**：

- `backend/gsc_service.py` 的 `GSCService.get_analytics()`（第 201 行起）簽章為：
  ```python
  def get_analytics(user, site_url, start_date, end_date, dimensions=['date'],
                     limit=None, offset=0, db=None, dimension_filters=None)
  ```
  內部組出的 `request_body`（第 281-285 行）只帶 `startDate`、`endDate`、`dimensions`，需要時才加上 `dimensionFilterGroups`、`rowLimit`、`startRow`。**目前完全沒有 `type` 欄位**，確認 `docs/29` 對現況限制的描述仍然正確。
- `backend/routers/gsc.py` 的 `GET /analytics`（第 68-91 行）目前參數為 `site_url`、`start_date`、`end_date`、`dimensions`（逗號分隔字串）、`limit`、`offset`，沒有 `search_type` 或裝置/國家專屬參數。`dimensions` 是直接 `.split(",")` 後透傳給 service 層，代表**裝置/國家交叉分析的維度組合（`page,device`、`query,device`、`page,country`、`query,country`）技術上已經可以透過現有端點做到**，缺的只是前端呈現。
- 前端 `frontend/src/components/GSC/constants.js` 的 `TABS`（第 25-34 行）目前 8 個分頁：`daily`、`query`、`page`、`trend`、`country`、`device`、`gap`、`searchAppearance`，皆為單一 dimension，沒有子頁籤結構。
- `frontend/src/components/GSC/DeviceTab.jsx`、`CountryTab.jsx` 目前各自只呈現單一維度（`device`、`country`）的排行，未做交叉。

## 目標

1. 新增「搜尋類型」（Search Type）篩選能力，讓使用者能查看 Image／Video／News／Discover 等非 Web 搜尋流量。
2. 在既有「裝置分佈」「地區分佈」分頁內新增交叉分析子頁籤，找出行動裝置落後頁面、跨國市場機會。
3. 全程沿用 `/api/gsc/analytics` 單一端點與既有快取機制，不新增 OAuth scope，不破壞現有分頁行為。

## 非目標

- 不含 Fresh/Hourly Data、Sitemap 健康、URL Inspection（見 `docs/29` 第 5-7 項，需另立文件）。
- 不含 Core Web Vitals、行動裝置可用性報表、GA4 交叉比對、CSV 匯出（`docs/29` 範圍外的缺口，需另立文件）。
- 不在本階段做語意關鍵字分群或排程異常警示。
- 不因新增 `search_type` 而重構既有 `dimensions` 參數格式，維持向後相容。

## 建議實作項目

### 1. 搜尋類型（Search Type）成效

**後端改動**：
- `GSCService.get_analytics()` 新增可選參數 `search_type: Optional[str] = None`，非 `None` 時寫入 `request_body['type']`。
- `routers/gsc.py` 的 `GET /analytics` 新增 query 參數 `search_type: Optional[str] = None`（可用值：`web`、`image`、`video`、`news`、`googleNews`、`discover`，交由 Google API 端驗證，本專案不重複做 enum 檢查以避免未來 Google 新增類型時要改程式碼）。
- cache key（`generate_cache_key` 呼叫處的 `cache_params`）必須加入 `search_type`，否則不同搜尋類型會共用錯誤的快取結果。

**前端改動**：
- 在既有的日期篩選列旁新增「搜尋類型」selector（預設 `Web`），影響 `daily`、`query`、`page`、`trend` 四個既有分頁的資料抓取，不新增獨立比較 tab（`docs/29` 原規劃的「搜尋類型比較」卡片式視圖可留待有實際需求時再做，避免一次改動過大）。
- `useGscAnalytics.js` 的請求參數需帶入目前選擇的 `search_type`。

### 2. Page/Query × Device 交叉分析

**後端改動**：無需新增程式碼，直接呼叫既有 `GET /analytics?dimensions=page,device` 或 `dimensions=query,device`。

**前端改動**：
- `DeviceTab.jsx` 內新增子頁籤：`總覽`（現有內容）、`頁面 x 裝置`、`關鍵字 x 裝置`。
- 交叉頁籤呼叫 `dimensions=page,device`／`query,device`，前端自行 pivot 成「Mobile 點擊／Desktop 點擊／Mobile CTR／Desktop CTR／Mobile 平均排名／Desktop 平均排名／差異標籤」表格。
- 差異標籤規則沿用 `docs/29`：`Mobile CTR 落後`、`Mobile 排名落後`、`Desktop 優勢`、`樣本不足`（例如曝光低於門檻時標記樣本不足，避免小樣本誤判）。

### 3. Page/Query × Country 交叉分析

**後端改動**：無需新增程式碼，直接呼叫既有 `GET /analytics?dimensions=page,country` 或 `dimensions=query,country`。

**前端改動**：
- `CountryTab.jsx` 內新增子頁籤：`總覽`、`頁面 x 國家`、`關鍵字 x 國家`。
- 表格以國家為欄位 pivot Top 5 國家，沿用現有 `COUNTRY_NAMES` 對照表。
- 在地化機會規則沿用 `docs/29`：曝光高、CTR 低 → `需優化標題/摘要`；曝光高、排名 8-20 → `內容在地化機會`；多國都有曝光 → `多語系擴展候選`。

## 實作順序建議

1. 先做「搜尋類型」——改動集中在單一參數穿透（service → router → 一個 selector 元件），影響面小，可先驗證 `type` 參數在此專案 OAuth scope 下確實可用。
2. 再做「裝置交叉」——沿用已驗證的多維度 dimensions 呼叫模式。
3. 最後做「國家交叉」——與裝置交叉共用 pivot 邏輯，可重構出共用的 pivot/差異標籤 hook 或工具函式，避免 `DeviceTab.jsx`／`CountryTab.jsx` 重複程式碼。

## 風險與對策

| 風險 | 影響 | 對策 |
|---|---|---|
| `search_type` 快取 key 漏加參數 | 不同搜尋類型顯示同一份快取資料 | 明確在 `cache_params` 加入 `search_type`，並補測試驗證不同 `search_type` 產生不同 cache key |
| 裝置/國家交叉查詢的資料列上限（25000 rows） | 長尾頁面/關鍵字交叉資料被截斷 | 沿用既有 pagination 機制，UI 標示僅顯示 Top N 結果 |
| `DeviceTab.jsx`／`CountryTab.jsx` 子頁籤增加後檔案膨脹 | 維護成本升高，與 `docs/33` 大型檔案拆分原則衝突 | 交叉分析拆成獨立子元件（如 `DeviceCrossView.jsx`、`CountryCrossView.jsx`），由 Tab 檔案引入 |
| Search Type 為 `image`/`video`/`news` 時部分站台完全無資料 | 使用者誤以為功能故障 | 沿用專案既有空狀態設計模式，顯示明確空狀態文案而非空白表格 |

## 測試規劃

**後端**：
- `search_type` 未傳時，`request_body` 不含 `type` 欄位，行為與現況一致。
- `search_type` 傳入時，正確映射到 `request_body['type']`。
- 不同 `search_type` 產生不同 cache key（可用 mock 驗證 `generate_cache_key` 呼叫參數）。

**前端**：
- 搜尋類型切換後，`daily`/`query`/`page`/`trend` 分頁重新抓取對應 type 資料。
- 裝置/國家交叉子頁籤在有資料、無資料兩種情境下正確顯示。
- 差異標籤／在地化機會規則的邊界值（如曝光剛好等於門檻）行為符合預期。

## 文件同步

實作完成後應更新：
- `docs/05_API_參考手冊.md`：`/api/gsc/analytics` 新增 `search_type` 參數說明。
- `docs/29_GSC_API_資料呈現擴充實作規劃.md`：標記第 2-4 項為已透過本文件（`docs/36`）實作完成，並記錄實際做法與原規劃的差異（若有）。

## 官方參考

- Search Analytics API: `https://developers.google.com/webmaster-tools/v1/searchanalytics/query`
