"""ethereum/src/application/interactors/block_processor.py."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from src.application.ports.events import EventPublisher
from src.application.ports.gateways import TransactionGateway
from src.application.ports.gateways import UnitOfWork
from src.application.ports.gateways import WalletGateway
from src.application.ports.providers import Web3Provider
from src.application.ports.utils import IdGenerator
from src.application.ports.utils import TimeProvider
from src.domain.entities.transaction import Transaction
from src.domain.entities.wallet import Wallet
from src.domain.value_objects.transaction import TransactionStatus

logger = logging.getLogger(__name__)


class ProcessNewBlockInteractor:
    """Use case for parsing a new block and processing relevant transactions."""

    def __init__(  # noqa: PLR0913
        self,
        wallet_gateway: WalletGateway,
        transaction_gateway: TransactionGateway,
        uow: UnitOfWork,
        web3_provider: Web3Provider,
        event_publisher: EventPublisher,
        id_generator: IdGenerator,
        time_provider: TimeProvider,
    ) -> None:
        """Initialize the interactor with gateways and providers."""
        self.wallet_gateway = wallet_gateway
        self.transaction_gateway = transaction_gateway
        self.uow = uow
        self.web3_provider = web3_provider
        self.event_publisher = event_publisher
        self.id_generator = id_generator
        self.time_provider = time_provider

    async def __call__(self, block_hash: str) -> None:
        """Fetch block, filter transactions, and update DB & balances."""
        block = await self.web3_provider.w3.eth.get_block(
            block_hash, full_transactions=True
        )
        if not block or not block.get("transactions"):
            return

        tracked_map = await self._get_tracked_wallets(block["transactions"])
        if not tracked_map:
            return

        now = self.time_provider.now()

        for tx in block["transactions"]:
            await self._process_transaction(tx, tracked_map, now)

    async def _get_tracked_wallets(
        self, transactions: list[dict[str, Any]]
    ) -> dict[str, Wallet]:
        """Extract addresses from block and fetch matching wallets from DB."""
        addresses_in_block = set()
        for tx in transactions:
            if tx.get("from"):
                addresses_in_block.add(tx["from"].lower())
            if tx.get("to"):
                addresses_in_block.add(tx["to"].lower())

        if not addresses_in_block:
            return {}

        matched_wallets = await self.wallet_gateway.get_wallets_by_addresses(
            list(addresses_in_block)
        )
        return {w.address.lower(): w for w in matched_wallets}

    async def _process_transaction(
        self, tx: dict[str, Any], tracked_map: dict[str, Wallet], now: datetime
    ) -> None:
        """Process a single transaction if it belongs to a tracked wallet."""
        from_addr = tx.get("from", "").lower() if tx.get("from") else ""
        to_addr = tx.get("to", "").lower() if tx.get("to") else ""

        is_from_us = from_addr in tracked_map
        is_to_us = to_addr in tracked_map

        if not is_from_us and not is_to_us:
            return

        tx_hash_hex = tx["hash"].hex()
        logger.info("Found relevant transaction %s in new block!", tx_hash_hex)

        receipt = await self.web3_provider.get_transaction_receipt(tx_hash_hex)
        if not receipt:
            return

        existing_tx = await self.transaction_gateway.get_transaction_by_hash(
            tx_hash_hex
        )
        is_success = receipt.get("status") == 1

        gas_used = Decimal(str(receipt.get("gasUsed", 0)))
        gas_price = Decimal(
            str(receipt.get("effectiveGasPrice", tx.get("gasPrice", 0)))
        )
        fee_eth = self.web3_provider.w3.from_wei(gas_used * gas_price, "ether")
        value_eth = self.web3_provider.w3.from_wei(tx.get("value", 0), "ether")

        wallet = tracked_map.get(to_addr) if is_to_us else tracked_map.get(from_addr)
        if not wallet:
            return

        async with self.uow:
            if existing_tx:
                await self._update_existing_transaction(
                    existing_tx, is_success, fee_eth, wallet, tx_hash_hex, now
                )
            elif is_success:
                await self._create_new_transaction(
                    tx, tx_hash_hex, fee_eth, value_eth, wallet, now
                )

    async def _update_existing_transaction(  # noqa: PLR0913
        self,
        existing_tx: Transaction,
        is_success: bool,  # noqa: FBT001
        fee_eth: Decimal,
        wallet: Wallet,
        tx_hash_hex: str,
        now: datetime,
    ) -> None:
        """Update a pending transaction that was found in the new block."""
        if existing_tx.status != TransactionStatus.PENDING:
            return

        if is_success:
            existing_tx.mark_success(fee=fee_eth)
        else:
            existing_tx.mark_failed()

        await self.transaction_gateway.update_transaction(existing_tx)

        if is_success:
            await self._update_wallet_balance(wallet, now)

        await self.event_publisher.publish_transaction_status_updated(
            wallet.user_id,
            existing_tx.id,
            existing_tx.status.value,
            tx_hash_hex,
        )

    async def _create_new_transaction(  # noqa: PLR0913
        self,
        tx: dict[str, Any],
        tx_hash_hex: str,
        fee_eth: Decimal,
        value_eth: Decimal,
        wallet: Wallet,
        now: datetime,
    ) -> None:
        """Create a new transaction record for incoming transfers."""
        new_tx = Transaction(
            id=self.id_generator.generate(),
            wallet_id=wallet.id,
            tx_hash=tx_hash_hex,
            from_address=tx.get("from"),
            to_address=tx.get("to"),
            value=value_eth,
            tx_fee=fee_eth,
            status=TransactionStatus.SUCCESS,
            created_at=now,
        )
        saved_tx = await self.transaction_gateway.add_transaction(new_tx)

        await self._update_wallet_balance(wallet, now)

        await self.event_publisher.publish_transaction_status_updated(
            wallet.user_id, saved_tx.id, saved_tx.status.value, tx_hash_hex
        )

    async def _update_wallet_balance(self, wallet: Wallet, now: datetime) -> None:
        """Fetch current balance from blockchain, update DB, and publish event."""
        new_balance = await self.web3_provider.get_balance(wallet.address)
        wallet.update_balance(new_balance, now)
        await self.wallet_gateway.update_wallet(wallet)

        await self.event_publisher.publish_balance_updated(
            wallet.user_id, wallet.id, wallet.balance
        )
