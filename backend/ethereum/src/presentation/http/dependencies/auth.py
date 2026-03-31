"""ethereum/src/presentation/http/dependencies/auth.py."""

import uuid
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status

from src.infrastructure.settings import AuthSettings


async def get_current_user_id(request: Request) -> uuid.UUID:
    """Extract and verify real user ID from JWT using Public Key."""
    token = request.cookies.get("access_token")

    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован",  # noqa: RUF001
        )

    auth_settings = AuthSettings()
    try:
        public_key = auth_settings.PUBLIC_KEY_PATH.read_text()
        payload = jwt.decode(token, public_key, algorithms=[auth_settings.ALGORITHM])
        return uuid.UUID(payload["sub"])
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Время действия токена истекло",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
        ) from e


CurrentUserId = Annotated[uuid.UUID, Depends(get_current_user_id)]
