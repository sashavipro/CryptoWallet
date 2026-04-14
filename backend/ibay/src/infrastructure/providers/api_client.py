"""ibay/src/infrastructure/providers/api_client.py."""

import logging
from http import HTTPStatus
from typing import Any

import aiohttp

from src.application.ports.providers.api_client import InternalApiClient

logger = logging.getLogger(__name__)


class RestApiClient(InternalApiClient):
    """HTTP Client for communicating with the main REST API service."""

    def __init__(self, base_url: str) -> None:
        """Initialize the API client with a base URL."""
        self.base_url = base_url

    async def get_order_by_tx_hash(self, tx_hash: str) -> dict[str, Any] | None:
        """Retrieve an order dictionary using its transaction hash."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/v1/ibay/internal/orders/by-tx/{tx_hash}"
            async with session.get(url) as response:
                if response.status == HTTPStatus.OK:
                    return await response.json()
                if response.status == HTTPStatus.NOT_FOUND:
                    return None
                response.raise_for_status()
                return None

    async def get_oldest_delivery_order(self) -> dict[str, Any] | None:
        """Retrieve the oldest order currently in the delivery state."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/v1/ibay/internal/orders/delivery/oldest"
            async with session.get(url) as response:
                if response.status == HTTPStatus.OK:
                    return await response.json()
                if response.status == HTTPStatus.NOT_FOUND:
                    return None
                response.raise_for_status()
                return None

    async def update_order_status(
        self,
        order_id: str,
        status: str,
        *,
        return_tx_hash: str | None = None,
        real_tx_hash: str | None = None,
        trigger_refund: bool = False,
    ) -> None:
        """Update an order's status and optionally its related transaction hashes."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/v1/ibay/internal/orders/{order_id}/status"
            payload = {"status": status, "trigger_refund": trigger_refund}
            if return_tx_hash:
                payload["return_tx_hash"] = return_tx_hash
            if real_tx_hash:
                payload["tx_hash"] = real_tx_hash
            async with session.patch(url, json=payload) as response:
                response.raise_for_status()

    async def get_transaction_by_hash(self, tx_hash: str) -> dict[str, Any] | None:
        """Retrieve transaction details using its hash."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/v1/internal/transactions/by-hash/{tx_hash}"
            async with session.get(url) as response:
                if response.status == HTTPStatus.OK:
                    return await response.json()
                if response.status == HTTPStatus.NOT_FOUND:
                    return None
                response.raise_for_status()
                return None

    async def create_transaction(
        self, from_wallet_id: str, to_wallet_id: str, amount_eth: float
    ) -> str | None:
        """Create a new transaction between two wallets."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/v1/internal/transactions"
            payload = {
                "from_wallet_id": from_wallet_id,
                "to_wallet_id": to_wallet_id,
                "amount": amount_eth,
            }
            async with session.post(url, json=payload) as response:
                if response.status in (HTTPStatus.OK, HTTPStatus.CREATED):
                    data = await response.json()
                    return data.get("tx_hash") or data.get("id")
                return None
