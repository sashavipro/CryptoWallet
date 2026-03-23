"""rest_api/src/application/ports/events.py."""

import uuid
from typing import Protocol


class EventPublisher(Protocol):
    """Port for publishing integration events to a message broker."""

    async def publish_user_registered(
        self, user_id: uuid.UUID, email: str, username: str
    ) -> None:
        """Publish an event indicating a new user has registered."""
        ...
