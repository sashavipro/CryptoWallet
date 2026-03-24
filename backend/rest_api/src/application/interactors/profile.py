"""rest_api/src/application/interactors/profile.py."""

import uuid

from src.application.dtos.request import ChangePasswordRequest
from src.application.dtos.request import UpdateUserRequest
from src.application.dtos.response import PublicProfileResponse
from src.application.dtos.response import UserResponse
from src.application.ports.gateways import UnitOfWork
from src.application.ports.gateways import UserGateway
from src.application.ports.providers import FileUploader
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import PasswordHasher
from src.domain.exceptions import InvalidCredentialsException
from src.domain.exceptions import UserNotFoundException
from src.domain.value_objects.user import Username
from src.domain.value_objects.user.password import PasswordHash
from src.domain.value_objects.user.password import RawPassword


class GetUserInteractor:
    """Use Case for retrieving the current user's profile."""

    def __init__(self, user_gateway: UserGateway) -> None:
        """Initialize the interactor with a user gateway."""
        self.user_gateway = user_gateway

    async def __call__(self, user_id: uuid.UUID) -> UserResponse:
        """Execute the retrieval of the current user's profile."""
        user = await self.user_gateway.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException("User not found")  # noqa: TRY003, EM101
        return UserResponse.model_validate(user)


class GetOtherProfileInteractor:
    """Use Case for retrieving another user's public profile."""

    def __init__(self, user_gateway: UserGateway) -> None:
        """Initialize the interactor with a user gateway."""
        self.user_gateway = user_gateway

    async def __call__(self, user_id: uuid.UUID) -> PublicProfileResponse:
        """Execute the retrieval of another user's public profile."""
        user = await self.user_gateway.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException("User not found")  # noqa: TRY003, EM101
        return PublicProfileResponse.model_validate(user)


class UpdateUserInteractor:
    """Use Case for updating user profile fields."""

    def __init__(self, user_gateway: UserGateway, uow: UnitOfWork) -> None:
        """Initialize the interactor with user gateway and unit of work."""
        self.user_gateway = user_gateway
        self.uow = uow

    async def __call__(
        self, user_id: uuid.UUID, request: UpdateUserRequest
    ) -> UserResponse:
        """Execute the update of user profile fields."""
        user = await self.user_gateway.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException("User not found")  # noqa: TRY003, EM101

        if request.username is not None:
            username_vo = Username(request.username)
            user.username = username_vo.value

        if request.avatar_url is not None:
            user.avatar_url = request.avatar_url

        async with self.uow:
            updated_user = await self.user_gateway.update_user(user)

        return UserResponse.model_validate(updated_user)


class DeleteAvatarInteractor:
    """Use Case for removing a user's avatar."""

    def __init__(
        self, user_gateway: UserGateway, file_uploader: FileUploader, uow: UnitOfWork
    ) -> None:
        """Initialize the interactor with required dependencies."""
        self.user_gateway = user_gateway
        self.file_uploader = file_uploader
        self.uow = uow

    async def __call__(self, user_id: uuid.UUID) -> UserResponse:
        """Execute the avatar deletion process."""
        user = await self.user_gateway.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException("User not found")  # noqa: TRY003, EM101

        if user.avatar_url:
            await self.file_uploader.delete_avatar(user.avatar_url)
            user.avatar_url = None

            async with self.uow:
                user = await self.user_gateway.update_user(user)

        return UserResponse.model_validate(user)


class ChangePasswordInteractor:
    """Use Case for changing the user's password."""

    def __init__(
        self,
        user_gateway: UserGateway,
        password_hasher: PasswordHasher,
        uow: UnitOfWork,
    ) -> None:
        """Initialize the interactor with required gateways and utilities."""
        self.user_gateway = user_gateway
        self.password_hasher = password_hasher
        self.uow = uow

    async def __call__(
        self, user_id: uuid.UUID, request: ChangePasswordRequest
    ) -> UserResponse:
        """Execute the password change process."""
        user = await self.user_gateway.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException("User not found")  # noqa: TRY003, EM101

        is_valid = self.password_hasher.verify(
            password=request.old_password,
            hashed_password=user.password_hash,
        )
        if not is_valid:
            raise InvalidCredentialsException("Invalid old password")  # noqa: TRY003, EM101

        raw_password_vo = RawPassword(request.new_password)
        new_hash = self.password_hasher.hash(raw_password_vo.value)
        password_hash_vo = PasswordHash(new_hash)

        user.password_hash = password_hash_vo.value

        async with self.uow:
            updated_user = await self.user_gateway.update_user(user)

        return UserResponse.model_validate(updated_user)


class GenerateAvatarUploadUrlInteractor:
    """Use Case for generating a presigned S3 upload URL for an avatar."""

    def __init__(self, file_uploader: FileUploader, id_generator: IdGenerator):
        """Initialize the interactor with a file uploader and ID generator."""
        self.file_uploader = file_uploader
        self.id_generator = id_generator

    async def __call__(
        self, user_id: uuid.UUID, extension: str, content_type: str
    ) -> dict:
        """Execute the generation of a secure, temporary upload link."""
        file_name = f"avatars/{user_id}/{self.id_generator.generate()}.{extension}"

        return await self.file_uploader.generate_presigned_upload_url(
            file_name=file_name, content_type=content_type
        )
