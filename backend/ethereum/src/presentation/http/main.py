"""ethereum/src/presentation/http/main.py."""

import logging
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
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
async def lifespan(app: FastAPI):
    """Manage app lifecycle and broker startup."""
    await rabbit_router.startup()

    container = app.state.dishka_container
    async with container() as request_container:
        web3_provider = await request_container.get(Web3Provider)
        await web3_provider._check_connection()  # noqa: SLF001

    yield

    await rabbit_router.shutdown()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(title="Ethereum Web3 Worker", lifespan=lifespan)
    app.include_router(rabbit_router)

    @app.get("/health")
    def healthcheck():
        return {"status": "ok", "service": "ethereum_worker"}

    container = create_container()
    setup_dishka(container, app)

    return app


app = create_app()
