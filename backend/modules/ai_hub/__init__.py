"""
AI Hub Module
AI 整合模組 - 提供 AI 客戶端、意圖分類器、以及相關 API

刻意不在此處 eager import `.router`/`.service`（比照 modules/gsc/__init__.py、
modules/ga4/__init__.py 的作法）：根目錄 `ai_service.py`（相容轉發層）會
import `modules.ai_hub.service`，若這裡的 `__init__.py` 又 eager import
`.router`（而 `.router` 需要 `from ai_service import AIService`），會形成
`ai_service.py` → `modules.ai_hub`（觸發 `__init__.py`）→ `.router` →
`ai_service.py` 的循環匯入。

使用方式：
    from modules.ai_hub.router import router as ai_router
    from modules.ai_hub.service import AIService
    from modules.ai_hub.intent_classifier import AIIntentClassifier
    from modules.ai_hub.clients import ZeaburAIClient, OpenRouterClient
"""

__all__ = ["router", "service", "intent_classifier", "clients"]
