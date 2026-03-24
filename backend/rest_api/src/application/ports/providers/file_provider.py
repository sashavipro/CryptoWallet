"""rest_api/src/application/ports/providers/file_provider.py."""

from typing import Protocol


class FileUploader(Protocol):
    """Port for file operations with S3/Object Storage."""

    async def generate_presigned_upload_url(
        self, file_name: str, content_type: str, expires_in: int = 3600
    ) -> dict[str, str]:
        """Generate a presigned URL for direct upload from frontend.

        Returns a dict with 'upload_url' and 'public_url'.
        """
        ...

    async def upload_avatar(
        self, file_content: bytes, file_name: str, content_type: str
    ) -> str:
        """Upload an avatar directly through the backend."""
        ...

    async def delete_avatar(self, file_url: str) -> None:
        """Delete a user avatar from the storage provider using its public URL."""
        ...
