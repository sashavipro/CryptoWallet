"""rest_api/src/application/tasks/chat.py."""

import logging

from dishka.integrations.taskiq import FromDishka
from dishka.integrations.taskiq import inject

from src.application.ports.gateways.chat import ChatUserGateway
from src.infrastructure.task_broker import taskiq_broker

logger = logging.getLogger(__name__)


@taskiq_broker.task
@inject
async def grant_chat_access_task(
    user_id: str, chat_user_gateway: FromDishka[ChatUserGateway]
) -> None:
    """Background task to grant a user access to the chat."""
    logger.info("Start of the grant_chat_access_task for %s", user_id)

    try:
        await chat_user_gateway.update_chat_access(user_id=user_id, has_access=True)

        logger.info("Chat access has been successfully granted to the user %s", user_id)
    except Exception:
        logger.exception("Error granting access to the chat for %s", user_id)
