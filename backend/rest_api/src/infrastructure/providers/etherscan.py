"""rest_api/src/infrastructure/providers/etherscan.py."""

import logging
from typing import Any

import httpx

from src.application.ports.providers.etherscan import EtherscanProvider
from src.infrastructure.settings import Web3Settings

logger = logging.getLogger(__name__)


class EtherscanProviderImpl(EtherscanProvider):
    """Implementation of EtherscanProvider for fetching blockchain data."""

    def __init__(self, settings: Web3Settings) -> None:
        """Initialize with Etherscan settings."""
        self.settings = settings
        self.base_url = settings.ETHERSCAN_BASE_URL
        self.api_key = settings.ETHERSCAN_API_KEY
        self.http_client = httpx.AsyncClient()

        logger.info("EtherscanProvider initialized with base URL: %s", self.base_url)

    async def get_wallet_transactions(self, address: str) -> list[dict[str, Any]]:
        """Fetch historical transaction data for a wallet address from Etherscan."""
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "asc",
            "apikey": self.api_key,
        }

        try:
            response = await self.http_client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError:
            logger.exception("HTTP error fetching Etherscan data")
            raise
        except Exception:
            logger.exception(
                "Unexpected error fetching Etherscan data for address %s", address
            )
            raise
        else:
            if data["status"] == "1":
                logger.debug(
                    "Fetched %d transactions for address %s",
                    len(data["result"]),
                    address,
                )
                return data["result"]

            logger.warning(
                "Etherscan API returned status %s for address %s: %s",
                data["status"],
                address,
                data["message"],
            )
            return []
