"""rest_api/src/infrastructure/settings.py."""

import base64
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

CERTS_DIR = Path(__file__).resolve().parent.parent.parent / "certs"


class DatabaseSettings(BaseSettings):
    """Database configuration loaded from .env file."""

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def database_url(self) -> str:
        """Generate async connection URL for PostgreSQL."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class AuthSettings(BaseSettings):
    """Authentication configuration."""

    PRIVATE_KEY_PATH: Path = CERTS_DIR / "private.pem"
    PUBLIC_KEY_PATH: Path = CERTS_DIR / "public.pem"
    ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    JWT_PRIVATE_KEY_B64: str | None = None
    JWT_PUBLIC_KEY_B64: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def private_key(self) -> str:
        """Read private RSA key from env (base64) or file."""
        if self.JWT_PRIVATE_KEY_B64:
            return base64.b64decode(self.JWT_PRIVATE_KEY_B64).decode("utf-8")
        return self.PRIVATE_KEY_PATH.read_text(encoding="utf-8")

    @property
    def public_key(self) -> str:
        """Read public RSA key from env (base64) or file."""
        if self.JWT_PUBLIC_KEY_B64:
            return base64.b64decode(self.JWT_PUBLIC_KEY_B64).decode("utf-8")
        return self.PUBLIC_KEY_PATH.read_text(encoding="utf-8")


class MailSettings(BaseSettings):
    """Mailjet configuration."""

    MAILJET_API_KEY: str | None = None
    MAILJET_API_SECRET: str | None = None
    MAILJET_SENDER_EMAIL: str = "noreply@cryptowallet.com"
    MAILJET_SENDER_NAME: str = "CryptoWallet Team"
    FRONTEND_DASHBOARD_URL: str = "http://localhost:3000/dashboard"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class SecuritySettings(BaseSettings):
    """General security configuration."""

    AES_SECRET_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class RabbitMQSettings(BaseSettings):
    """RabbitMQ configuration."""

    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class RedisSettings(BaseSettings):
    """Redis configuration."""

    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class S3Settings(BaseSettings):
    """S3 Storage configuration (AWS S3, MinIO, DigitalOcean Spaces, etc.)."""

    S3_ENDPOINT_URL: str | None = None  # Например: https://fra1.digitaloceanspaces.com
    S3_REGION_NAME: str = "us-east-1"
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str
    S3_PUBLIC_URL: str | None = (
        None  # Базовый URL для чтения файлов (если отличается от Endpoint)
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class CorsSettings(BaseSettings):
    """CORS configuration."""

    CORS_ALLOWED_ORIGINS: str = "http://localhost,http://127.0.0.1"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def origins_list(self) -> list[str]:
        """Convert comma-separated string to a list of origins."""
        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]


settings = DatabaseSettings()
auth_settings = AuthSettings()
mail_settings = MailSettings()
security_settings = SecuritySettings()
mq_settings = RabbitMQSettings()
redis_settings = RedisSettings()
s3_settings = S3Settings()
cors_settings = CorsSettings()
