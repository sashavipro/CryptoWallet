"""ibay/src/application/tasks/delivery.py."""

import asyncio
import logging

from dishka.integrations.taskiq import FromDishka
from dishka.integrations.taskiq import inject

from src.application.interactors.ibay_worker import ProcessDeliveryInteractor
from src.infrastructure.task_broker import taskiq_broker

logger = logging.getLogger(__name__)


@taskiq_broker.task(schedule=[{"cron": "* * * * *"}])
@inject
async def process_delivery_scheduler_task(
    interactor: FromDishka[ProcessDeliveryInteractor],
) -> None:
    """Execute a background logistics task.

    CRON cannot handle seconds (the minimum interval is 1 minute).
    Therefore, we run the task once a minute and, within it, perform
    12 ticks of 5 seconds each.
    """
    logger.info("Starting delivery batch (1 min duration, 5 sec intervals)...")

    for _ in range(12):
        try:
            await interactor()
        except Exception:
            logger.exception("Error during delivery processing")

        await asyncio.sleep(5)
