"""rest_api/src/application/interactors/transaction.py."""

import logging
import uuid
from decimal import Decimal
from typing import Any

from src.application.dtos.request import CreatePendingTransactionRequest
from src.application.dtos.response import TransactionResponse
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
    ) -> None:
        """Initialize with required gateways and providers."""
        self.wallet_gateway = wallet_gateway
        self.transaction_gateway = transaction_gateway
        self.uow = uow
        self.id_generator = id_generator
        self.time_provider = time_provider
        self.worker_client = worker_client

    async def __call__(
        self, user_id: uuid.UUID, request: CreatePendingTransactionRequest
    ) -> TransactionResponse:
        """Execute the pending transaction creation process.

        Validates the wallet, creates a local pending transaction record,
        publishes an event to the worker to process the transaction, and
        returns the created transaction details.
        """
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

        await self.worker_client.publish_send_transaction_event(
            tx_id=str(tx_id),
            private_key_encrypted=wallet.private_key_encrypted,
            from_address=wallet.address,
            to_address=request.to_address,
            value_eth=str(request.value),
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


class GetTransactionsInteractor:
    """Use case for retrieving transaction history.

    Merges confirmed transactions from Etherscan with local PENDING txs,
    verifying live status via Web3 to eliminate Etherscan index delays.
    """

    def __init__(
        self,
        wallet_gateway: WalletGateway,
        transaction_gateway: TransactionGateway,
        etherscan_provider: EtherscanProvider,
        uow: UnitOfWork,
        worker_client: EthereumWorkerClient,
    ) -> None:
        """Initialize with required gateways and providers."""
        self.wallet_gateway = wallet_gateway
        self.transaction_gateway = transaction_gateway
        self.etherscan_provider = etherscan_provider
        self.uow = uow
        self.worker_client = worker_client

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

        local_txs = await self.transaction_gateway.get_transactions_by_wallet_id(
            wallet_id
        )

        confirmed_hashes = {tx["hash"].lower() for tx in etherscan_txs if "hash" in tx}

        pending_txs = []
        for tx in local_txs:
            if tx.tx_hash.lower() in confirmed_hashes:
                continue

            if tx.status == TransactionStatus.PENDING and tx.tx_hash.startswith("0x"):
                live_status = await self.worker_client.check_tx_status(tx.tx_hash)

                if live_status:
                    new_status_str = live_status.get("status", "FAILED")
                    tx.status = TransactionStatus(new_status_str)

                    if "tx_fee" in live_status:
                        tx.tx_fee = Decimal(live_status["tx_fee"])

                    async with self.uow:
                        await self.transaction_gateway.update_transaction(tx)

            pending_txs.append(
                {
                    "hash": tx.tx_hash,
                    "from": tx.from_address,
                    "to": tx.to_address,
                    "value": str(int(tx.value * Decimal("1e18"))),
                    "timeStamp": str(int(tx.created_at.timestamp())),
                    "status": tx.status.value.lower(),
                    "isError": "1" if tx.status == TransactionStatus.FAILED else "0",
                }
            )

        return pending_txs + etherscan_txs
