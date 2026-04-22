"""rest_api/tests/unit/test_register_interactor.py."""

import uuid
from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING
from typing import cast
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from src.application.dtos.request import RegisterUserRequest
from src.application.interactors.register import RegisterUserInteractor
from src.domain.exceptions import UserAlreadyExistsException

if TYPE_CHECKING:
    from src.application.ports.events import EventPublisher
    from src.application.ports.gateways import PermissionGateway
    from src.application.ports.utils import IdGenerator
    from src.application.ports.utils import TimeProvider


@pytest.fixture
def mock_event_publisher():
    """Mock EventPublisher."""
    return AsyncMock()


@pytest.fixture
def register_interactor(
    mock_user_gateway,
    mock_uow,
    mock_jwt_provider,
    mock_password_hasher,
    mock_event_publisher,
):
    """Register interactor fixture."""
    return RegisterUserInteractor(
        user_gateway=mock_user_gateway,
        permission_gateway=cast("PermissionGateway", AsyncMock()),
        uow=mock_uow,
        jwt_provider=mock_jwt_provider,
        event_publisher=cast("EventPublisher", mock_event_publisher),
        password_hasher=mock_password_hasher,
        id_generator=cast("IdGenerator", MagicMock(generate=lambda: uuid.uuid4())),
        time_provider=cast("TimeProvider", MagicMock(now=lambda: datetime.now(UTC))),
    )


async def test_register_user_success(
    register_interactor, mock_user_gateway, mock_event_publisher
):
    """Test register user success."""
    request = RegisterUserRequest(
        email="test@test.com",
        username="tester",
        password="Password123",  # noqa: S106
    )
    mock_user_gateway.get_user_by_email.return_value = None

    mock_saved_user = MagicMock()
    mock_saved_user.id = uuid.uuid4()
    mock_user_gateway.add_user.return_value = mock_saved_user

    response = await register_interactor(request)

    assert response.access_token == "mocked_jwt_token"  # noqa: S105
    mock_user_gateway.get_user_by_email.assert_called_once_with("test@test.com")
    mock_user_gateway.add_user.assert_called_once()
    mock_event_publisher.publish_user_registered.assert_called_once()


async def test_register_user_already_exists(register_interactor, mock_user_gateway):
    """Test register user already exists."""
    request = RegisterUserRequest(
        email="exist@test.com",
        username="tester",
        password="ValidPass123",  # noqa: S106
    )
    mock_user_gateway.get_user_by_email.return_value = MagicMock()

    with pytest.raises(UserAlreadyExistsException) as exc_info:
        await register_interactor(request)

    assert str(exc_info.value) == "User with this email already exists"
    mock_user_gateway.add_user.assert_not_called()
