"""rest_api/src/presentation/amqp/consumers/chat.py."""

import logging

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.ports.gateways.chat import ChatMessageGateway
from src.domain.entities.chat import ChatMessage
from src.infrastructure.message_broker.broker import broker

logger = logging.getLogger(__name__)

router = RabbitRouter()


@router.subscriber("chat.process_message")
@inject
async def process_chat_message(
    payload: dict,
    message_gateway: FromDishka[ChatMessageGateway],
) -> None:
    """Receive messages from sockets, saves them to MongoDB, and broadcast back."""
    try:
        user_id = payload.get("user_id")
        text = payload.get("text", "")
        image_url = payload.get("image_url")

        message = ChatMessage(
            id=None, user_id=user_id, message_text=text, image_url=image_url
        )

        await message_gateway.add_message(message)
        logger.info("Message saved to Mongo! ID: %s", message.id)

        broadcast_payload = {
            "id": str(message.id),
            "user_id": user_id,
            "text": text,
            "image_url": image_url,
            "created_at": message.created_at.isoformat(),
            "room_id": payload.get("room_id", "chat_global"),
        }

        await broker.publish(broadcast_payload, queue="chat.broadcast_message")

    except Exception:
        logger.exception("Error saving message to DB")
