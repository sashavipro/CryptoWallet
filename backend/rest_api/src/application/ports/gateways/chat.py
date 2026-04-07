"""rest_api/src/application/ports/gateways/chat.py."""

from typing import Protocol

from src.domain.entities.chat import ChatMessage
from src.domain.entities.chat import ChatUser


class ChatUserGateway(Protocol):
    """Gateway for MongoDB chat users persistence."""

    async def upsert_user(self, user: ChatUser) -> None:
        """Insert or update user details in MongoDB."""
        ...

    async def get_user_by_id(self, user_id: str) -> ChatUser | None:
        """Retrieve cached user details."""
        ...


class ChatMessageGateway(Protocol):
    """Gateway for MongoDB chat message persistence."""

    async def add_message(self, message: ChatMessage) -> None:
        """Save a new message to MongoDB."""
        ...

    async def get_messages(self, limit: int, offset: int) -> list[ChatMessage]:
        """Retrieve recent messages."""
        ...
