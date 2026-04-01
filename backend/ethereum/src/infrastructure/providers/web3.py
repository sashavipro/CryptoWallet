"""ethereum/src/infrastructure/providers/web3.py."""

import logging
from decimal import Decimal
from typing import Any

from eth_account import Account
from web3 import AsyncWeb3
from web3.exceptions import TransactionNotFound
from web3.middleware.attrdict import AttributeDictMiddleware
from web3.middleware.pythonic import PythonicMiddleware

from src.application.ports.providers.web3 import Web3Provider
from src.domain.value_objects.shared.address import EthereumAddress
from src.infrastructure.settings import Web3Settings

logger = logging.getLogger(__name__)


class Web3ProviderImpl(Web3Provider):
    """Web3.py implementation for EVM blockchain interaction.

    Includes Fallback & EIP-1559 support.
    """

    def __init__(self, settings: Web3Settings) -> None:
        """Initialize with Web3 settings and prepare fallback nodes."""
        self.settings = settings
        self.w3: AsyncWeb3 | None = None

        primary_urls = [
            url.strip() for url in self.settings.WEB3_PROVIDER_URI.split(",")
        ]
        fallbacks = [
            "https://ethereum-sepolia-rpc.publicnode.com",
            "https://1rpc.io/sepolia",
            "https://rpc.ankr.com/eth_sepolia",
        ]

        self.rpc_nodes = primary_urls + [f for f in fallbacks if f not in primary_urls]

        logger.info(
            "Web3Provider initialized with %d potential RPC nodes.", len(self.rpc_nodes)
        )

    async def _get_working_w3(self) -> AsyncWeb3:
        """Iterate over RPC nodes and return the first working connection."""
        for url in self.rpc_nodes:
            try:
                if url.startswith("ws"):
                    provider = AsyncWeb3.AsyncWebsocketProvider(url)
                else:
                    provider = AsyncWeb3.AsyncHTTPProvider(
                        url, request_kwargs={"timeout": 10}
                    )

                w3 = AsyncWeb3(provider)
                w3.middleware_onion.inject(AttributeDictMiddleware, layer=0)
                w3.middleware_onion.inject(PythonicMiddleware, layer=0)

                if await w3.is_connected():
                    logger.debug("Successfully connected to Web3 Node: %s", url)
                    return w3
            except Exception as e:  # noqa: BLE001
                logger.warning("RPC node %s is unavailable: %s. Trying next...", url, e)

        logger.error(
            "Critical Error: No working RPC nodes found among %s", self.rpc_nodes
        )
        err_msg = "No working Web3 RPC nodes available."
        raise ConnectionError(err_msg)

    async def _check_connection(self) -> None:
        """Ensure active Web3 connection, reconnecting if necessary."""
        if self.w3 and await self.w3.is_connected():
            return

        logger.info("Connecting to a working Web3 RPC node...")
        self.w3 = await self._get_working_w3()

    def create_account(self) -> dict[str, str]:
        """Generate a new wallet account (address and private key)."""
        account = Account.create()
        logger.debug("New account created: %s", account.address)
        return {
            "address": account.address,
            "private_key": account.key.hex(),
        }

    def get_address_from_private_key(self, private_key: str) -> str:
        """Derive the public Ethereum address from a raw private key."""
        account = Account.from_key(private_key)
        return account.address

    async def get_balance(self, address: EthereumAddress) -> Decimal:
        """Get the native currency balance of a given address (e.g., ETH)."""
        await self._check_connection()
        balance_wei = await self.w3.eth.get_balance(address.value)
        balance_eth = self.w3.from_wei(balance_wei, "ether")
        logger.debug("Native balance for %s: %s ETH", address.value, balance_eth)
        return Decimal(str(balance_eth))

    async def get_transaction_count(self, address: EthereumAddress) -> int:
        """Get the number of transactions sent from an address (nonce)."""
        await self._check_connection()
        nonce = await self.w3.eth.get_transaction_count(address.value)
        logger.debug("Nonce for %s: %s", address.value, nonce)
        return nonce

    async def get_gas_price(self) -> Decimal:
        """Get the current gas price from the network."""
        await self._check_connection()
        gas_price_wei = await self.w3.eth.gas_price
        gas_price_gwei = self.w3.from_wei(gas_price_wei, "gwei")
        return Decimal(str(gas_price_gwei))

    async def send_transaction(  # noqa: PLR0913
        self,
        raw_private_key: str,
        from_address: EthereumAddress,
        to_address: EthereumAddress,
        value: Decimal,
        nonce: int,
        gas_limit: int = 21000,
    ) -> str:
        """Send native currency using dynamic Gas Estimation and EIP-1559."""
        await self._check_connection()

        amount_to_send = self.w3.to_wei(value, "ether")

        try:
            gas_estimate = await self.w3.eth.estimate_gas(
                {
                    "from": from_address.value,
                    "to": to_address.value,
                    "value": amount_to_send,
                }
            )
            safe_gas_limit = int(gas_estimate * 1.1)
            logger.debug(
                "Gas estimated: %s (Safe limit: %s)", gas_estimate, safe_gas_limit
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Gas estimation failed: %s. Using fallback limit: %s", e, gas_limit
            )
            safe_gas_limit = gas_limit

        latest_block = await self.w3.eth.get_block("latest")
        base_fee = latest_block.get("baseFeePerGas", await self.w3.eth.gas_price)
        max_priority_fee = self.w3.to_wei(1.5, "gwei")
        max_fee = (base_fee * 2) + max_priority_fee

        transaction = {
            "nonce": nonce,
            "to": to_address.value,
            "value": amount_to_send,
            "gas": safe_gas_limit,
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": max_priority_fee,
            "chainId": await self.w3.eth.chain_id,
        }

        signed_transaction = Account.sign_transaction(transaction, raw_private_key)
        tx_hash = await self.w3.eth.send_raw_transaction(
            signed_transaction.raw_transaction
        )

        formatted_hash = self.w3.to_hex(tx_hash)

        logger.info(
            "EIP-1559 Transaction sent from %s to %s for %s ETH. Hash: %s",
            from_address.value,
            to_address.value,
            value,
            formatted_hash,
        )
        return formatted_hash

    async def get_transaction_receipt(self, tx_hash: str) -> dict[str, Any] | None:
        """Check the status of a transaction on the blockchain."""
        await self._check_connection()
        try:
            receipt = await self.w3.eth.get_transaction_receipt(tx_hash)
            logger.debug(
                "Transaction receipt for %s: status=%s", tx_hash, receipt.get("status")
            )
            return dict(receipt)
        except TransactionNotFound:
            logger.debug("Transaction %s not found on blockchain.", tx_hash)
            return None
        except Exception:
            logger.exception("Error getting transaction receipt for %s", tx_hash)
            return None
