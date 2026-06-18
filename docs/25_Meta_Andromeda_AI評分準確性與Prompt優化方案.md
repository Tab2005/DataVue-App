# 25 Meta Andromeda AI評分準確性與Prompt優化方案

本文件針對 Meta Andromeda 模組在啟用 Base64 多模態傳輸後，AI 評估分數與內容結果仍可能與實際素材產生認知落差的問題，提出第二階段的 Prompt 優化與評估指標標準化方案。

---

## 🕳️ 為什麼評分與圖片素材會有認知落差？

在解決了「AI 看不到圖片」的傳輸通道問題後，評估結果若仍與真實素材不符，主要有以下三個核心因素：

1. **Prompt 缺乏明確的評分與美學標準**：
   * 舊有的 Prompt 僅要求 AI 扮演評分運行時並給出 0-100 分，卻沒有給予 AI 具體的廣告美學、視覺層次、文字占比與轉化率（CRO）評估準則，導致模型給分過於主觀、隨意或一律給予保守的中庸分數（如 70-80 分）。
2. **診斷指標（`diagnostic_breakdown`）無規範**：
   * 舊有的 Prompt 僅說明 `diagnostic_breakdown values as short strings`，使得 AI 每次產出的評估維度與鍵值（Key）都是隨機的，無法在前端形成穩定的指標圖表（例如雷達圖或條形圖）。
3. **輕量級 AI 語言模型的視覺能力限制**：
   * 在使用成本較低的輕量模型（如 `gpt-4o-mini` 或 `gemini-1.5-flash`）時，其視覺 OCR、細節感知（例如 CTA 按鈕的邊框、小字）以及美感判斷力顯著弱於高階旗艦模型（如 `gpt-4o` 或 `claude-3-5-sonnet`）。

---

## 🚀 優化方案：結構化多維度廣告評估法

為了提升評分精準度並與實際圖片素材高度契合，我們對 Prompt 與 runtime 邏輯進行以下優化：

### 1. 定義四大視覺評估指標（Core Visual Metrics）
在 Prompt 中強制要求 AI 從以下維度進行視覺與文案的綜合審查：
* **視覺焦點與層次 (Visual Focus & Hierarchy)**：主體人物或產品是否突出，背景是否雜亂干擾視覺。
* **文字占比與易讀性 (Text Ratio & Legibility)**：圖中文字是否過多（避免 Meta 早期 20% 文字規則的雷區），文字與背景對比度是否足夠，是否清晰易讀。
* **CTA 顯著性 (CTA Prominence)**：圖中是否有引導按鈕或明確的視覺引導，且與文案中的 CTA 目標一致。
* **圖文關聯度與一致性 (Relevance & Consistency)**：圖像的視覺風格、情境，與廣告標題（Headline）及主要文字（Primary Text）是否緊密扣合，避免文不對題。

### 2. 標準化診斷細分欄位（Standardized Diagnostic Breakdown）
將 `diagnostic_breakdown` 的 Key 予以標準化，要求 AI 必須回傳以下四個維度的簡短 Traditional Chinese 評價：
* `visual_appeal` (視覺吸引力)
* `copywriting` (文案吸引力)
* `cta_clarity` (行動呼籲清晰度)
* `relevance` (圖文一致性)

---

## 💻 程式碼修改實作

### 修改 [runtime.py](file:///C:/Users/BWM2/Documents/python/DataVue-App/backend/modules/meta_andromeda/runtime.py) 內 `OpenRouterScoringProvider` 的 Prompt 結構

```python
# 修改後的 prompt 與 system_prompt 定義：

        prompt = (
            "You are the Meta Andromeda creative scoring runtime, an expert in mobile ad conversion optimization (CRO) and ad design.\n"
            "Analyze both the provided ad image (via image_url) and the text metadata details to evaluate the overall performance.\n\n"
            
            "CRITICAL EVALUATION CRITERIA:\n"
            "1. Visual Focus & Hierarchy: Is the product/subject clear? Is the background clean and supportive?\n"
            "2. Text Ratio & Legibility: Are copy elements in the image readable? Is the text-to-image ratio balanced (avoiding overloaded text)?\n"
            "3. CTA Prominence: Is there a clear visual CTA in the image, and does it align with the text CTA?\n"
            "4. Relevance & Consistency: Does the visual style connect tightly with the Headline and Primary text?\n\n"
            
            "Return JSON only with keys: overall_score, roas_band, top_positive_drivers, "
            "top_negative_drivers, risk_tags, diagnostic_breakdown, summary.\n"
            "Use overall_score as integer 0-100. Be critical and conservative—do not give high scores (>80) unless the creative is truly premium and highly optimized.\n"
            "Use roas_band as one of high/mid/low/null.\n"
            
            "The diagnostic_breakdown object MUST contain exactly these keys with short Chinese evaluation:\n"
            "  - visual_appeal: Evaluates composition, focal point, and aesthetics.\n"
            "  - copywriting: Evaluates headline and primary text persuasiveness.\n"
            "  - cta_clarity: Evaluates CTA prominence and action clarity.\n"
            "  - relevance: Evaluates the consistency between the image and texts.\n\n"
            
            "All textual outputs (summary, top_positive_drivers, top_negative_drivers, diagnostic_breakdown values) MUST be in Traditional Chinese (繁體中文).\n"
            f"Asset type: {score_payload['asset_type']}\n"
            f"Objective: {score_payload.get('objective', 'purchase')}\n"
            f"Placement family: {score_payload.get('placement_family', 'all')}\n"
            f"Market: {score_payload.get('market', 'TW')}\n"
            f"Request mode: {request_mode}\n"
            f"Headline: {_clip(request_context.get('headline'))}\n"
            f"Primary text: {_clip(request_context.get('primary_text'))}\n"
            f"CTA: {_clip(request_context.get('cta'))}\n"
        )
        system_prompt = (
            "You are an elite performance marketing creative auditor. Score ad creatives conservatively based on CRO best practices.\n"
            "Always inspect the image details if available. Give objective, realistic scores. Do not sugarcoat.\n"
            "All explanations, summaries, and breakdowns MUST be written in Traditional Chinese (繁體中文)."
        )
```

---

## 🎯 預期改善與效益

1. **評估與實質畫面契合**：AI 獲得了明確的審查指標，在多模態圖片輸入時，會著重分析視覺焦點與 CTA，評分與分析結果不再單純依賴純文字文案。
2. **評估結果更加客觀**：透過 "Be critical and conservative" 的要求，避免 AI 無差別給予高分，讓行銷人員能真正篩選出優質素材。
3. **前端指標呈現穩定化**：由於 `diagnostic_breakdown` 的 Key 獲得標準化，前端可以穩定讀取 `visual_appeal`、`copywriting`、`cta_clarity` 與 `relevance` 等數值，以便於視覺化呈現。
