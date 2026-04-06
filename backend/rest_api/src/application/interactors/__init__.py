"""rest_api/src/application/interactors/__init__.py."""

from .asset import GetAssetsInteractor
from .faucet import RequestTestnetEthInteractor
from .login import LoginUserInteractor
from .profile import ChangePasswordInteractor
from .profile import DeleteAvatarInteractor
from .profile import GenerateAvatarUploadUrlInteractor
from .profile import GetOtherProfileInteractor
from .profile import GetUserInteractor
from .profile import UpdateUserInteractor
from .register import RegisterUserInteractor
from .stats import GetStatsInteractor
from .stats import IncrementTotalMessagesInteractor
from .transaction import CreatePendingTransactionInteractor
from .transaction import GetTransactionsInteractor
from .wallet import CreateWalletInteractor
from .wallet import DeleteWalletInteractor
from .wallet import GetBalanceInteractor
from .wallet import GetWalletsInteractor
from .wallet import ImportWalletInteractor

__all__ = (
    "ChangePasswordInteractor",
    "CreatePendingTransactionInteractor",
    "CreateWalletInteractor",
    "DeleteAvatarInteractor",
    "DeleteWalletInteractor",
    "GenerateAvatarUploadUrlInteractor",
    "GetAssetsInteractor",
    "GetBalanceInteractor",
    "GetOtherProfileInteractor",
    "GetStatsInteractor",
    "GetTransactionsInteractor",
    "GetUserInteractor",
    "GetWalletsInteractor",
    "ImportWalletInteractor",
    "IncrementTotalMessagesInteractor",
    "LoginUserInteractor",
    "RegisterUserInteractor",
    "RequestTestnetEthInteractor",
    "UpdateUserInteractor",
)
