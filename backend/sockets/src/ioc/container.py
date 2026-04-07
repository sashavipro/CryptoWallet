"""sockets/src/ioc/container.py."""

from dishka import AsyncContainer
from dishka import make_async_container

from src.ioc.providers import InfrastructureProvider
from src.ioc.providers import SettingsProvider


def create_container() -> AsyncContainer:
    """Create a DI container for sockets with all providers."""
    return make_async_container(
        SettingsProvider(),
        InfrastructureProvider(),
    )
