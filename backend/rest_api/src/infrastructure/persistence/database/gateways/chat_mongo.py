"""rest_api/src/infrastructure/database/gateways/chat_mongo.py."""

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from src.application.ports.gateways.chat import ChatMessageGateway
from src.application.ports.gateways.chat import ChatUserGateway
from src.domain.entities.chat import ChatMessage
from src.domain.entities.chat import ChatUser


class MongoChatUserGateway(ChatUserGateway):
    """Motor implementation of ChatUserGateway."""

    def __init__(self, client: AsyncIOMotorClient, db_name: str = "chat_db"):
        """Initialize the gateway with a MongoDB client and database name."""
        self.collection = client[db_name]["chat_users_mongo"]

    async def upsert_user(self, user: ChatUser) -> None:
        """Update user data or insert if it doesn't exist."""
        await self.collection.update_one(
            {"_id": user.id},
            {"$set": {"username": user.username, "avatar_url": user.avatar_url}},
            upsert=True,
        )

    async def get_user_by_id(self, user_id: str) -> ChatUser | None:
        """Find a user in the chat cache."""
        doc = await self.collection.find_one({"_id": user_id})
        if doc:
            return ChatUser(
                id=doc["_id"],
                username=doc["username"],
                avatar_url=doc.get("avatar_url"),
            )
        return None


class MongoChatMessageGateway(ChatMessageGateway):
    """Motor implementation of ChatMessageGateway."""

    def __init__(self, client: AsyncIOMotorClient, db_name: str = "chat_db"):
        """Initialize the gateway with a MongoDB client and database name."""
        self.collection = client[db_name]["chat_messages_mongo"]

    async def add_message(self, message: ChatMessage) -> None:
        """Insert a new chat message into the database."""
        doc = {
            "user_id": message.user_id,
            "message_text": message.message_text,
            "image_url": message.image_url,
            "created_at": message.created_at,
        }

        if message.id:
            doc["_id"] = ObjectId(message.id)

        result = await self.collection.insert_one(doc)
        message.id = str(result.inserted_id)

    async def get_messages(self, limit: int, offset: int) -> list[ChatMessage]:
        """Retrieve a paginated list of chat messages ordered by creation time."""
        cursor = self.collection.find().sort("created_at", -1).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)

        messages = [
            ChatMessage(
                id=str(doc["_id"]),
                user_id=doc["user_id"],
                message_text=doc.get("message_text", ""),
                image_url=doc.get("image_url"),
                created_at=doc["created_at"],
            )
            for doc in docs
        ]

        return list(reversed(messages))
