"""
AI Hub Module - AI Service
主要 AI 服務類別，提供統一的 AI 分析介面

此檔案重新導出 ai_service 以保持模組結構一致性。

使用方式:
    from modules.ai_hub.service import AIService
    
    # 取得可用提供者
    providers = AIService.get_available_providers()
    
    # 測試連線
    success = AIService.test_connection(api_key="key", provider="zeabur")
    
    # 分析資料（串流回應）
    for chunk in AIService.analyze_data(data, context):
        print(chunk)
"""

# 重新導出現有的 AI 服務
from ai_service import AIService

__all__ = ["AIService"]
