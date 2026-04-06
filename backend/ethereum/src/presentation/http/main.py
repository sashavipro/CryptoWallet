"""ethereum/src/presentation/http/main.py."""

import asyncio
import logging
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka as setup_dishka_fastapi
from dishka.integrations.faststream import setup_dishka as setup_dishka_faststream
from fastapi import FastAPI
from faststream.rabbit.fastapi import RabbitRouter

from src.application.ports.providers.web3 import Web3Provider
from src.infrastructure.log_config import setup_logging
from src.infrastructure.settings import mq_settings
from src.ioc.container import create_container
from src.presentation.amqp.consumers import router as amqp_router

setup_logging()
logger = logging.getLogger(__name__)

rabbit_router = RabbitRouter(mq_settings.RABBITMQ_URL)
rabbit_router.include_router(amqp_router)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage app lifecycle and broker startup."""
    max_retries = 5

    for attempt in range(max_retries):
        try:
            await rabbit_router.broker.connect()
            logger.info("Successfully connected to RabbitMQ!")
            break
        except Exception as e:
            if attempt == max_retries - 1:
                logger.exception("Failed to connect to RabbitMQ")
                raise
            logger.warning("RabbitMQ is not ready yet, retrying in 5s... Error: %s", e)
            await asyncio.sleep(5)

    container = application.state.dishka_container
    async with container() as request_container:
        web3_provider = await request_container.get(Web3Provider)
        await web3_provider._check_connection()  # noqa: SLF001
        logger.info("Successfully connected to Web3 Node!")

    async with rabbit_router.lifespan_context(application):
        yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    application = FastAPI(
        title="Ethereum Web3 Worker",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    application.include_router(rabbit_router)

    @application.get("/health")
    def healthcheck():
        return {"status": "ok", "service": "ethereum_worker"}

    container = create_container()

    setup_dishka_fastapi(container, application)
    setup_dishka_faststream(container, rabbit_router)

    return application


app = create_app()
