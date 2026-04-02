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
        """Execute transaction via RPC and save it to the database."""
        logger.info("Sending transaction request to worker for user: %s", user_id)

        wallet = await self.wallet_gateway.get_wallet_by_id(request.wallet_id)
        if not wallet or wallet.user_id != user_id:
            raise WalletNotFoundException

        tx_hash_from_worker = await self.worker_client.send_transaction(
            private_key_encrypted=wallet.encrypted_private_key.value,
            from_address=wallet.address.value,
            to_address=request.to_address,
            value_eth=str(request.value),
        )

        now = self.time_provider.get_current_time()

        tx = Transaction(
            id=self.id_generator.generate(),
            wallet_id=wallet.id,
            tx_hash=tx_hash_from_worker,
            from_address=wallet.address.value,
            to_address=request.to_address,
            value=Decimal(str(request.value)),
            tx_fee=Decimal("0"),
            status=TransactionStatus.PENDING,
            created_at=now,
        )

        async with self.uow:
            await self.transaction_gateway.add_transaction(tx)

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
    """Use case for retrieving transaction history from Etherscan and Local DB."""

    def __init__(
        self,
        wallet_gateway: WalletGateway,
        transaction_gateway: TransactionGateway,
        etherscan_provider: EtherscanProvider,
    ) -> None:
        """Initialize with required gateways and providers."""
        self.wallet_gateway = wallet_gateway
        self.transaction_gateway = transaction_gateway
        self.etherscan_provider = etherscan_provider

    async def __call__(self, wallet_id: uuid.UUID) -> list[dict[str, Any]]:
        """Retrieve and merge transactions from local database and Etherscan."""
        wallet = await self.wallet_gateway.get_wallet_by_id(wallet_id)
        if not wallet:
            raise WalletNotFoundException

        try:
            es_txs = await self.etherscan_provider.get_wallet_transactions(
                wallet.address
            )
        except Exception:  # noqa: BLE001
            es_txs = []

        db_txs = await self.transaction_gateway.get_transactions_by_wallet_id(wallet_id)

        merged_txs = {}
        for tx in es_txs:
            tx_hash = tx.get("hash", "").lower()
            merged_txs[tx_hash] = tx

        for tx in db_txs:
            tx_key = tx.tx_hash.lower() if tx.tx_hash else str(tx.id)
            if (
                tx_key not in merged_txs
                and (tx.tx_hash or "").lower() not in merged_txs
            ):
                merged_txs[tx_key] = {
                    "hash": tx.tx_hash or "Pending in queue...",
                    "from": tx.from_address,
                    "to": tx.to_address,
                    "value": str(tx.value),
                    "tx_fee": str(tx.tx_fee),
                    "status": tx.status.value.lower(),
                }

        return list(merged_txs.values())
