"""rest_api/src/presentation/http/dependencies/auth.py."""

import uuid
from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from src.application.ports.providers import JwtProvider

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    jwt_provider: FromDishka[JwtProvider],
) -> uuid.UUID:
    """Retrieve and validate JWT tokens from the request.

    Returns the current user's UUID.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt_provider.verify(credentials.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e!s}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user_id_str = payload.get("sub")

    if not user_id_str:
        msg = "Token payload missing 'sub' (user ID)"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return uuid.UUID(user_id_str)
