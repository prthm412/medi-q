import redis
import redis.asyncio as aioredis

from app.core.config import settings

# Shared sync client — used by REST routes and queue_manager for
# ZADD/ZRANK/ZREM/PUBLISH. Cheap to share across requests; redis-py's
# sync client is connection-pooled internally.
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_async_redis() -> aioredis.Redis:
    """Fresh async client per call — used only by the WebSocket handler's
    Pub/Sub listen loop, which needs to be non-blocking. Not shared/cached
    because each WS connection needs its own subscription lifecycle.
    """
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)