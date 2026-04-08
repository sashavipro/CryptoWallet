"""ethereum/src/presentation/amqp/consumers/__init__.py."""

from faststream.rabbit import RabbitRouter

from .faucet import router as faucet_router
from .transaction import router as transaction_router
from .wallet import router as wallet_router

router = RabbitRouter()

router.include_router(wallet_router)
router.include_router(transaction_router)
router.include_router(faucet_router)

__all__ = ("router",)
