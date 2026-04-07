"""rest_api/src/presentation/amqp/consumers/__init__.py."""

from src.infrastructure.message_broker.broker import broker

from .auth import router as auth_router
from .chat import router as chat_router
from .transaction import router as transaction_router

broker.include_router(auth_router)
broker.include_router(chat_router)
broker.include_router(transaction_router)

__all__ = ("broker",)
