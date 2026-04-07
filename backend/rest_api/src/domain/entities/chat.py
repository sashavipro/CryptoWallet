"""rest_api/src/domain/entities/chat.py."""

import datetime
from dataclasses import dataclass
from dataclasses import field


@dataclass
class ChatUser:
    """Domain entity representing a user's cached profile in MongoDB."""

    id: str
    username: str
    avatar_url: str | None = None


@dataclass
class ChatMessage:
    """Domain entity representing a chat message (MongoDB)."""

    id: str | None
    user_id: str
    message_text: str
    image_url: str | None = None
    created_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
