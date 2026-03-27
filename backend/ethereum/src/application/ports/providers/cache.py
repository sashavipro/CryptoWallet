"""ethereum/src/application/ports/providers/cache.py."""

from typing import Protocol


class NonceManager(Protocol):
    """Port for atomically managing transaction nonces in a cache (e.g., Redis)."""

    async def get_and_increment_nonce(self, address: str) -> int:
        """Get the current nonce for an address and immediately increment it."""
        ...
