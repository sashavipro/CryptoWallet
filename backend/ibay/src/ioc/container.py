"""ibay/src/ioc/container.py."""

from dishka import AsyncContainer
from dishka import make_async_container
from faststream.rabbit import RabbitBroker

from .providers import InfrastructureProvider
from .providers import InteractorProvider


def get_container(broker: RabbitBroker) -> AsyncContainer:
    """Initialize the container with separated providers."""
    return make_async_container(
        InfrastructureProvider(), InteractorProvider(), context={RabbitBroker: broker}
    )
