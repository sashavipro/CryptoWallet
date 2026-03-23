"""rest_api/src/presentation/http/main.py."""

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.domain.exceptions import DomainException
from src.infrastructure.log_config import setup_logging
from src.ioc.container import create_container
from src.presentation.http.exception_handlers import domain_exception_handler
from src.presentation.http.exception_handlers import http_exception_handler
from src.presentation.http.exception_handlers import validation_exception_handler
from src.presentation.http.exception_handlers import value_error_handler
from src.presentation.http.routers.auth import router as auth_router
from src.presentation.http.routers.profile import router as profile_router

setup_logging()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="CryptoWallet API", version="1.0.0")

    app.include_router(auth_router)
    app.include_router(profile_router)

    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    container = create_container()
    setup_dishka(container, app)

    return app


app = create_app()
