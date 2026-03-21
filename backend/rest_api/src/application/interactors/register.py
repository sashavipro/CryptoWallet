"""rest_api/src/application/interactors/register.py."""

import logging

from src.application.dtos.request import RegisterUserRequest
from src.application.dtos.response import TokenResponse
from src.application.ports.gateways import PermissionGateway
from src.application.ports.gateways import UserGateway
from src.application.ports.providers import JwtProvider
from src.application.ports.providers import MailProvider
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import PasswordHasher
from src.application.ports.utils import TimeProvider
from src.domain.entities.permissions import UserPermission
from src.domain.entities.user import User
from src.domain.value_objects.user.email import Email
from src.domain.value_objects.user.password import PasswordHash
from src.domain.value_objects.user.password import RawPassword
from src.domain.value_objects.user.username import Username

logger = logging.getLogger(__name__)


class RegisterUserInteractor:
    """Use Case for registering a new user."""

    def __init__(  # noqa: PLR0913
        self,
        user_gateway: UserGateway,
        permission_gateway: PermissionGateway,
        jwt_provider: JwtProvider,
        mail_provider: MailProvider,
        password_hasher: PasswordHasher,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
    ) -> None:
        """Initialize the interactor with required dependencies."""
        self.user_gateway = user_gateway
        self.permission_gateway = permission_gateway
        self.jwt_provider = jwt_provider
        self.mail_provider = mail_provider
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
            raise ValueError("User with this email already exists")  # noqa: TRY003, EM101

        raw_hash = self.password_hasher.hash(raw_password_vo.value)
        password_hash_vo = PasswordHash(raw_hash)

        user_id = self.id_generator.generate()
        current_time = self.time_provider.now()

        user = User(
            id=user_id,
            email=email_vo.value,
            username=username_vo.value,
            password_hash=password_hash_vo.value,
            avatar_url=None,
            is_active=True,
            created_at=current_time,
        )

        saved_user = await self.user_gateway.add_user(user)
        logger.info("User registered successfully with ID: %s", saved_user.id)

        permission = UserPermission(
            id=self.id_generator.generate(),
            user_id=saved_user.id,
            has_chat_access=True,
            granted_at=current_time,
        )
        await self.permission_gateway.add_permission(permission)
        logger.debug("Permissions granted for user ID: %s", saved_user.id)

        try:
            await self.mail_provider.send_welcome_email(
                to_email=saved_user.email,
                username=saved_user.username,
            )
            logger.info("Welcome email sent to user ID: %s", saved_user.id)
        except Exception:
            logger.exception("Failed to send welcome email to %s", saved_user.email)

        payload = {"sub": str(saved_user.id)}
        token = self.jwt_provider.sign(payload)

        return TokenResponse(access_token=token, token_type="bearer")  # noqa: S106
