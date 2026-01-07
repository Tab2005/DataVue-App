"""
Auth Module
認證模組 - 提供認證依賴、Token 管理、以及用戶相關 API

此模組是從 auth.py 和 dependencies.py 抽取出來的獨立模組，
可複用於其他 FastAPI 專案。

使用方式 (在其他專案):
    1. 複製 modules/auth/ 資料夾
    2. 複製 core/security.py（加密依賴）
    3. 安裝依賴: pip install cryptography google-auth python-jose

    from fastapi import FastAPI
    from modules.auth.router import router as auth_router
    from modules.auth.dependencies import get_current_user
    
    app = FastAPI()
    app.include_router(auth_router)

導出:
    - router: FastAPI Router，包含 /api/auth/* 端點
    - TokenManager: Token 管理服務
    - get_current_user: 取得當前用戶依賴
    - get_admin_user: 取得 Admin 用戶依賴
    - require_permission: 權限檢查依賴工廠
    - require_module: 模組存取檢查依賴工廠
"""

from .router import router
from .service import TokenManager
from .dependencies import (
    get_db,
    get_current_user,
    get_current_active_user,
    get_admin_user,
    get_super_admin,
    get_current_team,
    require_permission,
    require_module,
    require_super_admin,
    verify_google_token,
    security
)

__all__ = [
    # Router
    "router",
    
    # Services
    "TokenManager",
    
    # Dependencies
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "get_admin_user",
    "get_super_admin",
    "get_current_team",
    "require_permission",
    "require_module",
    "require_super_admin",
    "verify_google_token",
    "security",
]
