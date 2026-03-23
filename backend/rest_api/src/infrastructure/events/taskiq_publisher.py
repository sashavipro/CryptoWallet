"""rest_api/src/infrastructure/events/taskiq_publisher.py."""

import uuid

from src.application.ports.events import EventPublisher
from src.infrastructure.message_broker.tasks import handle_user_registered_event


class TaskiqEventPublisher(EventPublisher):
    """Implementation of EventPublisher using TaskIQ and RabbitMQ."""

    async def publish_user_registered(self, user_id: uuid.UUID, email: str) -> None:
        """Publish a user registration event to the message broker."""
        await handle_user_registered_event.kiq(str(user_id), email)
