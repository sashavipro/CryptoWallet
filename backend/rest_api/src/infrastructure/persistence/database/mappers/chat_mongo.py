"""rest_api/src/infrastructure/persistence/database/mappers/chat_mongo.py."""

from bson import ObjectId

from src.domain.entities.chat import ChatMessage
from src.domain.entities.chat import ChatUser
from src.infrastructure.persistence.database.models import ChatMessageDocument
from src.infrastructure.persistence.database.models import ChatUserDocument


def map_user_to_domain(doc: ChatUserDocument) -> ChatUser:
    """Convert MongoDB document to Domain ChatUser entity."""
    return ChatUser(
        id=doc["_id"],
        username=doc["username"],
        avatar_url=doc.get("avatar_url"),
    )


def map_message_to_domain(doc: ChatMessageDocument) -> ChatMessage:
    """Convert MongoDB document to Domain ChatMessage entity."""
    return ChatMessage(
        id=str(doc["_id"]),
        user_id=doc["user_id"],
        message_text=doc.get("message_text", ""),
        image_url=doc.get("image_url"),
        created_at=doc["created_at"],
    )


def map_domain_to_message_doc(message: ChatMessage) -> ChatMessageDocument:
    """Convert Domain ChatMessage entity to MongoDB document."""
    doc: ChatMessageDocument = {
        "user_id": message.user_id,
        "message_text": message.message_text,
        "image_url": message.image_url,
        "created_at": message.created_at,
    }

    if message.id:
        doc["_id"] = ObjectId(message.id)

    return doc
