"""sockets/src/ioc/providers.py."""

from collections.abc import AsyncIterable

from dishka import Provider
from dishka import Scope
from dishka import provide
from redis.asyncio import Redis

from src.infrastructure.cache.presence import OnlinePresenceGateway
from src.infrastructure.settings import RabbitMQSettings
from src.infrastructure.settings import RedisSettings
from src.infrastructure.settings import SecuritySettings
from src.infrastructure.settings import mq_settings
from src.infrastructure.settings import redis_settings
from src.infrastructure.settings import security_settings


class SettingsProvider(Provider):
    """Provider for app settings."""

    scope = Scope.APP

    @provide
    def provide_security_settings(self) -> SecuritySettings:
        """Provide the application security settings."""
        return security_settings

    @provide
    def provide_redis_settings(self) -> RedisSettings:
        """Provide the Redis configuration settings."""
        return redis_settings

    @provide
    def provide_mq_settings(self) -> RabbitMQSettings:
        """Provide the RabbitMQ configuration settings."""
        return mq_settings


class InfrastructureProvider(Provider):
    """Infrastructure dependency provider (cache, broker, etc.)."""

    scope = Scope.APP

    @provide
    async def provide_redis(self, settings: RedisSettings) -> AsyncIterable[Redis]:
        """Create and properly close a connection to Redis."""
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        yield client
        await client.aclose()

    presence_gateway = provide(OnlinePresenceGateway, scope=Scope.REQUEST)
