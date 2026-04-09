"""sockets/src/infrastructure/providers/api_client.py."""

import logging
from http import HTTPStatus
from typing import Any

import httpx

from src.application.ports.providers.api_client import CryptoApiClient
from src.infrastructure.settings import ApiSettings

logger = logging.getLogger(__name__)


class CryptoApiClientImpl(CryptoApiClient):
    """HTTP implementation of the CryptoApiClient."""

    def __init__(self, settings: ApiSettings) -> None:
        """Initialize the API client with the base service URL."""
        self.base_url = settings.API_SERVICE_URL.rstrip("/")

    async def get_user_profile(self, user_id: str, token: str) -> dict[str, Any] | None:
        """Fetch user profile and permissions from the REST API service.

        Returns the profile data if the request is successful, otherwise None.
        """
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"{self.base_url}/api/v1/profile/{user_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if res.status_code == HTTPStatus.OK:
                    return res.json()
        except Exception:
            logger.exception("API Error: Failed to fetch profile for %s", user_id)
        return None

    async def get_wallet_transactions(
        self, wallet_id: str, token: str
    ) -> list[dict[str, Any]] | None:
        """Fetch historical transaction data for a specific wallet from the REST API.

        Returns a list of transactions if the request is successful, otherwise None.
        """
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"{self.base_url}/api/v1/transactions/wallet/{wallet_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if res.status_code == HTTPStatus.OK:
                    return res.json()
        except Exception:
            logger.exception("API Error: Failed to fetch tx history for %s", wallet_id)
        return None
