"""rest_api/tests/conftest.py."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from dishka import Provider
from dishka import Scope
from dishka import make_async_container
from dishka import provide
from fastapi.testclient import TestClient
from src.application.ports.gateways import UnitOfWork
from src.application.ports.gateways import UserGateway
from src.application.ports.providers import JwtProvider
from src.application.ports.utils import PasswordHasher
from src.infrastructure.cache.rate_limiter import RedisRateLimiter
from src.presentation.http.main import app


@pytest.fixture
def mock_uow():
    """Mock UnitOfWork."""
    uow = AsyncMock(spec=UnitOfWork)
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow


@pytest.fixture
def mock_user_gateway():
    """Mock UserGateway."""
    return AsyncMock(spec=UserGateway)


@pytest.fixture
def mock_jwt_provider():
    """Mock JwtProvider."""
    provider = MagicMock(spec=JwtProvider)
    provider.sign.return_value = "mocked_jwt_token"
    provider.verify.return_value = {"sub": "123e4567-e89b-12d3-a456-426614174000"}
    return provider


@pytest.fixture
def mock_password_hasher():
    """Mock PasswordHasher."""
    hasher = MagicMock(spec=PasswordHasher)
    hasher.hash.return_value = "$argon2id$v=19$m=65536,t=3,p=4$dummyhash"
    hasher.verify.return_value = True
    return hasher


class MockInfrastructureProvider(Provider):
    """Mock infrastructure provider for tests."""

    scope = Scope.APP

    @provide
    def provide_rate_limiter(self) -> RedisRateLimiter:
        """Provide a mocked RedisRateLimiter."""
        limiter = AsyncMock(spec=RedisRateLimiter)
        limiter.is_allowed.return_value = True
        return limiter


@pytest.fixture
def api_client():
    """TestClient fixture with mocked infrastructure."""
    test_container = make_async_container(MockInfrastructureProvider())
    app.state.dishka_container = test_container

    with TestClient(app) as client:
        yield client
