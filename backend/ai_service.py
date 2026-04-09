import os
import json
from typing import Optional, Dict, Any, Generator

# Legacy Google GenAI SDK (for backward compatibility)
try:
    from google.genai import Client, types
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
    print("[WARN] google.genai not available, only Zeabur mode will work")

# New Zeabur AI Hub client
from services.ai.zeabur_client import ZeaburAIClient


class AIService:
    """
    Service for interacting with AI models.
    Supports Dual-Mode:
    1. Legacy Mode (google_gemini): Uses Google GenAI SDK directly
    2. Zeabur Mode (zeabur): Uses OpenAI-compatible API via Zeabur AI Hub (supports 10+ models)
    """

    # Available providers
    PROVIDERS = {
        "google_gemini": {
            "name": "Google Gemini",
            "description": "直接使用 Google Gemini API",
            "requires_sdk": True
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
        providers = {}
        for key, config in AIService.PROVIDERS.items():
            if key == "google_gemini" and not GOOGLE_GENAI_AVAILABLE:
                continue  # Skip if SDK not available
            providers[key] = config
        return providers

    @staticmethod
    def get_available_models(provider: str = "zeabur", remote: bool = False, api_key: Optional[str] = None) -> Dict[str, Dict]:
        """Get available models for a provider"""
        if provider == "zeabur":
            # If remote is true, we need a client to fetch. 
            # We use the provided api_key (or empty if None)
            client = AIService.get_zeabur_client(api_key=api_key)
            if client:
                return client.get_available_models(remote=remote)
            return ZeaburAIClient.MODELS
        elif provider == "google_gemini":
            # Direct Google Gemini Mode
            try:
                from services.ai.gemini_client import GoogleGeminiClient
                client = GoogleGeminiClient(api_key=api_key)
                models = client.get_available_models(remote=remote)
                
                # Transform to common format if needed (GoogleGeminiClient already returns a good format)
                # Just Ensure 'description' exists for unified UI
                for m_id, config in models.items():
                    if 'description' not in config:
                        config['description'] = config.get('display_name', m_id)
                    if 'provider' not in config:
                        config['provider'] = 'google'
                return models
            except Exception as e:
                print(f"Error fetching Google Gemini models: {e}")
                return {
                    "gemini-1.5-flash": {"description": "Gemini 1.5 Flash", "provider": "google"},
                    "gemini-1.5-pro": {"description": "Gemini 1.5 Pro", "provider": "google"},
                }
        return {}

    @staticmethod
    def get_legacy_client(api_key: Optional[str] = None) -> Optional["Client"]:
        """
        Initialize legacy Google GenAI Client.
        For backward compatibility with existing google_gemini provider.
        """
        if not GOOGLE_GENAI_AVAILABLE:
            return None

        zeabur_key = os.getenv("ZEABUR_AI_HUB_API_KEY")
        
        if api_key:
            # Standard Mode (User's own key)
            try:
                return Client(api_key=api_key)
            except Exception as e:
                print(f"Error initializing Standard Client: {e}")
                return None
                
        elif zeabur_key:
            # Zeabur Managed Mode (Legacy path through Google SDK)
            try:
                return Client(
                    api_key=zeabur_key,
                    vertexai=True,
                    http_options=types.HttpOptions(
                        base_url="https://hnd1.aihub.zeabur.ai/gemini",
                        headers={
                            "Authorization": zeabur_key
                        }
                    )
                )
            except Exception as e:
                print(f"Error initializing Zeabur Client (legacy): {e}")
                return None
        
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
        else:
            # Legacy Google Gemini mode
            client = AIService.get_legacy_client(api_key)
            if not client:
                return False
            try:
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents="Hello",
                )
                return True
            except Exception as e:
                print(f"AI Connection Test Failed: {e}")
                return False

    @staticmethod
    def analyze_data(
        data: Dict[str, Any], 
        context: str, 
        api_key: Optional[str] = None,
        provider: str = "zeabur",
        model: str = "gemini-1.5-flash",
        report_type: str = "ad_analysis",
        period: str = "weekly"
    ) -> Generator[str, None, None]:
        """
        Analyzes the provided data using the LLM.
        Returns a generator for streaming response.
        """
        
        # Build system prompt based on report type and period
        if report_type == "weekly_summary":
            period_labels = {
                "daily": "日報 (Daily)",
                "weekly": "週報 (Weekly)",
                "monthly": "月報 (Monthly)"
            }
            label = period_labels.get(period, "績效")
            
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
            yield from AIService._analyze_with_legacy(
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
    def _analyze_with_legacy(
        system_prompt: str,
        user_message: str,
        api_key: Optional[str],
        model: str
    ) -> Generator[str, None, None]:
        """Use legacy Google GenAI SDK for analysis"""
        if not GOOGLE_GENAI_AVAILABLE:
            yield "Error: Google GenAI SDK not available. Please use Zeabur provider."
            return

        client = AIService.get_legacy_client(api_key)
        if not client:
            yield "Error: No valid API Key or AI Service configured."
            return

        try:
            # 確保模型名稱路徑正確
            model_to_use = model
            if not model_to_use.startswith('models/'):
                model_to_use = f"models/{model_to_use}"

            response_stream = client.models.generate_content_stream(
                model=model_to_use,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=system_prompt),
                            types.Part.from_text(text=user_message)
                        ]
                    )
                ]
            )
            
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            yield f"\n[System Error during Analysis: {str(e)}]"
