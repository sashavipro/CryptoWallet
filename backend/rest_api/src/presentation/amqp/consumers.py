"""rest_api/src/presentation/amqp/consumers.py."""

import logging
import uuid

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject

from src.application.ports.gateways import ChatMessageGateway
from src.application.ports.gateways import ChatUserGateway
from src.application.ports.gateways import TransactionGateway
from src.application.ports.gateways import UnitOfWork
from src.application.ports.providers import MailProvider
from src.domain.entities import ChatMessage
from src.domain.entities import ChatUser
from src.infrastructure.message_broker.broker import broker

logger = logging.getLogger(__name__)


@broker.subscriber("eth.tx_initiated")
@inject
async def handle_tx_initiated(
    payload: dict,
    tx_gateway: FromDishka[TransactionGateway],
    uow: FromDishka[UnitOfWork],
) -> None:
    """Update the transaction hash when a transaction is successfully initiated."""
    tx_id = uuid.UUID(payload["tx_id"])
    tx_hash = payload["tx_hash"]

    async with uow:
        tx = await tx_gateway.get_transaction_by_id(tx_id)
        if tx:
            tx.tx_hash = tx_hash
            await tx_gateway.update_transaction(tx)
            logger.info("Transaction %s hash updated to %s", tx_id, tx_hash)


@broker.subscriber("eth.tx_failed_initiation")
@inject
async def handle_tx_failed_initiation(
    payload: dict,
    tx_gateway: FromDishka[TransactionGateway],
    uow: FromDishka[UnitOfWork],
) -> None:
    """Mark a transaction as failed if it could not be initiated."""
    tx_id = uuid.UUID(payload["tx_id"])

    async with uow:
        tx = await tx_gateway.get_transaction_by_id(tx_id)
        if tx:
            tx.mark_failed()
            await tx_gateway.update_transaction(tx)
            logger.warning("Transaction %s marked as FAILED", tx_id)


@broker.subscriber("user_events.registered")
@inject
async def handle_user_registered_event(
    payload: dict,
    mail_provider: FromDishka[MailProvider],
    chat_user_gateway: FromDishka[ChatUserGateway],
) -> None:
    """Process user registration by updating the chat store and sending an email."""
    user_id = payload["user_id"]
    email = payload["email"]
    username = payload["username"]

    logger.info("Event received - User registered: %s (Email: %s)", user_id, email)

    chat_user = ChatUser(id=user_id, username=username, avatar_url=None)
    await chat_user_gateway.upsert_user(chat_user)
    logger.info("User %s added to MongoDB chat_users_mongo", user_id)

    try:
        await mail_provider.send_welcome_email(to_email=email, username=username)
        logger.info("Welcome email sent asynchronously to user ID: %s", user_id)
    except Exception:
        logger.exception("Background task failed to send welcome email to %s", email)


@broker.subscriber("chat.process_message")
@inject
async def handle_chat_message(
    payload: dict,
    message_gateway: FromDishka[ChatMessageGateway],
) -> None:
    """Save an incoming chat message to the database and broadcast it."""
    user_id = payload["user_id"]
    text = payload["text"]
    image_key = payload.get("image_key")
    temp_id = payload.get("temp_id")

    image_url = f"https://my-s3-bucket.com/{image_key}" if image_key else None

    new_message = ChatMessage(
        id=None,
        user_id=user_id,
        message_text=text,
        image_url=image_url,
    )

    await message_gateway.add_message(new_message)

    broadcast_payload = {
        "id": new_message.id,
        "temp_id": temp_id,
        "user_id": new_message.user_id,
        "text": new_message.message_text,
        "image_url": new_message.image_url,
        "created_at": new_message.created_at.isoformat(),
        "room_id": "chat_global",
    }

    await broker.publish(broadcast_payload, queue="chat.broadcast_message")
    logger.info("Chat message saved to Mongo and broadcasted: %s", new_message.id)
