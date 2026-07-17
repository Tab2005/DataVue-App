# GSC AI Overview（生成式 AI 搜尋）數據擴充實作規劃

> 建立日期：2026-07-17
> 狀態：規劃中，尚未實作
> 範圍：透過 Google Search Console Search Analytics API 的 `searchAppearance` 維度，擷取網站在 AI Overview / 生成式 AI 搜尋結果中的成效數據。
> 前置關聯：本文件延伸自 [`docs/29_GSC_API_資料呈現擴充實作規劃.md`](./29_GSC_API_資料呈現擴充實作規劃.md) 第 1 項「Search Appearance 成效」，聚焦 AI Overview 這個子項目並補上專屬的驗證、風險與文案規劃。

## 背景

使用者詢問「專案內 GSC 的 API 能否抓到生成式 AI 的數據」，經程式碼盤點確認：

- `backend/gsc_service.py` 的 `GSCService.get_analytics()`（約第 184-337 行）目前 request body 只帶 `startDate`、`endDate`、`dimensions`、`dimensionFilterGroups`、`rowLimit`、`startRow`，**未傳入 `searchAppearance` 維度**。
- `backend/routers/gsc.py` 目前所有端點寫死的 `dimensions` 僅有 `date`、`query`、`page`、`country`、`device`、`page,query`，**沒有任何端點使用 `searchAppearance`**。
- `frontend/src/components/GSCStats.jsx` 的分頁僅有 `trend`、`country`、`device`、`gap`、`query`、`page`，**沒有搜尋外觀 tab**。
- 專案內 `google-generativeai`（Gemini SDK）依賴是站內「AI 搜尋意圖分析」等自建功能使用，與 GSC 官方的 AI Overview 報表是兩個不同的資料來源，避免混淆。

**GSC API 本身的能力**：Google Search Console 的 Search Analytics API（`searchanalytics.query`）自 2025 年起，在 `searchAppearance` 維度中新增了對應 AI Overview 的搜尋外觀類型，讓 Performance 報表（包含 API）可依此類型篩選、聚合 `clicks`、`impressions`、`ctr`、`position`。也就是說：

- **可以抓到「你的網站被 AI Overview 引用時的成效聚合數據」**（點擊數、曝光數、CTR、平均排名）。
- **無法抓到 AI Overview 的實際生成內容、引用文字片段、在答案中的排序位置**等細節，Google 未提供這類明細 API。

## 目標

1. 確認並打通 `searchAppearance` 維度的資料串接，讓後端能查詢包含 AI Overview 在內的所有搜尋外觀類型。
2. 前端新增「搜尋外觀」呈現，並能明確標示出 AI Overview 對應的列（若帳號有數據）。
3. 因 Google 未公開完整、穩定的 `searchAppearance` 列舉值文件，且歷史上出現過外觀類型調整（例如 FAQ rich result 下架），**不可在程式中硬編碼 AI Overview 的字串值**，需以 API 實際回傳值動態呈現，並於實作時對照當下最新官方文件核對正確值。
4. 保持 `/api/gsc/analytics` 既有行為相容，新增能力採 opt-in 參數。

## 非目標

- 不嘗試取得 AI Overview 生成內容本身、引用摘要、多來源排序等非 API 提供的資訊。
- 不建立長期資料倉儲或每日快照（沿用 `docs/29` 的既有立場）。
- 不新增 OAuth scope，現有 `webmasters.readonly` 已足夠。
- 不假設所有網站都有 AI Overview 曝光數據——中小型/低流量網站很可能在此維度下完全沒有資料列，需設計對應的空狀態。

## 現況限制與待確認事項

| 項目 | 現況 | 待確認 |
|---|---|---|
| `GSCService.get_analytics()` | 不支援任何非 date/query/page/country/device 以外的維度傳遞限制（技術上可傳，但從未用 `searchAppearance` 測試過） | 需實測 API 回傳的 `searchAppearance` 列舉值中，AI Overview 對應的實際字串（如 `AI_OVERVIEW` 或其他命名），以帳號本身有 AI Overview 曝光的站台驗證 |
| `routers/gsc.py` | 無 `searchAppearance` 相關端點 | 新增端點時的路徑與參數命名 |
| 前端 `GSCStats.jsx` | 無搜尋外觀 tab | 需拆成獨立子元件避免檔案再度膨脹（延續 `docs/33_大型檔案拆分重構實作計劃.md` 的原則） |
| 資料可得性 | 未知 | 需先用一個有實際 AI Overview 曝光的測試站台，確認 GSC 帳號層級是否已能查到此類型資料（部分地區/語言可能尚未大量出現 AI Overview） |

## 建議實作項目

### 1. 後端：擴充 `get_analytics()` 支援 `searchAppearance` 維度

- `backend/gsc_service.py`：`get_analytics()` 已接受任意 `dimensions` list，理論上呼叫端傳入 `["searchAppearance"]` 或 `["date", "searchAppearance"]` 即可運作，**先寫一支驗證腳本實測**，確認：
  - request body 是否需要額外欄位（目前不需要，`searchAppearance` 只是普通 dimension 值）。
  - 回傳的 `rows[].keys[0]` 實際字串內容，逐一比對是否有 AI Overview 對應值。
- 若驗證通過，於 `backend/routers/gsc.py` 新增端點或擴充既有 `/api/gsc/analytics`，允許 `dimensions=searchAppearance`（可與 `date` 組合）。

### 2. 後端：AI Overview 專屬彙總（可選）

- 若確認 AI Overview 值穩定可用，新增輕量彙總端點，例如：
  - `GET /api/gsc/ai-overview-summary?site_url=...&start_date=...&end_date=...`
  - 內部呼叫 `get_analytics(dimensions=["searchAppearance"])`，篩出 AI Overview 對應列，回傳：
    - `clicks`、`impressions`、`ctr`、`position`
    - 占全站總曝光的比例（需另查 `dimensions=["date"]` 的總量做分母）
    - 是否有資料（`has_data: boolean`），供前端顯示空狀態。
  - cache key 需包含 site_url + date range，TTL 可比照現有 analytics 快取策略。

### 3. 前端：搜尋外觀 / AI Overview 呈現

- 新增 `frontend/src/components/GSCStats/` 下的獨立子元件（暫定 `GSCSearchAppearanceTab.jsx`），沿用 `docs/29` 已規劃的搜尋外觀 tab 設計（KPI、長條圖、表格）。
- 在該 tab 內，若偵測到 AI Overview 對應列，額外呈現一張獨立 KPI 卡：
  - `AI Overview 曝光次數`
  - `AI Overview 點擊次數`
  - `AI Overview CTR`
  - `占總曝光比例`
- 若該站台完全沒有 AI Overview 資料，顯示明確空狀態文案，避免使用者誤以為功能故障，例如：
  - `此網站目前尚未偵測到 AI Overview 曝光紀錄，可能是流量規模、語言或地區尚未涵蓋。`

### 4. 文案與說明

- Tooltip 建議文案：
  - `AI Overview：Google 在搜尋結果頁以生成式 AI 摘要呈現答案時，若引用了你的頁面，這裡呈現的是聚合後的點擊與曝光成效，Google 目前不提供引用內容或排序細節。`
- 需在 `docs/05_API_參考手冊.md` 補充新端點說明（待實作完成後同步）。

## 實作階段

### Phase 0：可行性驗證（建議先做，成本低）

- 寫一支一次性驗證腳本（或在既有測試環境）呼叫 `searchanalytics.query`，`dimensions=["searchAppearance"]`，觀察：
  - 是否能成功呼叫（不需額外 scope 或參數）。
  - 帳號綁定站台中，是否已有 AI Overview 對應的列與非零數值。
- 驗收：確認 AI Overview 對應的 `searchAppearance` 字串值，並記錄在本文件或程式註解中，作為後續動態比對／展示用的已知範例值（非硬編碼判斷依據）。

### Phase 1：後端串接

- 擴充 `get_analytics()` 呼叫路徑支援 `searchAppearance`。
- 新增 `/api/gsc/analytics` 對應 query 參數或沿用既有 `dimensions` 傳遞方式。
- 加上 cache key 涵蓋新 dimension。

### Phase 2：前端呈現

- 拆出搜尋外觀子元件，加入 AI Overview 專屬 KPI 卡與空狀態。
- 串接 Phase 1 端點，驗證有資料/無資料兩種情境的 UI。

### Phase 3：文件同步

- 更新 `docs/05_API_參考手冊.md`、`docs/01_專案概覽.md`。
- 若 Phase 0 發現目前串接帳號完全無 AI Overview 資料，於文件中註明「功能已就緒，待實際站台累積曝光後生效」。

## 風險與對策

| 風險 | 影響 | 對策 |
|---|---|---|
| `searchAppearance` 實際列舉值與預期不符或隨時間變動 | UI 判斷錯誤或顯示空白 | 不硬編碼字串比對邏輯以外的顯示規則，優先以「動態列出所有回傳的 searchAppearance 值」呈現，AI Overview 僅作為其中一個高亮項目 |
| 帳號 / 站台尚無 AI Overview 曝光 | 功能看似無效，使用者誤判為 bug | 明確空狀態文案，並在 Phase 0 先確認至少一個測試站台有資料 |
| Google 未公開完整官方列舉文件 | 難以窮舉所有可能值 | 以實際 API 回傳為準，UI 動態渲染，不維護固定 enum 清單 |
| 與既有搜尋外觀規劃（`docs/29`）功能重疊 | 重複實作或衝突 | 本文件的 Phase 1-2 直接併入 `docs/29` 的「Search Appearance 成效」項目一併實作，不重複建立端點 |

## 測試規劃

- 後端：`dimensions=["searchAppearance"]` 呼叫回傳格式驗證（mock GSC API 回應，涵蓋有資料/無資料兩種情境）。
- 後端：AI Overview 彙總端點在無資料時回傳 `has_data: false` 而非錯誤。
- 前端：搜尋外觀 tab 在有 AI Overview 資料、無 AI Overview 資料（但有其他外觀類型）、完全無資料三種情境下的顯示皆正確。

## 官方參考

- Search Analytics API: `https://developers.google.com/webmaster-tools/v1/searchanalytics/query`
- Search Console Performance report（AI Overview 相關公告，實作前應重新查閱最新版本以核對欄位與可用性）：`https://support.google.com/webmasters/answer/96568`
