"""rest_api/src/infrastructure/providers/etherscan.py."""

import asyncio
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
        """Fetch normal AND internal transaction data for a wallet address."""
        base_params = {
            "module": "account",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "desc",
            "apikey": self.api_key,
        }

        try:
            normal_req = self.http_client.get(
                self.base_url, params={**base_params, "action": "txlist"}
            )
            internal_req = self.http_client.get(
                self.base_url, params={**base_params, "action": "txlistinternal"}
            )

            res_normal, res_internal = await asyncio.gather(
                normal_req, internal_req, return_exceptions=True
            )

            all_txs = []

            if (
                not isinstance(res_normal, Exception)
                and res_normal.status_code == httpx.codes.OK
            ):
                data = res_normal.json()
                if data.get("status") == "1":
                    all_txs.extend(data.get("result", []))

            if (
                not isinstance(res_internal, Exception)
                and res_internal.status_code == httpx.codes.OK
            ):
                data = res_internal.json()
                if data.get("status") == "1":
                    all_txs.extend(data.get("result", []))

            all_txs.sort(key=lambda x: int(x.get("timeStamp", 0)), reverse=True)

        except Exception:
            logger.exception(
                "Unexpected error fetching Etherscan data for address %s", address
            )
            return None
        else:
            return all_txs
