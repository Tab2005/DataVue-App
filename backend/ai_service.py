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
            # Limited models for legacy mode
            return {
                "gemini-2.0-flash": {"description": "Gemini 2.0 Flash", "provider": "google"},
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
                    model="gemini-2.5-flash",
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
        model: str = "gemini-2.5-flash",
        report_type: str = "ad_analysis"
    ) -> Generator[str, None, None]:
        """
        Analyzes the provided data using the LLM.
        Returns a generator for streaming response.
        
        Args:
            data: Data to analyze
            context: Context description
            api_key: User's API key (optional, falls back to env var)
            provider: AI provider ('zeabur' or 'google_gemini')
            model: Model to use
            report_type: 'ad_analysis' or 'weekly_summary'
        """
        
        # Build system prompt based on report type
        if report_type == "weekly_summary":
            system_prompt = """
            You are a Senior Facebook Ads Consultant helping a client prepare a Weekly Performance Report (週報).
            Your goal is to write a cohesive, professional summary based on the provided data context.
            
            Structure:
            1. **Executive Summary (本週總結)**: 2-3 sentences summarizing the overall performance (Spend, ROAS, Purchases) compared to the previous period (if available).
            2. **Key Wins (亮點分析)**: Identify 1-2 campaigns or ad sets that performed efficiently (High ROAS, Low CPA).
            3. **Areas for Improvement (優化空間)**: Identify 1-2 areas with declining performance or wasted budget.
            4. **Next Steps (下週建議)**: 2-3 specific actionable bullet points for the next week.

            Tone: Professional, Encouraging, Insightful.
            Language: Traditional Chinese (繁體中文).
            Format: Markdown (use bolding for key numbers).
            """
        else:
            system_prompt = """
            You are an expert Facebook Ads Analyst (Senior Media Buyer).
            Your task is to analyze the provided ad performance data and generate a professional diagnosis report.
            
            Structure your response in these 3 sections:
            
            ### 🔴 Critical Issues (紅燈警示)
            Identify ads or ad sets that are wasting budget (High CPA, Low ROAS, Saturation).
            Be specific with names and numbers.
            
            ### 🟢 Opportunities (綠燈機會)
            Identify high-performing assets that deserve more budget.
            
            ### 💡 Strategic Advice (策略建議)
            Give 1-2 high-level actionable suggestions based on the funnel data (CTR -> CVR).
            
            Tone: Professional, Concise, Action-oriented. No fluff.
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
            response_stream = client.models.generate_content_stream(
                model=model,
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
