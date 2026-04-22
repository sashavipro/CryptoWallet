"""rest_api/tests/unit/test_login_interactor.py."""

from unittest.mock import MagicMock

import pytest
from src.application.dtos.request import LoginUserRequest
from src.application.interactors.login import LoginUserInteractor
from src.domain.exceptions import InvalidCredentialsException


@pytest.fixture
def login_interactor(mock_user_gateway, mock_jwt_provider, mock_password_hasher):
    """Login interactor fixture."""
    return LoginUserInteractor(
        user_gateway=mock_user_gateway,
        jwt_provider=mock_jwt_provider,
        password_hasher=mock_password_hasher,
    )


async def test_login_success(login_interactor, mock_user_gateway, mock_password_hasher):
    """Test login success."""
    mock_user = MagicMock()
    mock_user.password_hash = "hashed_pass"  # noqa: S105
    mock_user_gateway.get_user_by_email.return_value = mock_user
    mock_password_hasher.verify.return_value = True

    request = LoginUserRequest(email="test@test.com", password="Password123")  # noqa: S106
    response = await login_interactor(request)

    assert response.access_token == "mocked_jwt_token"  # noqa: S105


async def test_login_invalid_password(
    login_interactor, mock_user_gateway, mock_password_hasher
):
    """Test login invalid password."""
    mock_user = MagicMock()
    mock_user_gateway.get_user_by_email.return_value = mock_user
    mock_password_hasher.verify.return_value = False

    request = LoginUserRequest(email="test@test.com", password="WrongPassword1")  # noqa: S106

    with pytest.raises(InvalidCredentialsException):
        await login_interactor(request)
