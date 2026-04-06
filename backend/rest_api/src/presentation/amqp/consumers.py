"""rest_api/src/presentation/amqp/consumers.py."""

import logging
import uuid

from dishka.integrations.faststream import FromDishka
from dishka.integrations.faststream import inject

from src.application.ports.gateways.transaction import TransactionGateway
from src.application.ports.gateways.uow import UnitOfWork
from src.application.ports.providers import MailProvider
from src.infrastructure.message_broker.broker import broker

logger = logging.getLogger(__name__)


@broker.subscriber("eth.tx_initiated")
@inject
async def handle_tx_initiated(
    payload: dict,
    tx_gateway: FromDishka[TransactionGateway],
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


@broker.subscriber("eth.tx_failed_initiation")
@inject
async def handle_tx_failed_initiation(
    payload: dict,
    tx_gateway: FromDishka[TransactionGateway],
    uow: FromDishka[UnitOfWork],
) -> None:
    """Mark a transaction as failed if it could not be initiated."""
    tx_id = uuid.UUID(payload["tx_id"])

    async with uow:
        tx = await tx_gateway.get_transaction_by_id(tx_id)
        if tx:
            tx.mark_failed()
            await tx_gateway.update_transaction(tx)
            logger.warning("Transaction %s marked as FAILED", tx_id)


@broker.subscriber("user_events.registered")
@inject
async def handle_user_registered_event(
    payload: dict, mail_provider: FromDishka[MailProvider]
) -> None:
    """Workflow for processing a successful registration."""
    user_id = payload["user_id"]
    email = payload["email"]
    username = payload["username"]

    logger.info("Event received - User registered: %s (Email: %s)", user_id, email)

    try:
        await mail_provider.send_welcome_email(to_email=email, username=username)
        logger.info("Welcome email sent asynchronously to user ID: %s", user_id)
    except Exception:
        logger.exception("Background task failed to send welcome email to %s", email)
