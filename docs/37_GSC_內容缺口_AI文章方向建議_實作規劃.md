# GSC 內容缺口 → AI 文章方向建議 實作規劃

> 建立日期：2026-07-21
> 狀態：規劃中，尚未實作
> 範圍：延伸現有 `POST /api/gsc/keyword-gap`（單一頁面的內容缺口分析），新增一層 AI 分析，把「有排名但內文未涵蓋」的關鍵字整理成具體的文章方向建議（補充現有頁面段落，或獨立成新文章）。
> 非範圍（列為後續延伸）：全站規模的「機會關鍵字 → 全新文章題目」分群建議，見文末「後續延伸（做法 B）」。

## 背景

使用者詢問能否把 GSC「內容缺口」功能找到的缺口關鍵字，進一步組成新文章方向建議。討論後確認兩種可能做法：

- **做法 A（本文件範圍）**：沿用現有 `keyword-gap` 端點的單頁分析結果，用 AI 針對缺口關鍵字給出「這頁該補什麼」或「該獨立寫新文章」的方向建議。範圍小、可直接延伸既有端點與畫面。
- **做法 B（後續延伸，本階段不做）**：新增全站規模的機會關鍵字掃描，找出「有曝光但沒有頁面明確涵蓋／排名差」的關鍵字，再用 AI 分群成數個全新文章主題。範圍大，需要新的資料判定邏輯，代價明顯較高。

使用者確認先做 A，B 留待 A 上線並有實際回饋後再評估。

**現況程式碼盤點（2026-07-21 確認）**：

- `backend/routers/gsc.py` 的 `POST /keyword-gap`（第 490-639 行）：輸入 `site_url`、`page_url`、`start_date`、`end_date`、`top_n`，內部呼叫 `GSCService.get_analytics(dimensions=['page','query'])` 取得該頁排名關鍵字，爬取頁面內容後逐一比對關鍵字是否出現在內文，回傳：
  ```json
  {
    "page": "...", "page_title": "...", "status": "success",
    "results": [{"query": "...", "clicks": 0, "impressions": 0, "ctr": 0, "position": 0, "in_content": false}],
    "total_analyzed": 0, "missing_count": 0, "total_found_in_gsc": 0
  }
  ```
- `backend/routers/gsc.py` 的 `POST /page-intents`（第 305 行起）是目前唯一使用 AI 的 GSC 端點，可作為新功能的實作範本：
  - Request 帶 `provider: Optional[str] = "zeabur"` 與 `ai_api_key: Optional[str] = None`。
  - API key 解析順序：`TokenManager.get_ai_api_key(user.google_id, provider=provider)` → `request.ai_api_key` → 環境變數（`GOOGLE_AI_API_KEY` 或 `ZEABUR_AI_HUB_API_KEY`）。
  - 未設定 API key 時**不報錯**，改回傳 `unknown`/空狀態的預設結構，讓前端能正常顯示「未設定」提示而非錯誤畫面。
  - 實際分類邏輯委派給 `backend/services/ai/intent_classifier.py` 的 `AIIntentClassifier`。
- `backend/services/ai/intent_classifier.py`：`AIIntentClassifier` 的結構可直接複用——`__init__(api_key, model, provider)` 依 provider 選擇 `ZeaburAIClient` 或 `OpenRouterClient`；`SYSTEM_PROMPT` + `_parse_json_response()`（含三層 fallback：直接解析、抓 ```json 區塊、抓第一個 `{`到最後一個`}`）是穩定的 JSON 輸出解析模式。
- 前端 `frontend/src/components/GSC/KeywordGapTab.jsx` 已有缺口分析結果的畫面，可在其下方新增「產生文章建議」動作。

## 目標

1. 新增一個 AI 分析步驟，把 `keyword-gap` 找到的缺口關鍵字（`in_content: false` 的項目）交由 AI 生成方向建議。
2. 沿用既有 AI provider 選擇機制（zeabur/gemini/openrouter）與 API key 解析順序，不新增另一套設定方式。
3. 建議輸出分兩種類型：
   - `expand_existing`：建議在現有頁面新增的段落方向。
   - `new_article`：建議獨立成一篇新文章的方向。
4. 只生成方向、標題、大綱層級的建議，不生成完整文章全文。
5. 保持現有 `/keyword-gap` 端點行為不變，新功能為獨立端點。

## 非目標

- 不做全站規模掃描（做法 B，見後續延伸）。
- 不自動發布文章或寫入 CMS/草稿系統。
- 不生成完整文章全文（避免內容農場疑慮、生成時間過長、品質不可控）。
- 不做多頁面批次同時分析，先聚焦使用者當下在看的單一頁面。

## 建議實作項目

### 1. 後端：新增 AI 文章方向建議服務類別

新增 `backend/services/ai/content_gap_suggester.py`，仿照 `intent_classifier.py` 的結構：

- `class AIContentGapSuggester`
  - `__init__(self, api_key=None, model="deepseek/deepseek-v4-flash", provider="zeabur")`：與 `AIIntentClassifier` 相同的 provider 選擇邏輯，可考慮抽出共用的 client 初始化邏輯，但為避免一次改動影響既有分類器，本階段先各自獨立實作，待兩者穩定後再評估共用。
  - `suggest_directions(self, page_url: str, page_title: str, missing_keywords: List[Dict]) -> Dict`：
    - 輸入：`missing_keywords` 為 `keyword-gap` 回傳結果中 `in_content == false` 的項目（`query`、`clicks`、`impressions`、`position`）。
    - System Prompt 設計重點：
      - 說明這些關鍵字目前該頁面有排名、有搜尋量，但內文沒有涵蓋。
      - 請 AI 依語意相關性把關鍵字分組（可能 1 組到多組，不強制固定數量）。
      - 每組判斷：內容量小、與頁面主題高度相關 → `expand_existing`；內容量大、值得獨立經營、或與頁面主題有落差 → `new_article`。
      - 依 `impressions`/`clicks` 加權估算每組的「機會分數」，用於前端排序。
      - 輸出繁體中文標題與大綱要點（3-6 條），不生成完整段落內容。
    - 輸出格式：
      ```json
      {
        "success": true,
        "model": "deepseek/deepseek-v4-flash",
        "page": "https://example.com/page",
        "suggestions": [
          {
            "type": "expand_existing",
            "title": "建議段落／文章標題",
            "outline": ["大綱要點 1", "大綱要點 2", "大綱要點 3"],
            "target_keywords": ["關鍵字 1", "關鍵字 2"],
            "estimated_opportunity": {"impressions": 1200, "avg_position": 15.3},
            "reasoning": "簡短說明為何建議補充現有頁面而非獨立新文章"
          }
        ]
      }
      ```
    - 沿用 `_parse_json_response()` 的三層 fallback 解析模式。
  - 無 API key 或呼叫失敗時，回傳 `{"success": false, "error": "..."}`，由端點決定如何呈現，不拋例外中斷。

### 2. 後端：新增端點 `POST /api/gsc/content-gap-suggestions`

- 位置：`backend/routers/gsc.py`，緊接在 `/keyword-gap` 之後。
- Request model（暫定）：
  ```python
  class ContentGapSuggestionRequest(BaseModel):
      site_url: str
      page_url: str
      start_date: str
      end_date: str
      top_n: Optional[int] = 100
      missing_keywords: Optional[List[Dict]] = None  # 若前端已呼叫過 keyword-gap，可直接帶入避免重複分析
      provider: Optional[str] = "zeabur"
      ai_api_key: Optional[str] = None
  ```
- 邏輯：
  1. 若 `missing_keywords` 為 `None`，內部重新執行一次 `keyword-gap` 的分析邏輯（抓 GSC 關鍵字 + 爬頁面內容 + 比對），取得 `in_content == false` 的項目；若前端已帶入則直接使用，避免重複打 GSC API 與重複爬頁面。
  2. API key 解析沿用 `page-intents` 的既有順序（`TokenManager.get_ai_api_key` → request 參數 → 環境變數）。
  3. 呼叫 `AIContentGapSuggester.suggest_directions()`，回傳結果。
  4. 缺口關鍵字為空（`missing_count == 0`）時直接回傳 `{"suggestions": [], "message": "此頁面內容已涵蓋所有排名關鍵字"}`，不呼叫 AI，節省成本。

### 3. 前端：`KeywordGapTab.jsx` 新增「產生文章建議」動作

- 在缺口分析結果表格下方新增按鈕：`🪄 產生文章方向建議`（缺口關鍵字為 0 時停用此按鈕）。
- 點擊後呼叫新端點，帶入當前畫面已有的 `keyword-gap` 結果（避免重複分析）。
- 結果以卡片列表呈現：
  - 類型 badge：`📝 補充現有內容` / `✨ 新文章方向`
  - 建議標題
  - 大綱要點（條列）
  - 涉及關鍵字（tag 列表）
  - 預估機會（曝光數、平均排名）
  - 說明文字（`reasoning`）
- Loading / Error / 空狀態沿用既有 `GSCUiStates.jsx` 模式。
- 明確標示「AI 生成建議僅供參考，請人工確認後再採用」，避免使用者直接照抄發布。

## 實作階段

### Phase 1：後端服務與端點
- 新增 `AIContentGapSuggester`、`content-gap-suggestions` 端點。
- 單元測試：mock AI client 回應，驗證 JSON 解析與空缺口情境。

### Phase 2：前端呈現
- `KeywordGapTab.jsx` 新增按鈕與建議卡片畫面。
- 涵蓋 loading/error/空狀態/正常顯示四種情境。

### Phase 3：文件同步
- `docs/05_API_參考手冊.md` 新增 `POST /gsc/content-gap-suggestions` 說明。

## 風險與對策

| 風險 | 影響 | 對策 |
|---|---|---|
| AI 生成內容品質不穩、可能生成不精準的大綱 | 使用者誤採用低品質建議 | 只生成方向/大綱層級，非全文；UI 明確標示「僅供參考，需人工確認」 |
| 重複呼叫 GSC API 與重複爬頁面，浪費配額與時間 | 效能差、GSC API 配額消耗 | 端點支援直接帶入既有 `keyword-gap` 結果，避免重算 |
| API Key 未設定 | 功能無法使用 | 沿用 `page-intents` 已驗證過的空狀態處理模式，不視為錯誤 |
| 缺口關鍵字為 0 時仍呼叫 AI，浪費成本 | 不必要的 API 呼叫費用 | 端點內判斷 `missing_count == 0` 時直接短路回傳，不呼叫 AI |
| `expand_existing` / `new_article` 分類不準確 | 建議類型誤導使用者 | Prompt 中明確給出分類標準，並讓使用者自行判斷是否採用，不強制自動執行 |

## 測試規劃

**後端**：
- `AIContentGapSuggester.suggest_directions()` 在 mock AI 回應下能正確解析 JSON 並回傳結構化建議。
- 端點在 `missing_keywords` 為 `None` 時能正確重跑缺口分析邏輯。
- 端點在 `missing_count == 0` 時不呼叫 AI，直接回傳空建議。
- API key 未設定時回傳空狀態結構，不拋 500 錯誤。

**前端**：
- 按鈕在缺口關鍵字為 0 時停用。
- 建議卡片在 `expand_existing`／`new_article` 兩種類型下正確顯示對應 badge。
- loading/error/空狀態畫面正常。

## 後續延伸（做法 B，本階段不實作）

**全站缺口 → 全新文章題目建議**：

- 需要新增「全站機會關鍵字掃描」機制：不限於使用者指定的單一頁面，而是比對網站上所有 GSC `query`，找出「有曝光量，但目前沒有頁面排名夠好或沒有清楚對應頁面」的關鍵字。這個判定邏輯比現有單頁 `in_content` 比對複雜得多，需要另外規劃「如何認定一個關鍵字已被涵蓋」的標準（例如：對應頁面的排名門檻、CTR 門檻，或該關鍵字是否有任何頁面出現在 GSC `page` 維度中）。
- 找出機會關鍵字後，用 AI 對整批關鍵字做語意分群，可參考本專案 MMM 模組已有的分群設計經驗（7 個關鍵詞類別 + 前綴聚類，動態收斂為 5-8 組），每群輸出一個全新文章主題、標題、大綱與預估流量機會。
- 需要新的批次掃描端點與可能的排程/快照機制（掃描全站關鍵字可能耗時較長，不適合每次請求即時計算）。
- 建議待做法 A 上線並取得使用者實際使用回饋後，再評估是否啟動此項目、以及優先順序。

## 官方參考

- Search Analytics API（缺口分析所需的關鍵字排名資料來源，與現有 `keyword-gap` 相同）：`https://developers.google.com/webmaster-tools/v1/searchanalytics/query`
