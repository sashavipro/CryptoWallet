"""rest_api/src/infrastructure/message_broker/broker.py."""

from dishka.integrations.taskiq import setup_dishka
from taskiq_aio_pika import AioPikaBroker

from src.infrastructure.settings import mq_settings
from src.ioc.container import create_container

broker = AioPikaBroker(mq_settings.RABBITMQ_URL)

container = create_container()
setup_dishka(container, broker)
