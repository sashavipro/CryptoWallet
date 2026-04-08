"""rest_api/src/infrastructure/task_broker.py."""

import logging

from dishka.integrations.taskiq import setup_dishka
from taskiq_aio_pika import AioPikaBroker

from src.infrastructure.settings import mq_settings
from src.ioc.container import create_container

logger = logging.getLogger(__name__)

taskiq_broker = AioPikaBroker(
    url=mq_settings.RABBITMQ_URL,
)

container = create_container()
setup_dishka(container, taskiq_broker)


@taskiq_broker.on_event("startup")
async def startup() -> None:
    """Handle the broker startup event."""
    logger.info("TaskIQ Broker started.")


@taskiq_broker.on_event("shutdown")
async def shutdown() -> None:
    """Handle the broker shutdown event."""
    logger.info("TaskIQ Broker stopped.")
