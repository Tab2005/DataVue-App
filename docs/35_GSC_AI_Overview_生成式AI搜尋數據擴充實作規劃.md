# GSC AI Overview（生成式 AI 搜尋）數據擴充實作規劃

> 建立日期：2026-07-17
> 狀態：Phase 0～3 全部完成（可行性驗證腳本、後端串接、前端呈現、文件同步）；仍待使用者用實際連接 GSC 的帳號跑過 Phase 0 腳本並在瀏覽器實測，才能確認真實資料與 UI 是否符合預期
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

### Phase 0：可行性驗證（建議先做，成本低）— 已建立驗證腳本

- 腳本位置：`backend/scripts/verify_gsc_search_appearance.py`
- 用法：
  ```
  python scripts/verify_gsc_search_appearance.py --email user@example.com --site-url sc-domain:example.com --days 90
  ```
  不帶 `--site-url` 時會先列出該使用者已連接的所有站台。
- 腳本直接沿用既有 `GSCService.get_analytics()`（`dimensions=["searchAppearance"]`），未修改任何服務層程式碼，證實現有架構已能傳遞此維度，只是從未有呼叫端使用過。
- 執行後會列出所有回傳的 `searchAppearance` 值與其 `clicks`/`impressions`/`ctr`/`position`，並對命中 `AI`/`OVERVIEW`/`GENERATIVE`/`SGE` 等關鍵字的值給出提示（僅供人工判讀，不作為程式篩選依據）。
- **已知限制**：本機開發資料庫目前沒有任何使用者連接 GSC（`gsc_refresh_token` 皆為空），因此無法在本機直接驗證出真實資料。需由使用者對正式環境資料庫、或自己本機已連接 GSC 的帳號執行此腳本，才能確認：
  - 是否能成功呼叫（不需額外 scope 或參數）— 目前判斷技術上可行，因為 dimensions 參數本就透傳給 GSC API。
  - 帳號綁定站台中，是否已有 AI Overview 對應的列與非零數值。
- 驗收：由使用者實際執行腳本後，確認 AI Overview 對應的 `searchAppearance` 字串值，並回填至本文件，作為後續動態比對／展示用的已知範例值（非硬編碼判斷依據）。

### Phase 1：後端串接 — 已完成

- `backend/gsc_service.py` 的 `get_analytics()` 本就透傳任意 `dimensions`，`backend/routers/gsc.py` 既有的 `GET /api/gsc/analytics?dimensions=searchAppearance` 也已可直接運作，**未修改**這兩處。
- 新增端點 `GET /api/gsc/search-appearance-summary`（`backend/routers/gsc.py`，緊接在既有 `/analytics` 端點之後）：
  - Query 參數：`site_url`、`start_date`、`end_date`。
  - 內部呼叫兩次 `GSCService.get_analytics()`：一次 `dimensions=["searchAppearance"]` 取得各外觀類型成效，一次 `dimensions=["date"]` 取得全站總量作為占比分母。
    - **原因**：同一次搜尋結果可能同時符合多種 `searchAppearance` 類型（例如同時是 AMP 又是 Rich Result），直接加總 `searchAppearance` 各列的 clicks/impressions 會重複計算，因此改用 `dimensions=["date"]` 的加總當分母，而非搜尋外觀列本身加總。
  - 回傳格式：
    ```json
    {
      "has_data": true,
      "total_clicks": 50,
      "total_impressions": 500,
      "types": [
        {
          "search_appearance": "AMP_BLUE_LINK",
          "clicks": 30,
          "impressions": 300,
          "ctr": 0.1,
          "position": 5.0,
          "click_share": 0.6,
          "impression_share": 0.6,
          "is_ai_related_hint": false
        }
      ]
    }
    ```
  - `is_ai_related_hint`：對 `search_appearance` 字串做關鍵字比對（`AI`、`OVERVIEW`、`GENERATIVE`、`SGE`），**僅是提示旗標，不是官方分類**，因為 Google 未公開穩定列舉值文件；前端可用它來高亮，但不應假設它等於「這一定是 AI Overview」。
  - 無資料時回傳 `has_data: false`，`types: []`，不視為錯誤。
  - GSC API 錯誤會以既有模式轉為 `HTTPException(400)`。
- 沿用既有 `GSCService.get_analytics()` 的快取機制（已包含 dimensions 於 cache key），未額外實作快取層。
- 測試：`backend/tests/test_gsc_search_appearance.py`（3 個案例：無資料、占比與 AI 提示旗標計算、錯誤傳遞），全數通過（`venv/Scripts/python.exe -m pytest tests/test_gsc_search_appearance.py`，此專案需用 `backend/venv`，`.venv311` 缺少 numpy 等依賴不可用於測試）。

### Phase 2：前端呈現 — 已完成

- `frontend/src/components/GSC/constants.js`：`TABS` 新增 `searchAppearance`（🎨 搜尋外觀）分頁。
- `frontend/src/hooks/useGscSearchAppearance.js`（新增）：獨立 hook，當 `activeTab === 'searchAppearance'` 時呼叫 Phase 1 的 `/api/gsc/search-appearance-summary`，含簡易 cache（依 site+日期區間，用 `useRef` 存放，避免切換分頁重複打 API）。
- `frontend/src/components/GSC/SearchAppearanceTab.jsx`（新增）：
  - KPI 卡：搜尋外觀類型數、最高 CTR 搜尋外觀、最大曝光搜尋外觀、疑似 AI Overview 點擊占比（依 `is_ai_related_hint` 加總，明確標示「關鍵字比對提示，非官方分類」）。
  - 表格：搜尋外觀／點擊／曝光／CTR／平均排名／點擊占比（含長條圖），`is_ai_related_hint` 為真的列會加上 🪄 圖示提示。
  - 無資料時顯示空狀態說明文字，而非誤判為故障。
- `frontend/src/components/GSCStats.jsx`：接入 `useGscSearchAppearance`，新增 `SearchAppearanceTab` 分頁渲染分支。
- `frontend/src/hooks/useGscAnalytics.js`：既有的通用 dimension 抓取流程新增排除分支，`searchAppearance` 分頁不會誤觸發 `/api/gsc/analytics?dimensions=searchAppearance` 的重複請求（改由專屬 hook 負責）。
- `frontend/src/components/GSC/GSCShared.jsx`：`GscSummaryCards`（各分頁共用的頂部 KPI 卡）在 `searchAppearance` 分頁回傳 `null`，避免直接加總 `searchAppearance` 各列造成的重複計算誤導使用者（原因見 Phase 1 說明），改由 `SearchAppearanceTab` 自行呈現正確的彙總數據。

**驗證方式與限制**：
- `npx eslint`（新增/修改的 6 個檔案）：0 error，僅既有檔案原有的 3 個無關 warning。
- `npx vite build`：建置成功。
- **未做**：實際瀏覽器操作驗證。原因與 Phase 0 相同——本機開發環境沒有任何已連接 GSC 的帳號/站台，且登入需要真實 Google OAuth，無法在此環境模擬出「有資料」與「AI Overview 有曝光」的畫面。待使用者用真實帳號跑過 Phase 0 腳本確認資料存在後，建議直接在瀏覽器切到「🎨 搜尋外觀」分頁做最終確認。

### Phase 3：文件同步 — 已完成

- `docs/05_API_參考手冊.md`：GSC 段落新增 `GET /gsc/search-appearance-summary` 說明（參數、回傳格式、`is_ai_related_hint` 的提示性質），並補充 `/gsc/analytics` 的 `dimensions` 可傳任意維度（含 `searchAppearance`）。
- `docs/01_專案概覽.md`：Roadmap 新增一行「GSC 搜尋外觀／AI Overview 曝光洞察」，並註明「待實際站台累積 AI Overview 曝光後生效」——因 Phase 0 尚未在真實帳號驗證過是否真的有 AI Overview 資料。
- `docs/29_GSC_API_資料呈現擴充實作規劃.md`：更新頂部狀態與第 1 項「Search Appearance 成效」，標記為已透過本文件（`docs/35`）實作完成，並說明實作與原規劃的差異（分母計算方式、新增 AI 提示旗標），避免兩份文件對現況描述互相矛盾。

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
