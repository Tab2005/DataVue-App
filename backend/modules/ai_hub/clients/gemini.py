"""
AI Hub Module - Google Gemini Client
Google Gemini API 客戶端

此檔案重新導出 services.ai.gemini_client 以保持模組結構一致性。

使用方式:
    from modules.ai_hub.clients.gemini import GoogleGeminiClient
    
    client = GoogleGeminiClient(api_key="your_key")
    result = client.classify_intents(["keyword1", "keyword2"])
"""

# 重新導出現有的 Gemini 客戶端
from services.ai.gemini_client import GoogleGeminiClient

__all__ = ["GoogleGeminiClient"]
