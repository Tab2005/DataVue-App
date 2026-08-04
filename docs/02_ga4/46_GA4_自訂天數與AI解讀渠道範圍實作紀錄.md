# 46_GA4 自訂天數與 AI 解讀渠道範圍實作紀錄

## 背景

延續渠道篩選功能（[[42_GA4_到達頁渠道篩選實作規劃]]、[[44_GA4_渠道值自訂分組實作規劃]]、[[45_GA4_商品渠道篩選實作紀錄]]）之後，順著使用者操作過程中提出的三個小需求直接動工，設計已在對話中確定，完工後補記錄（同 [[45_GA4_商品渠道篩選實作紀錄]] 的紀錄格式）。程式碼裡的註解已經寫 `docs/46`，本文件補上對應內容。

## 內容一：渠道對照／到達頁／商品共用天數選擇器加上「自訂」

- **需求**：右上角天數選擇原本只有 7/14/30 天按鈕，希望能自訂天數
- **確認可行性**：後端 `days` query 參數（`channels`/`landing-pages`/`items` 三個端點）本來就是 `Query(7, ge=1, le=90)`，不是只接受 7/14/30，所以自訂天數不用改後端
- **實作**：`frontend/src/pages/GA4Insights.jsx` 的共用 `DaySelector` 元件在三個預設按鈕旁加一個文字輸入框（`type="number"`, `min=1`, `max=90`），輸入後按 Enter 或失焦套用；外部切回 7/14/30 時輸入框自動清空回 placeholder；非預設值時輸入框邊框標色以示目前是自訂天數
- **範圍**：僅套用在渠道對照、到達頁、商品三個分頁（當日總覽分頁性質不同，不適用天數選擇）

## 內容二：AI 白話解讀要交代清楚渠道篩選範圍

- **問題**：到達頁／商品分頁篩選渠道後，畫面數字已經是篩選後的子集，但送給 AI 的 `contextLabel`/payload 完全沒有提到這件事，AI 容易用「整體/全店」的語氣下結論，造成誤導
- **釐清的前提**：這其實不是資料模型問題——渠道篩選後的到達頁/商品快照本來就用 `ch_`/`chg_` 雜湊前綴存成獨立的 `kind`（見 [[42_GA4_到達頁渠道篩選實作規劃]]/[[44_GA4_渠道值自訂分組實作規劃]]），所以「篩選後的 AI 解讀」跟「全域 AI 解讀」本來就各自存在不同的 `snapshot_id`，互不覆蓋，不用額外處理
- **實際要調整的是 AI 指令／context**：
  - 前端：`LandingPagesTab.jsx`/`ItemsTab.jsx` 呼叫 `<AIInsightNote>` 時，`contextLabel` 加上 `channelScopeLabel()`（渠道維度＋渠道值/自訂分組組成一句話），`buildPayload()` 也把 `channel_dimension`/`channel_value`/`channel_group` 一併帶進去
  - 後端：`ai_service.py` 的 `ga4_insights` 分支比照既有 `attribution_model` 的做法，從 payload 讀渠道欄位組成 `channel_scope_note`，塞進系統提示的硬性規則（規則 4-1），強制 AI 在「一句話總結」開頭先講清楚篩選範圍；商品分頁另外註明 `views_growth_rate`/`is_potential` 維持全渠道口徑、不受此篩選影響（因為篩選只套用在主指標，見 [[45_GA4_商品渠道篩選實作紀錄]] 的設計決策）

## 內容三：AI 解讀免責聲明動態顯示目前模型

- **需求**：免責聲明目前寫死「AI 解讀僅供參考，數字以上方圖表為準」，希望能動態顯示目前實際使用的模型（例如 `nvidia/nemotron-3-ultra-550b-a55b:free`），之後在 AI 設定頁換模型不用改程式碼
- **實作**：
  - `frontend/src/services/aiService.js` 新增 `getSettings()`，打 `GET /api/ai/settings`（既有端點，回傳目前使用者存的 `ai_provider`/`ai_model`）
  - `AIInsightNote`（`GA4InsightsShared.jsx`）掛載時抓一次設定，`ai_model` 有值時免責聲明改成「AI 解讀僅供參考（目前使用模型：{model}）…」；這個元件是共用的，渠道對照/到達頁/商品/當日總覽四個分頁都一起生效
  - 依據：`handleGenerate()` 呼叫 `analyzeDataStream` 時 provider/model 都傳 `null`，後端 `analyze_data` 會 fallback 用 `user_settings.get("ai_model", ...)`，跟 `/api/ai/settings` 回傳的 `ai_model` 是同一個來源，兩邊資訊不會對不起來

## 附帶修復：AI 串流回應中文字元亂碼（「???」）

- **症狀**：使用者回報 AI 解讀內容裡偶爾出現 `???`／`�`
- **根因**：`aiService.js::analyzeDataStream` 用 `TextDecoder` 逐段解碼串流回應時，`decoder.decode(value)` 沒有加 `{ stream: true }`，若一個中文字（UTF-8 多位元組）剛好被切在兩個網路封包之間，兩段各自解碼都會產生殘缺位元組、被 decoder 換成替代字元
- **證據**：同專案的 `frontend/src/pages/Analytics.jsx`（FB 廣告 AI 分析）呼叫同一支 `/api/ai/analyze` 串流端點，但那邊的 `decoder.decode(value, { stream: true })` 本來就寫對，所以不會有這個問題——確認純粹是 `aiService.js` 這處漏寫
- **修復**：補上 `{ stream: true }`
- **同時處理的另一個回報**：AI 解讀內容出現「仕階段」（應為「工作階段」）——判斷屬於所選免費模型（`nvidia/nemotron-3-ultra-550b-a55b:free`）生成品質問題，非串流解碼或指令錯誤（指令本來就正確要求「工作階段」四字）。已在系統提示補一句明確禁止「仕階段」等變體的提醒作為防呆，但不保證完全根治，若持續出現建議在 AI 設定頁換一個更穩定的模型（免責聲明現在會動態顯示模型，方便比對）

## 驗證結果

- 後端：`pytest tests/ -q -k "ga4 or ai"` 全數通過（224 個，含 [[45_GA4_商品渠道篩選實作紀錄]] 的測試），`ai_service.py` 的 prompt 組建邏輯另外用互動式腳本驗證多種 kind／渠道篩選組合都能正常組出 system_prompt 不噴錯
- 前端：`vite build` 編譯成功
- 這三個內容都是小幅前端/prompt 調整，未涉及資料模型或 API 契約變更，未額外撰寫自動化測試（AI 生成文字內容本質上無法用單元測試斷言）
