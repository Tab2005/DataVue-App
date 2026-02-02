"""
Core Security Module
提供加密/解密功能和安全相關工具

使用方式:
    from core.security import encrypt_value, decrypt_value, get_encryption_key
    
    encrypted = encrypt_value("my_secret")
    decrypted = decrypt_value(encrypted)
"""

import os
import sys
from typing import Optional
from cryptography.fernet import Fernet
from functools import lru_cache


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
