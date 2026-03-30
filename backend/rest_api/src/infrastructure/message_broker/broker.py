"""rest_api/src/infrastructure/message_broker/broker.py."""

from dishka.integrations.taskiq import setup_dishka
from taskiq_aio_pika import AioPikaBroker

from src.infrastructure.settings import mq_settings

broker = AioPikaBroker(mq_settings.RABBITMQ_URL)


@broker.on_event("startup")
async def startup_event(state) -> None:
    """Initialize DI container on worker startup to prevent circular imports."""
    from src.ioc.container import create_container

    container = create_container()
    setup_dishka(container, broker)
    state.dishka_container = container


@broker.on_event("shutdown")
async def shutdown_event(state) -> None:
    """Close DI container on worker shutdown to prevent memory leaks."""
    if hasattr(state, "dishka_container"):
        await state.dishka_container.close()
