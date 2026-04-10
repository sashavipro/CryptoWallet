"""ethereum/src/application/interactors/transaction_watcher.py."""

import asyncio
import logging
from decimal import Decimal

from src.application.ports.providers.web3 import Web3Provider
from src.application.ports.publishers import EventPublisher

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

        tx_fee_eth = tx_fee_wei / Decimal(10**18)

        return {
            "status": "SUCCESS" if is_success else "FAILED",
            "tx_fee": str(tx_fee_eth),
        }


class BackgroundTransactionWatcherInteractor:
    """Background worker to poll transaction status until completion."""

    def __init__(
        self, web3_provider: Web3Provider, event_publisher: EventPublisher
    ) -> None:
        """Initialize watcher with Web3 and message broker publisher."""
        self.web3_provider = web3_provider
        self.event_publisher = event_publisher

    async def __call__(self, tx_hash: str, tx_id: str | None = None) -> None:
        """Poll the transaction receipt every 5 seconds until mined."""
        logger.info("Starting background watcher for tx: %s", tx_hash)

        while True:
            try:
                receipt = await self.web3_provider.get_transaction_receipt(tx_hash)

                if receipt:
                    is_success = receipt.get("status") == 1
                    status = "success" if is_success else "failed"

                    gas_used = Decimal(str(receipt.get("gasUsed", 0)))
                    gas_price_wei = Decimal(str(receipt.get("effectiveGasPrice", 0)))
                    tx_fee_wei = gas_used * gas_price_wei

                    tx_fee_eth = tx_fee_wei / Decimal(10**18)

                    await self.event_publisher.publish_tx_processed(
                        tx_id=tx_id, tx_hash=tx_hash, status=status, fee=str(tx_fee_eth)
                    )

                    logger.info("Tx %s mined with status: %s", tx_hash, status)
                    break
            except Exception:
                logger.exception("Error checking background tx %s", tx_hash)

            await asyncio.sleep(5)
