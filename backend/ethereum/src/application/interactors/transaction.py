"""ethereum/src/application/interactors/transaction.py."""

import logging
import uuid
from decimal import Decimal
from typing import Any

from src.application.dtos.request import CreatePendingTransactionRequest
from src.application.dtos.response import TransactionResponse
from src.application.ports.events import EventPublisher
from src.application.ports.gateways.asset import AssetGateway
from src.application.ports.gateways.transaction import TransactionGateway
from src.application.ports.gateways.uow import UnitOfWork
from src.application.ports.gateways.wallet import WalletGateway
from src.application.ports.providers import NonceManager
from src.application.ports.providers import Web3Provider
from src.application.ports.providers.etherscan import EtherscanProvider
from src.application.ports.utils import Encryptor
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import TimeProvider
from src.domain.entities.transaction import Transaction
from src.domain.entities.transaction import TransactionStatus
from src.domain.exceptions import AssetNotFoundException
from src.domain.exceptions import InsufficientFundsException
from src.domain.exceptions import WalletNotFoundException
from src.domain.value_objects.shared import EthereumAddress
from src.domain.value_objects.transaction import TxHash
from src.domain.value_objects.transaction import TxValue
from src.domain.value_objects.wallet import EncryptedPrivateKey
from src.domain.value_objects.wallet import RawPrivateKey

logger = logging.getLogger(__name__)


class CreatePendingTransactionInteractor:
    """Use case for creating and sending a new blockchain transaction."""

    def __init__(  # noqa: PLR0913
        self,
        wallet_gateway: WalletGateway,
        asset_gateway: AssetGateway,
        transaction_gateway: TransactionGateway,
        uow: UnitOfWork,
        web3_provider: Web3Provider,
        encryptor: Encryptor,
        nonce_manager: NonceManager,
        event_publisher: EventPublisher,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
    ) -> None:
        """Initialize with required ports."""
        self.wallet_gateway = wallet_gateway
        self.asset_gateway = asset_gateway
        self.transaction_gateway = transaction_gateway
        self.uow = uow
        self.web3_provider = web3_provider
        self.encryptor = encryptor
        self.nonce_manager = nonce_manager
        self.event_publisher = event_publisher
        self.id_generator = id_generator
        self.time_provider = time_provider

    async def __call__(
        self, request: CreatePendingTransactionRequest
    ) -> TransactionResponse:
        """Execute the transaction creation and sending workflow."""
        logger.info(
            "Attempting to create transaction from wallet %s to %s for %s",
            request.wallet_id,
            request.to_address,
            request.value,
        )

        wallet = await self.wallet_gateway.get_wallet_by_id(request.wallet_id)
        if not wallet:
            raise WalletNotFoundException

        asset = await self.asset_gateway.get_asset_by_id(wallet.asset_id)
        if not asset:
            raise AssetNotFoundException

        to_address = EthereumAddress(request.to_address)
        tx_value = TxValue(request.value)

        current_wallet_balance = await self.web3_provider.get_balance(
            EthereumAddress(wallet.address)
        )
        if current_wallet_balance < tx_value.value:
            raise InsufficientFundsException

        encrypted_key = EncryptedPrivateKey(wallet.private_key_encrypted)
        raw_private_key_value = self.encryptor.decrypt(encrypted_key.value)
        raw_private_key = RawPrivateKey(raw_private_key_value)

        nonce = await self.nonce_manager.get_and_increment_nonce(wallet.address)

        tx_hash_str = await self.web3_provider.send_transaction(
            raw_private_key=raw_private_key.value,
            from_address=EthereumAddress(wallet.address),
            to_address=to_address,
            value=tx_value.value,
            nonce=nonce,
        )

        tx_hash_vo = TxHash(tx_hash_str)

        transaction = Transaction(
            id=self.id_generator.generate(),
            wallet_id=wallet.id,
            tx_hash=tx_hash_vo.value,
            from_address=wallet.address,
            to_address=to_address.value,
            value=tx_value.value,
            status=TransactionStatus.PENDING,
            created_at=self.time_provider.now(),
            tx_fee=Decimal("0.0"),
        )

        async with self.uow:
            saved_tx = await self.transaction_gateway.add_transaction(transaction)

            await self.event_publisher.publish_transaction_status_updated(
                user_id=wallet.user_id,
                tx_id=saved_tx.id,
                new_status=saved_tx.status.value,
                tx_hash=saved_tx.tx_hash,
            )

        logger.info(
            "Pending transaction created: %s. Hash: %s", saved_tx.id, saved_tx.tx_hash
        )

        return TransactionResponse(
            id=saved_tx.id,
            wallet_id=saved_tx.wallet_id,
            tx_hash=saved_tx.tx_hash,
            from_address=saved_tx.from_address,
            to_address=saved_tx.to_address,
            value=saved_tx.value,
            tx_fee=saved_tx.tx_fee,
            status=saved_tx.status.value,
            created_at=saved_tx.created_at,
        )


class GetTransactionsInteractor:
    """Use case for retrieving transaction history from Etherscan and Local DB."""

    def __init__(
        self,
        wallet_gateway: WalletGateway,
        transaction_gateway: TransactionGateway,
        etherscan_provider: EtherscanProvider,
    ) -> None:
        """Initialize the interactor with gateways and providers."""
        self.wallet_gateway = wallet_gateway
        self.transaction_gateway = transaction_gateway
        self.etherscan_provider = etherscan_provider

    async def __call__(self, wallet_id: uuid.UUID) -> list[dict[str, Any]]:
        """Execute the use case to retrieve wallet transactions."""
        logger.info("Retrieving transactions for wallet: %s", wallet_id)

        wallet = await self.wallet_gateway.get_wallet_by_id(wallet_id)
        if not wallet:
            raise WalletNotFoundException

        try:
            es_txs = await self.etherscan_provider.get_wallet_transactions(
                wallet.address
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Failed to fetch from Etherscan for wallet %s: %s",
                wallet_id,
                e,
            )
            es_txs = []

        db_txs = await self.transaction_gateway.get_transactions_by_wallet_id(wallet_id)

        merged_txs = {}

        for tx in es_txs:
            tx_hash = tx.get("hash", "").lower()
            merged_txs[tx_hash] = tx

        for tx in db_txs:
            tx_hash = tx.tx_hash.lower()
            if tx_hash not in merged_txs:
                merged_txs[tx_hash] = {
                    "hash": tx.tx_hash,
                    "from": tx.from_address,
                    "to": tx.to_address,
                    "value": str(tx.value),
                    "tx_fee": str(tx.tx_fee),
                    "status": tx.status.value.lower(),
                    "gasUsed": None,
                }

        return list(merged_txs.values())
