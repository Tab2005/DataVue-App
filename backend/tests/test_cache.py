"""
快取模組測試（使用 mock Redis）
"""
import pytest


@pytest.mark.unit
def test_generate_cache_key_consistent(mock_redis):
    """相同參數應生成相同的快取 key"""
    from cache import generate_cache_key

    key1 = generate_cache_key("test", 1, "30d")
    key2 = generate_cache_key("test", 1, "30d")
    assert key1 == key2


@pytest.mark.unit
def test_generate_cache_key_different_params(mock_redis):
    """不同參數應生成不同的快取 key"""
    from cache import generate_cache_key

    key1 = generate_cache_key("test", 1, "30d")
    key2 = generate_cache_key("test", 2, "30d")
    assert key1 != key2


@pytest.mark.unit
def test_generate_cache_key_is_string(mock_redis):
    """generate_cache_key 應回傳字串"""
    from cache import generate_cache_key

    key = generate_cache_key("test", "user_id", 123)
    assert isinstance(key, str)
    assert len(key) > 0


@pytest.mark.unit
def test_cache_miss_returns_none(mock_redis):
    """快取 miss 時應回傳 None"""
    from cache import cache_get

    result = cache_get("nonexistent_key_xyz_abc_123")
    assert result is None


@pytest.mark.unit
def test_cache_set_and_get_local(mock_redis):
    """快取寫入後，L1 本地快取應可立即讀取"""
    from cache import cache_set, cache_get

    test_key = "test_local_cache_key_999"
    test_value = {"data": "hello", "num": 42}

    cache_set(test_key, test_value, ttl=60)
    result = cache_get(test_key)

    assert result == test_value


@pytest.mark.unit
def test_cache_delete_removes_value(mock_redis):
    """刪除快取後應無法讀取"""
    from cache import cache_set, cache_get, cache_delete

    test_key = "test_delete_cache_key_888"
    cache_set(test_key, "some_value", ttl=60)
    cache_delete(test_key)
    result = cache_get(test_key)

    assert result is None


@pytest.mark.unit
def test_get_cached_compat_returns_none(mock_redis):
    """向後相容 get_cached 對不存在的 key 應回傳 None"""
    from cache import get_cached

    result = get_cached(None, "nonexistent_compat_key_777")
    assert result is None
