"""
Core Security Module
提供加密/解密功能、Google Token 驗證及安全相關工具

使用方式:
    from core.security import encrypt_value, decrypt_value, get_encryption_key
    from core.security import verify_google_token, verify_google_token_and_get_sub
    
    encrypted = encrypt_value("my_secret")
    decrypted = decrypt_value(encrypted)
    
    id_info = verify_google_token(google_id_token)
    google_id = verify_google_token_and_get_sub(google_id_token)
"""

import os
import sys
import threading
from typing import Optional
from cryptography.fernet import Fernet
from functools import lru_cache
from cachetools import TTLCache, cached

import logging

logger = logging.getLogger(__name__)


def get_encryption_key() -> str:
    """
    取得 Fernet 加密金鑰
    
    必須使用環境變數 ENCRYPTION_KEY。若未設定或格式錯誤，將涉及安全風險並導致資料無法解密。
    """
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        return None
    
    # Sanitize: Remove possible quotes and whitespace
    sanitized_key = key.strip().strip("'").strip('"')
    
    # Validation
    try:
        # Fernet keys must be 32 url-safe base64-encoded bytes (resulting in 44 chars)
        Fernet(sanitized_key)
        return sanitized_key
    except Exception as e:
        logger.error(f"CRITICAL: Invalid ENCRYPTION_KEY in .env: {e}")
        return None


@lru_cache()
def _get_fernet() -> Optional[Fernet]:
    """取得 Fernet 實例（快取）"""
    key = get_encryption_key()
    if not key:
        return None
    return Fernet(key)


from typing import Optional

def encrypt_value(message: str) -> Optional[str]:
    """
    加密字串
    
    Args:
        message: 要加密的字串
        
    Returns:
        加密後的字串，失敗時回傳 None
    """
    if not message:
        return None
    try:
        f = _get_fernet()
        if not f:
            return None
        return f.encrypt(message.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        return None


def decrypt_value(token: str) -> Optional[str]:
    """
    解密字串
    
    Args:
        token: 已加密的字串
        
    Returns:
        解密後的字串，失敗時回傳 None
    """
    if not token:
        return None
    try:
        f = _get_fernet()
        if not f:
            return None
        return f.decrypt(token.encode()).decode()
    except Exception as e:
        logger.debug(f"Decryption failed: {e}")
        return None


def validate_encryption_key() -> bool:
    """
    驗證加密金鑰是否有效
    
    Returns:
        True 如果金鑰有效
    """
    return get_encryption_key() is not None


# ==================================================
# Google Token 驗證（統一入口，TTL 快取 5 分鐘）
# ==================================================

# TTL 快取：5 分鐘（確保撤銷的 Token 不會被快取太久）
_token_cache: TTLCache = TTLCache(maxsize=128, ttl=300)
_token_cache_lock = threading.Lock()


@cached(cache=_token_cache, lock=_token_cache_lock)
def _verify_google_token_raw(token: str) -> dict:
    """
    底層 Google ID Token 驗證（帶 TTL 快取）。
    不應直接呼叫此函式，請使用公開的 verify_google_token()。
    """
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests

    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    return id_token.verify_oauth2_token(
        token,
        google_requests.Request(),
        google_client_id,
        clock_skew_in_seconds=60,
    )


def verify_google_token(token: str) -> dict:
    """
    驗證 Google ID Token 並返回完整的 id_info 字典。

    Args:
        token: Google ID Token 字串

    Returns:
        包含使用者資訊的字典（sub, email, name, picture, email_verified 等）

    Raises:
        ValueError: Token 無效（已過期、簽名不符、來源不正確、email 未驗證）
    """
    try:
        id_info = _verify_google_token_raw(token)

        if not id_info.get("email_verified", False):
            raise ValueError("Google 帳號 email 尚未驗證")

        return id_info
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"[Security] Token 驗證失敗: {e}")
        raise ValueError(f"Token 驗證失敗: {e}")


def verify_google_token_and_get_sub(token: str) -> str:
    """
    驗證 Google ID Token 並只返回 Google User ID（sub）。

    適用於只需要用戶 ID 的場景（如 routers/auth.py 的 exchange_token）。

    Returns:
        Google User ID 字串
    """
    id_info = verify_google_token(token)
    return id_info["sub"]
