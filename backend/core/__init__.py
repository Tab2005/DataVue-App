"""
Core Module - 共用核心功能
提供所有模組共用的基礎設施
"""

from .config import settings
from .security import get_encryption_key, encrypt_value, decrypt_value

__all__ = [
    "settings",
    "get_encryption_key",
    "encrypt_value", 
    "decrypt_value",
]
