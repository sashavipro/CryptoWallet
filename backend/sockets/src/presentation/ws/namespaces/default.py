"""sockets/src/presentation/ws/namespaces/default.py."""

import logging

import socketio
from dishka import AsyncContainer

logger = logging.getLogger(__name__)


class DefaultNamespace(socketio.AsyncNamespace):
    """Handles global WebSocket connections (notifications, balances, iBay)."""

    def __init__(self, namespace: str, container: AsyncContainer):
        """Initialize the namespace."""
        super().__init__(namespace)
        self.container = container

    async def on_connect(self, sid: str, environ: dict, auth: dict | None):
        """Subscribe user to their personal notification room and global iBay room."""
        session = await self.get_session(sid)
        user_id = session.get("user_id")

        if user_id:
            await self.enter_room(sid, f"user_{user_id}")
            await self.enter_room(sid, "ibay_global")
            logger.info("User %s connected to default namespace. sid: %s", user_id, sid)
        else:
            logger.warning(
                "Anonymous connection attempt to default namespace rejected."
            )
            error_msg = "Unauthorized"
            raise ConnectionRefusedError(error_msg)

    async def on_disconnect(self, sid: str):
        """Handle disconnection from default namespace."""
        session = await self.get_session(sid)
        user_id = session.get("user_id", "Unknown")
        logger.info(
            "User %s disconnected from default namespace. sid: %s", user_id, sid
        )
