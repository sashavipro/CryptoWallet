"""sockets/src/presentation/amqp/consumers.py."""

import logging
import uuid

from dishka import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.ports.gateways.message_gateway import MessageGateway
from src.application.ports.providers.s3_provider import S3Provider
from src.application.ports.uow import UnitOfWork
from src.domain.entities.message import Message
from src.presentation.ws.server import sio

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber("eth.tx_status_updated")
@inject
async def handle_tx_status_update(payload: dict) -> None:
    """Listen for transaction status updates from RabbitMQ.

    Immediately sends them to the wallet owner via WebSockets.
    """
    user_id = payload.get("user_id")
    tx_id = payload.get("tx_id")
    status = payload.get("status")

    if not user_id:
        return

    await sio.emit(
        "transaction_updated",
        {
            "tx_id": tx_id,
            "status": status,
            "message": f"Ваша транзакция теперь {status}",
        },
        room=f"user_{user_id}",
    )
    logger.info("Sent WS notification to user %s about tx %s", user_id, tx_id)


@router.subscriber("chat.process_message")
@inject
async def handle_chat_message(
    payload: dict,
    message_gateway: FromDishka[MessageGateway],
    s3_provider: FromDishka[S3Provider],
    uow: FromDishka[UnitOfWork],
) -> None:
    """REST API: Saves the message to the database and sends a command to Broadcast."""
    user_id = payload["user_id"]
    room_id = payload["room_id"]
    text = payload["text"]
    image_key = payload.get("image_key")
    temp_id = payload.get("temp_id")

    image_url = None
    if image_key:
        image_url = await s3_provider.generate_read_url(image_key)

    new_message = Message(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        room_id=room_id,
        text=text,
        image_url=image_url,
    )

    async with uow:
        await message_gateway.add_message(new_message)

    broadcast_payload = {
        "id": str(new_message.id),
        "temp_id": temp_id,
        "user_id": user_id,
        "room_id": room_id,
        "text": text,
        "image_url": image_url,
        "created_at": new_message.created_at.isoformat(),
    }

    await router.publish(broadcast_payload, queue="chat.broadcast_message")


@router.subscriber("chat.broadcast_message")
async def handle_broadcast_message(payload: dict) -> None:
    """Retrieve a saved message from the database and instantly broadcast it.

    Sends the message to all participants currently in the chat room.
    """
    room_id = payload.get("room_id")

    if not room_id:
        return

    await sio.emit("new_message", payload, room=room_id, namespace="/chat")

    logger.info("Broadcasted new message to room %s", room_id)
