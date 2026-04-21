from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.schemas.sales_order import (
    SalesOrderCreateRequest, StatusUpdateRequest, ReturnRequest,
    SalesOrderResponse, SalesOrderListResponse, APIResponse,
)
from app.services.sales_order_service import SalesOrderService
from app.repositories.sales_order_repository import SalesOrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.variant_repository import VariantRepository
from app.utils.dependencies import get_current_user, require_admin, require_roles, get_db
from app.models.user import UserRole
from app.models.sales_order import SalesOrderStatus
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/sales-orders", tags=["Sales Orders"])


from app.repositories.inventory_movement_repository import InventoryMovementRepository

def get_order_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> SalesOrderService:
    return SalesOrderService(
        order_repo=SalesOrderRepository(db),
        product_repo=ProductRepository(db),
        warehouse_repo=WarehouseRepository(db),
        variant_repo=VariantRepository(db),
        movement_repo=InventoryMovementRepository(db),
    )


# Create 

@router.post(
    "/",
    response_model=SalesOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a sales order [Customer / Admin]",
    description=(
        "Creates a draft sales order. Stock is NOT reserved yet — "
        "call `/confirm` to validate stock and reserve it."
    ),
)
async def create_order(
    payload: SalesOrderCreateRequest,
    service: SalesOrderService = Depends(get_order_service),
    current_user: dict = Depends(require_roles(
        UserRole.CUSTOMER, UserRole.ADMIN, UserRole.WAREHOUSE_STAFF
    )),
):
    return await service.create_order(payload, customer=current_user)


#  List & Get 

@router.get(
    "/",
    response_model=SalesOrderListResponse,
    summary="List sales orders",
    description="Customers see only their own orders. Admins see all.",
)
async def list_orders(
    status: Optional[SalesOrderStatus] = Query(default=None),
    warehouse_id: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None, description="Search by order number or customer name"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: SalesOrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user),
):
    return await service.list_orders(
        requesting_user=current_user,
        status=status.value if status else None,
        warehouse_id=warehouse_id,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/summary",
    summary="Get order count and value summary by status",
)
async def get_summary(
    service: SalesOrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user),
):
    customer_id = current_user["_id"] if current_user["role"] == "customer" else None
    return await service.get_order_summary(customer_id)


@router.get(
    "/{order_id}",
    response_model=SalesOrderResponse,
    summary="Get sales order by ID",
)
async def get_order(
    order_id: str,
    service: SalesOrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user),
):
    return await service.get_order(order_id, requesting_user=current_user)


# Status Transitions 

@router.post(
    "/{order_id}/confirm",
    response_model=SalesOrderResponse,
    summary="Confirm order — validates and reserves stock [Admin / Warehouse Staff]",
)
async def confirm_order(
    order_id: str,
    payload: StatusUpdateRequest = StatusUpdateRequest(),
    service: SalesOrderService = Depends(get_order_service),
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.WAREHOUSE_STAFF)),
):
    return await service.confirm_order(order_id, payload, updated_by=current_user["_id"])


@router.post(
    "/{order_id}/pack",
    response_model=SalesOrderResponse,
    summary="Mark order as packed [Admin / Warehouse Staff]",
)
async def pack_order(
    order_id: str,
    payload: StatusUpdateRequest = StatusUpdateRequest(),
    service: SalesOrderService = Depends(get_order_service),
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.WAREHOUSE_STAFF)),
):
    return await service.pack_order(order_id, payload, updated_by=current_user["_id"])


@router.post(
    "/{order_id}/ship",
    response_model=SalesOrderResponse,
    summary="Mark order as shipped / dispatched [Admin]",
)
async def ship_order(
    order_id: str,
    payload: StatusUpdateRequest = StatusUpdateRequest(),
    service: SalesOrderService = Depends(get_order_service),
    current_user: dict = Depends(require_admin),
):
    return await service.ship_order(order_id, payload, updated_by=current_user["_id"])


@router.post(
    "/{order_id}/deliver",
    response_model=SalesOrderResponse,
    summary="Mark order as delivered [Admin]",
)
async def deliver_order(
    order_id: str,
    payload: StatusUpdateRequest = StatusUpdateRequest(),
    service: SalesOrderService = Depends(get_order_service),
    current_user: dict = Depends(require_admin),
):
    return await service.deliver_order(order_id, payload, updated_by=current_user["_id"])


@router.post(
    "/{order_id}/cancel",
    response_model=SalesOrderResponse,
    summary="Cancel order — releases reserved stock [Admin / Customer]",
)
async def cancel_order(
    order_id: str,
    payload: StatusUpdateRequest = StatusUpdateRequest(),
    service: SalesOrderService = Depends(get_order_service),
    current_user: dict = Depends(require_roles(
        UserRole.ADMIN, UserRole.CUSTOMER, UserRole.WAREHOUSE_STAFF
    )),
):
    return await service.cancel_order(order_id, payload, updated_by=current_user["_id"])


@router.post(
    "/{order_id}/return",
    response_model=SalesOrderResponse,
    summary="Return order — restores stock [Admin]",
    description="Full or partial return. Stock is restored to the warehouse.",
)
async def return_order(
    order_id: str,
    payload: ReturnRequest,
    service: SalesOrderService = Depends(get_order_service),
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.WAREHOUSE_STAFF)),
):
    return await service.return_order(order_id, payload, updated_by=current_user["_id"])