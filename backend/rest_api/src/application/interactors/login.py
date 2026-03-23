"""rest_api/src/application/interactors/login.py."""

import logging
from datetime import timedelta

from src.application.dtos.request import LoginUserRequest
from src.application.dtos.response import TokenResponse
from src.application.ports.gateways import UserGateway
from src.application.ports.providers import JwtProvider
from src.application.ports.utils import PasswordHasher
from src.domain.exceptions import InvalidCredentialsException
from src.domain.value_objects.user import Email
from src.domain.value_objects.user import RawPassword

logger = logging.getLogger(__name__)


class LoginUserInteractor:
    """Use Case for authenticating an existing user."""

    def __init__(
        self,
        user_gateway: UserGateway,
        jwt_provider: JwtProvider,
        password_hasher: PasswordHasher,
    ) -> None:
        """Initialize the interactor with required dependencies."""
        self.user_gateway = user_gateway
        self.jwt_provider = jwt_provider
        self.password_hasher = password_hasher

    async def __call__(self, request: LoginUserRequest) -> TokenResponse:
        """Execute the login workflow."""
        logger.info("Attempting login for email: %s", request.email)

        email_vo = Email(request.email)
        raw_password_vo = RawPassword(request.password)

        user = await self.user_gateway.get_user_by_email(email_vo.value)
        if not user:
            logger.warning("Login failed: User not found for email %s", request.email)
            raise InvalidCredentialsException("Invalid email or password")  # noqa: TRY003, EM101

        is_valid = self.password_hasher.verify(
            password=raw_password_vo.value,
            hashed_password=user.password_hash,
        )
        if not is_valid:
            logger.warning("Login failed: Invalid password for email %s", request.email)
            raise InvalidCredentialsException("Invalid email or password")  # noqa: TRY003, EM101

        payload = {"sub": str(user.id)}

        if request.remember_me:
            expires_delta = timedelta(days=30)
        else:
            expires_delta = timedelta(seconds=15)

        token = self.jwt_provider.sign(payload, expires_delta=expires_delta)

        logger.info("User %s logged in successfully", user.id)
        return TokenResponse(access_token=token, token_type="bearer")  # noqa: S106
