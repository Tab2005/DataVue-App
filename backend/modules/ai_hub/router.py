"""
AI Hub Module - Router
AI 相關的 API 端點

此檔案重新導出 routers.ai 以保持模組結構一致性。

使用方式:
    from modules.ai_hub.router import router as ai_router
    app.include_router(ai_router, prefix="/api/ai")
"""

# 重新導出現有的 AI Router
from routers.ai import router

__all__ = ["router"]
