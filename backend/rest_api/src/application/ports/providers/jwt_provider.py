"""rest_api/src/application/ports/providers/jwt_provider.py."""

from datetime import timedelta
from typing import Any
from typing import Protocol


class JwtProvider(Protocol):
    """Port for JWT operations."""

    def sign(
        self, payload: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        """Sign a payload and generate a JWT token."""
        ...

    def verify(self, token: str) -> dict[str, Any]:
        """Verify a JWT token and return its decoded payload."""
        ...
