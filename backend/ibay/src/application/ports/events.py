"""ibay/src/application/ports/events.py."""

from typing import Protocol


class EventPublisher(Protocol):
    """Interface for publishing domain events to the message broker."""

    async def publish_ibay_order_updated(
        self, order_id: str, product_id: str, status: str, buyer_id: str
    ) -> None:
        """Publish an event when an order status is updated."""
        ...
