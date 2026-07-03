"""
Meta Andromeda 跨 process 並發限流

Redis 可用時用一個 List 當 token bucket：每次 acquire() 先把 list 原子性補到
`limit` 個 token（自我修復，process 崩潰未歸還的 token 會在下次 acquire 時補回），
再用 BLPOP 阻塞式取一個 token，用完歸還。Redis 不可用時 fallback 回本地
asyncio.Semaphore（單機行為與改動前一致）。
"""

import asyncio
from contextlib import asynccontextmanager

from redis_cache import get_redis_client

_TOPUP_SCRIPT = """
local key = KEYS[1]
local target = tonumber(ARGV[1])
local current = redis.call('LLEN', key)
if current < target then
    for i = current + 1, target do
        redis.call('RPUSH', key, '1')
    end
end
return redis.call('LLEN', key)
"""


class DistributedSemaphore:
    def __init__(self, name: str, limit: int, *, acquire_timeout: float = 30.0):
        self._key = f"ma:sem:{name}"
        self._limit = max(1, limit)
        self._acquire_timeout = acquire_timeout
        self._local_semaphore = asyncio.Semaphore(self._limit)

    @asynccontextmanager
    async def acquire(self):
        redis = get_redis_client()

        if redis is None:
            async with self._local_semaphore:
                yield
            return

        await asyncio.to_thread(redis.eval, _TOPUP_SCRIPT, 1, self._key, self._limit)
        token = await asyncio.to_thread(redis.blpop, self._key, self._acquire_timeout)
        if token is None:
            raise TimeoutError(f"timed out waiting for concurrency slot on {self._key}")
        try:
            yield
        finally:
            await asyncio.to_thread(redis.rpush, self._key, "1")
