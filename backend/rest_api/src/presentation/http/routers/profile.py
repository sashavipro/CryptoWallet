"""rest_api/src/presentation/http/routers/profile.py."""

import uuid
from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter
from fastapi import Depends

from src.application.dtos.request import ChangePasswordRequest
from src.application.dtos.response import UserResponse
from src.application.interactors.profile import ChangePasswordInteractor
from src.application.interactors.profile import GetUserInteractor
from src.presentation.http.dependencies.auth import get_current_user_id

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])

CurrentUserId = Annotated[uuid.UUID, Depends(get_current_user_id)]


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    user_id: CurrentUserId,
    interactor: FromDishka[GetUserInteractor],
) -> UserResponse:
    """Get the profile of the currently logged-in user."""
    return await interactor(user_id)


@router.put("/password", response_model=UserResponse)
async def change_password(
    request: ChangePasswordRequest,
    user_id: CurrentUserId,
    interactor: FromDishka[ChangePasswordInteractor],
) -> UserResponse:
    """Update the user's password."""
    return await interactor(user_id, request)
