"""rest_api/src/ioc/providers.py."""

from collections.abc import AsyncIterable
from pathlib import Path

from dishka import Provider
from dishka import Scope
from dishka import provide
from fastapi.templating import Jinja2Templates
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
from src.application.ports.providers.mail_provider import MailProvider
from src.application.ports.utils import Encryptor
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import PasswordHasher
from src.application.ports.utils import TimeProvider
from src.infrastructure.cache.rate_limiter import RedisRateLimiter
from src.infrastructure.cache.stats import RedisStatsGateway
from src.infrastructure.cache.user_cache import CachedUserGateway
from src.infrastructure.events.taskiq_publisher import TaskiqEventPublisher
from src.infrastructure.persistence.database.gateways import (
    PermissionGateway as SqlaPermissionGateway,
)
from src.infrastructure.persistence.database.gateways import SqlaUnitOfWork
from src.infrastructure.persistence.database.gateways import (
    UserGateway as SqlaUserGateway,
)
from src.infrastructure.providers.do_spaces_provider import DOSpacesUploader
from src.infrastructure.providers.jwt_provider import JwtProvider as JwtProviderImpl
from src.infrastructure.providers.mailjet_provider import MailjetProvider
from src.infrastructure.settings import AuthSettings
from src.infrastructure.settings import DatabaseSettings
from src.infrastructure.settings import MailSettings
from src.infrastructure.settings import RedisSettings
from src.infrastructure.settings import S3Settings
from src.infrastructure.settings import SecuritySettings
from src.infrastructure.settings import auth_settings
from src.infrastructure.settings import mail_settings
from src.infrastructure.settings import redis_settings
from src.infrastructure.settings import s3_settings
from src.infrastructure.settings import security_settings
from src.infrastructure.settings import settings as db_settings
from src.infrastructure.utils.aes_encryptor import AesEncryptor
from src.infrastructure.utils.datetime_generator import DatetimeGenerator
from src.infrastructure.utils.pwdlib_hasher import PwdlibHasher
from src.infrastructure.utils.uuid_generator import UuidGenerator


class UtilsProvider(Provider, scope=Scope.APP):
    """DI provider for utility services."""

    password_hasher = provide(PwdlibHasher, provides=PasswordHasher)
    id_generator = provide(UuidGenerator, provides=IdGenerator)
    time_provider = provide(DatetimeGenerator, provides=TimeProvider)
    encryptor = provide(AesEncryptor, provides=Encryptor)


class InfrastructureProvider(Provider, scope=Scope.APP):
    """DI provider for infrastructure and external integrations."""

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

    jwt_provider = provide(JwtProviderImpl, provides=JwtProviderPort)
    event_publisher = provide(TaskiqEventPublisher, provides=EventPublisher)
    mail_provider = provide(MailjetProvider, provides=MailProvider)
    file_uploader = provide(DOSpacesUploader, provides=FileUploader)

    stats_gateway = provide(
        RedisStatsGateway, scope=Scope.REQUEST, provides=StatsGateway
    )

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


class DbProvider(Provider, scope=Scope.APP):
    """DI provider for database and gateways."""

    @provide
    def provide_db_settings(self) -> DatabaseSettings:
        """Provide database connection settings."""
        return db_settings

    @provide
    def provide_engine(self, settings: DatabaseSettings) -> AsyncEngine:
        """Provide the SQLAlchemy async engine, injecting DatabaseSettings."""
        return create_async_engine(settings.database_url, echo=False)

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


class InteractorProvider(Provider, scope=Scope.REQUEST):
    """DI provider for application use cases."""

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
