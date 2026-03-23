"""rest_api/src/application/interactors/profile.py."""

import uuid

from src.application.dtos.request import UpdateUserRequest
from src.application.dtos.response import PublicProfileResponse
from src.application.dtos.response import UserResponse
from src.application.ports.gateways import UserGateway
from src.application.ports.providers import FileUploader
from src.domain.value_objects.user import Username


class GetUserInteractor:
    """Use Case for retrieving the current user's profile."""

    def __init__(self, user_gateway: UserGateway) -> None:
        """Initialize with user gateway."""
        self.user_gateway = user_gateway

    async def __call__(self, user_id: uuid.UUID) -> UserResponse:
        """Execute retrieval."""
        user = await self.user_gateway.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")  # noqa: TRY003, EM101
        return UserResponse.model_validate(user)


class GetOtherProfileInteractor:
    """Use Case for retrieving another user's public profile."""

    def __init__(self, user_gateway: UserGateway) -> None:
        """Initialize with user gateway."""
        self.user_gateway = user_gateway

    async def __call__(self, user_id: uuid.UUID) -> PublicProfileResponse:
        """Execute retrieval of public data."""
        user = await self.user_gateway.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")  # noqa: TRY003, EM101
        return PublicProfileResponse.model_validate(user)


class UpdateUserInteractor:
    """Use Case for updating user profile fields."""

    def __init__(self, user_gateway: UserGateway) -> None:
        """Initialize with user gateway."""
        self.user_gateway = user_gateway

    async def __call__(
        self, user_id: uuid.UUID, request: UpdateUserRequest
    ) -> UserResponse:
        """Execute profile update."""
        user = await self.user_gateway.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")  # noqa: TRY003, EM101

        if request.username is not None:
            username_vo = Username(request.username)
            user.username = username_vo.value

        if request.avatar_url is not None:
            user.avatar_url = request.avatar_url

        updated_user = await self.user_gateway.update_user(user)
        return UserResponse.model_validate(updated_user)


class DeleteAvatarInteractor:
    """Use Case for removing a user's avatar."""

    def __init__(self, user_gateway: UserGateway, file_uploader: FileUploader) -> None:
        """Initialize with gateway and uploader provider."""
        self.user_gateway = user_gateway
        self.file_uploader = file_uploader

    async def __call__(self, user_id: uuid.UUID) -> UserResponse:
        """Execute avatar deletion."""
        user = await self.user_gateway.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")  # noqa: TRY003, EM101

        if user.avatar_url:
            await self.file_uploader.delete_avatar(user.avatar_url)
            user.avatar_url = None
            user = await self.user_gateway.update_user(user)

        return UserResponse.model_validate(user)
