"""rest_api/src/presentation/http/routers/chat.py."""

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi import Query

from src.application.dtos.response.chat import MessageResponse
from src.application.ports.gateways.chat import ChatMessageGateway

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/messages", response_model=list[MessageResponse])
@inject
async def get_chat_history(
    message_gateway: FromDishka[ChatMessageGateway],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Retrieve chat history from MongoDB."""
    messages = await message_gateway.get_messages(limit, offset)

    return [
        MessageResponse(
            id=msg.id,
            user_id=msg.user_id,
            text=msg.message_text,
            image_url=msg.image_url,
            created_at=msg.created_at.isoformat(),
        )
        for msg in messages
    ]
