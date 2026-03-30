import os
import json
import logging
from typing import Any, Optional

import redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


def cache_get(key: str) -> Optional[Any]:
    try:
        client = get_redis_client()
        value = client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception as exc:
        logger.warning("Redis GET failed for key %s: %s", key, exc)
        return None


def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    try:
        client = get_redis_client()
        client.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as exc:
        logger.warning("Redis SET failed for key %s: %s", key, exc)
        return False


def cache_delete(key: str) -> bool:
    try:
        client = get_redis_client()
        client.delete(key)
        return True
    except Exception as exc:
        logger.warning("Redis DELETE failed for key %s: %s", key, exc)
        return False
