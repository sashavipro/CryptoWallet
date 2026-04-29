"""rest_api/src/application/interactors/transaction.py."""

import asyncio
import datetime
import logging
import uuid
from decimal import Decimal
from typing import Any

from src.application.dtos.request import CreatePendingTransactionRequest
from src.application.dtos.response import TransactionResponse
from src.application.ports.events import EventPublisher
from src.application.ports.gateways.transaction import TransactionGateway
from src.application.ports.gateways.uow import UnitOfWork
from src.application.ports.gateways.wallet import WalletGateway
from src.application.ports.providers.etherscan import EtherscanProvider
from src.application.ports.providers.worker_client import EthereumWorkerClient
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import TimeProvider
from src.domain.entities.transaction import Transaction
from src.domain.entities.transaction import TransactionStatus
from src.domain.exceptions import WalletNotFoundException

logger = logging.getLogger(__name__)


class CreatePendingTransactionInteractor:
    """Use case for executing transaction via RPC and saving as PENDING."""

    def __init__(  # noqa: PLR0913
        self,
        wallet_gateway: WalletGateway,
        transaction_gateway: TransactionGateway,
        uow: UnitOfWork,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
        worker_client: EthereumWorkerClient,
        event_publisher: EventPublisher,
    ) -> None:
        """Initialize with required gateways and providers."""
        self.wallet_gateway = wallet_gateway
        self.transaction_gateway = transaction_gateway
        self.uow = uow
        self.id_generator = id_generator
        self.time_provider = time_provider
        self.worker_client = worker_client
        self.event_publisher = event_publisher

    async def __call__(
        self, user_id: uuid.UUID, request: CreatePendingTransactionRequest
    ) -> TransactionResponse:
        """Execute the pending transaction creation process."""
        logger.info("Initiating async transaction for user: %s", user_id)

        wallet = await self.wallet_gateway.get_wallet_by_id(request.wallet_id)
        if not wallet or wallet.user_id != user_id:
            raise WalletNotFoundException

        now = self.time_provider.now()
        tx_id = self.id_generator.generate()

        tx = Transaction(
            id=tx_id,
            wallet_id=wallet.id,
            tx_hash=f"pending_{tx_id}",
            from_address=wallet.address,
            to_address=request.to_address,
            value=Decimal(str(request.value)),
            tx_fee=Decimal("0"),
            status=TransactionStatus.PENDING,
            created_at=now,
        )

        async with self.uow:
            await self.transaction_gateway.add_transaction(tx)

            affected_wallets = await self.wallet_gateway.get_wallets_by_addresses(
                [tx.from_address, tx.to_address]
            )

        await self.worker_client.publish_send_transaction_event(
            tx_id=str(tx_id),
            private_key_encrypted=wallet.private_key_encrypted,
            from_address=wallet.address,
            to_address=request.to_address,
            value_eth=str(request.value),
        )

        for w in affected_wallets:
            await self.event_publisher.publish_tx_status_updated(
                user_id=str(w.user_id),
                wallet_id=str(w.id),
                tx_hash=tx.tx_hash,
                status=tx.status.value.lower(),
                value=str(tx.value),
            )

        return TransactionResponse(
            id=tx.id,
            wallet_id=tx.wallet_id,
            tx_hash=tx.tx_hash,
            from_address=tx.from_address,
            to_address=tx.to_address,
            value=tx.value,
            tx_fee=tx.tx_fee,
            status=tx.status.value,
            created_at=tx.created_at,
        )


class ProcessTransactionCallbackInteractor:
    """Use case for handling background transaction status updates from the worker."""

    def __init__(
        self,
        transaction_gateway: TransactionGateway,
        wallet_gateway: WalletGateway,
        uow: UnitOfWork,
        worker_client: EthereumWorkerClient,
        event_publisher: EventPublisher,
    ) -> None:
        """Initialize the callback interactor with required dependencies."""
        self.tx_gateway = transaction_gateway
        self.wallet_gateway = wallet_gateway
        self.uow = uow
        self.worker_client = worker_client
        self.event_publisher = event_publisher

    async def __call__(
        self,
        status: str,
        tx_id: uuid.UUID | None = None,
        tx_hash: str | None = None,
        error: str | None = None,
    ) -> None:
        """Process the status update from the worker and update local state."""
        async with self.uow:
            tx = None
            if tx_id:
                tx = await self.tx_gateway.get_transaction_by_id(tx_id)
            elif tx_hash:
                tx = await self.tx_gateway.get_transaction_by_hash(tx_hash)

            if not tx:
                return

            tx.status = TransactionStatus(status.upper())
            if tx_hash:
                tx.tx_hash = tx_hash

            await self.tx_gateway.update_transaction(tx)

            affected_wallets = await self.wallet_gateway.get_wallets_by_addresses(
                [tx.from_address, tx.to_address]
            )

        for w in affected_wallets:
            await self.event_publisher.publish_tx_status_updated(
                user_id=str(w.user_id),
                wallet_id=str(w.id),
                tx_hash=tx.tx_hash,
                status=status,
                value=str(tx.value),
                error=error,
            )

        if status in ["success", "failed"]:
            await asyncio.sleep(3)
            try:
                async with self.uow:
                    for w in affected_wallets:
                        fresh_wallet = await self.wallet_gateway.get_wallet_by_id(w.id)
                        if fresh_wallet:
                            live_balance = await self.worker_client.get_balance(
                                w.address
                            )
                            fresh_wallet.balance = Decimal(str(live_balance))
                            fresh_wallet.balance_updated_at = datetime.datetime.now(
                                datetime.UTC
                            )
                            await self.wallet_gateway.update_wallet(fresh_wallet)

                            await self.event_publisher.publish_balance_updated(
                                user_id=str(w.user_id),
                                wallet_id=str(w.id),
                                balance=live_balance,
                            )
            except Exception:
                logger.exception("Failed to update balance after tx finish")


class GetTransactionsInteractor:
    """Use case for retrieving transaction history."""

    def __init__(  # noqa: PLR0913
        self,
        wallet_gateway: WalletGateway,
        transaction_gateway: TransactionGateway,
        etherscan_provider: EtherscanProvider,
        uow: UnitOfWork,
        worker_client: EthereumWorkerClient,
        process_callback: ProcessTransactionCallbackInteractor,
    ) -> None:
        """Initialize with required gateways and providers."""
        self.wallet_gateway = wallet_gateway
        self.transaction_gateway = transaction_gateway
        self.etherscan_provider = etherscan_provider
        self.uow = uow
        self.worker_client = worker_client
        self.process_callback = process_callback

    def _format_tx(self, tx: Transaction) -> dict[str, Any]:
        """Format a local Transaction entity into a JSON-ready dictionary."""
        return {
            "hash": tx.tx_hash,
            "from": tx.from_address,
            "to": tx.to_address,
            "value": str(int(tx.value * Decimal("1e18"))),
            "timeStamp": str(int(tx.created_at.timestamp())),
            "status": tx.status.value.lower(),
            "tx_fee": str(tx.tx_fee),
            "isError": "1" if tx.status == TransactionStatus.FAILED else "0",
        }

    async def _check_and_update_pending_tx(
        self, tx: Transaction, pending_txs: list[dict[str, Any]]
    ) -> None:
        """Check live status of pending transactions and update the list."""
        try:
            live_status = await self.worker_client.check_tx_status(tx.tx_hash)
            if live_status:
                new_status_str = live_status.get("status", "FAILED").lower()
                await self.process_callback(tx_id=tx.id, status=new_status_str)
                tx.status = TransactionStatus(new_status_str.upper())
                if "tx_fee" in live_status:
                    tx.tx_fee = Decimal(live_status["tx_fee"])
        except Exception as e:  # noqa: BLE001
            logger.warning("Error checking live status for %s: %s", tx.tx_hash, e)

        pending_txs.append(self._format_tx(tx))

    async def __call__(
        self, user_id: uuid.UUID, wallet_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        """Fetch history and verify pending txs via Web3."""
        logger.info("Fetching history for wallet %s", wallet_id)

        wallet = await self.wallet_gateway.get_wallet_by_id(wallet_id)
        if not wallet or wallet.user_id != user_id:
            raise WalletNotFoundException

        etherscan_txs = []
        try:
            etherscan_txs = await self.etherscan_provider.get_wallet_transactions(
                wallet.address
            )
        except Exception:
            logger.exception("Etherscan unreachable")

        local_txs = await self.transaction_gateway.get_transactions_by_address(
            wallet.address
        )

        confirmed_hashes = {tx["hash"].lower() for tx in etherscan_txs if "hash" in tx}
        pending_txs: list[dict[str, Any]] = []
        tasks = []

        for tx in local_txs:
            if tx.tx_hash.lower() in confirmed_hashes:
                continue

            if tx.status == TransactionStatus.PENDING and tx.tx_hash.startswith("0x"):
                tasks.append(self._check_and_update_pending_tx(tx, pending_txs))
            else:
                pending_txs.append(self._format_tx(tx))

        if tasks:
            await asyncio.gather(*tasks)

        return pending_txs + etherscan_txs


class ProcessDiscoveredTransactionInteractor:
    """Processing a transaction found by the block scanner."""

    def __init__(  # noqa: PLR0913
        self,
        wallet_gateway: WalletGateway,
        tx_gateway: TransactionGateway,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
    ) -> None:
        """Initialize the interactor with required gateways and utilities."""
        self.wallet_gateway = wallet_gateway
        self.tx_gateway = tx_gateway
        self.uow = uow
        self.event_publisher = event_publisher
        self.id_generator = id_generator
        self.time_provider = time_provider

    async def __call__(
        self,
        tx_hash: str,
        from_address: str,
        to_address: str,
        value: Decimal,
        fee: Decimal,
    ) -> None:
        """Execute the use case to process a newly discovered transaction."""
        async with self.uow:
            existing_tx = await self.tx_gateway.get_transaction_by_hash(tx_hash)
            if existing_tx:
                return

            wallets = await self.wallet_gateway.get_wallets_by_addresses(
                [from_address, to_address]
            )
            if not wallets:
                return

            for wallet in wallets:
                new_tx = Transaction(
                    id=self.id_generator.generate(),
                    wallet_id=wallet.id,
                    tx_hash=tx_hash,
                    from_address=from_address,
                    to_address=to_address,
                    value=value,
                    tx_fee=fee,
                    status=TransactionStatus.SUCCESS,
                    created_at=self.time_provider.now(),
                )
                await self.tx_gateway.add_transaction(new_tx)

                if to_address == wallet.address.lower():
                    wallet.balance += value
                elif from_address == wallet.address.lower():
                    wallet.balance -= value + fee

                await self.wallet_gateway.update_wallet(wallet)

                await self.event_publisher.publish_tx_status_updated(
                    user_id=str(wallet.user_id),
                    wallet_id=str(wallet.id),
                    tx_hash=tx_hash,
                    status="success",
                    value=str(value),
                )

                await self.event_publisher.publish_balance_updated(
                    user_id=str(wallet.user_id),
                    wallet_id=str(wallet.id),
                    balance=str(wallet.balance),
                )
