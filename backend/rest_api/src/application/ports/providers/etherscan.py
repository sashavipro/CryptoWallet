"""rest_api/src/application/ports/providers/etherscan.py."""

from typing import Any
from typing import Protocol


class EtherscanProvider(Protocol):
    """Port for interacting with Etherscan (or similar block explorer) API."""

    async def get_wallet_transactions(self, address: str) -> list[dict[str, Any]]:
        """Fetch historical transaction data for a wallet address."""
        ...
