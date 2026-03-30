import logging
from typing import Any, Optional

from src.config.redis_config import cache_delete, cache_get, cache_set

logger = logging.getLogger(__name__)

POLICY_CACHE_TTL = 300  # seconds
CLAIM_CACHE_TTL = 300   # seconds


def get_cached_policy(policy_id: str) -> Optional[Any]:
    """Retrieve a policy dict from Redis cache."""
    key = f"policy:{policy_id}"
    data = cache_get(key)
    if data:
        logger.debug("Cache HIT for policy %s", policy_id)
    return data


def set_cached_policy(policy_id: str, policy_data: Any) -> None:
    """Store a policy dict in Redis cache."""
    key = f"policy:{policy_id}"
    cache_set(key, policy_data, ttl=POLICY_CACHE_TTL)


def invalidate_policy_cache(policy_id: str) -> None:
    """Remove a policy from Redis cache."""
    key = f"policy:{policy_id}"
    cache_delete(key)
    logger.debug("Invalidated cache for policy %s", policy_id)


def get_cached_claim_status(claim_id: str) -> Optional[str]:
    """Retrieve a claim status from Redis cache."""
    key = f"claim_status:{claim_id}"
    return cache_get(key)


def set_cached_claim_status(claim_id: str, status: str) -> None:
    """Store a claim status in Redis cache."""
    key = f"claim_status:{claim_id}"
    cache_set(key, status, ttl=CLAIM_CACHE_TTL)


def invalidate_claim_cache(claim_id: str) -> None:
    """Remove a claim status from Redis cache."""
    key = f"claim_status:{claim_id}"
    cache_delete(key)
