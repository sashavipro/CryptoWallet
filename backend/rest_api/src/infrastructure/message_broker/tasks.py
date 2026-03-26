"""rest_api/src/infrastructure/message_broker/tasks.py."""

import logging

from dishka.integrations.taskiq import FromDishka

from src.application.ports.providers import MailProvider
from src.infrastructure.message_broker.broker import broker

logger = logging.getLogger(__name__)


@broker.task(task_name="user_events.registered")
async def handle_user_registered_event(
    user_id: str, email: str, username: str, mail_provider: FromDishka[MailProvider]
) -> None:
    """Workflow for processing a successful registration."""
    logger.info("Event received - User registered: %s (Email: %s)", user_id, email)

    try:
        await mail_provider.send_welcome_email(to_email=email, username=username)
        logger.info("Welcome email sent asynchronously to user ID: %s", user_id)
    except Exception:
        logger.exception("Background task failed to send welcome email to %s", email)
