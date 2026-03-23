"""rest_api/src/infrastructure/message_broker/tasks.py."""

import logging

from src.infrastructure.message_broker.broker import broker

logger = logging.getLogger(__name__)


@broker.task(task_name="user_events.registered")
async def handle_user_registered_event(user_id: str, email: str) -> None:
    """Task runner for handling user registration events."""
    logger.info("Event received - User registered: %s (Email: %s)", user_id, email)
    # тут мб логика обработки события на стороне подписчика
