"""rest_api/src/application/dtos/requests/user.py."""

from dataclasses import dataclass


@dataclass
class RegisterUserRequest:
    """DTO for user registration."""

    email: str
    username: str
    password: str


@dataclass
class LoginUserRequest:
    """DTO for user login."""

    email: str
    password: str
    remember_me: bool = False


@dataclass
class UpdateUserRequest:
    """DTO for updating user profile."""

    username: str | None = None
    avatar_url: str | None = None


@dataclass
class ChangePasswordRequest:
    """DTO for changing user password."""

    old_password: str
    new_password: str
