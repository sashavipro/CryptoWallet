"""ethereum/src/infrastructure/settings.py."""

import base64
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

# Путь к папке certs (для проверки JWT токенов от REST API)
# infrastructure(1) -> src(2) -> ethereum(3) -> backend(4) -> CryptoWallet(5)
CERTS_DIR = Path(__file__).resolve().parents[4] / "certs"


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
    """Authentication configuration (only needs Public Key to verify tokens)."""

    PUBLIC_KEY_PATH: Path = CERTS_DIR / "public.pem"
    ALGORITHM: str = "RS256"

    JWT_PUBLIC_KEY_B64: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def public_key(self) -> str:
        """Read public RSA key from env (base64) or file."""
        if self.JWT_PUBLIC_KEY_B64:
            return base64.b64decode(self.JWT_PUBLIC_KEY_B64).decode("utf-8")
        return self.PUBLIC_KEY_PATH.read_text(encoding="utf-8")


class SecuritySettings(BaseSettings):
    """General security configuration (AES key for Private Keys)."""

    AES_SECRET_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class RabbitMQSettings(BaseSettings):
    """RabbitMQ configuration for receiving/sending events."""

    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class Web3Settings(BaseSettings):
    """Blockchain Node provider settings (Infura, Alchemy, etc.)."""

    WEB3_PROVIDER_URI: str = "wss://ethereum-sepolia.publicnode.com"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class RedisSettings(BaseSettings):
    """Redis configuration."""

    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = DatabaseSettings()
auth_settings = AuthSettings()
security_settings = SecuritySettings()
mq_settings = RabbitMQSettings()
web3_settings = Web3Settings()
redis_settings = RedisSettings()
