"""sockets/src/presentation/ws/namespaces/ibay.py."""

import logging

import socketio
from dishka import AsyncContainer
from socketio.exceptions import ConnectionRefusedError as SocketConnectionRefusedError

from src.infrastructure.providers import JwtValidator
from src.infrastructure.settings import security_settings

logger = logging.getLogger(__name__)
jwt_validator = JwtValidator(public_key=security_settings.public_key)


class IbayNamespace(socketio.AsyncNamespace):
    """Handles WebSocket connections for iBay marketplace updates."""

    def __init__(self, namespace: str, container: AsyncContainer):
        """Initialize the namespace with a given name and Dishka container."""
        super().__init__(namespace)
        self.container = container

    async def on_connect(self, sid: str, environ: dict, auth: dict | None):
        """Auth and room subscription for marketplace updates."""
        if not auth or "token" not in auth:
            error_msg = "Authentication token is missing"
            raise SocketConnectionRefusedError(error_msg)

        token = auth.get("token")
        payload = jwt_validator.verify_token(token)
        if not payload or not payload.get("sub"):
            error_msg = "Invalid or expired token"
            raise SocketConnectionRefusedError(error_msg)

        user_id = payload.get("sub")

        await self.save_session(sid, {"user_id": user_id, "token": token})

        await self.enter_room(sid, f"user_{user_id}")

        await self.enter_room(sid, "ibay_global")

        logger.info("User %s connected to /ibay namespace. sid: %s", user_id, sid)

    async def on_disconnect(self, sid: str):
        """Handle disconnection."""
        session = await self.get_session(sid)
        user_id = session.get("user_id")
        if user_id:
            logger.info("User %s disconnected from /ibay. sid: %s", user_id, sid)
