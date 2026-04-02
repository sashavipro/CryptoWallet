"""ethereum/src/ioc/container.py."""

from dishka import AsyncContainer
from dishka import make_async_container

from src.ioc.providers import InfrastructureProvider
from src.ioc.providers import InteractorProvider
from src.ioc.providers import UtilsProvider


def create_container() -> AsyncContainer:
    """Create the DI container with all providers for the Ethereum stateless worker."""
    return make_async_container(
        UtilsProvider(),
        InfrastructureProvider(),
        InteractorProvider(),
    )
