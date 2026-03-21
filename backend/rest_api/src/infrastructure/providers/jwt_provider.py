"""rest_api/src/infrastructure/providers/jwt_provider.py."""

import logging
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Any

import jwt

from src.infrastructure.settings import auth_settings

logger = logging.getLogger(__name__)


class JwtProvider:
    """Provider for JWT operations using RS256 asymmetric encryption."""

    @staticmethod
    def sign(payload: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """Sign a payload and return a JWT token using the private key."""
        logger.debug(
            "Signing new JWT token for subject: %s", payload.get("sub", "unknown")
        )
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
        logger.debug("Verifying JWT token")
        try:
            return jwt.decode(
                token,
                auth_settings.public_key,
                algorithms=[auth_settings.ALGORITHM],
            )
        except jwt.ExpiredSignatureError as e:
            logger.warning("JWT verification failed: Token has expired")
            raise ValueError("Token has expired") from e  # noqa: TRY003, EM101
        except jwt.InvalidTokenError as e:
            logger.warning("JWT verification failed: %s", e)
            raise ValueError(f"Invalid token: {e}") from e  # noqa: TRY003, EM102
