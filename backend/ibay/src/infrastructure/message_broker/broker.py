"""ibay/src/infrastructure/message_broker/broker.py."""

from faststream.rabbit import RabbitBroker

from src.infrastructure.settings import Settings

settings = Settings()
broker = RabbitBroker(settings.RABBITMQ_URL)
