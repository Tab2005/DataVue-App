"""
GSC Module - Router
Google Search Console API 端點

此檔案重新導出 routers.gsc 以保持模組結構一致性。

使用方式:
    from modules.gsc.router import router as gsc_router
    app.include_router(gsc_router)
"""

# 重新導出現有的 GSC Router
from routers.gsc import router

__all__ = ["router"]
