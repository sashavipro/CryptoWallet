"""rest_api/src/presentation/http/admin/auth.py."""

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from src.application.ports.gateways import UserGateway
from src.application.ports.utils import PasswordHasher
from src.infrastructure.settings import security_settings


class AdminAuth(AuthenticationBackend):
    """Backend authorization for SQLAdmin via the database and Dishka."""

    async def login(self, request: Request) -> bool:
        """Authenticate user and set session token."""
        form = await request.form()
        email = form.get("username")
        password = form.get("password")

        if not email or not password:
            return False

        container = request.state.dishka_container

        user_gateway = await container.get(UserGateway)
        password_hasher = await container.get(PasswordHasher)

        user = await user_gateway.get_user_by_email(email)
        if not user:
            return False

        if not password_hasher.verify(password, user.password_hash):
            return False

        if user.username != "admin":
            return False

        request.session.update({"admin_id": str(user.id)})
        return True

    async def logout(self, request: Request) -> bool:
        """Clear the user session."""
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """Verify if the user is currently authenticated."""
        admin_id = request.session.get("admin_id")
        return admin_id is not None


admin_auth_backend = AdminAuth(secret_key=security_settings.AES_SECRET_KEY)
