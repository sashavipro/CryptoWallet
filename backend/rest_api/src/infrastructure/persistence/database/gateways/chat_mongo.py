"""rest_api/src/infrastructure/persistence/database/gateways/chat_mongo.py."""

from motor.motor_asyncio import AsyncIOMotorClient

from src.application.ports.gateways.chat import ChatMessageGateway
from src.application.ports.gateways.chat import ChatUserGateway
from src.domain.entities.chat import ChatMessage
from src.domain.entities.chat import ChatUser
from src.infrastructure.persistence.database.mappers.chat_mongo import (
    map_domain_to_message_doc,
)
from src.infrastructure.persistence.database.mappers.chat_mongo import (
    map_message_to_domain,
)
from src.infrastructure.persistence.database.mappers.user import map_user_to_domain


class MongoChatUserGateway(ChatUserGateway):
    """Motor implementation of ChatUserGateway."""

    def __init__(self, client: AsyncIOMotorClient, db_name: str):
        """Initialize the gateway without hardcoded db_name."""
        self.collection = client[db_name]["chat_users_mongo"]

    async def upsert_user(self, user: ChatUser) -> None:
        """Update user data or insert if it doesn't exist."""
        await self.collection.update_one(
            {"_id": user.id},
            {
                "$set": {"username": user.username, "avatar_url": user.avatar_url},
                "$setOnInsert": {"has_chat_access": False},
            },
            upsert=True,
        )

    async def update_chat_access(self, user_id: str, *, has_access: bool) -> None:
        """Update the chat access flag."""
        await self.collection.update_one(
            {"_id": user_id},
            {"$set": {"has_chat_access": has_access}},
        )

    async def get_user_by_id(self, user_id: str) -> ChatUser | None:
        """Find a user in the chat cache."""
        doc = await self.collection.find_one({"_id": user_id})
        if doc:
            return map_user_to_domain(doc)
        return None


class MongoChatMessageGateway(ChatMessageGateway):
    """Motor implementation of ChatMessageGateway."""

    def __init__(self, client: AsyncIOMotorClient, db_name: str):
        """Initialize the gateway without hardcoded db_name."""
        self.collection = client[db_name]["chat_messages_mongo"]

    async def add_message(self, message: ChatMessage) -> None:
        """Insert a new chat message into the database."""
        doc = map_domain_to_message_doc(message)
        result = await self.collection.insert_one(doc)
        message.id = str(result.inserted_id)

    async def get_messages(self, limit: int, offset: int) -> list[ChatMessage]:
        """Retrieve a paginated list of chat messages ordered by creation time."""
        cursor = self.collection.find().sort("created_at", -1).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)

        messages = [map_message_to_domain(doc) for doc in docs]

        return list(reversed(messages))
