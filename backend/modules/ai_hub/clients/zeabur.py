"""
AI Hub Module - Zeabur Client
Zeabur AI Hub 客戶端（OpenAI 相容 API）

此檔案重新導出 services.ai.zeabur_client 以保持模組結構一致性。

使用方式:
    from modules.ai_hub.clients.zeabur import ZeaburAIClient
    
    client = ZeaburAIClient(api_key="your_key")
    response = client.chat("Hello!")
"""

# 重新導出現有的 Zeabur 客戶端
from services.ai.zeabur_client import ZeaburAIClient

__all__ = ["ZeaburAIClient"]
