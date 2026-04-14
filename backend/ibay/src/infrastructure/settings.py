"""ibay/src/infrastructure/settings.py."""

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Message Brokers & Cache
    RABBITMQ_URL: str
    REDIS_URL: str

    # Internal Microservices
    REST_API_URL: str

    # iBay Logistics Settings
    STRESS_TEST_REQUESTS: int

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
