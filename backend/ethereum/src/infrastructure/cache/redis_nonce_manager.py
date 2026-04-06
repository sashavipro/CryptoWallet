"""ethereum/src/infrastructure/cache/redis_nonce_manager.py."""

import logging

from redis.asyncio import Redis

from src.application.ports.providers.nonce_manager import NonceManager
from src.application.ports.providers.web3 import Web3Provider
from src.domain.value_objects.shared.address import EthereumAddress

logger = logging.getLogger(__name__)


class RedisNonceManager(NonceManager):
    """Redis-based implementation of the NonceManager.

    Handles retrieving, caching, and incrementing Ethereum transaction
    nonces using Redis to prevent nonce collisions in concurrent environments.
    """

    NONCE_CACHE_TTL_SECONDS = 3600

    def __init__(self, redis_client: Redis, web3_provider: Web3Provider) -> None:
        """Initialize the RedisNonceManager."""
        self.redis = redis_client
        self.web3_provider = web3_provider

    def _get_nonce_key(self, address: str) -> str:
        return f"wallet:nonce:{address.lower()}"

    async def get_current_nonce(self, address: str) -> int:
        """Retrieve the current nonce for a given address.

        Checks the Redis cache first. If missing, locks the key, checks again,
        and falls back to querying the Web3 provider, caching the fresh nonce.
        """
        eth_address = EthereumAddress(address).value
        nonce_key = self._get_nonce_key(eth_address)

        cached_nonce = await self.redis.get(nonce_key)
        if cached_nonce is not None:
            return int(cached_nonce)

        lock_key = f"lock:nonce:{eth_address}"
        async with self.redis.lock(lock_key, timeout=10):
            cached_nonce = await self.redis.get(nonce_key)
            if cached_nonce is not None:
                return int(cached_nonce)

            fresh_nonce = await self.web3_provider.get_transaction_count(
                EthereumAddress(eth_address)
            )
            await self.redis.setex(
                nonce_key, self.NONCE_CACHE_TTL_SECONDS, str(fresh_nonce)
            )
            return fresh_nonce

    async def get_and_increment_nonce(self, address: str) -> int:
        """Retrieve the current nonce and increment it for the next transaction."""
        current_nonce = await self.get_current_nonce(address)
        await self.increment_nonce(address)
        return current_nonce

    async def increment_nonce(self, address: str) -> None:
        """Increment the stored nonce for a given address in Redis."""
        nonce_key = self._get_nonce_key(EthereumAddress(address).value)
        await self.redis.incr(nonce_key)
