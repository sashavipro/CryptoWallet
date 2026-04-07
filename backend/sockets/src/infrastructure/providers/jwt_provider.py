"""sockets/src/infrastructure/providers/jwt_provider.py."""

import logging

import jwt

logger = logging.getLogger(__name__)


class JwtValidator:
    """Validates JSON Web Tokens using a provided public key."""

    def __init__(self, public_key: str, algorithm: str = "RS256"):
        """Initialize the JWT validator with a public key and algorithm."""
        self.public_key = public_key
        self.algorithm = algorithm

    def verify_token(self, token: str) -> dict | None:
        """Decode and verify JWT. Returns payload or None if invalid."""
        try:
            payload = jwt.decode(token, self.public_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            logger.warning("JWT validation failed: Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("JWT validation failed: %s", e)
            return None
        else:
            return payload
