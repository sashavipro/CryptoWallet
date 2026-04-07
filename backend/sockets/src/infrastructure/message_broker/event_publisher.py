"""sockets/src/infrastructure/message_broker/event_publisher.py."""

import logging

from src.application.ports.publishers import EventPublisher
from src.infrastructure.message_broker.broker import broker

logger = logging.getLogger(__name__)


class EventPublisherImpl(EventPublisher):
    """RabbitMQ implementation of the EventPublisher interface."""

    async def publish_chat_message(
        self,
        user_id: str,
        room_id: str,
        text: str,
        image_key: str | None,
        temp_id: str | None,
    ) -> None:
        """Publish a raw chat message to the broker for background processing."""
        payload = {
            "user_id": user_id,
            "room_id": room_id,
            "text": text,
            "image_key": image_key,
            "temp_id": temp_id,
        }
        logger.info("Publishing raw chat message from WS to broker. User: %s", user_id)
        await broker.publish(payload, queue="chat.process_message")
