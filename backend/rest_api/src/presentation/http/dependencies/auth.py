"""rest_api/src/presentation/http/dependencies/auth.py."""

import uuid
from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from src.application.ports.providers import JwtProvider

bearer_scheme = HTTPBearer(auto_error=False)


@inject
async def get_current_user_id(
    request: Request,
    jwt_provider: FromDishka[JwtProvider],
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ] = None,
) -> uuid.UUID:
    """Retrieve and validate JWT tokens from Authorization header or cookies.

    Returns the current user's UUID.
    """
    token = credentials.credentials if credentials else None

    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt_provider.verify(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e!s}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user_id_str = payload.get("sub")

    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing 'sub' (user ID)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return uuid.UUID(user_id_str)


CurrentUserId = Annotated[uuid.UUID, Depends(get_current_user_id)]
