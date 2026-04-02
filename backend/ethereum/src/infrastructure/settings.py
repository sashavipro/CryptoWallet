"""ethereum/src/infrastructure/settings.py."""

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class SecuritySettings(BaseSettings):
    """Security configuration for encryption/decryption."""

    AES_SECRET_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class Web3Settings(BaseSettings):
    """Web3 configuration (RPC nodes and Faucet)."""

    WEB3_PROVIDER_URI: str = "wss://ethereum-sepolia.publicnode.com"

    FAUCET_PRIVATE_KEY_ENCRYPTED: str
    FAUCET_MASTER_ADDRESS: str
    FAUCET_AMOUNT_ETH: float = 0.001

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class RedisSettings(BaseSettings):
    """Redis configuration for NonceManager."""

    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class RabbitMQSettings(BaseSettings):
    """RabbitMQ configuration for FastStream."""

    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


security_settings = SecuritySettings()
web3_settings = Web3Settings()
redis_settings = RedisSettings()
mq_settings = RabbitMQSettings()
