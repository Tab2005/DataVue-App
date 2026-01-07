"""
AI Hub Module - Intent Classifier
AI 驅動的搜尋意圖分類器

此檔案重新導出 services.ai.intent_classifier 以保持模組結構一致性。

使用方式:
    from modules.ai_hub.intent_classifier import AIIntentClassifier
    
    classifier = AIIntentClassifier(api_key="your_key", provider="gemini")
    result = classifier.classify_queries(["如何減肥", "Nike 跑鞋價格"])
"""

# 重新導出現有的意圖分類器
from services.ai.intent_classifier import AIIntentClassifier

__all__ = ["AIIntentClassifier"]
