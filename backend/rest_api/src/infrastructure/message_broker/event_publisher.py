"""rest_api/src/infrastructure/message_broker/event_publisher.py."""

import logging
import uuid

from src.application.ports.events import EventPublisher
from src.infrastructure.message_broker.broker import broker

logger = logging.getLogger(__name__)


class EventPublisherImpl(EventPublisher):
    """Implementation of EventPublisher using FastStream."""

    async def publish_user_registered(
        self, user_id: uuid.UUID, email: str, username: str
    ) -> None:
        """Publish an event to RabbitMQ when a user registers."""
        payload = {
            "user_id": str(user_id),
            "email": email,
            "username": username,
        }
        logger.info("Publishing event: user_events.registered for %s", email)
        await broker.publish(payload, queue="user_events.registered")

    async def publish_stats_updated(
        self, user_id: uuid.UUID, messages_count: int, wallets_count: int
    ) -> None:
        """Publish an event to notify that user statistics have been updated."""
        payload = {
            "user_id": str(user_id),
            "messages_count": messages_count,
            "wallets_count": wallets_count,
        }
        logger.info("Publishing stats update for user: %s", user_id)
        await broker.publish(payload, queue="stats.updated")
