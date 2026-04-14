"""ibay/src/infrastructure/task_broker.py."""

from dishka.integrations.taskiq import setup_dishka
from taskiq import TaskiqEvents
from taskiq import TaskiqScheduler
from taskiq import TaskiqState
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import ListQueueBroker
from taskiq_redis import RedisAsyncResultBackend

from src.infrastructure.message_broker.broker import broker as rabbit_broker
from src.infrastructure.settings import Settings
from src.ioc.container import get_container

settings = Settings()

redis_result_backend = RedisAsyncResultBackend(
    redis_url=settings.REDIS_URL,
)

taskiq_broker = ListQueueBroker(
    url=settings.REDIS_URL,
).with_result_backend(redis_result_backend)


@taskiq_broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    """We initialize the DI container and start RabbitMQ when the worker starts."""
    await rabbit_broker.start()

    container = get_container(rabbit_broker)
    setup_dishka(container, taskiq_broker)
    state.container = container


@taskiq_broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState) -> None:
    """Close connections when the worker stops."""
    if hasattr(state, "container"):
        await state.container.close()

    await rabbit_broker.close()


scheduler = TaskiqScheduler(
    broker=taskiq_broker,
    sources=[LabelScheduleSource(taskiq_broker)],
)
