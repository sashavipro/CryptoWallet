"""rest_api/tests/unit/test_ibay_interactor.py."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING
from typing import cast
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from src.application.dtos.request.ibay import UpdateOrderRequestDTO
from src.application.interactors.ibay import UpdateOrderStatusInteractor
from src.domain.value_objects.order_status import OrderStatus

if TYPE_CHECKING:
    from src.application.ports.gateways import OrderGateway
    from src.application.ports.gateways import ProductGateway
    from src.application.ports.gateways import TransactionGateway
    from src.application.ports.gateways import WalletGateway
    from src.application.ports.providers import EthereumWorkerClient
    from src.application.ports.utils import IdGenerator
    from src.application.ports.utils import TimeProvider


@pytest.fixture
def mock_ibay_deps():
    """Mock dependencies for iBay."""
    return {
        "order_gw": AsyncMock(),
        "product_gw": AsyncMock(),
        "wallet_gw": AsyncMock(),
        "tx_gw": AsyncMock(),
        "worker_client": AsyncMock(),
    }


@pytest.fixture
def update_order_interactor(mock_uow, mock_ibay_deps):
    """Update order interactor fixture."""
    return UpdateOrderStatusInteractor(
        order_gateway=cast("OrderGateway", mock_ibay_deps["order_gw"]),
        product_gateway=cast("ProductGateway", mock_ibay_deps["product_gw"]),
        wallet_gateway=cast("WalletGateway", mock_ibay_deps["wallet_gw"]),
        tx_gateway=cast("TransactionGateway", mock_ibay_deps["tx_gw"]),
        worker_client=cast("EthereumWorkerClient", mock_ibay_deps["worker_client"]),
        id_generator=cast("IdGenerator", MagicMock(generate=lambda: uuid.uuid4())),
        time_provider=cast("TimeProvider", MagicMock()),
        uow=mock_uow,
    )


async def test_update_order_failed_with_refund(update_order_interactor, mock_ibay_deps):
    """Test update order failed with refund."""
    order_id = uuid.uuid4()

    mock_order = MagicMock()
    mock_order.id = order_id
    mock_order.product_id = uuid.uuid4()
    mock_order.tx_hash = "0xPayHash"
    mock_order.price_eth = MagicMock(amount=Decimal("1.0"))
    mock_ibay_deps["order_gw"].get_order_by_id.return_value = mock_order

    mock_product = MagicMock(wallet_id=uuid.uuid4())
    mock_ibay_deps["product_gw"].get_product_by_id.return_value = mock_product

    mock_orig_tx = MagicMock(from_address="0xBuyerAddress")
    mock_ibay_deps["tx_gw"].get_transaction_by_hash.return_value = mock_orig_tx

    mock_seller_wallet = MagicMock(
        id=uuid.uuid4(), address="0xSellerAddress", private_key_encrypted="pk"
    )
    mock_ibay_deps["wallet_gw"].get_wallet_by_id.return_value = mock_seller_wallet

    request = UpdateOrderRequestDTO(
        order_id=order_id, status=OrderStatus.FAILED, trigger_refund=True
    )

    await update_order_interactor(request)

    called_tx_id = mock_ibay_deps[
        "worker_client"
    ].publish_send_transaction_event.call_args[1]["tx_id"]

    mock_ibay_deps[
        "worker_client"
    ].publish_send_transaction_event.assert_called_once_with(
        tx_id=called_tx_id,
        private_key_encrypted="pk",
        from_address="0xSellerAddress",
        to_address="0xBuyerAddress",
        value_eth="0.90",
    )

    assert mock_order.status == OrderStatus.FAILED
    assert mock_order.return_tx_hash.startswith("pending_")
    mock_ibay_deps["order_gw"].update_order.assert_called_once_with(mock_order)
