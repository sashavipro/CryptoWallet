"""sockets/src/application/ports/publishers/event_publisher.py."""

from typing import Protocol


class EventPublisher(Protocol):
    """Protocol defining the interface for publishing domain events."""

    async def publish_chat_message(
        self,
        user_id: str,
        room_id: str,
        text: str,
        image_key: str | None,
        temp_id: str | None,
    ) -> None:
        """Publish a new chat message event to the message broker."""
        ...
