"""ethereum/src/infrastructure/cache/redis_balance_cache.py."""

import logging
import uuid
from datetime import datetime
from decimal import Decimal

from redis.asyncio import Redis

from src.application.dtos.response import CachedBalance
from src.application.ports.providers import BalanceCache

logger = logging.getLogger(__name__)


class RedisBalanceCache(BalanceCache):
    """Redis implementation for BalanceCache."""

    BALANCE_CACHE_TTL_SECONDS = 60

    def __init__(self, redis_client: Redis) -> None:
        """Initialize with Redis client."""
        self.redis = redis_client

    def _get_balance_key(self, wallet_id: uuid.UUID) -> str:
        return f"cache:balance:{wallet_id}"

    def _get_updated_at_key(self, wallet_id: uuid.UUID) -> str:
        return f"cache:balance_updated_at:{wallet_id}"

    async def get_balance(self, wallet_id: uuid.UUID) -> CachedBalance | None:
        """Retrieve cached balance and its last update timestamp."""
        balance_key = self._get_balance_key(wallet_id)
        updated_at_key = self._get_updated_at_key(wallet_id)

        pipe = self.redis.pipeline()
        pipe.get(balance_key)
        pipe.get(updated_at_key)
        balance_str, updated_at_str = await pipe.execute()

        if balance_str and updated_at_str:
            try:
                balance = Decimal(balance_str)
                updated_at = datetime.fromisoformat(updated_at_str)
                logger.debug("Cache hit for balance of wallet: %s", wallet_id)
                return CachedBalance(balance=balance, updated_at=updated_at)
            except (ValueError, TypeError):
                logger.warning(
                    "Corrupted cache for wallet: %s. Invalidating.", wallet_id
                )
                await self.invalidate_balance(wallet_id)
                return None

        logger.debug("Cache miss for balance of wallet: %s", wallet_id)
        return None

    async def set_balance(
        self, wallet_id: uuid.UUID, balance: Decimal, updated_at: datetime
    ) -> None:
        """Set/update cached balance with its update timestamp."""
        balance_key = self._get_balance_key(wallet_id)
        updated_at_key = self._get_updated_at_key(wallet_id)

        pipe = self.redis.pipeline()
        pipe.setex(balance_key, self.BALANCE_CACHE_TTL_SECONDS, str(balance))
        pipe.setex(
            updated_at_key, self.BALANCE_CACHE_TTL_SECONDS, updated_at.isoformat()
        )
        await pipe.execute()
        logger.debug("Cache set for balance of wallet: %s", wallet_id)

    async def invalidate_balance(self, wallet_id: uuid.UUID) -> None:
        """Remove cached balance for a wallet."""
        balance_key = self._get_balance_key(wallet_id)
        updated_at_key = self._get_updated_at_key(wallet_id)
        await self.redis.delete(balance_key, updated_at_key)
        logger.debug("Cache invalidated for balance of wallet: %s", wallet_id)
