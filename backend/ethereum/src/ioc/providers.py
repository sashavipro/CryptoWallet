"""ethereum/src/ioc/providers.py."""

from collections.abc import AsyncIterable

from dishka import Provider
from dishka import Scope
from dishka import provide
from redis.asyncio import Redis

from src.application.interactors.faucet import RequestTestnetEthInteractor
from src.application.interactors.transaction import SendTransactionInteractor
from src.application.interactors.transaction_watcher import (
    BackgroundTransactionWatcherInteractor,
)
from src.application.interactors.transaction_watcher import (
    CheckTransactionStatusInteractor,
)
from src.application.interactors.wallet import CreateWalletInteractor
from src.application.interactors.wallet import GetBalanceInteractor
from src.application.interactors.wallet import ImportWalletInteractor
from src.application.ports.providers.faucet import FaucetProvider
from src.application.ports.providers.nonce_manager import NonceManager
from src.application.ports.providers.web3 import Web3Provider
from src.application.ports.publishers import EventPublisher
from src.application.ports.utils import Encryptor
from src.infrastructure.cache.redis_nonce_manager import RedisNonceManager
from src.infrastructure.message_broker.event_publisher import EventPublisherImpl
from src.infrastructure.providers.faucet import FaucetProviderImpl
from src.infrastructure.providers.web3 import Web3ProviderImpl
from src.infrastructure.settings import RabbitMQSettings
from src.infrastructure.settings import RedisSettings
from src.infrastructure.settings import SecuritySettings
from src.infrastructure.settings import Web3Settings
from src.infrastructure.settings import mq_settings
from src.infrastructure.settings import redis_settings
from src.infrastructure.settings import security_settings
from src.infrastructure.settings import web3_settings
from src.infrastructure.utils.aes_encryptor import AesEncryptor


class UtilsProvider(Provider):
    """DI provider for utility services like encryption."""

    scope = Scope.APP

    encryptor = provide(AesEncryptor, provides=Encryptor)


class InfrastructureProvider(Provider):
    """DI provider for infrastructure settings and external clients."""

    scope = Scope.APP

    @provide
    def provide_web3_settings(self) -> Web3Settings:
        """Provide Web3 connection settings."""
        return web3_settings

    @provide
    def provide_redis_settings(self) -> RedisSettings:
        """Provide Redis connection settings."""
        return redis_settings

    @provide
    def provide_security_settings(self) -> SecuritySettings:
        """Provide security and encryption settings."""
        return security_settings

    @provide
    def provide_rabbitmq_settings(self) -> RabbitMQSettings:
        """Provide RabbitMQ connection settings."""
        return mq_settings

    @provide
    async def provide_redis(self, settings: RedisSettings) -> AsyncIterable[Redis]:
        """Provide an asynchronous Redis client with automatic cleanup."""
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        yield client
        await client.aclose()

    web3_provider = provide(Web3ProviderImpl, provides=Web3Provider)
    faucet_provider = provide(FaucetProviderImpl, provides=FaucetProvider)
    nonce_manager = provide(RedisNonceManager, provides=NonceManager)
    event_publisher = provide(EventPublisherImpl, provides=EventPublisher)


class InteractorProvider(Provider):
    """DI provider for pure stateless application use cases."""

    scope = Scope.REQUEST

    create_wallet_interactor = provide(CreateWalletInteractor)
    get_balance_interactor = provide(GetBalanceInteractor)
    import_wallet_interactor = provide(ImportWalletInteractor)
    send_transaction_interactor = provide(SendTransactionInteractor)
    request_testnet_eth_interactor = provide(RequestTestnetEthInteractor)
    check_transaction_status_interactor = provide(CheckTransactionStatusInteractor)
    background_transaction_watcher_interactor = provide(
        BackgroundTransactionWatcherInteractor
    )
