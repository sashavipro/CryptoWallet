"""rest_api/tests/integration/test_auth_api.py."""

from http import HTTPStatus
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from dishka import Provider
from dishka import Scope
from dishka import make_async_container
from dishka import provide
from fastapi.testclient import TestClient
from src.application.dtos.response import TokenResponse
from src.application.interactors import LoginUserInteractor
from src.infrastructure.cache.rate_limiter import RedisRateLimiter
from src.presentation.http.main import app


class MockAuthProvider(Provider):
    """Mock auth provider."""

    scope = Scope.APP

    @provide
    def provide_login_interactor(self) -> LoginUserInteractor:
        """Provide a mocked LoginUserInteractor."""
        interactor = AsyncMock(spec=LoginUserInteractor)
        interactor.return_value = TokenResponse(
            access_token="fake_token",  # noqa: S106
            token_type="bearer",  # noqa: S106
        )
        return interactor

    @provide
    def provide_rate_limiter(self) -> RedisRateLimiter:
        """Provide a mocked RedisRateLimiter."""
        limiter = AsyncMock(spec=RedisRateLimiter)
        limiter.is_allowed.return_value = True
        return limiter


@pytest.fixture
def auth_client():
    """Auth client fixture."""
    app.state.dishka_container = make_async_container(MockAuthProvider())

    with (
        patch("src.presentation.http.main.broker.start", new_callable=AsyncMock),
        patch("src.presentation.http.main.broker.close", new_callable=AsyncMock),
        TestClient(app) as client,
    ):
        yield client


def test_login_api_success(auth_client):
    """Test successful login."""
    payload = {"email": "test@test.com", "password": "Password123"}
    response = auth_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"access_token": "fake_token", "token_type": "bearer"}


def test_login_api_validation_error(auth_client):
    """Test login with validation error."""
    payload = {"email": "test@test.com"}
    response = auth_client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
