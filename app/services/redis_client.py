import logging
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.client = None

    async def connect(self) -> None:
        if not self.client:
            self.client = aioredis.from_url(settings.redis_url, decode_responses=True)
            logger.info("Connected to Redis")

    async def close(self) -> None:
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Closed Redis connection")

    async def ping(self) -> bool:
        if not self.client:
            await self.connect()
        try:
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    async def get(self, key: str) -> str | None:
        if not self.client:
            await self.connect()
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis get failed for key '{key}': {e}")
            return None

    async def setex(self, key: str, seconds: int, value: str) -> None:
        if not self.client:
            await self.connect()
        try:
            await self.client.setex(key, seconds, value)
        except Exception as e:
            logger.error(f"Redis setex failed for key '{key}': {e}")

    async def clear_cache_pattern(self, pattern: str) -> None:
        if not self.client:
            await self.connect()
        try:
            keys = await self.client.keys(pattern)
            if keys:
                await self.client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys matching pattern: '{pattern}'")
        except Exception as e:
            logger.error(f"Redis clear pattern failed for '{pattern}': {e}")

    async def check_rate_limit(self, ip: str, limit: int, window: int) -> bool:
        if not self.client:
            await self.connect()
        key = f"rate_limit:{ip}"
        try:
            pipe = self.client.pipeline()
            pipe.incr(key)
            pipe.ttl(key)
            results = await pipe.execute()
            
            count = results[0]
            ttl = results[1]
            
            # If key is newly created or missing expire, set the window TTL
            if count == 1 or ttl == -1:
                await self.client.expire(key, window)
                
            return count <= limit
        except Exception as e:
            logger.error(f"Redis rate limit check failed for IP {ip}: {e}")
            # Fail-open: don't block users if Redis has connectivity issues
            return True

redis_client = RedisClient()
