"""rest_api/src/application/interactors/stats.py."""

import uuid

from src.application.dtos.response import UserStatsResponse
from src.application.ports.gateways import StatsGateway


class GetStatsInteractor:
    """Use Case for retrieving user statistics (wallets, messages)."""

    def __init__(self, stats_gateway: StatsGateway) -> None:
        """Initialize with stats gateway."""
        self.stats_gateway = stats_gateway

    async def __call__(self, user_id: uuid.UUID) -> UserStatsResponse:
        """Execute stats retrieval."""
        messages_count = await self.stats_gateway.get_total_messages(user_id)
        wallets_count = await self.stats_gateway.get_wallets_count(user_id)

        return UserStatsResponse(
            total_messages=messages_count,
            wallets_count=wallets_count,
        )


class IncrementTotalMessagesInteractor:
    """Use Case for incrementing the global chat message counter."""

    def __init__(self, stats_gateway: StatsGateway) -> None:
        """Initialize with stats gateway."""
        self.stats_gateway = stats_gateway

    async def __call__(self, user_id: uuid.UUID) -> None:
        """Execute counter increment."""
        await self.stats_gateway.increment_messages(user_id)
