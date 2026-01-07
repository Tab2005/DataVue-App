"""
GSC Module
Google Search Console 整合模組 - 提供 GSC 認證、網站列表、分析資料等功能

此模組整合了所有 GSC 相關功能，可複用於其他 FastAPI 專案。

使用方式 (在其他專案):
    1. 複製 modules/gsc/ 資料夾
    2. 複製 gsc_service.py（核心服務）
    3. 安裝依賴: pip install google-auth google-api-python-client

    from fastapi import FastAPI
    from modules.gsc import router as gsc_router, GSCService
    
    app = FastAPI()
    app.include_router(gsc_router)

導出:
    - router: FastAPI Router，包含 /api/gsc/* 端點
    - GSCService: GSC 服務類別
"""

from .router import router
from .service import GSCService

__all__ = [
    # Router
    "router",
    
    # Services
    "GSCService",
]
