"""rest_api/src/infrastructure/providers/jwt_provider.py."""

from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Any

import jwt

from src.infrastructure.settings import auth_settings


class JwtProvider:
    """Provider for JWT operations using RS256 asymmetric encryption."""

    @staticmethod
    def sign(payload: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """Sign a payload and return a JWT token using the private key."""
        to_encode = payload.copy()

        expire = datetime.now(UTC) + (
            expires_delta
            if expires_delta
            else timedelta(minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})

        return jwt.encode(
            to_encode,
            auth_settings.private_key,
            algorithm=auth_settings.ALGORITHM,
        )

    @staticmethod
    def verify(token: str) -> dict[str, Any]:
        """Verify a JWT token using the public key and return the decoded payload."""
        try:
            return jwt.decode(
                token,
                auth_settings.public_key,
                algorithms=[auth_settings.ALGORITHM],
            )
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}") from e  # noqa: TRY003, EM102
