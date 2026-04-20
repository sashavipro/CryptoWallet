"""rest_api/src/application/dtos/responses/user.py."""

import uuid
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime


@dataclass
class UserResponse:
    """DTO for the current user's full profile."""

    id: uuid.UUID
    email: str
    username: str
    is_active: bool
    created_at: datetime
    avatar_url: str | None = None
    has_chat_access: bool = True


@dataclass
class PublicProfileResponse:
    """DTO for another user's public profile."""

    id: uuid.UUID
    username: str
    avatar_url: str | None = None
    has_chat_access: bool = True
    wallets: list[str] = field(default_factory=list)


@dataclass
class UserStatsResponse:
    """DTO for user statistics."""

    total_messages: int
    wallets_count: int
