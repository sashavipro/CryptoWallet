"""rest_api/src/application/dtos/requests/wallet.py."""

import uuid
from dataclasses import dataclass


@dataclass
class CreateWalletRequest:
    """DTO for creating a new crypto wallet from scratch."""

    asset_id: uuid.UUID
    user_id: uuid.UUID | None = None


@dataclass
class ImportWalletRequest:
    """DTO for importing an existing wallet via private key."""

    asset_id: uuid.UUID
    private_key: str
    user_id: uuid.UUID | None = None
