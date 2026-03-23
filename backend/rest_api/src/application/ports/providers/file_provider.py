"""rest_api/src/application/ports/providers/file_provider.py."""

from typing import Protocol


class FileUploader(Protocol):
    """Port for file uploading (e.g., AWS S3, DO Spaces)."""

    async def upload_avatar(
        self, file_content: bytes, file_name: str, content_type: str
    ) -> str:
        """Upload a user avatar and return its public URL."""
        ...

    async def delete_avatar(self, file_url: str) -> None:
        """Delete a user avatar from the storage provider."""
        ...
