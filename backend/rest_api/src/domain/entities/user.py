"""rest_api/src/domain/entities/user.py."""

from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime

from .base import BaseEntity


@dataclass(kw_only=True)
class User(BaseEntity):
    """Доменная сущность пользователя."""

    email: str
    username: str
    password_hash: str
    avatar_url: str | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
