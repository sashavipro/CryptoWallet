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

    async def publish_stats_updated(
        self, user_id: uuid.UUID, messages_count: int, wallets_count: int
    ) -> None:
        """Publish an event to notify the user that their stats have changed."""
        ...
