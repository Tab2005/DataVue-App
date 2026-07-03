"""
Meta Andromeda Module - Redis pub/sub cache invalidation (docs/20 task 3.3g / P2-7).

Multi-worker deployments each keep their own process-local in-memory cache
(prompt profiles, model registry, confidence calibration). A promote/approve
action handled by one worker must invalidate the SAME cache on every other
worker — otherwise other workers keep serving stale data until they happen to
restart. Uses Redis pub/sub when REDIS_URL is configured; silently degrades
to local-only invalidation (the pre-existing single-process behavior) when
Redis is unavailable, so this is purely additive and never blocks scoring.
"""

import json
import logging
import threading
from typing import Callable

logger = logging.getLogger(__name__)

CHANNEL = "ma:cache:invalidate"

_local_handlers: dict[str, Callable[[str | None], None]] = {}
_listener_started = False
_listener_lock = threading.Lock()


def register_invalidation_handler(cache_name: str, handler: Callable[[str | None], None]) -> None:
    """handler(scope_key) is called both immediately on this process (when this
    process itself triggers publish_invalidation) and whenever a matching
    message arrives from another worker via Redis pub/sub."""
    _local_handlers[cache_name] = handler


def publish_invalidation(cache_name: str, scope_key: str | None = None) -> None:
    """Invalidate locally right away (so this request sees fresh data even
    without Redis), then publish so other workers pick it up too."""
    handler = _local_handlers.get(cache_name)
    if handler:
        try:
            handler(scope_key)
        except Exception as exc:
            logger.warning("[MetaAndromeda] Local invalidation handler for '%s' failed: %s", cache_name, exc)

    try:
        from redis_cache import get_redis_client
        client = get_redis_client()
        if client is None:
            return
        client.publish(CHANNEL, json.dumps({"cache_name": cache_name, "scope_key": scope_key}))
    except Exception as exc:
        logger.debug("[MetaAndromeda] Redis publish for cache invalidation failed: %s", exc)


def start_invalidation_listener() -> None:
    """Start a daemon thread subscribing to CHANNEL. Idempotent — safe to call
    once per worker process at startup even if Redis isn't configured."""
    global _listener_started
    with _listener_lock:
        if _listener_started:
            return
        _listener_started = True

    try:
        from redis_cache import get_redis_client
        if get_redis_client() is None:
            logger.info(
                "[MetaAndromeda] Redis unavailable; prompt/registry/confidence cache "
                "invalidation stays process-local (fine for single-worker deployments)."
            )
            return
    except Exception as exc:
        logger.warning("[MetaAndromeda] Could not check Redis availability for cache invalidation listener: %s", exc)
        return

    def _listen():
        try:
            from redis_cache import get_redis_client
            client = get_redis_client()
            pubsub = client.pubsub()
            pubsub.subscribe(CHANNEL)
            logger.info("[MetaAndromeda] Cache invalidation listener subscribed to '%s'.", CHANNEL)
            for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                try:
                    payload = json.loads(message["data"])
                    cache_name = payload.get("cache_name")
                    scope_key = payload.get("scope_key")
                except Exception as exc:
                    logger.warning("[MetaAndromeda] Malformed cache invalidation message: %s", exc)
                    continue
                handler = _local_handlers.get(cache_name)
                if handler:
                    try:
                        handler(scope_key)
                        logger.info(
                            "[MetaAndromeda] Invalidated local cache '%s' (scope=%s) via Redis pub/sub.",
                            cache_name, scope_key,
                        )
                    except Exception as exc:
                        logger.warning("[MetaAndromeda] Invalidation handler for '%s' failed: %s", cache_name, exc)
        except Exception as exc:
            logger.warning("[MetaAndromeda] Cache invalidation listener stopped unexpectedly: %s", exc)

    thread = threading.Thread(target=_listen, name="ma-cache-invalidation-listener", daemon=True)
    thread.start()
