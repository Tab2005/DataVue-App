"""
GA4 Module - Router
Google Analytics 4 API 端點

此檔案重新導出 routers.ga4 以保持模組結構一致性。

使用方式:
    from modules.ga4.router import router as ga4_router
    app.include_router(ga4_router)
"""

# 重新導出現有的 GA4 Router
from routers.ga4 import router

__all__ = ["router"]