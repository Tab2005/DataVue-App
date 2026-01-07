"""
AI Hub Module
AI 整合模組 - 提供 AI 客戶端、意圖分類器、以及相關 API

此模組整合了所有 AI 相關功能，可複用於其他 FastAPI 專案。

使用方式 (在其他專案):
    1. 複製 modules/ai_hub/ 資料夾
    2. 複製 services/ai/ 資料夾（核心實作）
    3. 複製 ai_service.py（主服務）
    4. 安裝依賴: pip install google-genai openai

    from fastapi import FastAPI
    from modules.ai_hub import router as ai_router, AIService
    
    app = FastAPI()
    app.include_router(ai_router, prefix="/api/ai")
    
    # 使用 AI 服務
    result = AIService.test_connection(api_key="key", provider="zeabur")

導出:
    - router: FastAPI Router，包含 /api/ai/* 端點
    - AIService: 主要 AI 服務類別
    - AIIntentClassifier: 搜尋意圖分類器
    - ZeaburAIClient: Zeabur AI Hub 客戶端
    - GoogleGeminiClient: Google Gemini 客戶端
"""

from .router import router
from .service import AIService
from .intent_classifier import AIIntentClassifier
from .clients import ZeaburAIClient, GoogleGeminiClient

__all__ = [
    # Router
    "router",
    
    # Services
    "AIService",
    "AIIntentClassifier",
    
    # Clients
    "ZeaburAIClient",
    "GoogleGeminiClient",
]
