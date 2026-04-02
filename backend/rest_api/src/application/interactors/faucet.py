"""rest_api/src/application/interactors/faucet.py."""

import logging
import uuid
from decimal import Decimal

from src.application.dtos.response.transaction import TransactionResponse
from src.application.ports.gateways.transaction import TransactionGateway
from src.application.ports.gateways.uow import UnitOfWork
from src.application.ports.gateways.wallet import WalletGateway
from src.application.ports.providers.worker_client import EthereumWorkerClient
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import TimeProvider
from src.domain.entities.transaction import Transaction
from src.domain.entities.transaction import TransactionStatus
from src.domain.exceptions import WalletNotFoundException

logger = logging.getLogger(__name__)


class RequestTestnetEthInteractor:
    """Use case for requesting testnet ETH via RabbitMQ and saving it."""

    def __init__(  # noqa: PLR0913
        self,
        wallet_gateway: WalletGateway,
        transaction_gateway: TransactionGateway,
        uow: UnitOfWork,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
        worker_client: EthereumWorkerClient,
    ) -> None:
        """Initialize the interactor with necessary gateways and providers."""
        self.wallet_gateway = wallet_gateway
        self.transaction_gateway = transaction_gateway
        self.uow = uow
        self.id_generator = id_generator
        self.time_provider = time_provider
        self.worker_client = worker_client

    async def __call__(self, wallet_id: uuid.UUID) -> TransactionResponse:
        """Request faucet ETH for the specified wallet and save the transaction."""
        logger.info("Requesting faucet ETH for wallet: %s", wallet_id)

        wallet = await self.wallet_gateway.get_wallet_by_id(wallet_id)
        if not wallet:
            raise WalletNotFoundException

        tx_hash = await self.worker_client.request_faucet(address=wallet.address.value)

        now = self.time_provider.now()
        tx = Transaction(
            id=self.id_generator.generate(),
            wallet_id=wallet.id,
            tx_hash=tx_hash,
            from_address="0xFaucetMasterAddress0000000000000000000",  # Заглушка
            to_address=wallet.address.value,
            value=Decimal("0.001"),  # Сумма из фаусета
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
