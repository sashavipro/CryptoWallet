"""sockets/src/infrastructure/settings.py."""

import base64
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

CERTS_DIR = Path(__file__).resolve().parents[4] / "certs"


class SecuritySettings(BaseSettings):
    """Security settings for JWT validation."""

    PUBLIC_KEY_PATH: Path = CERTS_DIR / "public.pem"
    ALGORITHM: str = "RS256"
    JWT_PUBLIC_KEY_B64: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def public_key(self) -> str:
        """Read the public key to decrypt the token."""
        if self.JWT_PUBLIC_KEY_B64:
            return base64.b64decode(self.JWT_PUBLIC_KEY_B64).decode("utf-8")
        return self.PUBLIC_KEY_PATH.read_text(encoding="utf-8")


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


security_settings = SecuritySettings()
mq_settings = RabbitMQSettings()
redis_settings = RedisSettings()
