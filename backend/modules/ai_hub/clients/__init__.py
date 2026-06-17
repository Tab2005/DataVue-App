"""
AI Hub Module - Clients
AI 客戶端集合

可用客戶端:
- ZeaburAIClient: Zeabur AI Hub (OpenAI 相容)
- GoogleGeminiClient: Google Gemini API
"""

from .zeabur import ZeaburAIClient
from .openrouter import OpenRouterClient

__all__ = ["ZeaburAIClient", "OpenRouterClient"]
