"""ibay/src/presentation/http/main.py."""

import asyncio
import logging
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka as setup_dishka_fastapi
from dishka.integrations.faststream import setup_dishka as setup_dishka_faststream
from fastapi import FastAPI
from faststream import FastStream

from src.application.interactors.ibay_worker import ProcessDeliveryInteractor
from src.infrastructure.message_broker.broker import broker
from src.ioc.container import get_container
from src.presentation.amqp.consumers import router as amqp_router

logger = logging.getLogger(__name__)

broker.include_router(amqp_router)
faststream_app = FastStream(broker)

container = get_container(broker)

MAX_RETRIES = 5


async def background_delivery_worker(dishka_container):
    """Execute a continuous loop to process delivery tasks in the background."""
    logger.info("Background delivery worker started...")
    while True:
        processed_any = False
        try:
            async with dishka_container() as request_container:
                delivery_interactor = await request_container.get(
                    ProcessDeliveryInteractor
                )
                processed_any = await delivery_interactor()
        except Exception:
            logger.exception("Error in background delivery worker")

        if not processed_any:
            await asyncio.sleep(5)
        else:
            await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the FastAPI app lifespan and handle the broker connection with retries."""
    for attempt in range(MAX_RETRIES):
        try:
            await broker.start()
            logger.info("Successfully connected to RabbitMQ!")
            break
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                logger.exception(
                    "Failed to connect to RabbitMQ after %s attempts.", MAX_RETRIES
                )
                raise
            logger.warning("RabbitMQ is not ready yet, retrying in 5s... Error: %s", e)
            await asyncio.sleep(5)

    yield
    await broker.close()


app = FastAPI(lifespan=lifespan, title="iBay Worker Service")

setup_dishka_fastapi(container, app)
setup_dishka_faststream(container, faststream_app)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return the health status of the application."""
    return {"status": "ok"}
