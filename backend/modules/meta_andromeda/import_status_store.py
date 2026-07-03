"""
Meta Andromeda 觀察匯入進度狀態儲存

Redis 可用時用 `ma:import_status:{id}` 存進度（TTL 自動淡出），並用
`ma:import_status_by_score_event:{score_event_id}` 做反向索引供維護排程清理；
Redis 不可用時 fallback 回本地 dict + threading.Lock（單機開發行為與改動前一致）。
"""

import json
import threading
from typing import Any

from redis_cache import get_redis_client

IMPORT_STATUS_KEY = "ma:import_status:{observed_creative_id}"
IMPORT_STATUS_BY_SCORE_EVENT_KEY = "ma:import_status_by_score_event:{score_event_id}"
IMPORT_STATUS_TTL_SECONDS = 3600

_local_statuses: dict[str, dict[str, Any]] = {}
_local_score_event_index: dict[str, str] = {}
_local_lock = threading.Lock()


def set_import_status(observed_creative_id: str, **updates: Any) -> dict[str, Any]:
    from datetime import UTC, datetime

    timestamp = datetime.now(UTC).isoformat()
    redis = get_redis_client()

    if redis is None:
        with _local_lock:
            current = _local_statuses.get(observed_creative_id, {})
            current.update(updates)
            current["updated_at"] = timestamp
            _local_statuses[observed_creative_id] = current
            score_event_id = current.get("score_event_id")
            if score_event_id:
                _local_score_event_index[score_event_id] = observed_creative_id
            return dict(current)

    key = IMPORT_STATUS_KEY.format(observed_creative_id=observed_creative_id)
    current = json.loads(redis.get(key) or "{}")
    current.update(updates)
    current["updated_at"] = timestamp
    redis.setex(key, IMPORT_STATUS_TTL_SECONDS, json.dumps(current))

    score_event_id = current.get("score_event_id")
    if score_event_id:
        index_key = IMPORT_STATUS_BY_SCORE_EVENT_KEY.format(score_event_id=score_event_id)
        redis.setex(index_key, IMPORT_STATUS_TTL_SECONDS, observed_creative_id)

    return dict(current)


def get_import_status(observed_creative_id: str) -> dict[str, Any]:
    redis = get_redis_client()
    if redis is None:
        with _local_lock:
            return dict(_local_statuses.get(observed_creative_id, {}))

    key = IMPORT_STATUS_KEY.format(observed_creative_id=observed_creative_id)
    raw = redis.get(key)
    if not raw:
        return {}
    return json.loads(raw)


def clear_import_status_by_score_event_ids(score_event_ids: set[str]) -> int:
    if not score_event_ids:
        return 0

    redis = get_redis_client()
    removed = 0

    if redis is None:
        with _local_lock:
            for score_event_id in score_event_ids:
                observed_creative_id = _local_score_event_index.pop(score_event_id, None)
                if observed_creative_id and _local_statuses.pop(observed_creative_id, None) is not None:
                    removed += 1
        return removed

    for score_event_id in score_event_ids:
        index_key = IMPORT_STATUS_BY_SCORE_EVENT_KEY.format(score_event_id=score_event_id)
        observed_creative_id = redis.get(index_key)
        if not observed_creative_id:
            continue
        status_key = IMPORT_STATUS_KEY.format(observed_creative_id=observed_creative_id)
        deleted = redis.delete(status_key, index_key)
        if deleted:
            removed += 1

    return removed
