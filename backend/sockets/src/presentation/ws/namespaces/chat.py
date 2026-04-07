"""sockets/src/presentation/ws/namespaces/chat.py."""

import logging

import socketio
from dishka import AsyncContainer

from src.application.ports.publishers import EventPublisher
from src.infrastructure.cache import OnlinePresenceGateway
from src.infrastructure.providers import JwtValidator
from src.infrastructure.settings import security_settings

logger = logging.getLogger(__name__)

jwt_validator = JwtValidator(public_key=security_settings.public_key)


class ChatNamespace(socketio.AsyncNamespace):
    """Handles WebSocket connections and events for the /chat namespace."""

    def __init__(self, namespace: str, container: AsyncContainer):
        """Initialize the namespace with a given name and Dishka container."""
        super().__init__(namespace)
        self.container = container

    async def on_connect(self, sid: str, environ: dict, auth: dict | None):
        """Handle connections specifically to the /chat channel."""
        if not auth or "token" not in auth:
            msg = "Authentication token is missing"
            raise socketio.exceptions.ConnectionRefusedError(msg)

        payload = jwt_validator.verify_token(auth.get("token"))
        if not payload or not payload.get("sub"):
            msg = "Invalid or expired token"
            raise socketio.exceptions.ConnectionRefusedError(msg)

        user_id = payload.get("sub")
        await self.save_session(sid, {"user_id": user_id})

        await self.enter_room(sid, f"user_{user_id}")
        await self.enter_room(sid, "chat_global")

        async with self.container() as request_container:
            presence = await request_container.get(OnlinePresenceGateway)
            is_new_online = await presence.user_connected(user_id)
            online_users = await presence.get_online_users()

        if is_new_online:
            await self.emit(
                "online_users_list", {"users": online_users}, room="chat_global"
            )
        else:
            await self.emit("online_users_list", {"users": online_users}, to=sid)

        logger.info("User %s connected to chat. sid: %s", user_id, sid)

    async def on_disconnect(self, sid: str):
        """Handle disconnection and update online presence status."""
        session = await self.get_session(sid)
        user_id = session.get("user_id")

        if not user_id:
            return

        async with self.container() as request_container:
            presence = await request_container.get(OnlinePresenceGateway)
            is_offline = await presence.user_disconnected(user_id)
            online_users = await presence.get_online_users()

        if is_offline:
            await self.emit(
                "online_users_list", {"users": online_users}, room="chat_global"
            )

        logger.info("User %s disconnected from chat. sid: %s", user_id, sid)

    async def on_typing(self, sid: str, data: dict):
        """Broadcast a typing event to other users in the global chat."""
        session = await self.get_session(sid)
        user_id = session.get("user_id")
        await self.emit(
            "user_typing", {"user_id": user_id}, room="chat_global", skip_sid=sid
        )

    async def on_send_message(self, sid: str, data: dict):
        """Process an incoming message from the client."""
        session = await self.get_session(sid)
        user_id = session.get("user_id")

        if not user_id:
            return {"status": "error", "message": "Unauthorized"}

        text = data.get("text", "").strip()
        image_key = data.get("image_key")
        room_id = data.get("room_id", "chat_global")
        temp_id = data.get("temp_id")

        if not text and not image_key:
            return {"status": "error", "message": "Message cannot be empty"}

        logger.info("User %s sending message to room %s", user_id, room_id)

        async with self.container() as request_container:
            publisher = await request_container.get(EventPublisher)
            await publisher.publish_chat_message(
                user_id=user_id,
                room_id=room_id,
                text=text,
                image_key=image_key,
                temp_id=temp_id,
            )

        return {"status": "processing"}
