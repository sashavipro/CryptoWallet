"""rest_api/src/application/interactors/chat.py."""

from src.application.ports.gateways.chat import ChatMessageGateway
from src.domain.entities.chat import ChatMessage


class GetChatHistoryInteractor:
    """Interactor that handles the logic of fetching chat history."""

    def __init__(self, message_gateway: ChatMessageGateway):
        """Initialize the interactor."""
        self.message_gateway = message_gateway

    async def execute(self, limit: int = 50, offset: int = 0) -> list[ChatMessage]:
        """Retrieve chat messages with pagination and return them in reversed order."""
        messages = await self.message_gateway.get_messages(limit=limit, offset=offset)
        return list(reversed(messages))
