"""rest_api/src/presentation/amqp/consumers/auth.py."""

import logging

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import ExchangeType
from faststream.rabbit import RabbitExchange
from faststream.rabbit import RabbitQueue
from faststream.rabbit import RabbitRouter

from src.application.ports.gateways import ChatUserGateway
from src.application.ports.providers import MailProvider
from src.application.tasks.chat import grant_chat_access_task
from src.domain.entities import ChatUser

logger = logging.getLogger(__name__)

router = RabbitRouter()

user_exchange = RabbitExchange("user_events", type=ExchangeType.TOPIC)


@router.subscriber(
    RabbitQueue("rest_api_auth_queue", routing_key="auth.user_registered"),
    exchange=user_exchange,
)
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
        await grant_chat_access_task.kiq(user_id, delay=60)
        logger.info(
            "TaskIQ: The task to access the chat is scheduled for %s in 60 seconds.",
            user_id,
        )
    except Exception:
        logger.exception("TaskIQ Error: Unable to schedule the task for %s", user_id)

    try:
        await mail_provider.send_welcome_email(to_email=email, username=username)
        logger.info("Welcome email sent asynchronously to user ID %s", user_id)
    except Exception:
        logger.exception("Error sending welcome email to %s", email)
