"""rest_api/src/application/ports/events.py."""

import uuid
from typing import Protocol


class EventPublisher(Protocol):
    """Port for publishing integration events to a message broker."""

    async def publish_user_registered(
        self, user_id: uuid.UUID, email: str, username: str
    ) -> None:
        """Publish an event indicating a new user has registered."""
        ...

    async def publish_stats_updated(
        self,
        user_id: uuid.UUID,
        messages_count: int | None = None,
        wallets_count: int | None = None,
    ) -> None:
        """Publish an event to notify the user that their stats have changed."""
        ...

    async def publish_tx_status_updated(  # noqa: PLR0913
        self,
        user_id: str,
        wallet_id: str,
        tx_hash: str,
        status: str,
        value: str,
        error: str | None = None,
    ) -> None:
        """Publish transaction status update for WebSocket."""
        ...

    async def publish_balance_updated(
        self, user_id: str, wallet_id: str, balance: str
    ) -> None:
        """Publish wallet balance update for WebSocket."""
        ...

    async def publish_ibay_product_created(
        self, product_id: str, title: str, price: str, photo_url: str | None
    ) -> None:
        """Publish an event when a new iBay product is created."""
        ...

    async def publish_ibay_order_created(
        self, order_id: str, product_id: str, buyer_id: str, status: str, price: str
    ) -> None:
        """Publish an event when an order is created."""
        ...
