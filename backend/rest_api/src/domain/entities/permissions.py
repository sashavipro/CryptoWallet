"""rest_api/src/domain/entities/permissions.py."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from .base import BaseEntity


@dataclass(kw_only=True)
class UserPermission(BaseEntity):
    """Domain-specific user rights."""

    user_id: uuid.UUID
    has_chat_access: bool = False
    granted_at: datetime | None = None

    def grant_chat_access(self, timestamp: datetime) -> None:
        """Busines process for granting chat permissions."""
        self.has_chat_access = True
        self.granted_at = timestamp
