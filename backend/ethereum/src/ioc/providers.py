"""ethereum/src/ioc/providers.py."""

from collections.abc import AsyncIterable

from dishka import Provider
from dishka import Scope
from dishka import provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from src.application.interactors import CreatePendingTransactionInteractor
from src.application.interactors import CreateWalletInteractor
from src.application.interactors import DeleteWalletInteractor
from src.application.interactors import GetBalanceInteractor
from src.application.interactors import GetTransactionsInteractor
from src.application.interactors import GetWalletsInteractor
from src.application.interactors import ImportWalletInteractor
from src.application.interactors import RequestTestnetEthInteractor
from src.application.interactors import WatchTransactionStatusInteractor
from src.application.ports.events import EventPublisher
from src.application.ports.gateways import AssetGateway
from src.application.ports.gateways import TransactionGateway
from src.application.ports.gateways import UnitOfWork
from src.application.ports.gateways import WalletGateway
from src.application.ports.providers import BalanceCache
from src.application.ports.providers import EtherscanProvider
from src.application.ports.providers import FaucetProvider
from src.application.ports.providers import NonceManager
from src.application.ports.providers import Web3Provider
from src.application.ports.utils import Encryptor
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import TimeProvider
from src.infrastructure.cache import RedisBalanceCache
from src.infrastructure.cache import RedisNonceManager
from src.infrastructure.events import TaskiqEventPublisherImpl
from src.infrastructure.persistence.database.gateways import (
    AssetGateway as SqlaAssetGateway,
)
from src.infrastructure.persistence.database.gateways import SqlaUnitOfWork
from src.infrastructure.persistence.database.gateways import (
    TransactionGateway as SqlaTransactionGateway,
)
from src.infrastructure.persistence.database.gateways import (
    WalletGateway as SqlaWalletGateway,
)
from src.infrastructure.providers.etherscan import EtherscanProviderImpl
from src.infrastructure.providers.faucet import FaucetProviderImpl
from src.infrastructure.providers.jwt_provider import JwtProvider
from src.infrastructure.providers.web3 import Web3ProviderImpl
from src.infrastructure.settings import AuthSettings
from src.infrastructure.settings import DatabaseSettings
from src.infrastructure.settings import RabbitMQSettings
from src.infrastructure.settings import RedisSettings
from src.infrastructure.settings import SecuritySettings
from src.infrastructure.settings import Web3Settings
from src.infrastructure.settings import mq_settings
from src.infrastructure.settings import redis_settings
from src.infrastructure.settings import security_settings
from src.infrastructure.settings import settings
from src.infrastructure.settings import web3_settings
from src.infrastructure.utils import AesEncryptor
from src.infrastructure.utils import DatetimeGenerator
from src.infrastructure.utils import UuidGenerator


class UtilsProvider(Provider):
    """DI provider for utility services for the Ethereum microservice."""

    scope = Scope.APP

    id_generator = provide(UuidGenerator, provides=IdGenerator)
    time_provider = provide(DatetimeGenerator, provides=TimeProvider)

    @provide
    def provide_encryptor(self, settings: SecuritySettings) -> Encryptor:
        """Provide an instance of the AES Encryptor."""
        return AesEncryptor(settings)


class InfrastructureProvider(Provider):
    """DI provider for infrastructure and external integrations."""

    scope = Scope.APP

    @provide
    def provide_auth_settings(self) -> AuthSettings:
        """Provide the Auth settings for JWT."""
        return AuthSettings()

    @provide
    def provide_db_settings(self) -> DatabaseSettings:
        """Provide the database settings."""
        return settings

    @provide
    def provide_web3_settings(self) -> Web3Settings:
        """Provide the Web3 and blockchain settings."""
        return web3_settings

    @provide
    def provide_redis_settings(self) -> RedisSettings:
        """Provide the Redis cache settings."""
        return redis_settings

    @provide
    def provide_security_settings(self) -> SecuritySettings:
        """Provide the security settings for encryption."""
        return security_settings

    @provide
    def provide_rabbitmq_settings(self) -> RabbitMQSettings:
        """Provide the RabbitMQ message broker settings."""
        return mq_settings

    web3_provider = provide(Web3ProviderImpl, provides=Web3Provider)
    faucet_provider = provide(FaucetProviderImpl, provides=FaucetProvider)
    etherscan_provider = provide(EtherscanProviderImpl, provides=EtherscanProvider)

    nonce_manager = provide(RedisNonceManager, provides=NonceManager)
    balance_cache = provide(RedisBalanceCache, provides=BalanceCache)
    event_publisher = provide(TaskiqEventPublisherImpl, provides=EventPublisher)

    jwt_provider = provide(JwtProvider)

    @provide
    async def provide_redis(self, settings: RedisSettings) -> AsyncIterable[Redis]:
        """Provide an async Redis client instance."""
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        yield client
        await client.aclose()


class DbProvider(Provider):
    """DI provider for database and gateways for the Ethereum microservice."""

    scope = Scope.APP

    @provide
    def provide_engine(self, settings: DatabaseSettings) -> AsyncEngine:
        """Provide the SQLAlchemy asynchronous engine."""
        return create_async_engine(settings.database_url, echo=False)

    @provide
    def provide_sessionmaker(
        self, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        """Provide the SQLAlchemy asynchronous sessionmaker."""
        return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def provide_session(
        self, sessionmaker: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AsyncSession]:
        """Provide an asynchronous database session."""
        async with sessionmaker() as session:
            yield session

    wallet_gateway = provide(
        SqlaWalletGateway, scope=Scope.REQUEST, provides=WalletGateway
    )
    asset_gateway = provide(
        SqlaAssetGateway, scope=Scope.REQUEST, provides=AssetGateway
    )
    transaction_gateway = provide(
        SqlaTransactionGateway, scope=Scope.REQUEST, provides=TransactionGateway
    )
    uow = provide(SqlaUnitOfWork, scope=Scope.REQUEST, provides=UnitOfWork)


class InteractorProvider(Provider):
    """DI provider for application use cases for the Ethereum microservice."""

    scope = Scope.REQUEST

    create_wallet_interactor = provide(CreateWalletInteractor)
    import_wallet_interactor = provide(ImportWalletInteractor)
    delete_wallet_interactor = provide(DeleteWalletInteractor)
    get_wallets_interactor = provide(GetWalletsInteractor)
    get_balance_interactor = provide(GetBalanceInteractor)

    create_pending_transaction_interactor = provide(CreatePendingTransactionInteractor)
    get_transactions_interactor = provide(GetTransactionsInteractor)

    request_testnet_eth_interactor = provide(RequestTestnetEthInteractor)
    watch_transaction_status_interactor = provide(WatchTransactionStatusInteractor)
