"""rest_api/src/application/ports/gateways/stats.py."""

import uuid
from typing import Protocol


class StatsGateway(Protocol):
    """Port for user statistics operations."""

    async def get_total_messages(self, user_id: uuid.UUID) -> int:
        """Retrieve the total number of chat messages sent by the user."""
        ...

    async def increment_messages(self, user_id: uuid.UUID) -> None:
        """Increment the user's global chat message counter."""
        ...

    async def get_wallets_count(self, user_id: uuid.UUID) -> int:
        """Retrieve the total number of wallets owned by the user."""
        ...
