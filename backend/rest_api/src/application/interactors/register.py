"""rest_api/src/application/interactors/register.py."""

import logging

from src.application.dtos.request import RegisterUserRequest
from src.application.dtos.response import TokenResponse
from src.application.ports.events import EventPublisher
from src.application.ports.gateways import PermissionGateway
from src.application.ports.gateways import UnitOfWork
from src.application.ports.gateways import UserGateway
from src.application.ports.providers import JwtProvider
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import PasswordHasher
from src.application.ports.utils import TimeProvider
from src.domain.entities import User
from src.domain.entities import UserPermission
from src.domain.exceptions import UserAlreadyExistsException
from src.domain.value_objects.user import Email
from src.domain.value_objects.user import PasswordHash
from src.domain.value_objects.user import RawPassword
from src.domain.value_objects.user import Username

logger = logging.getLogger(__name__)


class RegisterUserInteractor:
    """Use Case for registering a new user."""

    def __init__(  # noqa: PLR0913
        self,
        user_gateway: UserGateway,
        permission_gateway: PermissionGateway,
        uow: UnitOfWork,
        jwt_provider: JwtProvider,
        event_publisher: EventPublisher,
        password_hasher: PasswordHasher,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
    ) -> None:
        """Initialize the interactor with required dependencies."""
        self.user_gateway = user_gateway
        self.permission_gateway = permission_gateway
        self.uow = uow
        self.jwt_provider = jwt_provider
        self.event_publisher = event_publisher
        self.password_hasher = password_hasher
        self.id_generator = id_generator
        self.time_provider = time_provider

    async def __call__(self, request: RegisterUserRequest) -> TokenResponse:
        """Execute the registration workflow."""
        logger.info("Attempting to register new user with email: %s", request.email)

        email_vo = Email(request.email)
        username_vo = Username(request.username)
        raw_password_vo = RawPassword(request.password)

        existing_user = await self.user_gateway.get_user_by_email(email_vo.value)
        if existing_user:
            logger.warning(
                "Registration failed: email %s already exists", request.email
            )
            raise UserAlreadyExistsException("User with this email already exists")  # noqa: TRY003, EM101

        password_hash_vo = PasswordHash(
            self.password_hasher.hash(raw_password_vo.value)
        )
        current_time = self.time_provider.now()

        user = User(
            id=self.id_generator.generate(),
            email=email_vo.value,
            username=username_vo.value,
            password_hash=password_hash_vo.value,
            created_at=current_time,
        )

        async with self.uow:
            saved_user = await self.user_gateway.add_user(user)

            permission = UserPermission(
                id=self.id_generator.generate(),
                user_id=saved_user.id,
                has_chat_access=False,
                granted_at=None,
            )
            await self.permission_gateway.add_permission(permission)

            await self.event_publisher.publish_user_registered(
                user_id=saved_user.id,
                email=saved_user.email,
                username=saved_user.username,
            )

        logger.info(
            "User registered, event published, and transaction committed: %s",
            saved_user.id,
        )

        token = self.jwt_provider.sign({"sub": str(saved_user.id)})
        return TokenResponse(access_token=token)
