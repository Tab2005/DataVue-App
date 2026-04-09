"""
Google Gemini 直連客戶端
直接使用 Google AI Studio 的 API Key 呼叫 Gemini 模型
"""
import google.genai as genai
from google.genai import types
import logging
import sys
from typing import Optional, Dict, List
import os

logger = logging.getLogger(__name__)


class GoogleGeminiClient:
    """Google Gemini 直連客戶端 - 使用 Google AI Studio API Key"""

    # 支援的 Gemini 模型
    MODELS = {
        "gemini-2.0-flash": {
            "display_name": "Gemini 2.0 Flash",
            "description": "最新世代、極速 ✅ 推薦",
            "max_tokens": 8192
        },
        "gemini-1.5-flash": {
            "display_name": "Gemini 1.5 Flash",
            "description": "穩定版",
            "max_tokens": 8192
        },
        "gemini-1.5-pro": {
            "display_name": "Gemini 1.5 Pro",
            "description": "高品質、長文本",
            "max_tokens": 32000
        }
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Google Gemini 客戶端
        """
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY")
        if not self.api_key:
            raise ValueError("Google AI API Key is required.")
        
        # 使用新版 SDK 的 Client 模式
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.0-flash"  # 預設改用 2.0

    def set_model(self, model_name: str):
        """設定使用的模型"""
        # 這裡不強限制，因為可能會有同步下來的新模型
        self.model_name = model_name

    def generate_content(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        生成內容 (使用新版 SDK 語法)
        """
        model_name = model or self.model_name
        
        logger.debug(f"[GoogleGeminiClient] generate_content with model={model_name}")
        
        try:
            # 準備配置
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens or self.MODELS.get(model_name, {}).get("max_tokens", 8192)
            )

            # 呼叫 API
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )

            return response.text
            
        except Exception as e:
            logger.error(f"[GoogleGeminiClient] ERROR: {str(e)}", exc_info=True)
            raise

    def test_connection(self) -> Dict:
        """測試連線"""
        try:
            response = self.generate_content(
                prompt="Respond with 'OK'",
                temperature=0
            )
            
            return {
                "success": True,
                "message": "Connected to Google Gemini API Successfully",
                "response": response,
                "model": self.model_name
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "model": self.model_name
            }

    @classmethod
    def get_available_models(cls) -> Dict:
        """取得可用模型列表"""
        return cls.MODELS
