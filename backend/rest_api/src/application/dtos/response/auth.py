"""rest_api/src/application/dtos/responses/auth.py."""

from dataclasses import dataclass


@dataclass
class TokenResponse:
    """DTO for login response returning the access token."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105


@dataclass
class JWTPayload:
    """DTO representing the decoded JWT payload."""

    sub: str
    exp: int
