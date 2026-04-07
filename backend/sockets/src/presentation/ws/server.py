"""sockets/src/presentation/ws/server.py."""

import logging

import socketio

from src.infrastructure.providers.jwt_provider import JwtValidator
from src.infrastructure.settings import redis_settings
from src.infrastructure.settings import security_settings

logger = logging.getLogger(__name__)

jwt_validator = JwtValidator(public_key=security_settings.public_key)

redis_mgr = socketio.AsyncRedisManager(redis_settings.REDIS_URL)

sio = socketio.AsyncServer(
    async_mode="asgi",
    client_manager=redis_mgr,
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=False,
)


@sio.on("connect")
async def global_connect(sid: str, environ: dict, auth: dict | None):
    """Global Handshake (authentication)."""
    if not auth or "token" not in auth:
        error_msg = "Authentication token is missing"
        raise socketio.exceptions.ConnectionRefusedError(error_msg)

    payload = jwt_validator.verify_token(auth.get("token"))
    if not payload or not payload.get("sub"):
        error_msg = "Invalid token"
        raise socketio.exceptions.ConnectionRefusedError(error_msg)

    async with sio.session(sid) as session:
        session["user_id"] = payload.get("sub")

    return True


@sio.on("disconnect")
async def disconnect(sid: str):
    """Disconnection handler (tab closed, internet connection lost, etc.)."""
    async with sio.session(sid) as session:
        user_id = session.get("user_id", "Unknown")

    logger.info("User %s disconnected. sid: %s", user_id, sid)
