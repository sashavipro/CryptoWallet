"""rest_api/src/application/dtos/responses/auth.py."""

from pydantic import BaseModel
from pydantic import Field


class TokenResponse(BaseModel):
    """DTO for login response returning the access token."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class JWTPayload(BaseModel):
    """DTO representing the decoded JWT payload."""

    sub: str = Field(..., description="Subject (User UUID)")
    exp: int = Field(..., description="Expiration timestamp")
