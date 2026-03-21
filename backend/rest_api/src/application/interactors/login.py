"""rest_api/src/application/interactors/login.py."""

from src.application.dtos.request import LoginUserRequest
from src.application.dtos.response import TokenResponse
from src.application.ports.gateways import UserGateway
from src.application.ports.providers import JwtProvider
from src.application.ports.utils import PasswordHasher
from src.domain.value_objects.user.email import Email
from src.domain.value_objects.user.password import RawPassword


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
        email_vo = Email(request.email)
        raw_password_vo = RawPassword(request.password)

        user = await self.user_gateway.get_user_by_email(email_vo.value)
        if not user:
            raise ValueError("Invalid email or password")  # noqa: TRY003, EM101

        is_valid = self.password_hasher.verify(
            password=raw_password_vo.value,
            hashed_password=user.password_hash,
        )
        if not is_valid:
            raise ValueError("Invalid email or password")  # noqa: TRY003, EM101

        payload = {"sub": str(user.id)}
        token = self.jwt_provider.sign(payload)

        return TokenResponse(access_token=token, token_type="bearer")  # noqa: S106
