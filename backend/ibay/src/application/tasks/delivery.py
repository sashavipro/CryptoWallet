"""ibay/src/application/tasks/delivery.py."""

import logging

from dishka.integrations.taskiq import FromDishka
from dishka.integrations.taskiq import inject
from taskiq import TaskiqDepends

from src.application.interactors.ibay_worker import ProcessDeliveryInteractor
from src.infrastructure.task_broker import taskiq_broker

logger = logging.getLogger(__name__)


@taskiq_broker.task(schedule=[{"cron": "*/5 * * * * *"}])
@inject
async def process_delivery_scheduler_task(
    interactor: FromDishka[ProcessDeliveryInteractor] = TaskiqDepends(),  # noqa: B008
) -> None:
    """Retrieve a delivery request every 5 seconds via a background worker."""
    try:
        await interactor()
    except Exception:
        logger.exception("Error occurred in Process Delivery Scheduler")
