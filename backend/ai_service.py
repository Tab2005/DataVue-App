import os
import json
from typing import Optional, Dict, Any, Generator
from google.genai import Client, types
from pydantic import BaseModel

class AIService:
    """
    Service for interacting with AI models (Google Gemini via Zeabur or Direct).
    Supports Dual-Mode:
    1. Zeabur Managed: Uses ZEABUR_AI_HUB_API_KEY from env.
    2. Standard: Uses user-provided API Key.
    """

    @staticmethod
    def get_client(api_key: Optional[str] = None) -> Optional[Client]:
        """
        Initialize Google GenAI Client based on available credentials.
        Priority:
        1. Zeabur Managed (Env Var) - Ignores user api_key if present? 
           Actually, we might want to allow override. 
           But for now, if Zeabur Key exists, we use it as the default system-wide AI.
           
        Wait, if the user explicitly provides a key in the request (e.g. BYOK mode), we should strictly use that.
        If no key is provided in request, we check for Zeabur env var.
        """
        
        # 1. Zeabur Managed Mode (System Level)
        # Check environment variable
        zeabur_key = os.getenv("ZEABUR_AI_HUB_API_KEY")
        
        # Logic: If api_key is provided (BYOK), use it standardly.
        # If NOT provided, try Zeabur.
        
        if api_key:
            # Standard Mode (User's own key)
            # Default to standard Google Endpoint
            try:
                return Client(api_key=api_key)
            except Exception as e:
                print(f"Error initializing Standard Client: {e}")
                return None
                
        elif zeabur_key:
            # Zeabur Managed Mode
            try:
                # Based on user provided example
                return Client(
                    api_key=zeabur_key,
                    vertexai=True, # User example used this, likely required for Zeabur Hub? Or maybe not, but let's follow example. 
                    # Wait, user example: client = Client(api_key=..., vertexai=True, ...)
                    # Let's stick to the example.
                    http_options=types.HttpOptions(
                        base_url="https://hnd1.aihub.zeabur.ai/gemini", # Default to Tokyo, maybe make configurable?
                        headers={
                            "Authorization": zeabur_key
                        }
                    )
                )
            except Exception as e:
                print(f"Error initializing Zeabur Client: {e}")
                return None
        
        return None

    @staticmethod
    def test_connection(api_key: Optional[str] = None) -> bool:
        """
        Test if the AI service is reachable.
        """
        client = AIService.get_client(api_key)
        if not client:
            return False
            
        try:
            # Simple generation to test
            response = client.models.generate_content(
                model="gemini-2.5-flash", # Use a fast model
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
        model: str = "gemini-2.5-flash",
        report_type: str = "ad_analysis"
    ) -> Generator[str, None, None]:
        """
        Analyzes the provided data using the LLM.
        Returns a generator for streaming response.
        """
        client = AIService.get_client(api_key)
        if not client:
            yield "Error: No valid API Key or AI Service configured."
            return

        # key_metrics = ... (We assume data is already summarized or Raw)
        # For Phase 1, we pass the JSON dumps directly but truncated if needed.
        
        system_prompt = ""
        
        if report_type == "weekly_summary":
            # 🟢 WEEKLY SUMMARY REPORT PROMPT
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
            # 🔴 DEFAULT: DIRECT AD ANALYSIS PROMPT
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
        
        try:
            # Stream the response
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
