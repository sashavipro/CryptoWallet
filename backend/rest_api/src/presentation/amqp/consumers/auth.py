"""rest_api/src/presentation/amqp/consumers/auth.py."""

import logging

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.ports.gateways import ChatUserGateway
from src.application.ports.providers import MailProvider
from src.domain.entities import ChatUser

logger = logging.getLogger(__name__)

router = RabbitRouter()


@router.subscriber("auth.user_registered")
@inject
async def handle_user_registered(
    payload: dict,
    chat_user_gateway: FromDishka[ChatUserGateway],
    mail_provider: FromDishka[MailProvider],
) -> None:
    """Handle new user registration to sync with Mongo and send an email."""
    user_id = payload["user_id"]
    username = payload["username"]
    email = payload["email"]

    chat_user = ChatUser(id=user_id, username=username, avatar_url=None)
    await chat_user_gateway.upsert_user(chat_user)
    logger.info("User %s added to MongoDB chat_users_mongo", user_id)

    try:
        await mail_provider.send_welcome_email(to_email=email, username=username)
        logger.info("Welcome email sent asynchronously to user ID: %s", user_id)
    except Exception:
        logger.exception("Background task failed to send welcome email to %s", email)
