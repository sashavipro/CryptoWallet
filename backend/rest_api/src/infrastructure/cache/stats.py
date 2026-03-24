"""rest_api/src/infrastructure/cache/stats.py."""

import uuid

from redis.asyncio import Redis

from src.application.ports.gateways.stats import StatsGateway


class RedisStatsGateway(StatsGateway):
    """An infrastructure adapter for working with statistics via Redis."""

    def __init__(self, redis_client: Redis) -> None:
        """Initialize with active Redis client."""
        self.redis = redis_client

    async def get_total_messages(self, user_id: uuid.UUID) -> int:
        """Retrieve the total number of chat messages sent by the user."""
        val = await self.redis.get(f"stats:{user_id}:messages")
        return int(val) if val else 0

    async def increment_messages(self, user_id: uuid.UUID) -> None:
        """Increment the user's global chat message counter."""
        await self.redis.incr(f"stats:{user_id}:messages")

    async def get_wallets_count(self, user_id: uuid.UUID) -> int:
        """Retrieve the total number of wallets owned by the user."""
        # TODO Пока возвращаем 0. Реальный подсчет будет через ETH-сервис
        val = await self.redis.get(f"stats:{user_id}:wallets")
        return int(val) if val else 0
