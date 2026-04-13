"""rest_api/src/presentation/http/routers/ibay.py."""

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi import status

from src.application.dtos.request.ibay import CreateOrderRequestDTO
from src.application.dtos.request.ibay import CreateProductRequestDTO
from src.application.dtos.response.ibay import OrderResponseDTO
from src.application.dtos.response.ibay import ProductResponseDTO
from src.application.interactors.ibay import CreateOrderInteractor
from src.application.interactors.ibay import CreateProductInteractor
from src.application.interactors.ibay import GetOrdersInteractor
from src.application.interactors.ibay import GetProductsInteractor
from src.domain.exceptions import ProductNotFoundException
from src.domain.exceptions import WalletNotFoundException
from src.presentation.http.dependencies.auth import CurrentUserId
from src.presentation.http.responses import create_error_responses

router = APIRouter(prefix="/api/v1/ibay", tags=["ibay"])


@router.get(
    "/products",
    response_model=list[ProductResponseDTO],
    summary="Get All Products",
    description="Retrieve a list of all active products on iBay.",
)
@inject
async def get_products(
    interactor: FromDishka[GetProductsInteractor],
) -> list[ProductResponseDTO]:
    """Retrieve all iBay products."""
    return await interactor()


@router.post(
    "/products",
    response_model=ProductResponseDTO,
    status_code=status.HTTP_201_CREATED,
    responses=create_error_responses(WalletNotFoundException),
    summary="Create Product",
    description="Create a new product listing on iBay.",
)
@inject
async def create_product(
    request: CreateProductRequestDTO,
    user_id: CurrentUserId,
    interactor: FromDishka[CreateProductInteractor],
) -> ProductResponseDTO:
    """Create a new iBay product."""
    request.user_id = user_id
    return await interactor(user_id, request)


@router.get(
    "/orders",
    response_model=list[OrderResponseDTO],
    summary="Get My Orders",
    description="Retrieve all orders placed by the current user.",
)
@inject
async def get_my_orders(
    user_id: CurrentUserId,
    interactor: FromDishka[GetOrdersInteractor],
) -> list[OrderResponseDTO]:
    """Get all orders for the current user."""
    return await interactor(user_id)


@router.post(
    "/orders",
    response_model=OrderResponseDTO,
    status_code=status.HTTP_201_CREATED,
    responses=create_error_responses(ProductNotFoundException),
    summary="Create Order",
    description="Place an order for an iBay product.",
)
@inject
async def create_order(
    request: CreateOrderRequestDTO,
    user_id: CurrentUserId,
    interactor: FromDishka[CreateOrderInteractor],
) -> OrderResponseDTO:
    """Create a new order."""
    request.buyer_user_id = user_id
    return await interactor(user_id, request)
