"""
AI Hub Module - Clients
AI 客戶端集合

可用客戶端:
- OpenRouterClient: OpenRouter API 聚合服務
- GoogleGeminiClient: Google Gemini API
"""

from .openrouter import OpenRouterClient

__all__ = ["OpenRouterClient"]
