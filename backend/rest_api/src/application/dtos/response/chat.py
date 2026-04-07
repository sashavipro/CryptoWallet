"""rest_api/src/application/dtos/response/chat.py."""

from dataclasses import dataclass


@dataclass
class MessageResponse:
    """DTO for chat message response."""

    id: str
    user_id: str
    text: str
    image_url: str | None
    created_at: str
