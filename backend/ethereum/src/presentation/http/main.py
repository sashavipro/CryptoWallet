"""ethereum/src/presentation/http/main.py."""

import asyncio
import logging
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka as setup_dishka_fastapi
from dishka.integrations.faststream import setup_dishka as setup_dishka_faststream
from fastapi import FastAPI
from faststream import FastStream

from src.application.interactors.block_scanner import BlockScannerInteractor
from src.application.ports.providers.web3 import Web3Provider
from src.infrastructure.log_config import setup_logging
from src.infrastructure.message_broker.broker import broker
from src.ioc.container import create_container
from src.presentation.amqp.consumers import router as amqp_router

setup_logging()
logger = logging.getLogger(__name__)


broker.include_router(amqp_router)
faststream_app = FastStream(broker)


async def run_block_scanner(container):
    """Wrap the block scanner to keep the DI container open."""
    async with container() as request_container:
        scanner = await request_container.get(BlockScannerInteractor)
        await scanner()


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage app lifecycle and broker startup."""
    max_retries = 5

    for attempt in range(max_retries):
        try:
            await broker.connect()
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

    scanner_task = asyncio.create_task(
        run_block_scanner(application.state.dishka_container)
    )

    await faststream_app.start()
    yield
    await faststream_app.stop()
    scanner_task.cancel()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    application = FastAPI(
        title="Ethereum Web3 Worker",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @application.get("/health")
    def healthcheck():
        return {"status": "ok", "service": "ethereum_worker"}

    container = create_container()

    setup_dishka_fastapi(container, application)
    setup_dishka_faststream(container, faststream_app)

    return application


app = create_app()
