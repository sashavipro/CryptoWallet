"""rest_api/src/presentation/http/routers/ibay.py."""

import uuid

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status

from src.application.dtos.request.ibay import CreateOrderRequestDTO
from src.application.dtos.request.ibay import CreateOrderSchema
from src.application.dtos.request.ibay import CreateProductRequestDTO
from src.application.dtos.request.ibay import CreateProductSchema
from src.application.dtos.request.ibay import UpdateOrderRequestDTO
from src.application.dtos.request.ibay import UpdateStatusSchema
from src.application.dtos.response.ibay import OrderResponseDTO
from src.application.dtos.response.ibay import ProductResponseDTO
from src.application.interactors.ibay import CreateOrderInteractor
from src.application.interactors.ibay import CreateProductInteractor
from src.application.interactors.ibay import GetOldestDeliveryOrderInteractor
from src.application.interactors.ibay import GetOrderByTxHashInteractor
from src.application.interactors.ibay import GetOrdersInteractor
from src.application.interactors.ibay import GetProductsInteractor
from src.application.interactors.ibay import UpdateOrderStatusInteractor
from src.domain.exceptions import ProductNotFoundException
from src.domain.exceptions import WalletNotFoundException
from src.domain.value_objects.order_status import OrderStatus
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
    body: CreateProductSchema,
    user_id: CurrentUserId,
    interactor: FromDishka[CreateProductInteractor],
) -> ProductResponseDTO:
    """Create a new iBay product."""
    dto = CreateProductRequestDTO(
        user_id=user_id,
        wallet_id=body.wallet_id,
        title=body.title,
        price_eth=body.price_eth,
        photo_url=body.photo_url,
    )
    return await interactor(user_id, dto)


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
    body: CreateOrderSchema,
    user_id: CurrentUserId,
    interactor: FromDishka[CreateOrderInteractor],
) -> OrderResponseDTO:
    """Place a new order."""
    dto = CreateOrderRequestDTO(
        product_id=body.product_id,
        buyer_user_id=user_id,
        tx_hash=body.tx_hash,
        price_eth=body.price_eth,
    )
    return await interactor(user_id, dto)


@router.get(
    "/internal/orders/by-tx/{tx_hash}",
    response_model=OrderResponseDTO,
    include_in_schema=False,
)
@inject
async def get_order_by_tx(
    tx_hash: str, interactor: FromDishka[GetOrderByTxHashInteractor]
) -> OrderResponseDTO:
    """Retrieve an order by its transaction hash (Internal system endpoint)."""
    order = await interactor(tx_hash)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )
    return order


@router.get(
    "/internal/orders/delivery/oldest",
    response_model=OrderResponseDTO,
    include_in_schema=False,
)
@inject
async def get_oldest_delivery_order(
    interactor: FromDishka[GetOldestDeliveryOrderInteractor],
) -> OrderResponseDTO:
    """Retrieve the oldest order in DELIVERY status (Internal system endpoint)."""
    order = await interactor()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No orders in delivery"
        )
    return order


@router.patch(
    "/internal/orders/{order_id}/status",
    include_in_schema=False,
)
@inject
async def update_order_status(
    order_id: uuid.UUID,
    body: UpdateStatusSchema,
    interactor: FromDishka[UpdateOrderStatusInteractor],
) -> dict:
    """Update an order's status (Internal system endpoint)."""
    try:
        new_status = OrderStatus(body.status)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status value: {body.status}",
        ) from e

    dto = UpdateOrderRequestDTO(
        order_id=order_id,
        status=new_status,
        return_tx_hash=body.return_tx_hash,
        tx_hash=body.tx_hash,
        trigger_refund=body.trigger_refund,
    )

    await interactor(dto)
    return {"status": "success"}
