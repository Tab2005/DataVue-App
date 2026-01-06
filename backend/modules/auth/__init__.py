"""
Auth Module - 認證與 Token 管理模組
提供 Google OAuth、Facebook Token 管理、加密儲存等功能

使用方式:
    from modules.auth import TokenManager, get_current_user
    
    # Facebook Token 管理
    TokenManager.save_user_token(google_id, token, ...)
    token = TokenManager.get_user_token(google_id)
    
    # AI API Key 管理
    TokenManager.save_ai_settings(google_id, zeabur_key=...)
    settings = TokenManager.get_ai_settings(google_id)
"""

from .service import TokenManager

__all__ = [
    "TokenManager",
]
