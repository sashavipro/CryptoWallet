"""rest_api/src/infrastructure/persistence/database/models/chat_mongo.py."""

import datetime
from typing import NotRequired
from typing import TypedDict

from bson import ObjectId


class ChatUserDocument(TypedDict):
    """MongoDB document schema for ChatUser."""

    _id: str
    username: str
    avatar_url: str | None


class ChatMessageDocument(TypedDict):
    """MongoDB document schema for ChatMessage."""

    _id: NotRequired[ObjectId]
    user_id: str
    message_text: str
    image_url: str | None
    created_at: datetime.datetime
