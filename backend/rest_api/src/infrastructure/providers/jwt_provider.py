"""rest_api/src/infrastructure/providers/jwt_provider.py."""

import logging
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Any

import jwt

from src.infrastructure.settings import AuthSettings

logger = logging.getLogger(__name__)


class JwtProvider:
    """Provider for JWT operations using RS256 asymmetric encryption."""

    def __init__(self, settings: AuthSettings) -> None:
        """Initialize provider with authentication settings."""
        self.settings = settings

    def sign(
        self, payload: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        """Sign a payload and return a JWT token using the private key."""
        logger.debug(
            "Signing new JWT token for subject: %s", payload.get("sub", "unknown")
        )
        to_encode = payload.copy()

        expire = datetime.now(UTC) + (
            expires_delta
            if expires_delta
            else timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})

        return jwt.encode(
            to_encode,
            self.settings.private_key,
            algorithm=self.settings.ALGORITHM,
        )

    def verify(self, token: str) -> dict[str, Any]:
        """Verify a JWT token using the public key and return the decoded payload."""
        logger.debug("Verifying JWT token")
        try:
            return jwt.decode(
                token,
                self.settings.public_key,
                algorithms=[self.settings.ALGORITHM],
            )
        except jwt.ExpiredSignatureError as e:
            logger.warning("JWT verification failed: Token has expired")
            raise ValueError("Token has expired") from e  # noqa: TRY003, EM101
        except jwt.InvalidTokenError as e:
            logger.warning("JWT verification failed: %s", e)
            raise ValueError(f"Invalid token: {e}") from e  # noqa: TRY003, EM102
