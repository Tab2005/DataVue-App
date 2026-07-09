import os
import json
from typing import Optional, Dict, Any, Generator

# New Zeabur AI Hub client
from services.ai.zeabur_client import ZeaburAIClient
from services.ai.openrouter_client import OpenRouterClient


class AIService:
    """
    Service for interacting with AI models.
    Supports Dual-Mode:
    1. OpenRouter Mode (openrouter): Uses OpenRouter API aggregator (defaulting to DeepSeek)
    2. Zeabur Mode (zeabur): Uses OpenAI-compatible API via Zeabur AI Hub (supports 10+ models)
    """

    # Available providers
    PROVIDERS = {
        "openrouter": {
            "name": "OpenRouter",
            "description": "使用 OpenRouter API 聚合服務",
            "requires_sdk": False
        },
        "zeabur": {
            "name": "Zeabur AI Hub",
            "description": "透過 Zeabur 統一介面，支援多種模型 (Gemini, Claude, GPT 等)",
            "requires_sdk": False
        }
    }

    @staticmethod
    def get_available_providers() -> Dict[str, Dict]:
        """Get list of available AI providers"""
        return AIService.PROVIDERS.copy()

    @staticmethod
    def get_available_models(provider: str = "zeabur", remote: bool = False, api_key: Optional[str] = None) -> Dict[str, Dict]:
        """Get available models for a provider"""
        if provider == "zeabur":
            client = AIService.get_zeabur_client(api_key=api_key)
            if client:
                return client.get_available_models(remote=remote)
            return ZeaburAIClient.MODELS
        elif provider == "openrouter":
            client = AIService.get_openrouter_client(api_key=api_key)
            if client:
                return client.get_available_models(remote=remote)
            return OpenRouterClient.MODELS
        return {}

    @staticmethod
    def get_openrouter_client(api_key: Optional[str] = None) -> Optional[OpenRouterClient]:
        """Initialize OpenRouter Client."""
        try:
            return OpenRouterClient(api_key=api_key)
        except Exception as e:
            print(f"Error initializing OpenRouter Client: {e}")
            return None

    @staticmethod
    def get_zeabur_client(api_key: Optional[str] = None) -> Optional[ZeaburAIClient]:
        """
        Initialize Zeabur AI Hub Client (OpenAI-compatible).
        """
        try:
            return ZeaburAIClient(api_key=api_key)
        except Exception as e:
            print(f"Error initializing Zeabur Client: {e}")
            return None

    @staticmethod
    def test_connection(
        api_key: Optional[str] = None,
        provider: str = "zeabur",
        model: str = "gemini-2.5-flash"
    ) -> bool:
        """
        Test if the AI service is reachable.
        """
        if provider == "zeabur":
            client = AIService.get_zeabur_client(api_key)
            if not client:
                return False
            return client.test_connection(model=model)
        elif provider == "openrouter":
            client = AIService.get_openrouter_client(api_key)
            if not client:
                return False
            try:
                res = client.test_connection()
                return res.get("success", False)
            except Exception as e:
                print(f"OpenRouter Connection Failed: {e}")
                return False
        return False

    @staticmethod
    def analyze_data(
        data: Dict[str, Any], 
        context: str, 
        api_key: Optional[str] = None,
        provider: str = "zeabur",
        model: str = "deepseek/deepseek-v4-flash",
        report_type: str = "ad_analysis",
        period: str = "weekly",
        module_type: str = "fb_ads"
    ) -> Generator[str, None, None]:
        """
        Analyzes the provided data using the LLM.
        Returns a generator for streaming response.
        """
        
        # Build system prompt based on report type, period and module type
        if report_type == "contribution_analysis":
            # MMM 廣告活動貢獻衡量白話解讀（docs/21 任務 2.3）
            system_prompt = """
            您是一位資深行銷顧問，正在向一位「不懂統計」的行銷主管口頭報告 MMM 廣告活動貢獻分析的結果。
            您的目標是把 MMM 引擎算出的 results / diagnostics 翻成白話文，讓對方可以據此討論預算配置。

            最重要的硬性規則（違反即為錯誤）：
            1. **禁止統計術語直出**：當您需要提到「共線性 / 中位數 / 區間 / R² / 邊際報酬 / 雜訊天花板 / 基線」等詞時，必須立刻用一句白話比喻接在後面，讓對方真的能理解。比喻方向：
               - 共線性 → 「這兩組活動總是一起加減預算，模型分不清功勞是誰的」
               - 中位數 / 區間 → 「我們跑了五次重新估計，大約落在這個範圍，不是單一精確值」
               - R² → 「模型解釋了幾成的轉換變化」
               - 邊際報酬 → 「現在再多投一些錢，大約能多帶來幾筆訂單」
               - 雜訊天花板 → 「就算模型完美，雜訊讓預測最多也只能到這個準度」
               - 基線 → 「就算完全不投廣告，也會自然發生的那部分」
            2. **區間語氣**：貢獻一律以「大約 X%～Y% 之間」呈現，**禁止**寫成單一精確數字。邊際也是「大概多帶來幾筆」而非「精確 N 筆」。
            3. **存疑組必須明說**：被標為「存疑 / DOUBTFUL」的組別，請明確寫出「這組的數字目前不可信，建議先不要據此做預算決策」。
            4. **禁止線性外推**：談到邊際報酬時必須提醒「這是在目前花費水位附近的估計，不代表加十倍預算就有十倍效果」。
            5. **只引用 payload 內的數字**：禁止編造 payload 沒有的活動、占比或金額。
            6. **禁止 LaTeX 符號**（不要寫 \\rightarrow、\\Delta 等），改用 → 或一般文字。
            7. **語言**：繁體中文（台灣市場用語，例如「工作」「曝光」）。

            嚴格的 Markdown 格式規範（前端用 ReactMarkdown 渲染，必須遵守才能正確顯示）：
            - 必須用 `## 二級標題` 開頭分節（**不要**用 `###` 或更大，**不要**用粗體偽裝標題）
            - 列點必須用 `- ` 開頭（**禁止**用 `<br>` 連接，**禁止**用全形 `·` 或 `、` 拼湊偽清單）
            - 比較資料用 markdown 表格（`| col1 | col2 |` 格式），**禁止**用 inline 文字拼湊
            - 關鍵數字與組名用 `**粗體**`，**禁止**用其他格式強調
            - 段落之間用**空一行**分隔，**禁止**用 `<br>` 或 `  `（雙空格）當換行
            - 條列與表格上下都要空一行
            - **完全禁止**使用任何 HTML 標籤（`<br>` `<sub>` 等）
            - 表情符號僅在分節標題開頭可加一個（✅ ⚠️ ❓），內文不要濫用

            報告結構（依此順序產出四段，每段都用 `##` 開頭）：
            ```markdown
            ## 一句話總結
            （1-2 句話講最重要的一件事）

            ## 功勞被高估 / 被低估的組別
            - **G1 主力常態**：自報占比 49%，MMM 貢獻大約 50%–55% 之間（簡述）
            - **G2 官網檔期**：自報占比 23%，MMM 貢獻大約 40%–45% 之間（簡述，且標註「收割嫌疑」或「真實引擎」）
            - 表格總覽（用 markdown 表格總結所有組別的對照）：

            | 組別 | 自報占比 | MMM 貢獻 | 解讀 |
            |---|---|---|---|
            | G1 主力 | 49% | 50%–55% | 略高估 |
            | G2 官網 | 23% | 40%–45% | 收割嫌疑 |

            ## 下一塊錢建議投給誰
            **首選：G2 官網檔期**（理由：邊際報酬最高，但需註明共線性警告）。
            若首選被標存疑，必須寫「但因共線性，結論待釐清」。

            ## 這份分析要保留的地方
            - Holdout R² = 0.10（偏低 → 「模型解釋力有限，結論需保守」）
            - G1 與 G3 共線 r=0.77（→ 「這兩組總是同步加減，預算結論待釐清」）
            ```
            """
        elif report_type == "weekly_summary":
            period_labels = {
                "daily": "日報 (Daily)",
                "weekly": "週報 (Weekly)",
                "monthly": "月報 (Monthly)"
            }
            label = period_labels.get(period, "績效")
            
            # --- Module-Specific Focus ---
            if module_type == "ga4":
                # GA4 Prompt
                system_prompt = f"""
                您是一位資深的 網站分析師 與 增長顧問，正在協助客戶撰寫一份 GA4 {label}分析報告。
                您的目標是根據提供的數據，產出一份專業且具備深度洞察的摘要。
                
                重要規則：
                1. **禁止使用 LaTeX 數學符號** (例如 $\rightarrow$ 或 \Delta)，請改用一般文字或符號 (例如 → 或 成長/下降)。
                2. **語言與語氣**：必須使用繁體中文 (Traditional Chinese)，且專業術語需符合台灣市場慣例 (例如：使用「工作階段」而非「回話」)。
                3. **數據導向**：對關鍵指標數字加粗，並解釋數據背後的商業意義。

                報告結構：
                1. **數據總覽 ({label}核心指標)**：總結網站流量（使用者、工作階段）與品質指標（參與率、平均參與時間），並與前期對比。
                2. **流量來源分析**：識別表現最優異或成長最顯著的流量管道。
                3. **轉換與收益分析**：分析轉換數、轉換率與收益趨勢。
                4. **優化行動建議**：提供 2-3 個針對網站內容優化、流量獲取策略或轉換漏斗改善的具體建議。

                語氣：專業、銳利、數據導向。
                格式：Markdown。
                """
            else:
                # Facebook Ads Prompt (Default)
                period_focus = ""
                if period == "daily":
                    period_focus = "請特別關注昨日與前日的數據波動、預算消耗情況，以及是否需要立即進行開關調整或排除異常。"
                elif period == "weekly":
                    period_focus = "請著重於本週與上週的趨勢對比、廣告組合（Ad Sets）的表現差異，以及下一階段的預算分配建議。"
                elif period == "monthly":
                    period_focus = "請從戰略角度分析本月整體 ROI、不同廣告創意（Creative）的長期表現趨勢，並提供下個月的整體投放策略建議。"

                system_prompt = f"""
                您是一位資深的 Facebook 廣告顧問，正在協助客戶撰寫一份{label}分析報告。
                您的目標是根據提供的數據，產出一份專業且具備深度洞察的摘要。
                
                報告結構：
                1. **執行摘要 ({label}總結)**：用 2-3 句話總結整體表現（花費、ROAS、成交數），並嘗試與前期對比。
                2. **亮點分析**：識別 1-2 個表現優秀的廣告活動或組合（例如高 ROAS 或低 CPA）。
                3. **優化空間與異常檢測**：{period_focus}
                4. **後續行動建議**：提供 2-3 個最具體且可執行的建議。
     
                語氣：專業、鼓勵、數據導向。
                語言：繁體中文 (Traditional Chinese)。
                格式：Markdown（對關鍵指標數字加粗）。
                """
        else:
            system_prompt = """
            You are an expert Facebook Ads Analyst (Senior Media Buyer).
            Your task is to analyze the provided ad performance data and generate a professional diagnosis report.
            
            Structure your response in these 3 sections:
            
            ### 🔴 Critical Issues (紅燈警示)
            Identify ads or ad sets that are wasting budget (High CPA, Low ROAS, Saturation).
            
            ### 🟢 Opportunities (綠燈機會)
            Identify high-performing assets that deserve more budget.
            
            ### 💡 Strategic Advice (策略建議)
            Give 1-2 high-level actionable suggestions based on the funnel data.
            
            Tone: Professional, Concise, Action-oriented.
            Language: Traditional Chinese (繁體中文).
            """
        
        user_message = f"""
        Context: {context}
        
        Data:
        {json.dumps(data, indent=2, ensure_ascii=False)}
        """

        # Use appropriate provider
        if provider == "zeabur":
            yield from AIService._analyze_with_zeabur(
                system_prompt=system_prompt,
                user_message=user_message,
                api_key=api_key,
                model=model
            )
        else:
            yield from AIService._analyze_with_openrouter(
                system_prompt=system_prompt,
                user_message=user_message,
                api_key=api_key,
                model=model
            )

    @staticmethod
    def _analyze_with_zeabur(
        system_prompt: str,
        user_message: str,
        api_key: Optional[str],
        model: str
    ) -> Generator[str, None, None]:
        """Use Zeabur AI Hub (OpenAI-compatible) for analysis"""
        client = AIService.get_zeabur_client(api_key)
        if not client:
            yield "Error: No valid API Key or AI Service configured."
            return

        try:
            response = client.generate_content(
                prompt=user_message,
                model=model,
                system_prompt=system_prompt,
                stream=True
            )
            
            for chunk in response:
                yield chunk
                
        except Exception as e:
            yield f"\n[System Error during Analysis: {str(e)}]"

    @staticmethod
    def _analyze_with_openrouter(
        system_prompt: str,
        user_message: str,
        api_key: Optional[str],
        model: str
    ) -> Generator[str, None, None]:
        """Use OpenRouter client for analysis"""
        client = AIService.get_openrouter_client(api_key)
        if not client:
            yield "Error: No valid API Key or AI Service configured."
            return

        try:
            model_to_use = model or "deepseek/deepseek-v4-flash"
            response_stream = client.generate_content_stream(
                prompt=user_message,
                model=model_to_use,
                system_prompt=system_prompt
            )
            
            for chunk in response_stream:
                yield chunk
                    
        except Exception as e:
            yield f"\n[System Error during Analysis: {str(e)}]"
