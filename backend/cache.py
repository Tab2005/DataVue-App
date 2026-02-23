"""
Cache Service Module
雙層快取架構：
  L1 - 本地記憶體（TTLCache，10 秒超短 TTL，同一進程內減少序列化開銷）
  L2 - Redis（主要共享快取層，適用多進程/多實例部署）

若 Redis 不可用，自動降級至 L1 本地快取。
"""

import json
import logging
import sys
import hashlib
import threading
from functools import wraps
from typing import Any, Optional, Callable

from cachetools import TTLCache

logger = logging.getLogger(__name__)

# ============================
# L1：本地記憶體快取（極短 TTL，同進程複用）
# ============================
_L1_TTL = 10          # 秒
_l1_cache: TTLCache = TTLCache(maxsize=500, ttl=_L1_TTL)
_l1_lock = threading.Lock()


# ============================
# L2：Redis 快取（延遲初始化）
# ============================
def _get_redis():
    """取得 Redis 客戶端，不可用時回傳 None"""
    try:
        from redis_cache import get_redis_client
        return get_redis_client()
    except Exception:
        return None


# ============================
# 核心讀寫 API
# ============================

def cache_get(key: str) -> Optional[Any]:
    """
    雙層快取讀取：先查 L1（本地），再查 L2（Redis）
    Returns:
        快取的值（已反序列化），或 None（未命中）
    """
    # L1 查詢
    with _l1_lock:
        if key in _l1_cache:
            logger.debug(f"[Cache] L1 命中: {key[:20]}...")
            return _l1_cache[key]

    # L2 查詢（Redis）
    redis = _get_redis()
    if redis:
        try:
            cached = redis.get(key)
            if cached:
                value = json.loads(cached)
                # 回填 L1
                with _l1_lock:
                    _l1_cache[key] = value
                logger.debug(f"[Cache] L2 命中: {key[:20]}...")
                return value
        except Exception as e:
            logger.warning(f"[Cache] Redis 讀取失敗 {key[:20]}: {e}")

    logger.debug(f"[Cache] 未命中: {key[:20]}...")
    return None


def cache_set(key: str, value: Any, ttl: int = 120) -> None:
    """
    雙層快取寫入
    Args:
        key: 快取鍵
        value: 要快取的值（必須可 JSON 序列化）
        ttl: L2（Redis）存活秒數；L1 固定 10 秒
    """
    # 寫入 L1
    with _l1_lock:
        _l1_cache[key] = value

    # 寫入 L2（Redis）
    redis = _get_redis()
    if redis:
        try:
            redis.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.warning(f"[Cache] Redis 寫入失敗 {key[:20]}: {e}")


def cache_delete(key: str) -> None:
    """刪除快取（L1 + L2）"""
    with _l1_lock:
        _l1_cache.pop(key, None)

    redis = _get_redis()
    if redis:
        try:
            redis.delete(key)
        except Exception as e:
            logger.warning(f"[Cache] Redis 刪除失敗 {key[:20]}: {e}")


def cache_delete_pattern(pattern: str) -> int:
    """依模式刪除 Redis 快取（使用 SCAN 避免阻塞）；L1 僅清空全部"""
    # L1 無法按 pattern 刪除，全清
    with _l1_lock:
        _l1_cache.clear()

    redis = _get_redis()
    if not redis:
        return 0

    deleted = 0
    try:
        for key in redis.scan_iter(pattern):
            redis.delete(key)
            deleted += 1
    except Exception as e:
        logger.warning(f"[Cache] Redis 模式刪除失敗 {pattern}: {e}")

    return deleted


def cached(ttl: int = 120, key_prefix: str = ""):
    """
    快取裝飾器（用於 async 函式）

    使用範例：
        @cached(ttl=300, key_prefix="fb_accounts")
        async def get_accounts(user_id: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                return cached_value
            result = await func(*args, **kwargs)
            if result is not None:
                cache_set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator


# ============================
# 向後相容：保留舊 TTLCache 介面
# 底層已替換為雙層快取，外部呼叫無需修改
# ============================

def generate_cache_key(*args) -> str:
    """生成唯一快取鍵（MD5 雜湊）"""
    key_string = ":".join(str(arg) for arg in args if arg is not None)
    return hashlib.md5(key_string.encode()).hexdigest()


def get_cached(cache_obj, key: str):
    """向後相容：忽略 cache_obj，使用雙層快取查詢"""
    value = cache_get(key)
    if value is not None:
        print(f"[CACHE HIT] Key: {key[:16]}...", file=sys.stderr)
    return value


def set_cached(cache_obj, key: str, value):
    """向後相容：忽略 cache_obj，使用雙層快取寫入"""
    # 根據 cache_obj 的原始 TTL 決定 Redis TTL（若能讀取）
    ttl = getattr(cache_obj, 'ttl', 120) if cache_obj is not None else 120
    cache_set(key, value, ttl=int(ttl))
    print(f"[CACHE SET] Key: {key[:16]}...", file=sys.stderr)


def invalidate_cache(cache_obj, key: str = None):
    """向後相容：刪除單一鍵或清空"""
    if key:
        cache_delete(key)
        print(f"[CACHE INVALIDATE] Key: {key[:16]}...", file=sys.stderr)
    else:
        with _l1_lock:
            _l1_cache.clear()
        print("[CACHE CLEAR] All L1 entries cleared", file=sys.stderr)


# ============================
# 舊程式碼相容：保留快取實例（TTL 資訊保留供 set_cached 使用）
# ============================
ad_accounts_cache = TTLCache(maxsize=100, ttl=300)
insights_cache = TTLCache(maxsize=500, ttl=120)
analytics_cache = TTLCache(maxsize=500, ttl=120)
trend_cache = TTLCache(maxsize=200, ttl=120)


# ============================
# 便捷函式（保持原有介面）
# ============================

def get_account_cache(user_id: str, team_id: str = None):
    key = generate_cache_key("accounts", user_id, team_id)
    return get_cached(None, key)


def set_account_cache(user_id: str, team_id: str, value):
    key = generate_cache_key("accounts", user_id, team_id)
    cache_set(key, value, ttl=300)


def get_insights_cache(account_id: str, days: int):
    key = generate_cache_key("insights", account_id, days)
    return get_cached(None, key)


def set_insights_cache(account_id: str, days: int, value):
    key = generate_cache_key("insights", account_id, days)
    cache_set(key, value, ttl=120)


def get_analytics_cache(account_id: str, since: str, until: str, level: str):
    key = generate_cache_key("analytics", account_id, since, until, level)
    return get_cached(None, key)


def set_analytics_cache(account_id: str, since: str, until: str, level: str, value):
    key = generate_cache_key("analytics", account_id, since, until, level)
    cache_set(key, value, ttl=120)


def get_trend_cache(account_id: str, since: str, until: str, prev_since: str, prev_until: str):
    key = generate_cache_key("trend", account_id, since, until, prev_since, prev_until)
    return get_cached(None, key)


def set_trend_cache(account_id: str, since: str, until: str, prev_since: str, prev_until: str, value):
    key = generate_cache_key("trend", account_id, since, until, prev_since, prev_until)
    cache_set(key, value, ttl=120)
