"""ethereum/src/application/interactors/faucet.py."""

import logging
import uuid
from decimal import Decimal

from src.application.dtos.response import TransactionResponse
from src.application.ports.events import EventPublisher
from src.application.ports.gateways import AssetGateway
from src.application.ports.gateways import TransactionGateway
from src.application.ports.gateways import UnitOfWork
from src.application.ports.gateways import WalletGateway
from src.application.ports.providers import FaucetProvider
from src.application.ports.providers import Web3Provider
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import TimeProvider
from src.domain.entities.asset import AssetType
from src.domain.entities.transaction import Transaction
from src.domain.entities.transaction import TransactionStatus
from src.domain.exceptions import AssetNotFoundException
from src.domain.exceptions import WalletNotFoundException
from src.domain.value_objects.shared import EthereumAddress
from src.domain.value_objects.transaction import TxHash
from src.domain.value_objects.transaction import TxValue

logger = logging.getLogger(__name__)


class RequestTestnetEthInteractor:
    """Use case for requesting testnet ETH from the faucet."""

    def __init__(  # noqa: PLR0913
        self,
        wallet_gateway: WalletGateway,
        asset_gateway: AssetGateway,
        transaction_gateway: TransactionGateway,
        uow: UnitOfWork,
        web3_provider: Web3Provider,
        faucet_provider: FaucetProvider,
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
        self.faucet_provider = faucet_provider
        self.event_publisher = event_publisher
        self.id_generator = id_generator
        self.time_provider = time_provider

    async def __call__(self, wallet_id: uuid.UUID) -> TransactionResponse:
        """Execute the faucet request workflow."""
        logger.info("User requested testnet ETH for wallet: %s", wallet_id)

        wallet = await self.wallet_gateway.get_wallet_by_id(wallet_id)
        if not wallet:
            raise WalletNotFoundException

        asset = await self.asset_gateway.get_asset_by_id(wallet.asset_id)
        if not asset or asset.asset_type != AssetType.NATIVE:
            raise AssetNotFoundException

        tx_hash_str = await self.faucet_provider.request_testnet_eth(
            to_address=EthereumAddress(wallet.address)
        )

        tx_hash_vo = TxHash(tx_hash_str)

        faucet_amount = Decimal(str(self.faucet_provider.settings.FAUCET_AMOUNT_ETH))

        transaction = Transaction(
            id=self.id_generator.generate(),
            wallet_id=wallet.id,
            tx_hash=tx_hash_vo.value,
            from_address=self.faucet_provider.settings.FAUCET_MASTER_ADDRESS,
            to_address=wallet.address,
            value=TxValue(faucet_amount).value,
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
            "Faucet request successful for wallet %s. Tx Hash: %s",
            wallet_id,
            saved_tx.tx_hash,
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
