"""sockets/src/application/ports/providers/api_client.py."""

from typing import Any
from typing import Protocol


class CryptoApiClient(Protocol):
    """Port for communicating with the REST API service."""

    async def get_user_profile(self, user_id: str, token: str) -> dict[str, Any] | None:
        """Fetch user profile and permissions."""
        ...

    async def get_wallet_transactions(
        self, wallet_id: str, token: str
    ) -> list[dict[str, Any]] | None:
        """Fetch transaction history for a specific wallet."""
        ...
