"""ibay/src/presentation/amqp/consumers/__init__.py."""

from faststream.rabbit import RabbitRouter

from .ethereum import router as eth_router

router = RabbitRouter()

router.include_router(eth_router)

__all__ = ("router",)
