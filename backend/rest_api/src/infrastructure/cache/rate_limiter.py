"""rest_api/src/infrastructure/cache/rate_limiter.py."""

import logging

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """Rate limiter and IP banner using Redis."""

    def __init__(
        self,
        redis_client: Redis,
        max_requests: int = 100,
        window_seconds: int = 60,
        ban_seconds: int = 3600,
    ) -> None:
        """Initialize parameters for limiting and banning."""
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.ban_seconds = ban_seconds

    async def is_allowed(self, ip_address: str) -> bool:
        """Check if IP is allowed to make a request.

        Uses atomic INCR and TTL to manage limits.
        """
        ban_key = f"ban:{ip_address}"
        rate_key = f"rate:{ip_address}"

        if await self.redis.exists(ban_key):
            logger.warning("Blocked request from banned IP: %s", ip_address)
            return False

        request_count = await self.redis.incr(rate_key)

        if request_count == 1:
            await self.redis.expire(rate_key, self.window_seconds)

        if request_count > self.max_requests:
            logger.warning(
                "IP %s exceeded rate limit (%d). Banning for %s seconds.",
                ip_address,
                self.max_requests,
                self.ban_seconds,
            )
            await self.redis.setex(ban_key, self.ban_seconds, "1")
            return False

        return True
