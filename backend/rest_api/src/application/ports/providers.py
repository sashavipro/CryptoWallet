"""rest_api/src/application/ports/providers.py."""

from datetime import timedelta
from typing import Any
from typing import Protocol


class JwtProvider(Protocol):
    """Port for JWT operations."""

    def sign(
        self, payload: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        """Sign a payload and generate a JWT token."""
        ...

    def verify(self, token: str) -> dict[str, Any]:
        """Verify a JWT token and return its decoded payload."""
        ...


class MailProvider(Protocol):
    """Port for email delivery via SMTP or external API."""

    async def send_welcome_email(self, to_email: str, username: str) -> None:
        """Send a welcome email to a newly registered user."""
        ...


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
