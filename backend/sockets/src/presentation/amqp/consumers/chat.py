"""sockets/src/presentation/amqp/consumers/chat.py."""

import logging

from faststream.rabbit import RabbitQueue
from faststream.rabbit import RabbitRouter

from src.infrastructure.message_broker.event_publisher import chat_exchange
from src.presentation.ws.server import sio

logger = logging.getLogger(__name__)
router = RabbitRouter()


@router.subscriber(
    RabbitQueue("sockets_chat_queue", routing_key="chat.broadcast_message"),
    exchange=chat_exchange,
)
async def handle_broadcast_message(payload: dict) -> None:
    """Broadcast a new chat message to all users in the specified room."""
    room_id = payload.get("room_id")
    if not room_id:
        return
    await sio.emit("new_message", payload, room=room_id, namespace="/chat")
    logger.info("WS: Broadcasted new message to chat room %s", room_id)


@router.subscriber(
    RabbitQueue("sockets_profile_queue", routing_key="chat.profile_updated"),
    exchange=chat_exchange,
)
async def handle_profile_updated(payload: dict) -> None:
    """Notify all users in chat that a specific user's profile changed."""
    user_id = payload.get("user_id")
    if not user_id:
        return
    await sio.emit(
        "user_profile_updated",
        {"user_id": user_id},
        room="chat_global",
        namespace="/chat",
    )
    logger.info("WS: Broadcasted profile update for user %s", user_id)
