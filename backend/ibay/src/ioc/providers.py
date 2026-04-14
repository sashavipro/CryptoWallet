"""ibay/src/ioc/providers.py."""

from dishka import Provider
from dishka import Scope
from dishka import provide
from faststream.rabbit import RabbitBroker

from src.application.interactors import ProcessDeliveryInteractor
from src.application.interactors import UpdateOrderStatusInteractor
from src.application.ports.events import EventPublisher
from src.application.ports.providers import GoogleCheckerProvider
from src.application.ports.providers import InternalApiClient
from src.infrastructure.message_broker.event_publisher import RabbitMQEventPublisher
from src.infrastructure.providers import AiohttpGoogleChecker
from src.infrastructure.providers import RestApiClient
from src.infrastructure.settings import Settings


class InfrastructureProvider(Provider):
    """Infrastructure layer dependencies."""

    scope = Scope.APP

    @provide()
    def get_settings(self) -> Settings:
        """Provide the application settings instance."""
        return Settings()

    @provide()
    def get_api_client(self, settings: Settings) -> InternalApiClient:
        """Provide the internal REST API client."""
        return RestApiClient(base_url=settings.REST_API_URL)

    @provide()
    def get_google_checker(self) -> GoogleCheckerProvider:
        """Provide the aiohttp Google checker instance."""
        return AiohttpGoogleChecker()

    @provide()
    def get_event_publisher(self, broker: RabbitBroker) -> EventPublisher:
        """Provide the RabbitMQ event publisher."""
        return RabbitMQEventPublisher(broker)


class InteractorProvider(Provider):
    """Application layer interactors."""

    scope = Scope.REQUEST

    update_order_status = provide(UpdateOrderStatusInteractor)
    process_delivery = provide(ProcessDeliveryInteractor)
