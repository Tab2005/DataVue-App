"""
AI Hub Module - OpenRouter Client
OpenRouter API 客戶端

此檔案重新導出 services.ai.openrouter_client 以保持模組結構一致性。

使用方式:
    from modules.ai_hub.clients.openrouter import OpenRouterClient
    
    client = OpenRouterClient(api_key="your_key")
    result = client.test_connection()
"""

# 重新導出現有的 OpenRouter 客戶端
from services.ai.openrouter_client import OpenRouterClient

__all__ = ["OpenRouterClient"]
