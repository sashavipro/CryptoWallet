"""rest_api/src/domain/entities/permissions.py."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from .base import BaseEntity


@dataclass(kw_only=True)
class UserPermission(BaseEntity):
    """Доменная сущность прав пользователя."""

    user_id: uuid.UUID
    has_chat_access: bool = False
    granted_at: datetime | None = None

    def grant_chat_access(self, timestamp: datetime) -> None:
        """Бизнес-метод для выдачи прав на чат."""
        self.has_chat_access = True
        self.granted_at = timestamp
