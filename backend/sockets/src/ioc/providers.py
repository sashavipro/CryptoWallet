"""sockets/src/ioc/providers.py."""

from collections.abc import AsyncIterable

from dishka import Provider
from dishka import Scope
from dishka import provide
from redis.asyncio import Redis

from src.application.ports.providers.api_client import CryptoApiClient
from src.application.ports.publishers.event_publisher import EventPublisher
from src.infrastructure.cache.presence import OnlinePresenceGateway
from src.infrastructure.message_broker.event_publisher import EventPublisherImpl
from src.infrastructure.providers.api_client import CryptoApiClientImpl
from src.infrastructure.settings import ApiSettings
from src.infrastructure.settings import RabbitMQSettings
from src.infrastructure.settings import RedisSettings
from src.infrastructure.settings import SecuritySettings
from src.infrastructure.settings import api_settings
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

    @provide
    def provide_api_settings(self) -> ApiSettings:
        """Provide the settings for internal API communication."""
        return api_settings


class InfrastructureProvider(Provider):
    """Infrastructure dependency provider (cache, broker, etc.)."""

    scope = Scope.APP

    @provide
    async def provide_redis(self, settings: RedisSettings) -> AsyncIterable[Redis]:
        """Create and properly close a connection to Redis."""
        client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        yield client
        await client.aclose()

    @provide(scope=Scope.REQUEST)
    def provide_presence_gateway(self, redis: Redis) -> OnlinePresenceGateway:
        """Provide OnlinePresenceGateway resolving the string prefix issue."""
        return OnlinePresenceGateway(redis=redis)

    event_publisher = provide(EventPublisherImpl, provides=EventPublisher)
    api_client = provide(CryptoApiClientImpl, provides=CryptoApiClient)
