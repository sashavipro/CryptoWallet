"""rest_api/src/ioc/providers.py."""

from collections.abc import AsyncIterable
from pathlib import Path

from dishka import Provider
from dishka import Scope
from dishka import provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from starlette.templating import Jinja2Templates

from src.application.interactors import ChangePasswordInteractor
from src.application.interactors import CreatePendingTransactionInteractor
from src.application.interactors import CreateWalletInteractor
from src.application.interactors import DeleteAvatarInteractor
from src.application.interactors import DeleteWalletInteractor
from src.application.interactors import GenerateAvatarUploadUrlInteractor
from src.application.interactors import GetAssetsInteractor
from src.application.interactors import GetBalanceInteractor
from src.application.interactors import GetOtherProfileInteractor
from src.application.interactors import GetStatsInteractor
from src.application.interactors import GetTransactionsInteractor
from src.application.interactors import GetUserInteractor
from src.application.interactors import GetWalletsInteractor
from src.application.interactors import ImportWalletInteractor
from src.application.interactors import IncrementTotalMessagesInteractor
from src.application.interactors import LoginUserInteractor
from src.application.interactors import RegisterUserInteractor
from src.application.interactors import RequestTestnetEthInteractor
from src.application.interactors import UpdateUserInteractor
from src.application.ports.events import EventPublisher
from src.application.ports.gateways import AssetGateway
from src.application.ports.gateways import PermissionGateway
from src.application.ports.gateways import StatsGateway
from src.application.ports.gateways import TransactionGateway
from src.application.ports.gateways import UnitOfWork
from src.application.ports.gateways import UserGateway
from src.application.ports.gateways import WalletGateway
from src.application.ports.providers import EthereumWorkerClient
from src.application.ports.providers import EtherscanProvider
from src.application.ports.providers import FileUploader
from src.application.ports.providers import JwtProvider as JwtProviderPort
from src.application.ports.providers import MailProvider
from src.application.ports.utils import Encryptor
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import PasswordHasher
from src.application.ports.utils import TimeProvider
from src.infrastructure.cache import CachedUserGateway
from src.infrastructure.cache import RedisRateLimiter
from src.infrastructure.cache import RedisStatsGateway
from src.infrastructure.message_broker.broker import broker
from src.infrastructure.message_broker.event_publisher import EventPublisherImpl
from src.infrastructure.persistence.database.gateways import (
    AssetGateway as SqlaAssetGateway,
)
from src.infrastructure.persistence.database.gateways import (
    PermissionGateway as SqlaPermissionGateway,
)
from src.infrastructure.persistence.database.gateways import SqlaUnitOfWork
from src.infrastructure.persistence.database.gateways import (
    TransactionGateway as SqlaTransactionGateway,
)
from src.infrastructure.persistence.database.gateways import (
    UserGateway as SqlaUserGateway,
)
from src.infrastructure.persistence.database.gateways import (
    WalletGateway as SqlaWalletGateway,
)
from src.infrastructure.providers import DOSpacesUploader
from src.infrastructure.providers import EthereumWorkerClientImpl
from src.infrastructure.providers import EtherscanProviderImpl
from src.infrastructure.providers import JwtProvider
from src.infrastructure.providers import MailjetProvider
from src.infrastructure.settings import AuthSettings
from src.infrastructure.settings import DatabaseSettings
from src.infrastructure.settings import FaucetSettings
from src.infrastructure.settings import MailSettings
from src.infrastructure.settings import RedisSettings
from src.infrastructure.settings import S3Settings
from src.infrastructure.settings import SecuritySettings
from src.infrastructure.settings import Web3Settings
from src.infrastructure.settings import auth_settings
from src.infrastructure.settings import db_settings
from src.infrastructure.settings import faucet_settings
from src.infrastructure.settings import mail_settings
from src.infrastructure.settings import redis_settings
from src.infrastructure.settings import s3_settings
from src.infrastructure.settings import security_settings
from src.infrastructure.settings import web3_settings
from src.infrastructure.utils import AesEncryptor
from src.infrastructure.utils import DatetimeGenerator
from src.infrastructure.utils import PwdlibHasher
from src.infrastructure.utils import UuidGenerator


class UtilsProvider(Provider):
    """DI provider for utility services."""

    scope = Scope.APP

    password_hasher = provide(PwdlibHasher, provides=PasswordHasher)
    id_generator = provide(UuidGenerator, provides=IdGenerator)
    time_provider = provide(DatetimeGenerator, provides=TimeProvider)
    encryptor = provide(AesEncryptor, provides=Encryptor)


class InfrastructureProvider(Provider):
    """DI provider for infrastructure and external integrations."""

    scope = Scope.APP

    @provide
    def provide_auth_settings(self) -> AuthSettings:
        """Provide authentication settings."""
        return auth_settings

    @provide
    def provide_mail_settings(self) -> MailSettings:
        """Provide Mailjet and email settings."""
        return mail_settings

    @provide
    def provide_s3_settings(self) -> S3Settings:
        """Provide S3 and file storage settings."""
        return s3_settings

    @provide
    def provide_redis_settings(self) -> RedisSettings:
        """Provide Redis connection settings."""
        return redis_settings

    @provide
    def provide_security_settings(self) -> SecuritySettings:
        """Provide security and encryption settings."""
        return security_settings

    @provide
    def provide_templates(self) -> Jinja2Templates:
        """Provide Jinja2 templates for Server-Side Rendering."""
        project_root = Path(__file__).resolve().parents[4]
        templates_dir = project_root / "frontend" / "templates"
        return Jinja2Templates(directory=str(templates_dir))

    @provide
    def provide_worker_client(self) -> EthereumWorkerClient:
        """Provide the Ethereum worker client implementation."""
        return EthereumWorkerClientImpl(broker)

    @provide
    def provide_web3_settings(self) -> Web3Settings:
        """Provide Web3 connection settings."""
        return web3_settings

    @provide
    def provide_faucet_settings(self) -> FaucetSettings:
        """Provide faucet rate limit settings."""
        return faucet_settings

    jwt_provider = provide(JwtProvider, provides=JwtProviderPort)
    mail_provider = provide(MailjetProvider, provides=MailProvider)
    file_uploader = provide(DOSpacesUploader, provides=FileUploader)
    etherscan_provider = provide(EtherscanProviderImpl, provides=EtherscanProvider)

    stats_gateway = provide(
        RedisStatsGateway, scope=Scope.REQUEST, provides=StatsGateway
    )
    event_publisher = provide(EventPublisherImpl, provides=EventPublisher)

    @provide
    async def provide_redis(self, settings: RedisSettings) -> AsyncIterable[Redis]:
        """Provide a Redis client instance, injecting RedisSettings."""
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        yield client
        await client.aclose()

    @provide
    def provide_rate_limiter(self, redis_client: Redis) -> RedisRateLimiter:
        """Provide the Redis-based rate limiter."""
        return RedisRateLimiter(
            redis_client=redis_client,
            max_requests=5,
            window_seconds=60,
            ban_seconds=300,
        )


class DbProvider(Provider):
    """DI provider for database and gateways."""

    scope = Scope.APP

    @provide
    def provide_db_settings(self) -> DatabaseSettings:
        """Provide database connection settings."""
        return db_settings

    @provide
    def provide_engine(self, settings: DatabaseSettings) -> AsyncEngine:
        """Provide the SQLAlchemy async engine, injecting DatabaseSettings."""
        return create_async_engine(
            settings.database_url,
            echo=False,
            pool_size=20,
            max_overflow=30,
            pool_timeout=30.0,
        )

    @provide
    def provide_sessionmaker(
        self, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        """Provide the SQLAlchemy async sessionmaker."""
        return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def provide_session(
        self, sessionmaker: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AsyncSession]:
        """Provide a database session scoped to the current request."""
        async with sessionmaker() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def provide_cached_user_gateway(
        self, db_gateway: SqlaUserGateway, redis: Redis
    ) -> UserGateway:
        """Convert the database gateway to a Redis cache."""
        return CachedUserGateway(db_gateway=db_gateway, redis_client=redis)

    permission_gateway = provide(
        SqlaPermissionGateway, scope=Scope.REQUEST, provides=PermissionGateway
    )
    uow = provide(SqlaUnitOfWork, scope=Scope.REQUEST, provides=UnitOfWork)
    sqla_user_gateway = provide(SqlaUserGateway, scope=Scope.REQUEST)
    asset_gateway = provide(
        SqlaAssetGateway, scope=Scope.REQUEST, provides=AssetGateway
    )
    tx_gateway = provide(
        SqlaTransactionGateway, scope=Scope.REQUEST, provides=TransactionGateway
    )
    wallet_gateway = provide(
        SqlaWalletGateway, scope=Scope.REQUEST, provides=WalletGateway
    )


class InteractorProvider(Provider):
    """DI provider for application use cases."""

    scope = Scope.REQUEST

    # Auth
    login_interactor = provide(LoginUserInteractor)
    register_interactor = provide(RegisterUserInteractor)

    # Profile
    get_user_interactor = provide(GetUserInteractor)
    update_user_interactor = provide(UpdateUserInteractor)
    get_other_profile_interactor = provide(GetOtherProfileInteractor)
    delete_avatar_interactor = provide(DeleteAvatarInteractor)
    change_password_interactor = provide(ChangePasswordInteractor)
    generate_avatar_upload_url_interactor = provide(GenerateAvatarUploadUrlInteractor)

    # Stats
    get_stats_interactor = provide(GetStatsInteractor)
    increment_messages_interactor = provide(IncrementTotalMessagesInteractor)

    # Wallets
    create_wallet_interactor = provide(CreateWalletInteractor)
    get_wallets_interactor = provide(GetWalletsInteractor)
    get_balance_interactor = provide(GetBalanceInteractor)
    delete_wallet_interactor = provide(DeleteWalletInteractor)
    import_wallet_interactor = provide(ImportWalletInteractor)

    # Transactions
    create_transaction_interactor = provide(CreatePendingTransactionInteractor)
    get_transactions_interactor = provide(GetTransactionsInteractor)

    # Faucet
    request_faucet_interactor = provide(RequestTestnetEthInteractor)

    # Assets
    get_assets_interactor = provide(GetAssetsInteractor)
