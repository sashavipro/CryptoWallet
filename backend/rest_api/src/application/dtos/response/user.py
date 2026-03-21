"""rest_api/src/application/dtos/responses/user.py."""

import uuid
from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class UserResponse(BaseModel):
    """DTO for the current user's full profile.

    Used as a response for Registration, Get Me, and Update User endpoints.
    """

    id: uuid.UUID = Field(..., description="Unique identifier of the user")
    email: str = Field(..., description="User's email address")
    username: str = Field(..., description="User's display name")
    avatar_url: str | None = Field(None, description="URL to the user's avatar")
    is_active: bool = Field(..., description="Account activation status")
    created_at: datetime = Field(..., description="Timestamp of account creation")

    model_config = ConfigDict(from_attributes=True)


class PublicProfileResponse(BaseModel):
    """DTO for another user's public profile.

    Excludes sensitive information such as email, active status, and creation date.
    """

    id: uuid.UUID = Field(..., description="Unique identifier of the user")
    username: str = Field(..., description="User's display name")
    avatar_url: str | None = Field(None, description="URL to the user's avatar")

    model_config = ConfigDict(from_attributes=True)
