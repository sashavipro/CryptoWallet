"""ethereum/src/presentation/http/main.py."""

import asyncio
import logging
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from faststream.rabbit.fastapi import RabbitRouter

from src.application.ports.providers.web3 import Web3Provider
from src.infrastructure.log_config import setup_logging
from src.infrastructure.message_broker.block_subscriber import listen_to_new_blocks
from src.infrastructure.settings import mq_settings
from src.ioc.container import create_container
from src.presentation.amqp.consumers import router as amqp_router

setup_logging()
logger = logging.getLogger(__name__)

rabbit_router = RabbitRouter(mq_settings.RABBITMQ_URL)
rabbit_router.include_router(amqp_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle, broker startup, and block listening."""
    await rabbit_router.startup()

    container = app.state.dishka_container
    async with container() as request_container:
        web3_provider = await request_container.get(Web3Provider)
        await web3_provider._check_connection()  # noqa: SLF001
        w3 = web3_provider.w3

    block_listener_task = asyncio.create_task(listen_to_new_blocks(w3, container))

    yield

    block_listener_task.cancel()
    await rabbit_router.shutdown()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance with DI and routing."""
    app = FastAPI(title="Ethereum Web3 Worker", lifespan=lifespan)
    app.include_router(rabbit_router)

    @app.get("/health")
    def healthcheck():
        """Return the service health status."""
        return {"status": "ok", "service": "ethereum_worker"}

    container = create_container()
    setup_dishka(container, app)

    return app


app = create_app()
