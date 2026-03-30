"""ethereum/src/presentation/http/main.py."""

import asyncio
import logging
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.domain.exceptions import DomainException
from src.infrastructure.log_config import setup_logging
from src.infrastructure.message_broker.broker_instance import broker
from src.ioc.container import create_container
from src.presentation.http.exception_handlers import domain_exception_handler
from src.presentation.http.exception_handlers import http_exception_handler
from src.presentation.http.exception_handlers import validation_exception_handler
from src.presentation.http.exception_handlers import value_error_handler
from src.presentation.http.routers.asset import router as asset_router
from src.presentation.http.routers.faucet import router as faucet_router
from src.presentation.http.routers.transaction import router as transaction_router
from src.presentation.http.routers.wallet import router as wallet_router

setup_logging()
logger = logging.getLogger(__name__)

MAX_RETRIES = 5


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the application lifespan, including background connections."""
    for attempt in range(MAX_RETRIES):
        try:
            await broker.startup()
            logger.info("Successfully connected to RabbitMQ!")
            break
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            logger.warning("RabbitMQ is not ready yet, retrying in 5s... Error: %s", e)
            await asyncio.sleep(5)

    yield
    await broker.shutdown()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application for Ethereum microservice."""
    app = FastAPI(title="Ethereum Service API", version="1.0.0", lifespan=lifespan)

    app.include_router(faucet_router)
    app.include_router(wallet_router)
    app.include_router(transaction_router)
    app.include_router(asset_router)

    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    container = create_container()
    setup_dishka(container, app)

    return app


app = create_app()
