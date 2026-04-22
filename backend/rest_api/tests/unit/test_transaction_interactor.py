"""rest_api/tests/unit/test_transaction_interactor.py."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING
from typing import cast
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from src.application.dtos.request import CreatePendingTransactionRequest
from src.application.interactors.transaction import CreatePendingTransactionInteractor
from src.domain.entities.transaction import TransactionStatus
from src.domain.exceptions import WalletNotFoundException

if TYPE_CHECKING:
    from src.application.ports.gateways.transaction import TransactionGateway
    from src.application.ports.gateways.wallet import WalletGateway
    from src.application.ports.providers.worker_client import EthereumWorkerClient
    from src.application.ports.utils import IdGenerator
    from src.application.ports.utils import TimeProvider


@pytest.fixture
def mock_wallet_gw():
    """Mock WalletGateway."""
    return AsyncMock()


@pytest.fixture
def mock_tx_gw():
    """Mock TransactionGateway."""
    return AsyncMock()


@pytest.fixture
def mock_worker_client():
    """Mock EthereumWorkerClient."""
    return AsyncMock()


@pytest.fixture
def tx_interactor(mock_uow, mock_wallet_gw, mock_tx_gw, mock_worker_client):
    """Transaction interactor fixture."""
    return CreatePendingTransactionInteractor(
        wallet_gateway=cast("WalletGateway", mock_wallet_gw),
        transaction_gateway=cast("TransactionGateway", mock_tx_gw),
        uow=mock_uow,
        id_generator=cast("IdGenerator", MagicMock(generate=lambda: uuid.uuid4())),
        time_provider=cast("TimeProvider", MagicMock()),
        worker_client=cast("EthereumWorkerClient", mock_worker_client),
    )


async def test_create_pending_tx_success(
    tx_interactor, mock_wallet_gw, mock_tx_gw, mock_worker_client
):
    """Test create pending transaction successfully."""
    user_id = uuid.uuid4()
    wallet_id = uuid.uuid4()

    mock_wallet = MagicMock()
    mock_wallet.id = wallet_id
    mock_wallet.user_id = user_id
    mock_wallet.address = "0x123"
    mock_wallet.private_key_encrypted = "encrypted_pk"
    mock_wallet_gw.get_wallet_by_id.return_value = mock_wallet

    request = CreatePendingTransactionRequest(
        wallet_id=wallet_id, to_address="0x456", value=Decimal("0.5")
    )

    response = await tx_interactor(user_id=user_id, request=request)

    assert response.status == TransactionStatus.PENDING.value
    assert response.value == Decimal("0.5")
    assert response.from_address == "0x123"

    mock_tx_gw.add_transaction.assert_called_once()
    mock_worker_client.publish_send_transaction_event.assert_called_once_with(
        tx_id=str(response.id),
        private_key_encrypted="encrypted_pk",
        from_address="0x123",
        to_address="0x456",
        value_eth="0.5",
    )


async def test_create_pending_tx_not_owner(tx_interactor, mock_wallet_gw):
    """Test create pending transaction for another owner."""
    user_id = uuid.uuid4()
    mock_wallet = MagicMock()
    mock_wallet.user_id = uuid.uuid4()
    mock_wallet_gw.get_wallet_by_id.return_value = mock_wallet

    request = CreatePendingTransactionRequest(
        wallet_id=uuid.uuid4(), to_address="0x456", value=Decimal("1")
    )

    with pytest.raises(WalletNotFoundException):
        await tx_interactor(user_id=user_id, request=request)
