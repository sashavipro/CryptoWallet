"""ethereum/src/application/dtos/requests/wallet.py."""

import uuid
from dataclasses import dataclass


@dataclass
class CreateWalletRequest:
    """DTO for creating a new crypto wallet from scratch."""

    user_id: uuid.UUID
    asset_id: uuid.UUID


@dataclass
class ImportWalletRequest:
    """DTO for importing an existing wallet via private key."""

    user_id: uuid.UUID
    asset_id: uuid.UUID
    private_key: str
