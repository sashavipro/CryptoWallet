"""rest_api/src/presentation/http/main.py."""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dishka.integrations.fastapi import setup_dishka
from dishka.integrations.faststream import setup_dishka as setup_dishka_faststream
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from faststream import FastStream
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

import src.presentation.amqp.consumers  # noqa: F401
from src.domain.exceptions import DomainException
from src.infrastructure.log_config import setup_logging
from src.infrastructure.message_broker.broker import broker
from src.infrastructure.settings import cors_settings
from src.ioc.container import create_container
from src.presentation.http.exception_handlers import domain_exception_handler
from src.presentation.http.exception_handlers import http_exception_handler
from src.presentation.http.exception_handlers import validation_exception_handler
from src.presentation.http.exception_handlers import value_error_handler
from src.presentation.http.routers.asset import router as asset_router
from src.presentation.http.routers.auth import router as auth_router
from src.presentation.http.routers.chat import router as chat_router
from src.presentation.http.routers.faucet import router as faucet_router
from src.presentation.http.routers.ibay import router as ibay_router
from src.presentation.http.routers.pages import router as pages_router
from src.presentation.http.routers.profile import router as profile_router
from src.presentation.http.routers.transaction import router as transaction_router
from src.presentation.http.routers.wallet import router as wallet_router

setup_logging()
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[5]
STATIC_DIR = PROJECT_ROOT / "frontend" / "static"

MAX_RETRIES = 5


async def background_balance_sync(container) -> None:
    """Trigger the background balance sync every 30 seconds."""
    from src.application.interactors.wallet import SyncAllWalletsBalanceInteractor

    while True:
        try:
            async with container() as request_container:
                sync_interactor = await request_container.get(
                    SyncAllWalletsBalanceInteractor
                )
                await sync_interactor()
        except Exception:
            logger.exception("Background sync error")

        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the application lifespan, including background connections."""
    for attempt in range(MAX_RETRIES):
        try:
            await broker.start()
            logger.info("Successfully connected to RabbitMQ!")
            break
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            logger.warning("RabbitMQ is not ready yet, retrying in 5s... Error: %s", e)
            await asyncio.sleep(5)
    sync_task = asyncio.create_task(background_balance_sync(app.state.dishka_container))
    yield
    sync_task.cancel()
    await broker.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="CryptoWallet API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_settings.origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.include_router(pages_router)
    app.include_router(auth_router)
    app.include_router(profile_router)
    app.include_router(faucet_router)
    app.include_router(wallet_router)
    app.include_router(transaction_router)
    app.include_router(asset_router)
    app.include_router(chat_router)
    app.include_router(ibay_router)

    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    container = create_container()

    setup_dishka(container, app)

    faststream_app = FastStream(broker)
    setup_dishka_faststream(container, faststream_app)

    return app


app = create_app()
