"""ibay/src/application/ports/providers/api_client.py."""

from typing import Any
from typing import Protocol


class InternalApiClient(Protocol):
    """Port for communicating with the main REST API service."""

    async def get_order_by_tx_hash(self, tx_hash: str) -> dict[str, Any] | None:
        """Retrieve an order dictionary using its transaction hash."""
        ...

    async def get_oldest_delivery_order(self) -> dict[str, Any] | None:
        """Retrieve the oldest order currently in the delivery state."""
        ...

    async def update_order_status(
        self,
        order_id: str,
        status: str,
        *,
        return_tx_hash: str | None = None,
        real_tx_hash: str | None = None,
        trigger_refund: bool = False,
    ) -> None:
        """Update an order's status and optionally its related transaction hashes."""
        ...

    async def get_transaction_by_hash(self, tx_hash: str) -> dict[str, Any] | None:
        """Retrieve transaction details using its hash."""
        ...

    async def create_transaction(
        self, from_wallet_id: str, to_wallet_id: str, amount_eth: float
    ) -> str | None:
        """Create a new transaction between two wallets."""
        ...
