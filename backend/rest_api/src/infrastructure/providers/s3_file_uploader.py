"""rest_api/src/infrastructure/providers/s3_file_uploader.py."""

import logging
from urllib.parse import urlparse

import aioboto3
from botocore.exceptions import ClientError

from src.application.ports.providers.file_provider import FileUploader
from src.infrastructure.settings import S3Settings

logger = logging.getLogger(__name__)


class S3FileUploader(FileUploader):
    """Aioboto3 implementation for S3 compatible storage."""

    def __init__(self, settings: S3Settings) -> None:
        """Initialize the S3 file uploader."""
        self.settings = settings
        self.session = aioboto3.Session()
        self.bucket = self.settings.S3_BUCKET_NAME

        self.client_kwargs = {
            "service_name": "s3",
            "region_name": self.settings.S3_REGION_NAME,
            "aws_access_key_id": self.settings.S3_ACCESS_KEY_ID,
            "aws_secret_access_key": self.settings.S3_SECRET_ACCESS_KEY,
        }
        if self.settings.S3_ENDPOINT_URL:
            self.client_kwargs["endpoint_url"] = self.settings.S3_ENDPOINT_URL

    def _get_public_url(self, file_name: str) -> str:
        """Construct the public URL for a file."""
        if self.settings.S3_PUBLIC_URL:
            return f"{self.settings.S3_PUBLIC_URL.rstrip('/')}/{file_name}"
        # Fallback (AWS style)
        return f"https://{self.bucket}.s3.{self.settings.S3_REGION_NAME}.amazonaws.com/{file_name}"

    def _extract_key_from_url(self, file_url: str) -> str:
        """Extract the S3 Object Key from a public URL."""
        parsed_url = urlparse(file_url)
        return parsed_url.path.lstrip("/")

    async def generate_presigned_upload_url(
        self, file_name: str, content_type: str, expires_in: int = 3600
    ) -> dict[str, str]:
        """Generate a temporary URL for the frontend to upload a file."""
        logger.debug("Generating presigned URL for %s", file_name)

        async with self.session.client(**self.client_kwargs) as client:
            try:
                upload_url = await client.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={
                        "Bucket": self.bucket,
                        "Key": file_name,
                        "ContentType": content_type,
                        "ACL": "public-read",
                    },
                    ExpiresIn=expires_in,
                )

                return {
                    "upload_url": upload_url,
                    "public_url": self._get_public_url(file_name),
                }
            except ClientError as e:
                logger.exception("Failed to generate presigned URL")
                err_msg = "Could not generate upload URL"
                raise ValueError(err_msg) from e

    async def upload_avatar(
        self, file_content: bytes, file_name: str, content_type: str
    ) -> str:
        """Upload file bytes directly from backend to S3."""
        logger.info("Uploading %s directly to S3", file_name)
        async with self.session.client(**self.client_kwargs) as client:
            await client.put_object(
                Bucket=self.bucket,
                Key=file_name,
                Body=file_content,
                ContentType=content_type,
                ACL="public-read",
            )
        return self._get_public_url(file_name)

    async def delete_avatar(self, file_url: str) -> None:
        """Delete an object from S3 using its URL."""
        key = self._extract_key_from_url(file_url)
        logger.info("Deleting S3 object with key: %s", key)

        async with self.session.client(**self.client_kwargs) as client:
            try:
                await client.delete_object(Bucket=self.bucket, Key=key)
            except ClientError:
                logger.exception("Failed to delete object %s", key)
