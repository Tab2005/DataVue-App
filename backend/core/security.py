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
from cryptography.fernet import Fernet
from functools import lru_cache


def get_encryption_key() -> str:
    """
    取得 Fernet 加密金鑰
    
    優先使用環境變數 ENCRYPTION_KEY，若未設定則產生臨時金鑰（僅供開發使用）
    """
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        # For Dev/Demo Only: Generate a volatile key if missing to prevent crash
        key = Fernet.generate_key().decode()
        print(f"⚠ WARNING: ENCRYPTION_KEY not set. Using volatile key: {key[:10]}...", file=sys.stderr)
        return key
    
    # Sanitize: Remove possible quotes and whitespace
    sanitized_key = key.strip().strip("'").strip('"')
    
    # Validation
    try:
        # Fernet keys must be 32 url-safe base64-encoded bytes (resulting in 44 chars)
        Fernet(sanitized_key)
        return sanitized_key
    except Exception as e:
        print(f"❌ CRITICAL: Invalid ENCRYPTION_KEY in .env: {e}", file=sys.stderr)
        print(f"Key length: {len(sanitized_key)}, Content starts with: {sanitized_key[:5]}...", file=sys.stderr)
        # Fallback to volatile to prevent blocking server start
        volatile_key = Fernet.generate_key().decode()
        return volatile_key


@lru_cache()
def _get_fernet() -> Fernet:
    """取得 Fernet 實例（快取）"""
    return Fernet(get_encryption_key())


def encrypt_value(message: str) -> str | None:
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
        f = Fernet(get_encryption_key())
        return f.encrypt(message.encode()).decode()
    except Exception as e:
        print(f"Encryption error: {e}", file=sys.stderr)
        return None


def decrypt_value(token: str) -> str | None:
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
        f = Fernet(get_encryption_key())
        return f.decrypt(token.encode()).decode()
    except Exception as e:
        print(f"[DEBUG] Decryption failed. Error: {e}", file=sys.stderr)
        return None


def validate_encryption_key() -> bool:
    """
    驗證加密金鑰是否有效
    
    Returns:
        True 如果金鑰有效
    """
    try:
        key = get_encryption_key()
        Fernet(key)
        return True
    except Exception:
        return False
