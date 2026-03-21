"""rest_api/src/domain/entities/permissions.py."""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime

from .base import BaseEntity

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class UserPermission(BaseEntity):
    """Domain-specific user rights."""

    user_id: uuid.UUID
    has_chat_access: bool = False
    granted_at: datetime | None = None

    def grant_chat_access(self, timestamp: datetime) -> None:
        """Busines process for granting chat permissions."""
        logger.info("Granting chat access for user_id: %s", self.user_id)
        self.has_chat_access = True
        self.granted_at = timestamp
