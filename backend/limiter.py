"""
Rate Limiter 模組
統一提供 slowapi Limiter 實例，避免循環 import。

使用方式:
    from limiter import limiter

    @router.post("/some-endpoint")
    @limiter.limit("10/minute")
    async def endpoint(request: Request, ...):
        ...
"""

import os
from slowapi import Limiter
from slowapi.util import get_remote_address

_redis_url = os.getenv("REDIS_URL")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
    storage_uri=_redis_url if _redis_url else None,
)
