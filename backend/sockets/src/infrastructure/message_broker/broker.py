"""sockets/src/infrastructure/message_broker/broker.py."""

from faststream.rabbit import RabbitBroker

from src.infrastructure.settings import mq_settings

broker = RabbitBroker(mq_settings.RABBITMQ_URL)
