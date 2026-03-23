"""rest_api/src/application/dtos/requests/user.py."""

from pydantic import BaseModel
from pydantic import Field


class RegisterUserRequest(BaseModel):
    """DTO for user registration."""

    email: str = Field(
        ...,
        description="User's email address",
        examples=["test@example.com"],
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="User's display name",
        examples=["crypto_ninja"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=20,
        description="Raw password",
        examples=["SuperSecret123!"],
    )


class LoginUserRequest(BaseModel):
    """DTO for user login."""

    email: str = Field(
        ...,
        description="User's email address",
        examples=["test@example.com"],
    )
    password: str = Field(
        ...,
        description="Raw password",
        examples=["SuperSecret123!"],
    )
    remember_me: bool = Field(
        default=False, description="Flag for long-lived session (eternal vs 15 seconds)"
    )


class UpdateUserRequest(BaseModel):
    """DTO for updating user profile.

    All fields are optional, meaning the user can send only the fields
    they want to update.
    """

    username: str | None = Field(
        None,
        min_length=3,
        max_length=50,
        description="New display name",
    )
    avatar_url: str | None = Field(
        None,
        description="URL to the new avatar image",
    )


class ChangePasswordRequest(BaseModel):
    """DTO for changing user password."""

    old_password: str = Field(
        ...,
        description="Current raw password",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=20,
        description="New raw password",
    )
