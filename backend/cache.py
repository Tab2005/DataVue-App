"""
Cache Service Module
Provides in-memory caching for Facebook API responses to reduce API calls and improve response times.
"""
from cachetools import TTLCache
import hashlib
import json
import sys

# Cache instances with different TTL values
# Ad Accounts: 5 minutes (300 seconds) - rarely changes
ad_accounts_cache = TTLCache(maxsize=100, ttl=300)

# Insights/Dashboard: 2 minutes (120 seconds) - balance between freshness and performance
insights_cache = TTLCache(maxsize=500, ttl=120)

# Analytics Reports: 2 minutes (120 seconds)
analytics_cache = TTLCache(maxsize=500, ttl=120)

# Trend Data: 2 minutes (120 seconds)
trend_cache = TTLCache(maxsize=200, ttl=120)


def generate_cache_key(*args) -> str:
    """
    Generate a unique cache key from multiple arguments.
    Uses MD5 hash for consistent key length.
    """
    key_string = ":".join(str(arg) for arg in args if arg is not None)
    return hashlib.md5(key_string.encode()).hexdigest()


def get_cached(cache: TTLCache, key: str):
    """
    Get value from cache if exists.
    Returns None if not found or expired.
    """
    try:
        value = cache.get(key)
        if value is not None:
            print(f"[CACHE HIT] Key: {key[:16]}...", file=sys.stderr)
        return value
    except Exception as e:
        print(f"[CACHE ERROR] Get failed: {e}", file=sys.stderr)
        return None


def set_cached(cache: TTLCache, key: str, value):
    """
    Store value in cache.
    """
    try:
        cache[key] = value
        print(f"[CACHE SET] Key: {key[:16]}...", file=sys.stderr)
    except Exception as e:
        print(f"[CACHE ERROR] Set failed: {e}", file=sys.stderr)


def invalidate_cache(cache: TTLCache, key: str = None):
    """
    Invalidate cache entry or entire cache.
    """
    try:
        if key:
            cache.pop(key, None)
            print(f"[CACHE INVALIDATE] Key: {key[:16]}...", file=sys.stderr)
        else:
            cache.clear()
            print(f"[CACHE CLEAR] All entries cleared", file=sys.stderr)
    except Exception as e:
        print(f"[CACHE ERROR] Invalidate failed: {e}", file=sys.stderr)


# Convenience functions for specific cache types
def get_account_cache(user_id: str, team_id: str = None):
    key = generate_cache_key("accounts", user_id, team_id)
    return get_cached(ad_accounts_cache, key)


def set_account_cache(user_id: str, team_id: str, value):
    key = generate_cache_key("accounts", user_id, team_id)
    set_cached(ad_accounts_cache, key, value)


def get_insights_cache(account_id: str, days: int):
    key = generate_cache_key("insights", account_id, days)
    return get_cached(insights_cache, key)


def set_insights_cache(account_id: str, days: int, value):
    key = generate_cache_key("insights", account_id, days)
    set_cached(insights_cache, key, value)


def get_analytics_cache(account_id: str, since: str, until: str, level: str):
    key = generate_cache_key("analytics", account_id, since, until, level)
    return get_cached(analytics_cache, key)


def set_analytics_cache(account_id: str, since: str, until: str, level: str, value):
    key = generate_cache_key("analytics", account_id, since, until, level)
    set_cached(analytics_cache, key, value)


def get_trend_cache(account_id: str, since: str, until: str, prev_since: str, prev_until: str):
    key = generate_cache_key("trend", account_id, since, until, prev_since, prev_until)
    return get_cached(trend_cache, key)


def set_trend_cache(account_id: str, since: str, until: str, prev_since: str, prev_until: str, value):
    key = generate_cache_key("trend", account_id, since, until, prev_since, prev_until)
    set_cached(trend_cache, key, value)
