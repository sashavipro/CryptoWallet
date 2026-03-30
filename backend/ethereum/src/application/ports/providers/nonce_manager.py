"""ethereum/src/application/ports/providers/nonce_manager.py."""

from typing import Protocol


class NonceManager(Protocol):
    """Port for atomically managing transaction nonces in a cache (e.g., Redis)."""

    async def get_current_nonce(self, address: str) -> int:
        """Retrieve the current nonce for an address (from cache or Web3)."""
        ...

    async def get_and_increment_nonce(self, address: str) -> int:
        """Get the current nonce and immediately increment it atomically."""
        ...

    async def set_nonce(self, address: str, nonce: int) -> None:
        """Explicitly set the nonce for an address."""
        ...

    async def invalidate_nonce(self, address: str) -> None:
        """Remove cached nonce for an address."""
        ...
