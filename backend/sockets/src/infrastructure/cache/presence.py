"""sockets/src/infrastructure/cache/presence.py."""

import logging

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class OnlinePresenceGateway:
    """Manages a list of online users with support for multiple tabs."""

    def __init__(self, redis: Redis, prefix: str = "chat:presence:"):
        """Initialize the gateway with a Redis client and key prefix."""
        self.redis = redis
        self.prefix = prefix
        self.online_set_key = f"{prefix}online_users"

    async def user_connected(self, user_id: str) -> bool:
        """Increment the tab counter.

        Returns True if this is the FIRST connection (the user has just logged in).
        """
        count_key = f"{self.prefix}count:{user_id}"
        count = await self.redis.incr(count_key)

        if count == 1:
            await self.redis.sadd(self.online_set_key, user_id)
            return True
        return False

    async def user_disconnected(self, user_id: str) -> bool:
        """Decrement the tab counter.

        Returns True if this is the LAST logout (the user has completely logged out).
        """
        count_key = f"{self.prefix}count:{user_id}"
        count = await self.redis.decr(count_key)

        if count <= 0:
            await self.redis.delete(count_key)
            await self.redis.srem(self.online_set_key, user_id)
            return True
        return False

    async def get_online_users(self) -> list[str]:
        """Return a list of the IDs of all online users."""
        users = await self.redis.smembers(self.online_set_key)
        return list(users)
