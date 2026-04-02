"""ethereum/src/domain/value_objects/asset/asset_type.py."""

from enum import Enum


class AssetType(str, Enum):
    """Value object (Enum) representing the type of crypto asset."""

    NATIVE = "native"
    ERC20 = "erc20"
