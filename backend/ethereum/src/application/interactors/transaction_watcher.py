"""ethereum/src/application/interactors/transaction_watcher.py."""

import logging
from decimal import Decimal

from src.application.ports.providers.web3 import Web3Provider

logger = logging.getLogger(__name__)


class CheckTransactionStatusInteractor:
    """Stateless worker use case to check tx status on blockchain."""

    def __init__(self, web3_provider: Web3Provider) -> None:
        """Initialize the interactor with a Web3 provider."""
        self.web3_provider = web3_provider

    async def __call__(self, tx_hash: str) -> dict | None:
        """Go to Web3 and return the status. If pending, return None."""
        logger.info("Checking Web3 status for transaction: %s", tx_hash)

        receipt = await self.web3_provider.get_transaction_receipt(tx_hash)

        if not receipt:
            return None

        status_code = receipt.get("status")
        is_success = status_code == 1

        gas_used = Decimal(str(receipt.get("gasUsed", 0)))
        gas_price_wei = Decimal(str(receipt.get("effectiveGasPrice", 0)))
        tx_fee_wei = gas_used * gas_price_wei
        tx_fee_eth = self.web3_provider.w3.from_wei(tx_fee_wei, "ether")

        return {
            "status": "SUCCESS" if is_success else "FAILED",
            "tx_fee": str(tx_fee_eth),
        }
