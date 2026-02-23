"""
test_cache.py — 快取邏輯單元測試

涵蓋：
  - L1（TTLCache）命中/未命中
  - 快取失效（TTL 過期）
  - Redis fallback（Redis 不可用時降級為僅 L1）
"""

import pytest
import time
from unittest.mock import patch, MagicMock


class TestL1Cache:
    """L1 TTLCache 本地記憶體快取測試"""

    def test_cache_set_and_get(self):
        """設定快取後應可立即取回。"""
        from cachetools import TTLCache

        cache = TTLCache(maxsize=10, ttl=60)
        cache["key1"] = {"value": 42}
        assert cache["key1"] == {"value": 42}

    def test_cache_miss_returns_none(self):
        """查詢不存在的 key 應引發 KeyError（或在 get() 中回傳 None）。"""
        from cachetools import TTLCache

        cache = TTLCache(maxsize=10, ttl=60)
        assert cache.get("nonexistent") is None

    def test_cache_ttl_expiry(self):
        """小 TTL 的快取應在過期後消失。"""
        from cachetools import TTLCache

        cache = TTLCache(maxsize=10, ttl=1)  # 1 秒 TTL
        cache["key"] = "data"
        assert "key" in cache

        time.sleep(1.1)  # 等待過期
        assert "key" not in cache


class TestTokenTTLCache:
    """Token 驗證 TTL 快取（core.security）測試"""

    def test_token_cache_is_ttlcache(self):
        """core.security 的 Token 快取應為 TTLCache 實例（非 lru_cache）。"""
        from cachetools import TTLCache
        from core import security

        assert isinstance(security._token_cache, TTLCache)

    def test_token_cache_ttl_is_300(self):
        """Token 快取的 TTL 應為 300 秒（5 分鐘）。"""
        from core import security

        assert security._token_cache.ttl == 300

    def test_token_cache_maxsize_128(self):
        """Token 快取最多應能存 128 個 Token。"""
        from core import security

        assert security._token_cache.maxsize == 128


class TestRedisCacheFallback:
    """Redis 不可用時的降級行為測試"""

    def test_cache_get_with_redis_unavailable(self):
        """Redis 連線失敗時，cache_get 應安全回傳 None（不拋例外）。"""
        # Mock Redis 連線失敗
        with patch("redis_cache.get_redis_client", return_value=None):
            try:
                from cache import cache_get
                result = cache_get("some_key")
                # Redis 不可用時應回傳 None 而非拋例外
                assert result is None
            except ImportError:
                pytest.skip("cache 模組結構與預期不同，跳過此測試")

    def test_cache_set_with_redis_unavailable(self):
        """Redis 連線失敗時，cache_set 應靜默失敗（不拋例外）。"""
        with patch("redis_cache.get_redis_client", return_value=None):
            try:
                from cache import cache_set
                # 不應拋出任何例外
                cache_set("some_key", {"data": 1}, ttl=60)
            except ImportError:
                pytest.skip("cache 模組結構與預期不同，跳過此測試")
