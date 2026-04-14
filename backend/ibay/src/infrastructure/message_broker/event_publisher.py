"""ibay/src/infrastructure/message_broker/event_publisher.py."""

import logging

from faststream.rabbit import ExchangeType
from faststream.rabbit import RabbitBroker
from faststream.rabbit import RabbitExchange

from src.application.ports.events import EventPublisher

logger = logging.getLogger(__name__)
ibay_exchange = RabbitExchange("ibay_events", type=ExchangeType.TOPIC)


class RabbitMQEventPublisher(EventPublisher):
    """RabbitMQ implementation for publishing domain events."""

    def __init__(self, broker: RabbitBroker) -> None:
        """Initialize the publisher with a RabbitBroker."""
        self.broker = broker

    async def publish_ibay_order_updated(
        self, order_id: str, product_id: str, status: str, buyer_id: str
    ) -> None:
        """Publish an event indicating that an order's status has been updated."""
        payload = {
            "order_id": order_id,
            "product_id": product_id,
            "status": status,
            "buyer_id": buyer_id,
        }
        logger.info("Publishing ibay.order_updated event: %s", payload)
        await self.broker.publish(
            payload, exchange=ibay_exchange, routing_key="ibay.order_updated"
        )
