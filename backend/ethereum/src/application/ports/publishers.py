"""ethereum/src/application/ports/publishers.py."""

from typing import Protocol


class EventPublisher(Protocol):
    """Protocol defining the interface for publishing transaction-related events."""

    async def publish_tx_initiated(self, tx_id: str, tx_hash: str) -> None:
        """Publish event when tx is successfully sent to mempool."""
        ...

    async def publish_tx_failed_initiation(self, tx_id: str, error: str) -> None:
        """Publish event when tx failed to be sent."""
        ...

    async def publish_tx_processed(
        self, tx_id: str | None, tx_hash: str, status: str, fee: str
    ) -> None:
        """Publish event when tx is mined and processed."""
        ...
