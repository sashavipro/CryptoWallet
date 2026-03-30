"""ethereum/src/application/interactors/transaction_watcher.py."""

import logging
from decimal import Decimal

from src.application.ports.events import EventPublisher
from src.application.ports.gateways.transaction import TransactionGateway
from src.application.ports.gateways.uow import UnitOfWork
from src.application.ports.gateways.wallet import WalletGateway
from src.application.ports.providers.etherscan import EtherscanProvider
from src.application.ports.providers.web3 import Web3Provider
from src.application.ports.utils import TimeProvider
from src.domain.entities.transaction import TransactionStatus
from src.domain.exceptions import TransactionNotFoundException
from src.domain.exceptions import WalletNotFoundException
from src.domain.value_objects.shared import EthereumAddress
from src.domain.value_objects.transaction.tx_fee import TxFee

logger = logging.getLogger(__name__)


class WatchTransactionStatusInteractor:
    """Use case for watching pending transactions and updating their status."""

    def __init__(  # noqa: PLR0913
        self,
        transaction_gateway: TransactionGateway,
        wallet_gateway: WalletGateway,
        uow: UnitOfWork,
        web3_provider: Web3Provider,
        etherscan_provider: EtherscanProvider,
        event_publisher: EventPublisher,
        time_provider: TimeProvider,
    ) -> None:
        """Initialize with required ports."""
        self.transaction_gateway = transaction_gateway
        self.wallet_gateway = wallet_gateway
        self.uow = uow
        self.web3_provider = web3_provider
        self.etherscan_provider = etherscan_provider
        self.event_publisher = event_publisher
        self.time_provider = time_provider

    async def __call__(self, tx_hash: str) -> None:
        """Execute the workflow to check and update transaction status."""
        logger.info("Watching status for transaction with hash: %s", tx_hash)

        transaction = await self.transaction_gateway.get_transaction_by_hash(tx_hash)
        if not transaction:
            raise TransactionNotFoundException

        if transaction.status != TransactionStatus.PENDING:
            logger.debug(
                "Transaction %s is already in status %s. Skipping.",
                tx_hash,
                transaction.status.value,
            )
            return

        receipt = await self.web3_provider.get_transaction_receipt(tx_hash)

        if receipt:
            if receipt.get("status") == 1:  # 1 = SUCCESS, 0 = FAILED
                logger.info("Transaction %s confirmed as SUCCESS.", tx_hash)
                gas_used = Decimal(str(receipt.get("gasUsed", 0)))
                gas_price_wei = Decimal(str(receipt.get("effectiveGasPrice", 0)))
                tx_fee_wei = gas_used * gas_price_wei
                tx_fee_eth = self.web3_provider.w3.from_wei(tx_fee_wei, "ether")

                transaction.mark_success(fee=TxFee(tx_fee_eth).value)

                wallet = await self.wallet_gateway.get_wallet_by_id(
                    transaction.wallet_id
                )
                if not wallet:
                    raise WalletNotFoundException

                new_balance = await self.web3_provider.get_balance(
                    EthereumAddress(wallet.address)
                )
                wallet.update_balance(new_balance, self.time_provider.now())

            else:
                logger.warning("Transaction %s failed on blockchain.", tx_hash)
                transaction.mark_failed()

            async with self.uow:
                updated_tx = await self.transaction_gateway.update_transaction(
                    transaction
                )
                updated_wallet = await self.wallet_gateway.update_wallet(wallet)

                await self.event_publisher.publish_transaction_status_updated(
                    user_id=wallet.user_id,
                    tx_id=updated_tx.id,
                    new_status=updated_tx.status.value,
                    tx_hash=updated_tx.tx_hash,
                )
                await self.event_publisher.publish_balance_updated(
                    user_id=wallet.user_id,
                    wallet_id=updated_wallet.id,
                    new_balance=updated_wallet.balance,
                )
        else:
            logger.debug("Transaction %s still pending or not found in block.", tx_hash)
