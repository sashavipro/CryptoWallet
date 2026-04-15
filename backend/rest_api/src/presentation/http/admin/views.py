"""rest_api/src/presentation/http/admin/views.py."""

from sqladmin import ModelView

from src.infrastructure.persistence.database.models import Order
from src.infrastructure.persistence.database.models import Product
from src.infrastructure.persistence.database.models import Transaction
from src.infrastructure.persistence.database.models import User
from src.infrastructure.persistence.database.models import Wallet


class UserAdmin(ModelView, model=User):  # type: ignore[call-arg, misc]
    """Admin view for the User model."""

    column_list = [User.id, User.username, User.email]
    column_searchable_list = [User.username, User.email]
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-users"


class WalletAdmin(ModelView, model=Wallet):  # type: ignore[call-arg, misc]
    """Admin view for the Wallet model."""

    column_list = [Wallet.id, Wallet.user_id, Wallet.address, Wallet.balance]
    column_searchable_list = [Wallet.address]
    name = "Кошелек"
    name_plural = "Кошельки"
    icon = "fa-solid fa-wallet"


class OrderAdmin(ModelView, model=Order):  # type: ignore[call-arg, misc]
    """Admin view for the Order model."""

    column_list = [Order.id, Order.buyer_user_id, Order.status, Order.price_eth]
    column_sortable_list = [Order.status, Order.created_at]
    name = "Заказ iBay"
    name_plural = "Заказы iBay"
    icon = "fa-solid fa-shopping-cart"


class TransactionAdmin(ModelView, model=Transaction):  # type: ignore[call-arg, misc]
    """Admin view for the Transaction model."""

    column_list = [Transaction.id, Transaction.tx_hash, Transaction.status]
    name = "Транзакция"
    name_plural = "Транзакции"
    icon = "fa-solid fa-exchange-alt"


class ProductAdmin(ModelView, model=Product):  # type: ignore[call-arg, misc]
    """Admin view for the Product model."""

    column_list = [Product.id, Product.title, Product.price_eth]
    name = "Товар"
    name_plural = "Товары"
    icon = "fa-solid fa-box"
