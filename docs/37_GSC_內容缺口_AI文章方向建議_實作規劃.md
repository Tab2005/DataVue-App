# GSC 內容缺口 → AI 文章方向建議 實作規劃

> 建立日期：2026-07-21
> 狀態：Phase 1（後端服務與端點）、Phase 2（前端呈現）已完成並通過測試/建置驗證；Phase 3（文件同步）`docs/05` 已同步更新。
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

### Phase 1：後端服務與端點 — 已完成（2026-07-21）

- 新增 `backend/services/ai/content_gap_suggester.py` 的 `AIContentGapSuggester`，結構仿照 `AIIntentClassifier`（system prompt + `_parse_json_response` 三層 fallback），並在 `backend/services/ai/__init__.py` 加入匯出。
- `backend/routers/gsc.py`：
  - 把原本寫死在 `/keyword-gap` 端點內的分析邏輯抽成共用的 `_compute_keyword_gap()`，`/keyword-gap` 與新端點皆呼叫它，避免重複程式碼、也讓新端點在未帶 `missing_keywords` 時能重跑同一套分析。
  - 新增 `ContentGapSuggestionRequest` 與 `POST /content-gap-suggestions` 端點：支援直接帶入 `missing_keywords`（略過重新分析）或不帶（內部重跑 `_compute_keyword_gap` 並篩出 `in_content=false` 的項目）；API Key 解析沿用 `page-intents` 既有順序（`TokenManager.get_ai_api_key` → request 參數 → 環境變數）；缺口關鍵字為 0 時直接短路回傳，不呼叫 AI。
- 測試：`backend/tests/test_gsc_content_gap_suggestions.py`（5 案例：直接帶入缺口關鍵字、空缺口短路、API Key 未設定的空狀態、退回重跑 `keyword-gap` 分析並正確過濾、AI 失敗回傳 500），與既有 `test_gsc_search_appearance.py`、其餘 GSC/AI 相關測試（共 86 項）全數通過。

**⚠️ 實作過程中發現並修復一個既有、無關本次規劃的 bug**：`backend/services/ai/zeabur_client.py` 的 `ZeaburAIClient` 原本**沒有可用的 `generate_content()` 方法**。追查 git 歷史發現，commit `c59a69f`（"fix(ai): deep fix for NoneType startswith crash and frontend model matching"）誤刪了 `generate_content` 的方法簽章與前段程式碼，導致該方法主體變成 `fetch_remote_models()` 內部 `return` 之後的一段不可執行的死代碼（dead code），`generate_content` 這個方法名稱在類別上實際上**不存在**。

這代表：**任何使用預設 provider（`"zeabur"`）呼叫 AI 的既有功能都會拋出 `AttributeError`**，包含既有的 `/api/gsc/page-intents` 端點（`AIIntentClassifier` 預設 `provider="zeabur"`）——這不是本次新功能造成的迴歸，而是先前某次修復遺留的既有缺陷，只是没有測試覆蓋到才沒被發現。已將方法簽章與 guard clause（`if not self.client: raise RuntimeError(...)`、`if not model: raise ValueError(...)`）還原到正確位置並保留其餘邏輯不變，修復後 `hasattr(ZeaburAIClient(...), "generate_content")` 為 `True`，且不影響任何既有測試（`-k "gsc or ai"` 86 項測試修復前後行為一致，因先前無測試覆蓋此路徑）。

**未做**：實際瀏覽器 / 真實 API Key 端到端驗證。原因與 `docs/35` 相同——本機環境沒有真實 Zeabur AI Hub / Gemini API Key 可用於整合測試，僅完成 mock 層級的單元測試。建議待前端（Phase 2）完成後，用真實帳號一併驗證。

**2026-07-21 追加清理：移除 `provider == "gemini"` 死代碼**

使用者詢問「`gemini_api_key` 不是已經完全移除不用了嗎，為何還看到相關資訊」，追查後確認：

- 獨立的 Gemini 直連 API 整合已於 commit `23847e6`（2026-06-17，「整合 OpenRouter 並遷移 Gemini 為選用備援方案」）移除：`backend/services/ai/gemini_client.py` 整支刪除，前端 `ActiveAiProviderSelector.jsx` 只剩 Zeabur／OpenRouter 兩個選項。
- `modules.auth.service.TokenManager._normalize_ai_provider()` 會把任何 `"gemini"`/`"google_gemini"` 值正規化為 `"openrouter"`，`user.gemini_api_key` 欄位保留下來只作為「使用者選 OpenRouter、但只填過 Gemini Key」情境的備援讀取來源，這是刻意保留的相容設計。
- 但 `backend/routers/gsc.py` 的 `/page-intents`（既有功能）與 `/content-gap-suggestions`（本文件 Phase 1 新增，直接複製了 `/page-intents` 的寫法）都還留著一段**沒有正規化、獨立判斷 `provider == "gemini"`** 的 fallback 死代碼，讀取的是已經不再有意義的 `GOOGLE_AI_API_KEY` 環境變數，且就算被觸發，`AIIntentClassifier`/`AIContentGapSuggester` 建構子只認 `"openrouter"` 這個字串，`"gemini"` 會被誤判走 `ZeaburAIClient`，行為是錯的（只是前端已不會送出這個值，才沒有實際爆炸）。

**已修復**：兩個端點都在讀取 `TokenManager.get_ai_api_key()` 之前，先把 `provider in ("gemini", "google_gemini")` 正規化為 `"openrouter"`，並把 fallback 環境變數從 `GOOGLE_AI_API_KEY` 改成正確的 `OPENROUTER_API_KEY`（對應 `OpenRouterClient.__init__` 本身的 env fallback 順序）。`PageIntentRequest`/`ContentGapSuggestionRequest` 的 `provider` 欄位註解也同步更新，說明 `"gemini"` 只是相容用的舊值。修復後 `pytest tests/ -k "gsc or ai"` 86 項測試仍全數通過。`docs/05_API_參考手冊.md` 的 `content-gap-suggestions` 參數說明已同步更新。

**2026-07-21 追加修復：GSC 的 AI 端點從未讀取使用者在設定頁選的模型**

使用者實測時在「AI 模組設定」選了 OpenRouter 的 `Nemotron 3 Ultra (free)`，但 OpenRouter 後台 Log 顯示實際打的是 `DeepSeek V4 Flash`。追查後確認：

- `AIIntentClassifier`／`AIContentGapSuggester` 的建構子都有預設值 `model="deepseek/deepseek-v4-flash"`。
- `backend/routers/gsc.py` 的 `/page-intents`（既有功能）與 `/content-gap-suggestions`（本文件新增）呼叫建構子時都**只傳了 `api_key` 與 `provider`，從未傳 `model`**，也從未查詢使用者存在 `user.ai_model` 欄位裡的選擇——不管使用者在設定頁選什麼模型，這兩個端點永遠都送出硬編碼的 `deepseek/deepseek-v4-flash`。
- 專案裡其實已有正確做法可參考：`backend/routers/ai.py` 的 `/api/ai/analyze` 端點（第 117-122 行）會先 `TokenManager.get_ai_settings(user.google_id)` 取出 `ai_model`，再決定實際送出的模型，只是 GSC 這兩個端點沒跟上這個既有模式。

**已修復**：兩個端點都改成先呼叫 `TokenManager.get_ai_settings(user.google_id)` 取得 `ai_provider`／`ai_model`，`model = user_ai_settings.get("ai_model") or "deepseek/deepseek-v4-flash"` 後傳入建構子（`AIIntentClassifier(..., model=model)`／`AIContentGapSuggester(..., model=model)`），使用者在設定頁選的模型才會真正生效。新增測試 `test_content_gap_suggestions_uses_user_configured_model` 驗證此行為，過程中也發現：測試環境的 `db` fixture（獨立 in-memory SQLite）與 `TokenManager` 內部自建的 `SessionLocal()` 是兩個不同的資料庫連線，直接寫入 `sample_user.ai_model` 再呼叫真正的 `get_ai_settings` 不會生效，需改為直接 mock `TokenManager.get_ai_settings`（與既有測試 mock `get_ai_api_key` 的手法一致）。修復後 `pytest tests/ -k "gsc or ai"` 87 項測試全數通過。

**前端修復：頁面分析分頁的「缺口分析」按鈕在分析意圖後消失**

使用者回報：在「頁面分析」分頁，尚未點「分析意圖」時看得到「🎯 缺口分析」按鈕，但點過分析意圖、分析完成後按鈕就不見了。追查 `frontend/src/components/GSC/RegularDataTab.jsx` 發現，每列的動作區是一個 4 分支條件渲染（尚未分析／分析中／分析完成／分析失敗），缺口分析按鈕當初只寫在「尚未分析」分支，「分析完成」與「分析失敗」兩個分支都沒有渲染它——不是樣式問題，是這兩個分支的 JSX 從一開始就漏寫了這顆按鈕。已在這兩個分支都補上相同的缺口分析按鈕（沿用一致的樣式與 `fetchKeywordGap(pageUrl)` 呼叫）。`npx eslint`／`npx vite build` 皆通過。

**2026-07-21 追加修復：AI 產生文章建議報「Failed to parse JSON from response: ...」**

使用者用 OpenRouter 的 `Nemotron 3 Ultra (free)` 模型測試時遇到此錯誤，要求把 JSON 解析邏輯改寬容，或直接查伺服器 log 診斷。透過 `npx zeabur@latest deployment log --service-id <backend-service-id> -t runtime` 查看 Zeabur 後端 runtime log，找到真正原因：

```
[OpenRouterClient] API response returned no choices: ChatCompletion(..., error={'message': 'Upstream error from Nvidia: ResourceExhausted: Worker local total request limit reached (32/32)', 'code': 502})
```

真正的成因**不是 JSON 格式問題**，而是 NVIDIA 提供的免費 Nemotron 3 Ultra 端點觸發了自身的流量上限（`ResourceExhausted`，上游回傳 502），導致這次請求完全沒有內容。但 `backend/services/ai/openrouter_client.py` 的 `generate_content()`（第 192-194 行舊版）遇到 `response.choices` 為空時，只記一筆 WARNING log 就直接 `return ""`（吞掉了 `response.error` 裡的真正錯誤訊息），空字串再往下傳到 `AIContentGapSuggester._parse_json_response()` 自然三層 fallback 都解析失敗，才產生了完全誤導的「JSON 解析失敗」錯誤，實際上跟 JSON 格式一點關係都沒有。

**已修復**：
- `openrouter_client.py`：`response.choices` 為空時，改成讀取 `response.error` 並 `raise RuntimeError(f"OpenRouter upstream error ({model}): {error_message}")`，把上游真正的錯誤訊息（例如 NVIDIA 的流量限制訊息）往上拋，不再靜默吞掉；沒有 `error` 欄位時也拋出明確訊息而非回傳空字串。所有既有呼叫端（`content_gap_suggester.py`、`intent_classifier.py`、`ai_service.py`、`calibration_pipeline.py`）本來就都有 `try/except` 包住 `generate_content()`，不受影響。
- `content_gap_suggester.py`：`_parse_json_response()` 開頭新增空字串檢查，明確拋出「AI provider returned an empty response (no error code) — likely rate-limited or overloaded upstream」，避免未來若有其他 provider 路徑也靜默回傳空字串時，又出現同樣誤導性的「JSON 解析失敗」訊息。
- 新增測試：`backend/tests/test_openrouter_client.py`（3 案例：無 choices 且有 error 訊息時正確拋出、無 choices 且無 error 訊息時拋出通用訊息、正常有 choices 時正確回傳內容）、`backend/tests/test_content_gap_suggester.py`（3 案例：空缺口關鍵字短路、空 AI 回應時錯誤訊息清楚可辨識、正常 JSON 回應能正確解析）。
- **這是免費模型本身的流量限制，不是程式錯誤，重試通常就會成功**；修復後使用者遇到這類情況時，看到的錯誤訊息會直接是「OpenRouter upstream error (nvidia/nemotron-3-ultra-550b-a55b:free): Upstream error from Nvidia: ResourceExhausted: ...」，能一眼看出是上游限流問題該重試或換模型，而不是誤以為程式碼壞了。
- 驗證：`pytest tests/ -k "gsc or ai or openrouter"` 92 項測試全數通過。

### Phase 2：前端呈現 — 已完成（2026-07-21）

- `frontend/src/hooks/useGscPageAnalysis.js`：新增狀態 `suggestLoading`、`suggestResults`、`suggestError`，以及 `fetchContentGapSuggestions()`——從目前的 `gapResults.results` 篩出 `in_content === false` 的項目組成 `missing_keywords`，呼叫 `POST /api/gsc/content-gap-suggestions`（`provider` 沿用既有的 `localStorage.getItem('ai_provider')` 慣例，與 `fetchPageIntent` 一致）。`fetchKeywordGap()` 重新分析時會重置 `suggestResults`/`suggestError`，避免顯示上一個頁面的舊建議。
- `frontend/src/components/GSC/KeywordGapTab.jsx`：在缺口結果表格下方（`missing_count > 0` 時）新增：
  - `🪄 產生文章方向建議` 按鈕（分析中顯示 loading 文案並停用）。
  - 錯誤訊息區塊（沿用既有 `gapError` 的視覺樣式）。
  - 建議卡片列表：每張卡片顯示類型 badge（📝 補充現有內容／✨ 新文章方向）、標題、大綱條列、關鍵字 tag、AI 判斷理由；卡片區塊上方固定顯示「AI 生成建議僅供參考，請人工確認後再採用」提示；空建議時顯示後端回傳的 `message`。
- 驗證：`npx eslint`（僅 3 個既有、與本次改動無關的 pre-existing warning，0 error）；`npx vite build` 建置成功。
- **未做**：實際瀏覽器操作驗證與真實 API Key 端到端測試，原因與 Phase 1 相同——本機無真實 GSC 連線帳號與 AI API Key。

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

## 2026-07-22 追加修復：改用串流呼叫，比照 GA4 轉換洞察 AI 分析功能

**背景**：上一版修復（2026-07-21）已讓 `openrouter_client.py` 在遇到 `response.choices` 為空時拋出上游真實錯誤（NVIDIA 免費 Nemotron 模型當時剛好額滿限流），但屬於治標：只是讓錯誤訊息變清楚，沒有解決「非串流請求容易在免費/限流模型上拿到空 choices」這個根本行為差異。

使用者回報：後來用同一顆 Nemotron 3 Ultra (free) 模型測試 GA4「即時轉換洞察」頁面的 AI 分析功能，完全沒有出現任何問題，並要求參考該功能的呼叫方式來調整內容缺口建議功能。

**差異分析**：比對 `backend/ai_service.py`（GA4 轉換洞察等其他 AI 分析功能共用的服務層）與 `backend/services/ai/content_gap_suggester.py`：

| | GA4 轉換洞察等（`ai_service.py`） | 內容缺口建議（修復前） |
|---|---|---|
| Zeabur 呼叫方式 | `client.generate_content(..., stream=True)`，逐 chunk yield | `client.generate_content(...)`（阻塞、一次性） |
| OpenRouter 呼叫方式 | `client.generate_content_stream(...)`，逐 chunk yield | 同上（阻塞、一次性） |

也就是說，目前唯一「已知在免費/限流模型下穩定運作」的呼叫路徑是**串流**。`AIIntentClassifier`（意圖分析）與 `AIContentGapSuggester`（本功能）兩者都是走非串流的 `generate_content()`，屬於同一類風險，但只有本功能被實際回報出錯。

**修復**：
- `backend/services/ai/content_gap_suggester.py`：新增 `_generate_full_content()`，內部依 provider 分流：
  - `openrouter` → 呼叫 `client.generate_content_stream(...)`
  - `zeabur` → 呼叫 `client.generate_content(..., stream=True)`
  再用 `"".join(chunks)` 組回完整字串後才進入既有的 JSON 解析邏輯（`_parse_json_response` 不變，仍保留 2026-07-21 加的空回應防呆訊息）。`suggest_directions()` 改呼叫這個新方法取代原本直接呼叫 `client.generate_content(...)`。
- `backend/services/ai/openrouter_client.py`：`generate_content_stream()` 補上與 `generate_content()` 對稱的防呆——遇到某個 chunk 沒有 `choices` 時，若該 chunk 帶有 `error` 資訊就拋出 `RuntimeError` 附上游真實訊息，否則略過該 chunk 繼續處理下一個（避免 `IndexError` 蓋掉真正原因）。

**測試**：
- 新增 `test_suggest_directions_uses_streaming_call_for_openrouter`（`backend/tests/test_content_gap_suggester.py`）：驗證 OpenRouter provider 會呼叫 `generate_content_stream` 而非 `generate_content`，且分段 chunk 組合後仍能正確解析 JSON。
- 既有 `test_content_gap_suggester.py`／`test_openrouter_client.py`／`test_gsc_content_gap_suggestions.py` 全數維持通過（mock 的 `generate_content.return_value` 字串本身可逐字元迭代，`"".join(...)` 後結果不變，無需修改既有測試）。
- `pytest tests/ -k "gsc or ai or openrouter"` → 93 passed。

**備註**：`AIIntentClassifier`（頁面意圖分析）原本仍走非串流路徑——已於同日追加修復一併調整，見下一節。

## 2026-07-22 追加修復（順手調整）：`AIIntentClassifier` 比照同樣改為串流呼叫

上一節備註提到 `AIIntentClassifier`（GSC「頁面分析」頁籤的「分析意圖」功能）有相同的非串流風險但尚未被回報，使用者要求順手一併調整，避免日後在免費/限流模型下遇到同樣的空回應問題。

**修復**（`backend/services/ai/intent_classifier.py`）：
- 新增 `_generate_full_content()`，與 `AIContentGapSuggester` 相同的 provider 分流邏輯（openrouter → `generate_content_stream`；zeabur → `generate_content(..., stream=True)`），收集 chunk 組回完整字串。
- `classify_queries()`（單批）與 `_classify_queries_batched()`（OpenRouter 超過 10 個關鍵字時的批次路徑）都改呼叫這個新方法。
- `_parse_json_response()` 補上與 `AIContentGapSuggester` 一致的空回應防呆訊息（原本完全沒有這層防呆，空字串會直接進入三層 JSON fallback 全部失敗，跳出誤導性的「Failed to parse JSON」訊息）。

**測試**：新增 `backend/tests/test_intent_classifier.py`（3 個測試：OpenRouter 走串流呼叫、空回應清楚報錯、有效 JSON 正確解析）。`pytest tests/ -k "gsc or ai or openrouter or intent"` → 96 passed。

## 官方參考

- Search Analytics API（缺口分析所需的關鍵字排名資料來源，與現有 `keyword-gap` 相同）：`https://developers.google.com/webmaster-tools/v1/searchanalytics/query`
