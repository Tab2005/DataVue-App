"""
P1-4: Meta Andromeda 匯入進度狀態 / 並發限流改用 Redis 後的測試
涵蓋 Redis 不可用時的本地 fallback，以及 Redis 可用時的呼叫序列。
"""
import asyncio
import json
from unittest.mock import Mock

import pytest

import modules.meta_andromeda.concurrency as concurrency_module
import modules.meta_andromeda.import_status_store as import_status_store_module
from modules.meta_andromeda.concurrency import DistributedSemaphore
from modules.meta_andromeda.import_status_store import (
    clear_import_status_by_score_event_ids,
    get_import_status,
    set_import_status,
)


@pytest.fixture(autouse=True)
def _reset_local_state(monkeypatch):
    monkeypatch.setattr(import_status_store_module, "_local_statuses", {})
    monkeypatch.setattr(import_status_store_module, "_local_score_event_index", {})
    yield


@pytest.mark.unit
def test_import_status_local_fallback_roundtrip(monkeypatch):
    """Redis 不可用時，set/get 走本地 dict fallback"""
    monkeypatch.setattr(import_status_store_module, "get_redis_client", lambda: None)

    set_import_status("obs_1", observation_status="queued", score_event_id="se_1")
    result = get_import_status("obs_1")

    assert result["observation_status"] == "queued"
    assert result["score_event_id"] == "se_1"
    assert "updated_at" in result


@pytest.mark.unit
def test_import_status_local_fallback_missing_returns_empty(monkeypatch):
    monkeypatch.setattr(import_status_store_module, "get_redis_client", lambda: None)
    assert get_import_status("does_not_exist") == {}


@pytest.mark.unit
def test_import_status_local_fallback_clear_by_score_event_ids(monkeypatch):
    monkeypatch.setattr(import_status_store_module, "get_redis_client", lambda: None)

    set_import_status("obs_1", observation_status="processing", score_event_id="se_1")
    set_import_status("obs_2", observation_status="processing", score_event_id="se_2")

    removed = clear_import_status_by_score_event_ids({"se_1"})

    assert removed == 1
    assert get_import_status("obs_1") == {}
    assert get_import_status("obs_2") != {}


@pytest.mark.unit
def test_import_status_redis_set_writes_key_with_ttl_and_reverse_index(monkeypatch):
    redis_mock = Mock()
    redis_mock.get.return_value = None
    monkeypatch.setattr(import_status_store_module, "get_redis_client", lambda: redis_mock)

    set_import_status("obs_1", observation_status="queued", score_event_id="se_1")

    setex_calls = redis_mock.setex.call_args_list
    assert len(setex_calls) == 2

    status_call = setex_calls[0]
    assert status_call.args[0] == "ma:import_status:obs_1"
    assert status_call.args[1] == import_status_store_module.IMPORT_STATUS_TTL_SECONDS
    payload = json.loads(status_call.args[2])
    assert payload["observation_status"] == "queued"

    index_call = setex_calls[1]
    assert index_call.args[0] == "ma:import_status_by_score_event:se_1"
    assert index_call.args[2] == "obs_1"


@pytest.mark.unit
def test_import_status_redis_get_returns_decoded_payload(monkeypatch):
    redis_mock = Mock()
    redis_mock.get.return_value = json.dumps({"observation_status": "completed"})
    monkeypatch.setattr(import_status_store_module, "get_redis_client", lambda: redis_mock)

    result = get_import_status("obs_1")

    assert result == {"observation_status": "completed"}
    redis_mock.get.assert_called_once_with("ma:import_status:obs_1")


@pytest.mark.unit
def test_import_status_redis_clear_deletes_status_and_index_keys(monkeypatch):
    redis_mock = Mock()
    redis_mock.get.return_value = "obs_1"
    redis_mock.delete.return_value = 2
    monkeypatch.setattr(import_status_store_module, "get_redis_client", lambda: redis_mock)

    removed = clear_import_status_by_score_event_ids({"se_1"})

    assert removed == 1
    redis_mock.get.assert_called_once_with("ma:import_status_by_score_event:se_1")
    redis_mock.delete.assert_called_once_with("ma:import_status:obs_1", "ma:import_status_by_score_event:se_1")


@pytest.mark.unit
async def test_distributed_semaphore_local_fallback_limits_concurrency(monkeypatch):
    """Redis 不可用時，走本地 asyncio.Semaphore，並發數不應超過 limit"""
    monkeypatch.setattr(concurrency_module, "get_redis_client", lambda: None)

    sem = DistributedSemaphore("test_local", limit=2)
    concurrent_count = 0
    max_observed = 0

    async def worker():
        nonlocal concurrent_count, max_observed
        async with sem.acquire():
            concurrent_count += 1
            max_observed = max(max_observed, concurrent_count)
            await asyncio.sleep(0.05)
            concurrent_count -= 1

    await asyncio.gather(*(worker() for _ in range(5)))

    assert max_observed <= 2


@pytest.mark.unit
async def test_distributed_semaphore_redis_acquire_release_sequence(monkeypatch):
    redis_mock = Mock()
    redis_mock.eval.return_value = 3
    redis_mock.blpop.return_value = ("ma:sem:test_redis", "1")
    monkeypatch.setattr(concurrency_module, "get_redis_client", lambda: redis_mock)

    sem = DistributedSemaphore("test_redis", limit=3, acquire_timeout=5.0)
    async with sem.acquire():
        pass

    redis_mock.eval.assert_called_once_with(concurrency_module._TOPUP_SCRIPT, 1, "ma:sem:test_redis", 3)
    redis_mock.blpop.assert_called_once_with("ma:sem:test_redis", 5.0)
    redis_mock.rpush.assert_called_once_with("ma:sem:test_redis", "1")


@pytest.mark.unit
async def test_distributed_semaphore_redis_timeout_raises_and_does_not_release(monkeypatch):
    redis_mock = Mock()
    redis_mock.eval.return_value = 1
    redis_mock.blpop.return_value = None
    monkeypatch.setattr(concurrency_module, "get_redis_client", lambda: redis_mock)

    sem = DistributedSemaphore("test_redis_timeout", limit=1, acquire_timeout=0.01)

    with pytest.raises(TimeoutError):
        async with sem.acquire():
            pass

    redis_mock.rpush.assert_not_called()


@pytest.mark.unit
async def test_distributed_semaphore_redis_release_happens_even_on_exception(monkeypatch):
    redis_mock = Mock()
    redis_mock.eval.return_value = 1
    redis_mock.blpop.return_value = ("ma:sem:test_redis_exc", "1")
    monkeypatch.setattr(concurrency_module, "get_redis_client", lambda: redis_mock)

    sem = DistributedSemaphore("test_redis_exc", limit=1)

    with pytest.raises(ValueError):
        async with sem.acquire():
            raise ValueError("boom")

    redis_mock.rpush.assert_called_once_with("ma:sem:test_redis_exc", "1")
