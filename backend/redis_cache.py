import json
import os
from typing import Optional

try:
    import redis
except Exception:
    redis = None


def get_redis_client():
    """Return Redis client if REDIS_URL is set and redis package is available."""
    redis_url = os.getenv("REDIS_URL")
    if not redis_url or not redis:
        return None
    try:
        return redis.Redis.from_url(redis_url, decode_responses=True)
    except Exception:
        return None


def get_cached_redis(key: str):
    client = get_redis_client()
    if not client:
        return None
    try:
        value = client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception:
        return None


def set_cached_redis(key: str, value, ttl_seconds: int):
    client = get_redis_client()
    if not client:
        return False
    try:
        payload = json.dumps(value)
        client.setex(key, ttl_seconds, payload)
        return True
    except Exception:
        return False
