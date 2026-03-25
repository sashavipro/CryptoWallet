"""rest_api/src/ioc/providers.py."""

from collections.abc import AsyncIterable

from dishka import Provider
from dishka import Scope
from dishka import provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from src.application.interactors.login import LoginUserInteractor
from src.application.interactors.profile import ChangePasswordInteractor
from src.application.interactors.profile import DeleteAvatarInteractor
from src.application.interactors.profile import GenerateAvatarUploadUrlInteractor
from src.application.interactors.profile import GetOtherProfileInteractor
from src.application.interactors.profile import GetUserInteractor
from src.application.interactors.profile import UpdateUserInteractor
from src.application.interactors.register import RegisterUserInteractor
from src.application.interactors.stats import GetStatsInteractor
from src.application.interactors.stats import IncrementTotalMessagesInteractor
from src.application.ports.events import EventPublisher
from src.application.ports.gateways import PermissionGateway
from src.application.ports.gateways import UnitOfWork
from src.application.ports.gateways import UserGateway
from src.application.ports.gateways.stats import StatsGateway
from src.application.ports.providers import JwtProvider as JwtProviderPort
from src.application.ports.providers.file_provider import FileUploader
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import PasswordHasher
from src.application.ports.utils import TimeProvider
from src.infrastructure.cache.rate_limiter import RedisRateLimiter
from src.infrastructure.cache.stats import RedisStatsGateway
from src.infrastructure.events.taskiq_publisher import TaskiqEventPublisher
from src.infrastructure.persistence.database.gateways import (
    PermissionGateway as SqlaPermissionGateway,
)
from src.infrastructure.persistence.database.gateways import SqlaUnitOfWork
from src.infrastructure.persistence.database.gateways import (
    UserGateway as SqlaUserGateway,
)
from src.infrastructure.providers.jwt_provider import JwtProvider as JwtProviderImpl
from src.infrastructure.providers.s3_file_uploader import S3FileUploader
from src.infrastructure.settings import redis_settings
from src.infrastructure.settings import settings
from src.infrastructure.utils.datetime_generator import DatetimeGenerator
from src.infrastructure.utils.pwdlib_hasher import PwdlibHasher
from src.infrastructure.utils.uuid_generator import UuidGenerator


class UtilsProvider(Provider):
    """DI provider for utility services."""

    password_hasher = provide(PwdlibHasher, scope=Scope.APP, provides=PasswordHasher)
    id_generator = provide(UuidGenerator, scope=Scope.APP, provides=IdGenerator)
    time_provider = provide(DatetimeGenerator, scope=Scope.APP, provides=TimeProvider)


class InfrastructureProvider(Provider):
    """DI provider for infrastructure and external integrations."""

    jwt_provider = provide(JwtProviderImpl, scope=Scope.APP, provides=JwtProviderPort)
    event_publisher = provide(
        TaskiqEventPublisher, scope=Scope.APP, provides=EventPublisher
    )
    stats_gateway = provide(
        RedisStatsGateway, scope=Scope.REQUEST, provides=StatsGateway
    )

    @provide(scope=Scope.APP)
    async def provide_redis(self) -> AsyncIterable[Redis]:
        """Provide a Redis client instance."""
        client = Redis.from_url(redis_settings.REDIS_URL, decode_responses=True)
        yield client
        await client.aclose()

    @provide(scope=Scope.APP)
    def provide_rate_limiter(self, redis_client: Redis) -> RedisRateLimiter:
        """Provide the Redis-based rate limiter.

        Using stricter rules for auth endpoints
        (e.g., 5 requests per minute, ban for 5 min).
        """
        return RedisRateLimiter(
            redis_client=redis_client,
            max_requests=5,
            window_seconds=60,
            ban_seconds=300,
        )

    @provide(scope=Scope.APP)
    def provide_file_uploader(self) -> FileUploader:
        """Provide S3 file uploader implementation."""
        return S3FileUploader()


class DbProvider(Provider):
    """DI provider for database and gateways."""

    @provide(scope=Scope.APP)
    def provide_engine(self) -> AsyncEngine:
        """Provide the SQLAlchemy async engine."""
        return create_async_engine(settings.database_url, echo=False)

    @provide(scope=Scope.APP)
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

    user_gateway = provide(SqlaUserGateway, scope=Scope.REQUEST, provides=UserGateway)
    permission_gateway = provide(
        SqlaPermissionGateway, scope=Scope.REQUEST, provides=PermissionGateway
    )
    uow = provide(SqlaUnitOfWork, scope=Scope.REQUEST, provides=UnitOfWork)


class InteractorProvider(Provider):
    """DI provider for application use cases."""

    # Auth
    login_interactor = provide(LoginUserInteractor, scope=Scope.REQUEST)
    register_interactor = provide(RegisterUserInteractor, scope=Scope.REQUEST)

    # Profile
    get_user_interactor = provide(GetUserInteractor, scope=Scope.REQUEST)
    update_user_interactor = provide(UpdateUserInteractor, scope=Scope.REQUEST)
    get_other_profile_interactor = provide(
        GetOtherProfileInteractor, scope=Scope.REQUEST
    )
    delete_avatar_interactor = provide(DeleteAvatarInteractor, scope=Scope.REQUEST)
    change_password_interactor = provide(ChangePasswordInteractor, scope=Scope.REQUEST)
    generate_avatar_upload_url_interactor = provide(
        GenerateAvatarUploadUrlInteractor, scope=Scope.REQUEST
    )

    # Stats
    get_stats_interactor = provide(GetStatsInteractor, scope=Scope.REQUEST)
    increment_messages_interactor = provide(
        IncrementTotalMessagesInteractor, scope=Scope.REQUEST
    )
