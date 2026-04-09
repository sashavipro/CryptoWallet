"""sockets/src/presentation/ws/namespaces/transaction.py."""

import logging

import socketio
from dishka import AsyncContainer
from socketio.exceptions import ConnectionRefusedError as SocketConnectionRefusedError

from src.application.ports.providers.api_client import CryptoApiClient
from src.infrastructure.providers import JwtValidator
from src.infrastructure.settings import security_settings

logger = logging.getLogger(__name__)
jwt_validator = JwtValidator(public_key=security_settings.public_key)


class TransactionNamespace(socketio.AsyncNamespace):
    """Handles WebSocket connections for wallet and transaction updates."""

    def __init__(self, namespace: str, container: AsyncContainer):
        """Initialize the namespace with a given name and Dishka container."""
        super().__init__(namespace)
        self.container = container

    async def on_connect(self, sid: str, environ: dict, auth: dict | None):
        """Auth and room subscription for transaction updates."""
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
        logger.info(
            "User %s connected to /transaction namespace. sid: %s", user_id, sid
        )

    async def on_get_tx_history(self, sid: str, data: dict):
        """Fetch transaction history for a wallet via Internal API client."""
        session = await self.get_session(sid)
        user_id = session.get("user_id")
        token = session.get("token")
        wallet_id = data.get("wallet_id")

        if not user_id or not wallet_id:
            return {"status": "error", "message": "Unauthorized or missing wallet_id"}

        try:
            async with self.container() as request_container:
                api_client = await request_container.get(CryptoApiClient)
                tx_history = await api_client.get_wallet_transactions(wallet_id, token)

                if tx_history is not None:
                    return {"status": "success", "data": tx_history}

                return {"status": "error", "message": "Failed to fetch transactions"}
        except Exception:
            logger.exception(
                "Error fetching tx history via WS for wallet %s", wallet_id
            )
            return {"status": "error", "message": "Internal server error"}
