"""
Redis Cache Module
提供 Redis 客戶端的延遲初始化與防護性連線處理。
若 REDIS_URL 未設定或 Redis 不可用，所有操作均靜默降級。
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# 單例快取
_redis_client = None
_redis_available: Optional[bool] = None  # None = 尚未嘗試


def get_redis_client():
    """
    取得 Redis 客戶端。
    - 若 REDIS_URL 未設定，回傳 None（靜默降級）
    - 若連線失敗，記錄警告並回傳 None
    - 使用單例模式，避免重複建立連線
    """
    global _redis_client, _redis_available

    # 已知可用：直接回傳
    if _redis_available is True:
        return _redis_client

    # 已知不可用：快速失敗
    if _redis_available is False:
        return None

    # 首次嘗試初始化
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.info("[Redis] REDIS_URL 未設定，使用本地記憶體快取（L1 only）")
        _redis_available = False
        return None

    try:
        import redis
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            retry_on_timeout=True,
        )
        # 測試連線
        client.ping()
        _redis_client = client
        _redis_available = True
        logger.info(f"[Redis] 連線成功: {_mask_url(redis_url)}")
        return _redis_client
    except Exception as e:
        logger.warning(f"[Redis] 連線失敗，降級至本地快取: {e}")
        _redis_available = False
        return None


def reset_redis_client():
    """重置 Redis 客戶端（用於測試或重新連線）"""
    global _redis_client, _redis_available
    _redis_client = None
    _redis_available = None


def _mask_url(url: str) -> str:
    """遮蔽 URL 中的密碼，避免記錄到日誌"""
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        if parsed.password:
            masked = parsed._replace(netloc=f"{parsed.username}:***@{parsed.hostname}:{parsed.port}")
            return urlunparse(masked)
    except Exception:
        pass
    return url


# ============================
# 向後相容：保留舊版函式
# ============================

def get_cached_redis(key: str):
    """向後相容：直接從 Redis 讀取（不包含 L1）"""
    client = get_redis_client()
    if not client:
        return None
    try:
        value = client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception as e:
        logger.warning(f"[Redis] get_cached_redis 失敗 {key}: {e}")
        return None


def set_cached_redis(key: str, value, ttl_seconds: int):
    """向後相容：直接寫入 Redis（不包含 L1）"""
    client = get_redis_client()
    if not client:
        return False
    try:
        payload = json.dumps(value, default=str)
        client.setex(key, ttl_seconds, payload)
        return True
    except Exception as e:
        logger.warning(f"[Redis] set_cached_redis 失敗 {key}: {e}")
        return False
