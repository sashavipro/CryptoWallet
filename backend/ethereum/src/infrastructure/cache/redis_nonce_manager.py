"""ethereum/src/infrastructure/cache/redis_nonce_manager.py."""

import logging

from redis.asyncio import Redis

from src.application.ports.providers.nonce_manager import NonceManager
from src.application.ports.providers.web3 import Web3Provider
from src.domain.value_objects.shared.address import EthereumAddress

logger = logging.getLogger(__name__)


class RedisNonceManager(NonceManager):
    """Redis implementation for NonceManager, with Web3 fallback."""

    NONCE_CACHE_TTL_SECONDS = 3600

    def __init__(self, redis_client: Redis, web3_provider: Web3Provider) -> None:
        """Initialize with Redis client and Web3 provider."""
        self.redis = redis_client
        self.web3_provider = web3_provider

    def _get_nonce_key(self, address: str) -> str:
        """Get the Redis key for a given address's nonce."""
        return f"wallet:nonce:{address.lower()}"

    async def _fetch_nonce_from_web3(self, address: str) -> int:
        """Fetch the latest nonce from the blockchain via Web3 provider."""
        logger.info("Fetching fresh nonce from Web3 for address: %s", address)
        return await self.web3_provider.get_transaction_count(EthereumAddress(address))

    async def get_current_nonce(self, address: str) -> int:
        """Retrieve the current nonce for an address (from cache or Web3)."""
        eth_address = EthereumAddress(address).value
        nonce_key = self._get_nonce_key(eth_address)

        cached_nonce_str = await self.redis.get(nonce_key)

        if cached_nonce_str:
            return int(cached_nonce_str)

        fresh_nonce = await self._fetch_nonce_from_web3(eth_address)
        await self.redis.setex(
            nonce_key, self.NONCE_CACHE_TTL_SECONDS, str(fresh_nonce)
        )
        return fresh_nonce

    async def get_and_increment_nonce(self, address: str) -> int:
        """Get the current nonce and immediately increment it atomically."""
        eth_address = EthereumAddress(address).value
        nonce_key = self._get_nonce_key(eth_address)
        current_nonce_str = await self.redis.get(nonce_key)

        if current_nonce_str is None:
            fresh_nonce_from_web3 = await self._fetch_nonce_from_web3(eth_address)
            await self.redis.setex(
                nonce_key, self.NONCE_CACHE_TTL_SECONDS, str(fresh_nonce_from_web3)
            )
            current_nonce_to_return = fresh_nonce_from_web3
        else:
            current_nonce_to_return = int(current_nonce_str)

        await self.redis.incr(nonce_key)

        return current_nonce_to_return

    async def set_nonce(self, address: str, nonce: int) -> None:
        """Explicitly set the nonce for an address in cache."""
        eth_address = EthereumAddress(address).value
        nonce_key = self._get_nonce_key(eth_address)
        await self.redis.setex(nonce_key, self.NONCE_CACHE_TTL_SECONDS, str(nonce))
        logger.debug("Nonce set for address %s: %s", eth_address, nonce)

    async def invalidate_nonce(self, address: str) -> None:
        """Remove cached nonce for an address."""
        eth_address = EthereumAddress(address).value
        nonce_key = self._get_nonce_key(eth_address)
        await self.redis.delete(nonce_key)
        logger.debug("Nonce invalidated for address %s", eth_address)
