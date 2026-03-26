"""rest_api/src/infrastructure/providers/do_spaces_provider.py."""

import logging
from urllib.parse import urlparse

import aioboto3
from botocore.exceptions import ClientError

from src.application.ports.providers.file_provider import FileUploader
from src.infrastructure.settings import S3Settings

logger = logging.getLogger(__name__)


class DOSpacesUploader(FileUploader):
    """DigitalOcean Spaces implementation with CDN support."""

    def __init__(self, settings: S3Settings) -> None:
        """Initialize the DigitalOcean Spaces client."""
        self.settings = settings
        self.session = aioboto3.Session()
        self.space_name = self.settings.S3_BUCKET_NAME

        self.client_kwargs = {
            "service_name": "s3",
            "region_name": self.settings.S3_REGION_NAME,
            "aws_access_key_id": self.settings.S3_ACCESS_KEY_ID,
            "aws_secret_access_key": self.settings.S3_SECRET_ACCESS_KEY,
            "endpoint_url": self.settings.S3_ENDPOINT_URL,
        }

    def _get_cdn_url(self, file_name: str) -> str:
        """Return the public CDN URL for reading the file."""
        cdn_base = str(self.settings.S3_PUBLIC_URL).rstrip("/")
        return f"{cdn_base}/{file_name}"

    def _extract_key_from_url(self, file_url: str) -> str:
        """Extract the object key (file path) from the CDN URL."""
        parsed_url = urlparse(file_url)
        return parsed_url.path.lstrip("/")

    async def generate_presigned_upload_url(
        self, file_name: str, content_type: str, expires_in: int = 3600
    ) -> dict[str, str]:
        """Generate a temporary URL for the frontend to upload a file to DO Spaces."""
        logger.debug("Generating DO Spaces presigned URL for %s", file_name)

        async with self.session.client(**self.client_kwargs) as client:
            try:
                upload_url = await client.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={
                        "Bucket": self.space_name,
                        "Key": file_name,
                        "ContentType": content_type,
                        "ACL": "public-read",
                    },
                    ExpiresIn=expires_in,
                )

                return {
                    "upload_url": upload_url,
                    "public_url": self._get_cdn_url(file_name),
                }
            except ClientError as e:
                logger.exception("Failed to generate presigned URL for DO Spaces")
                err_msg = f"Could not generate upload URL: {e}"
                raise ValueError(err_msg) from e

    async def upload_avatar(
        self, file_content: bytes, file_name: str, content_type: str
    ) -> str:
        """Upload file bytes directly from backend to DO Spaces."""
        logger.info("Uploading %s directly to DO Spaces", file_name)

        async with self.session.client(**self.client_kwargs) as client:
            try:
                await client.put_object(
                    Bucket=self.space_name,
                    Key=file_name,
                    Body=file_content,
                    ContentType=content_type,
                    ACL="public-read",
                )
                logger.info("Successfully uploaded %s to DO Spaces", file_name)
                return self._get_cdn_url(file_name)
            except ClientError as e:
                logger.exception("Failed to upload %s to DO Spaces", file_name)
                err_msg = f"Could not upload file: {e}"
                raise RuntimeError(err_msg) from e

    async def delete_avatar(self, file_url: str) -> None:
        """Delete an object from DO Spaces using its CDN URL."""
        key = self._extract_key_from_url(file_url)
        logger.info("Deleting object from DO Spaces with key: %s", key)

        async with self.session.client(**self.client_kwargs) as client:
            try:
                await client.delete_object(Bucket=self.space_name, Key=key)
                logger.info("Successfully deleted %s from DO Spaces", key)
            except ClientError as e:
                logger.exception("Failed to delete object %s from DO Spaces", key)
                err_msg = f"Could not delete file: {e}"
                raise RuntimeError(err_msg) from e
