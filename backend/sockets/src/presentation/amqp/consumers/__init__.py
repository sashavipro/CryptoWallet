"""sockets/src/presentation/amqp/consumers/__init__.py."""

from faststream.rabbit import RabbitRouter

from .chat import router as chat_router
from .stats import router as stats_router
from .transaction import router as tx_router

router = RabbitRouter()

router.include_router(chat_router)
router.include_router(tx_router)
router.include_router(stats_router)

__all__ = ("router",)
