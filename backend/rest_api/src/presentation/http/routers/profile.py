"""rest_api/src/presentation/http/routers/profile.py."""

import uuid
from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi import Depends

from src.application.dtos.request import ChangePasswordRequest
from src.application.dtos.request import UpdateUserRequest
from src.application.dtos.response import PublicProfileResponse
from src.application.dtos.response import UserResponse
from src.application.interactors.profile import ChangePasswordInteractor
from src.application.interactors.profile import DeleteAvatarInteractor
from src.application.interactors.profile import GenerateAvatarUploadUrlInteractor
from src.application.interactors.profile import GetOtherProfileInteractor
from src.application.interactors.profile import GetUserInteractor
from src.application.interactors.profile import UpdateUserInteractor
from src.presentation.http.dependencies.auth import get_current_user_id

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])

CurrentUserId = Annotated[uuid.UUID, Depends(get_current_user_id)]


@router.get("/me", response_model=UserResponse)
@inject
async def get_current_user_profile(
    user_id: CurrentUserId,
    interactor: FromDishka[GetUserInteractor],
) -> UserResponse:
    """Get the profile of the currently logged-in user."""
    return await interactor(user_id)


@router.patch("/me", response_model=UserResponse)
@inject
async def update_current_user_profile(
    request: UpdateUserRequest,
    user_id: CurrentUserId,
    interactor: FromDishka[UpdateUserInteractor],
) -> UserResponse:
    """Update the profile fields of the currently logged-in user."""
    return await interactor(user_id, request)


@router.delete("/me/avatar", response_model=UserResponse)
@inject
async def delete_current_user_avatar(
    user_id: CurrentUserId,
    interactor: FromDishka[DeleteAvatarInteractor],
) -> UserResponse:
    """Delete the avatar of the currently logged-in user."""
    return await interactor(user_id)


@router.put("/password", response_model=UserResponse)
@inject
async def change_password(
    request: ChangePasswordRequest,
    user_id: CurrentUserId,
    interactor: FromDishka[ChangePasswordInteractor],
) -> UserResponse:
    """Update the user's password."""
    return await interactor(user_id, request)


@router.get("/{target_user_id}", response_model=PublicProfileResponse)
@inject
async def get_other_user_profile(
    target_user_id: uuid.UUID,
    user_id: CurrentUserId,
    interactor: FromDishka[GetOtherProfileInteractor],
) -> PublicProfileResponse:
    """Get the public profile of another user."""
    return await interactor(target_user_id)


@router.get("/me/avatar/presigned-url")
@inject
async def get_avatar_presigned_url(
    user_id: CurrentUserId,
    extension: str,  # например 'png'
    content_type: str,  # например 'image/png'
    interactor: FromDishka[GenerateAvatarUploadUrlInteractor],
):
    """Get a direct S3 upload link for a new avatar."""
    return await interactor(user_id, extension, content_type)
