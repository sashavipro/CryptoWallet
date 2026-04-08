"""rest_api/src/presentation/amqp/consumers/transaction.py."""

import logging
import uuid

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject
from faststream.rabbit import RabbitRouter

from src.application.ports.gateways import TransactionGateway
from src.application.ports.gateways import UnitOfWork
from src.application.ports.gateways.wallet import WalletGateway
from src.infrastructure.message_broker.broker import broker

logger = logging.getLogger(__name__)

router = RabbitRouter()


@router.subscriber("eth.tx_initiated")
@inject
async def handle_tx_initiated(
    payload: dict,
    tx_gateway: FromDishka[TransactionGateway],
    wallet_gateway: FromDishka[WalletGateway],
    uow: FromDishka[UnitOfWork],
) -> None:
    """Update the transaction hash when a transaction is successfully initiated."""
    tx_id = uuid.UUID(payload["tx_id"])
    tx_hash = payload["tx_hash"]

    async with uow:
        tx = await tx_gateway.get_transaction_by_id(tx_id)
        if tx:
            tx.tx_hash = tx_hash
            await tx_gateway.update_transaction(tx)
            logger.info("Transaction %s hash updated to %s", tx_id, tx_hash)

            wallet = await wallet_gateway.get_wallet_by_id(tx.wallet_id)
            if wallet:
                await broker.publish(
                    {
                        "user_id": str(wallet.user_id),
                        "wallet_id": str(tx.wallet_id),
                        "tx_hash": tx_hash,
                        "status": "pending",
                        "value": str(tx.value),
                    },
                    queue="ws.tx_updated",
                )


@router.subscriber("eth.tx_failed_initiation")
@inject
async def handle_tx_failed_initiation(
    payload: dict,
    tx_gateway: FromDishka[TransactionGateway],
    wallet_gateway: FromDishka[WalletGateway],
    uow: FromDishka[UnitOfWork],
) -> None:
    """Handle transaction initiation failure."""
    tx_id = uuid.UUID(payload["tx_id"])
    error = payload.get("error", "Unknown error")

    async with uow:
        tx = await tx_gateway.get_transaction_by_id(tx_id)
        if tx:
            tx.status = "failed"
            await tx_gateway.update_transaction(tx)
            logger.info("Transaction %s marked as failed: %s", tx_id, error)

            wallet = await wallet_gateway.get_wallet_by_id(tx.wallet_id)
            if wallet:
                await broker.publish(
                    {
                        "user_id": str(wallet.user_id),
                        "wallet_id": str(tx.wallet_id),
                        "tx_hash": tx.tx_hash,
                        "status": "failed",
                        "value": str(tx.value),
                        "error": error,
                    },
                    queue="ws.tx_updated",
                )


@router.subscriber("eth.tx_success")
@inject
async def handle_tx_success(
    payload: dict,
    tx_gateway: FromDishka[TransactionGateway],
    wallet_gateway: FromDishka[WalletGateway],
    uow: FromDishka[UnitOfWork],
) -> None:
    """Handle successful transaction mining on the blockchain."""
    tx_id = uuid.UUID(payload["tx_id"])

    async with uow:
        tx = await tx_gateway.get_transaction_by_id(tx_id)
        if tx:
            tx.status = "success"
            await tx_gateway.update_transaction(tx)
            logger.info("Transaction %s marked as success", tx_id)

            wallet = await wallet_gateway.get_wallet_by_id(tx.wallet_id)
            if wallet:
                await broker.publish(
                    {
                        "user_id": str(wallet.user_id),
                        "wallet_id": str(tx.wallet_id),
                        "tx_hash": tx.tx_hash,
                        "status": "success",
                        "value": str(tx.value),
                    },
                    queue="ws.tx_updated",
                )


@router.subscriber("eth.tx_failed")
@inject
async def handle_tx_failed(
    payload: dict,
    tx_gateway: FromDishka[TransactionGateway],
    wallet_gateway: FromDishka[WalletGateway],
    uow: FromDishka[UnitOfWork],
) -> None:
    """Handle transaction execution failure on the blockchain."""
    tx_id = uuid.UUID(payload["tx_id"])
    error = payload.get("error", "Execution failed on chain")

    async with uow:
        tx = await tx_gateway.get_transaction_by_id(tx_id)
        if tx:
            tx.status = "failed"
            await tx_gateway.update_transaction(tx)
            logger.info("Transaction %s marked as failed execution", tx_id)

            wallet = await wallet_gateway.get_wallet_by_id(tx.wallet_id)
            if wallet:
                await broker.publish(
                    {
                        "user_id": str(wallet.user_id),
                        "wallet_id": str(tx.wallet_id),
                        "tx_hash": tx.tx_hash,
                        "status": "failed",
                        "value": str(tx.value),
                        "error": error,
                    },
                    queue="ws.tx_updated",
                )
