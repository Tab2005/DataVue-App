# OpenRouter 整合與 Google Gemini 替換規格書 (openrouter_migration_spec.md)

> [!IMPORTANT]
> 本文件規劃將 DataVue 的 AI 核心由 Google Gemini SDK 直連，全面替換為 OpenRouter 聚合服務架構，並將評分工作台的預設模型指定為 `deepseek/deepseek-v4-flash`。

---

## 1. 背景與目標 (Background & Objectives)
### 1.1 重構初衷
目前 DataVue 系統直連 Google Gemini API Studio。然而，在多用戶、多素材併發評分的背景任務場景下，免費版金鑰常遭遇 `429 RESOURCE_EXHAUSTED` (頻率與配額限制) 報錯。為了提升系統可用性，並提供更靈活的多模型切換能力，決定將底層 AI 整合架構遷移至 OpenRouter 平台。

### 1.2 選擇 DeepSeek 作為評分預設模型的優勢
在評分工作台的實作中，預設採用 `deepseek/deepseek-v4-flash` 模型。其優勢如下：
* **卓越性價比**：DeepSeek 的 Token 單價僅為同等級模型的數十分之一，適合背景大批量廣告素材的常態性評估。
* **中文語義理解與創意評分**：DeepSeek 對繁體中文 (Traditional Chinese) 具有優秀的掌握力，在創意診斷（如 Hook 吸引力、行動呼籲 CTA 完整度）上能提供自然、精準且口語化的回饋。
* **低延遲與高吞吐量**：使用 Flash 版本模型能有效降低背景隊列排隊時間，確保工作台前端響應迅速。

### 1.3 架構目標
* **熱插拔遷移**：在保持前端 UI 界面與呈現方式（Scoring Lineage 展示、Review Queue 介面）完全不變的前提下，替換底層 API 客戶端與資料庫儲存模型。
* **多模型支援**：建立動態模型同步與快取機制，讓用戶能自由配置金鑰並於前端選單中彈性選擇 OpenRouter 提供的各種 AI 模型。

## 2. 影響範圍與架變動 (Scope & Architectural Changes)
### 2.1 資料庫設計與 Alembic 遷移
* **`User` 模型變更** (位於 [backend/database/models/user.py](file:///C:/Users/BWM2/Documents/python/DataVue-App/backend/database/models/user.py))：
  * 保留舊的 `gemini_api_key` 欄位以實現漸進式相容與無損升級。
  * 新增 `openrouter_api_key = Column(String, nullable=True)` 欄位，同樣採用基於 `Fernet` 的雙向加密儲存。
  * `ai_provider` 欄位的合法枚舉值與註解更新，支援 `"zeabur"` 與 `"openrouter"`。將模型的 `default` 預設值修正為 `"deepseek/deepseek-v4-flash"`。
* **資料庫與用戶遷移計畫**：
  * 執行 `alembic revision --autogenerate -m "add_openrouter_api_key"` 生成自動遷移腳本。
  * 遷移腳本中必須包含 **資料遷移 (Data Migration)** 步驟：將現有歷史資料中，`ai_provider == "gemini"` 的舊用戶自動更新為 `"openrouter"`，避免因找不到 gemini 客戶端造成執行期崩潰。
  * 系統啟動時執行 `alembic upgrade head` 自動更新生產與雲端環境資料庫。

### 2.2 後端客戶端與服務重構 (AI Hub)
* **意圖分類器重構與客戶端移除**：
  * ⚠️ **重要**：在移除 `backend/services/ai/gemini_client.py` 之前，必須先修改 `backend/services/ai/intent_classifier.py`，將其引用的 `GoogleGeminiClient` 替換為 `OpenRouterClient`。
  * 同步調整 `intent_classifier.py` 內針對於 `provider == "gemini"` 的批處理與速率控制判斷，對接為 `"openrouter"`。
* **新增 OpenRouter 客戶端** (建立 [backend/services/ai/openrouter_client.py](file:///C:/Users/BWM2/Documents/python/DataVue-App/backend/services/ai/openrouter_client.py))：
  * 採用 `openai` SDK 封裝並指向 OpenRouter API。
  * 配置示例如下：
    ```python
    from openai import OpenAI
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://datavue-app.zeabur.app",
            "X-Title": "DataVue-App",
        }
    )
    ```
* **AI 服務層調整與模型快取過濾** (修改 `backend/modules/ai_hub/service.py` 及 `backend/ai_service.py`)：
  * 當 `provider` 設定為 `"openrouter"` 時，調用 `OpenRouterClient`。
  * 重新實作 `/api/ai/models` 的模型同步：呼叫 OpenRouter 模型清單端點。
  * **快取與過濾設計**：為了防止 OpenRouter 數百個模型導致前端卡頓，後端需對模型清單進行過濾（僅保留 `deepseek/`、`anthropic/`、`google/` 等主流提供商模型），並使用記憶體做 1 小時快取 (TTL = 3600s)。
  * 更新 `AIService.PROVIDERS` 字典，並將 `_analyze_with_legacy` 重構為對接 OpenRouter 的串流生成。

### 2.3 Meta Andromeda 評分工作台與註冊表
* **更新註冊表條目與環境變數覆蓋** (修改 [model_registry.py](file:///C:/Users/BWM2/Documents/python/DataVue-App/backend/modules/meta_andromeda/model_registry.py))：
  * 將 `prod_v2026_05_28`、`cand_v2026_06_05_a` 以及遺漏的 `cand_v2026_06_04_b` 的 `provider` 全面由 `"gemini"` 改為 `"openrouter"`。
  * 將預設的 `provider_model` 設定為 `"deepseek/deepseek-v4-flash"`。
  * ⚠️ **重構 `get_entry()` 方法中的覆蓋邏輯**：將硬編碼 of `provider_override == "gemini"` 修改為支援 `"openrouter"`，使全域環境變數覆蓋可正常運作。
* **重構背景評分 Provider與 429 異常捕獲** (修改 [runtime.py](file:///C:/Users/BWM2/Documents/python/DataVue-App/backend/modules/meta_andromeda/runtime.py))：
  * 將 `GeminiScoringProvider` 類別更名為 `OpenRouterScoringProvider`。
  * 內部對接 OpenRouter 客戶端，並支援傳入用戶級解密金鑰。
  * ⚠️ **異常捕獲調整**：OpenRouter 調用時拋出的 429 異常為 `openai.RateLimitError`，需確保異常處理能捕獲此類型，並執行指數退避重試。

### 2.4 前端介面與金鑰設定更名
* **金鑰設定彈窗** (修改 `frontend/src/components/SettingsModal.jsx`)：
  * 將所有 "Google Gemini API Key" 文字、圖示全面更名為 "OpenRouter API Key"。
  * 前端狀態變數重新命名：`geminiData` -> `openrouterData`，`googleModels` -> `openrouterModels`，避免程式碼命名混亂。
  * 選擇 OpenRouter 提供商後，下拉選單動態載入過濾後的模型，預設選取為 `deepseek/deepseek-v4-flash`。
* **連線測試端點統一**：
  * 統一使用 `/api/ai/test-connection?provider=openrouter` 作為前後端連線測試端點，避免維護多個重複且參數不一致的測試端點。
* **評分工作台** (修改 `ScoreLab.jsx` 與 `ReviewQueue.jsx`)：
  * Lineage 展示將原有的 `Gemini AI` 文字更新為 `OpenRouter (deepseek/deepseek-v4-flash)`。

## 3. 實作步驟與程式碼異動清單 (Implementation Steps)

### 步驟 1：擴充資料庫 Schema 與 Alembic 遷移
1. 修改 `backend/database/models/user.py`：
   * 在 `User` 類別中新增欄位：`openrouter_api_key = Column(String, nullable=True)`。
   * 將 `ai_model` 的預設值修改為 `"deepseek/deepseek-v4-flash"`。
2. 產生遷移腳本：
   * 在 `backend/` 下執行 `alembic revision --autogenerate -m "add_openrouter_api_key"`。
3. 編輯遷移腳本加入**數據遷移 (Data Migration)**：
   * 在 `upgrade()` 方法中，執行 SQL 更新：`UPDATE users SET ai_provider = 'openrouter' WHERE ai_provider = 'gemini'`。
   * 確保歷史用戶能順暢過渡。

### 步驟 2：後端依賴模組與客戶端重構
1. 重構 `backend/services/ai/intent_classifier.py`：
   * 將 `GoogleGeminiClient` 替換為 `OpenRouterClient`。
   * 調整意圖分類器中對 `gemini` 提供商名稱的 Rate Limit 邏輯。
2. 建立 `backend/services/ai/openrouter_client.py`：
   * 基於 `openai` SDK 實作 `OpenRouterClient`。
   * 封裝並對齊 `generate_content`、`test_connection` 介面。
3. 安全地棄用並刪除 `backend/services/ai/gemini_client.py`。
4. 修改 `backend/core/config.py`：
   * 新增屬性 `OPENROUTER_API_KEY`，優先讀取全域環境變數。

### 步驟 3：重構 AI Hub 服務層與加密儲存管理 (TokenManager)
1. 修改 `backend/modules/auth/service.py` 中的 `TokenManager`：
   * 讓 `save_ai_settings` 與 `get_ai_api_key` 支援對資料庫中 `openrouter_api_key` 的加密與解密。
2. 修改 `backend/modules/ai_hub/service.py` 與 `backend/ai_service.py`：
   * 將 `google_gemini` 提供商改為 `openrouter`。
   * 實作模型過濾（主流廠商模型）並使用記憶體做 1 小時快取。

### 步驟 4：Meta Andromeda 評估引擎與診斷重構
1. 修改 `backend/modules/meta_andromeda/model_registry.py`：
   * 將 `prod_v2026_05_28`、`cand_v2026_06_05_a` 以及 `cand_v2026_06_04_b` 條目的 `provider` 改為 `"openrouter"`。
   * 將其 `provider_model` 設為 `"deepseek/deepseek-v4-flash"`。
   * 重構 `get_entry()` 方法中的環境變數覆蓋判斷（`provider_override == "openrouter"`）。
2. 修改 `backend/modules/meta_andromeda/runtime.py`：
   * 將 `GeminiScoringProvider` 重構更名為 `OpenRouterScoringProvider`，對接 `OpenRouterClient`。
   * 改為讀取解密用戶的 `openrouter_api_key`。
   * 補齊對 `openai.RateLimitError` 的捕獲與 429 退避重試。
3. 修改 `backend/main.py` 的 `/api/health` 診斷端點：
   * 統計 `openrouter_api_key` 的用戶數 `db_users_with_openrouter_key_count`。
   * 曝露環境變數 `OPENROUTER_API_KEY_len` 長度資訊。

### 步驟 5：前端 UI 介面更名與 API 對接
1. 修改 `frontend/src/components/SettingsModal.jsx`：
   * 將「Google Gemini 金鑰」介面全面更名為「OpenRouter 金鑰」。
   * 重命名狀態變數：`geminiData` -> `openrouterData`，`googleModels` -> `openrouterModels`。
   * 統一連線測試端點為 `/api/ai/test-connection?provider=openrouter`，移除舊有 `/api/ai/test-gemini` 呼叫。
2. 修改 `ScoreLab.jsx` 與 `ReviewQueue.jsx`：
   * 在評估來源 (Lineage) 與 Fallback 警告中，將原有的 `Gemini AI` 更名為 `OpenRouter (deepseek/deepseek-v4-flash)`。

## 4. 測試與驗證計畫 (Testing & Verification Plan)

### 4.1 連線測試與模型同步驗證
1. **連線功能測試**：
   * 在 DataVue 的「AI 設定」彈窗中，選擇供應商為 `OpenRouter`，輸入 API Key 並點選 **「測試連線」**。
   * 驗證後端 API `/api/ai/test-connection` 是否成功透過 `OpenRouterClient` 呼叫測試接口，前端是否正確彈出「AI 服務連線成功」提示。
2. **模型清單同步**：
   * 點選 **「同步最新模型」** 按鈕。
   * 驗證後端 API `/api/ai/models?provider=openrouter` 能成功解析 OpenRouter 返回的模型列表。
   * 驗證前端下拉選單是否成功列出包括 `deepseek/deepseek-v4-flash` 在內的多個模型供用戶選擇與保存。

### 4.2 評分工作台煙霧測試 (Smoke Test)
1. **背景評估金鑰解密測試**：
   * 重新在評分工作台發送一個素材評估任務。
   * 觀察後台 `APScheduler` 日誌，確認是否出現 `[MetaAndromeda] generate_score_result` 日誌，並顯示 `DB Key present: True`。
2. **評估核心與 Lineage 驗證**：
   * 評分完成後，於「評估結果」與「審核佇列」面板中，檢查「評估核心 (Scoring Engine)」資訊。
   * 驗證其顯示為：**`🤖 OpenRouter (deepseek/deepseek-v4-flash)`**，且回傳的總得分、正向驅動因素、負向驅動因素等，均為 OpenRouter AI 生成的繁體中文結果。
3. **診斷端點確認**：
   * 瀏覽後端 `/api/health` 端點，檢查 `"ai_config_debug"` 的回傳結構。
   * 驗證 `db_users_with_openrouter_key_count` 大於 0，且 `OPENROUTER_API_KEY_len` 顯示出正確的全域變數金鑰長度（若有設定）。

### 4.3 Fallback 容錯與重試機制驗證
1. **429 速率重試測試**：
   * 故意在一瞬間向工作台排隊發送超過 20 個素材評估，觀察背景日誌。
   * 驗證遇到 OpenRouter 429 速率限制時，後端是否會列印 `[MetaAndromeda] OpenRouter 429 Rate Limit hit. Retrying...`，並等待數秒後成功完成評分。
2. **無金鑰 Heuristic Fallback 測試**：
   * 故意清空資料庫中測試用戶的 OpenRouter 金鑰，並不設定 `OPENROUTER_API_KEY` 全域變數，再次點選評估。
   * 驗證系統是否平滑退回到 Heuristic 引擎（總評分為Heuristic公式所得），且前端在 Lineage 處展示黃色警告：
     **`⚠️ AI 服務不可用，已啟用備用方案：openrouter:ClientError (API_KEY_INVALID...)`**。

### 4.4 本地編譯與打包檢查
1. **後端語法檢查**：
   * 在本機執行：`python -m py_compile backend/main.py backend/services/ai/openrouter_client.py backend/modules/meta_andromeda/runtime.py`。
   * 確保所有 Python 腳本編譯成功。
2. **前端打包測試**：
   * 在本機執行：`npm run build`。
   * 確保前端專案無任何 React 19 / Vite 7 編譯錯誤，成功打包出 `dist/` 目錄。
