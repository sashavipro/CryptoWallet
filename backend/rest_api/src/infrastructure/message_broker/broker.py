"""rest_api/src/infrastructure/message_broker/broker.py."""

from taskiq_aio_pika import AioPikaBroker

from src.infrastructure.settings import mq_settings

broker = AioPikaBroker(mq_settings.RABBITMQ_URL)
