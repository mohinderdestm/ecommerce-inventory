from typing import Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException

from app.schemas.warehouse import (
    WarehouseCreateRequest, WarehouseUpdateRequest,
    WarehouseResponse, WarehouseListResponse,
    StaffAssignRequest, StockUpdateRequest, StockTransferRequest,
    WarehouseStockSummary, TransferResponse, APIResponse,
)
from app.services.warehouse_service import WarehouseService
from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.user_repository import UserRepository
from app.utils.dependencies import (
    get_current_user, require_admin,
    require_admin_or_warehouse_staff, get_db,
)
from app.models.user import UserRole
from app.models.warehouse import WarehouseStatus, TransferStatus
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])


from app.repositories.inventory_movement_repository import InventoryMovementRepository

def get_warehouse_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> WarehouseService:
    return WarehouseService(
        warehouse_repo=WarehouseRepository(db),
        product_repo=ProductRepository(db),
        user_repo=UserRepository(db),
        movement_repo=InventoryMovementRepository(db),
    )


# Assignment check helper 

async def verify_warehouse_access(
    warehouse_id: str,
    current_user: dict,
    service: WarehouseService,
):
    """
    Admins can access any warehouse.
    Warehouse staff can only access warehouses they are assigned to.
    """
    if current_user["role"] == UserRole.ADMIN.value:
        return  # admin passes always

    wh = await service.get_warehouse(warehouse_id)
    if current_user["_id"] not in wh.get("staff_ids", []):
        raise HTTPException(
            status_code=403,
            detail="Access denied. You are not assigned to this warehouse."
        )


# CRUD — Admin only 

@router.post(
    "/",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new warehouse [Admin only]",
)
async def create_warehouse(
    payload: WarehouseCreateRequest,
    service: WarehouseService = Depends(get_warehouse_service),
    current_user: dict = Depends(require_admin),
):
    return await service.create_warehouse(payload, created_by=current_user["_id"])


@router.get(
    "/",
    response_model=WarehouseListResponse,
    summary="List warehouses",
    description="Admins see all warehouses. Warehouse staff see only their assigned warehouses.",
)
async def list_warehouses(
    search: Optional[str] = Query(default=None),
    status: Optional[WarehouseStatus] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: WarehouseService = Depends(get_warehouse_service),
    current_user: dict = Depends(require_admin_or_warehouse_staff),
):
    result = await service.list_warehouses(
        status=status.value if status else None,
        search=search, page=page, page_size=page_size,
    )
    # Staff only see their assigned warehouses
    if current_user["role"] == UserRole.WAREHOUSE_STAFF.value:
        result["warehouses"] = [
            wh for wh in result["warehouses"]
            if current_user["_id"] in wh.get("staff_ids", [])
        ]
        result["total"] = len(result["warehouses"])
    return result


@router.get(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
    summary="Get warehouse by ID",
)
async def get_warehouse(
    warehouse_id: str,
    service: WarehouseService = Depends(get_warehouse_service),
    current_user: dict = Depends(require_admin_or_warehouse_staff),
):
    await verify_warehouse_access(warehouse_id, current_user, service)
    return await service.get_warehouse(warehouse_id)


@router.put(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
    summary="Update warehouse [Admin only]",
)
async def update_warehouse(
    warehouse_id: str,
    payload: WarehouseUpdateRequest,
    service: WarehouseService = Depends(get_warehouse_service),
    current_user: dict = Depends(require_admin),
):
    return await service.update_warehouse(warehouse_id, payload, updated_by=current_user["_id"])


@router.delete(
    "/{warehouse_id}",
    response_model=APIResponse,
    summary="Delete warehouse [Admin only]",
)
async def delete_warehouse(
    warehouse_id: str,
    service: WarehouseService = Depends(get_warehouse_service),
    _: dict = Depends(require_admin),
):
    await service.delete_warehouse(warehouse_id)
    return {"success": True, "message": "Warehouse deleted successfully."}


# Staff Assignment — Admin only 

@router.post(
    "/{warehouse_id}/staff",
    response_model=WarehouseResponse,
    summary="Assign staff to warehouse [Admin only]",
)
async def assign_staff(
    warehouse_id: str,
    payload: StaffAssignRequest,
    service: WarehouseService = Depends(get_warehouse_service),
    current_user: dict = Depends(require_admin),
):
    return await service.assign_staff(warehouse_id, payload, updated_by=current_user["_id"])


@router.delete(
    "/{warehouse_id}/staff",
    response_model=WarehouseResponse,
    summary="Remove staff from warehouse [Admin only]",
)
async def unassign_staff(
    warehouse_id: str,
    payload: StaffAssignRequest,
    service: WarehouseService = Depends(get_warehouse_service),
    current_user: dict = Depends(require_admin),
):
    return await service.unassign_staff(warehouse_id, payload, updated_by=current_user["_id"])


# Stock Management — Admin + Warehouse Staff (assigned only)

@router.post(
    "/{warehouse_id}/stock",
    summary="Update stock in warehouse [Admin / Warehouse Staff]",
    description="Staff can only update stock in warehouses they are assigned to.",
)
async def update_stock(
    warehouse_id: str,
    payload: StockUpdateRequest,
    service: WarehouseService = Depends(get_warehouse_service),
    current_user: dict = Depends(require_admin_or_warehouse_staff),
):
    await verify_warehouse_access(warehouse_id, current_user, service)
    return await service.update_stock(warehouse_id, payload, updated_by=current_user["_id"])


@router.get(
    "/{warehouse_id}/stock",
    response_model=WarehouseStockSummary,
    summary="Get stock summary for a warehouse [Admin / Warehouse Staff]",
)
async def get_stock_summary(
    warehouse_id: str,
    service: WarehouseService = Depends(get_warehouse_service),
    current_user: dict = Depends(require_admin_or_warehouse_staff),
):
    await verify_warehouse_access(warehouse_id, current_user, service)
    return await service.get_stock_summary(warehouse_id)


@router.get(
    "/stock/product/{product_id}",
    summary="Get stock for a product across all warehouses [Admin / Warehouse Staff]",
)
async def get_product_stock(
    product_id: str,
    service: WarehouseService = Depends(get_warehouse_service),
    _: dict = Depends(require_admin_or_warehouse_staff),
):
    return await service.get_product_stock_across_warehouses(product_id)


# Stock Transfers — Admin + Warehouse Staff (assigned only) 

@router.post(
    "/{warehouse_id}/transfer",
    response_model=TransferResponse,
    summary="Transfer stock between warehouses [Admin / Warehouse Staff]",
    description=(
        "Staff can only initiate transfers FROM warehouses they are assigned to. "
        "Stock is deducted from source and added to destination atomically."
    ),
)
async def transfer_stock(
    warehouse_id: str,
    payload: StockTransferRequest,
    service: WarehouseService = Depends(get_warehouse_service),
    current_user: dict = Depends(require_admin_or_warehouse_staff),
):
    await verify_warehouse_access(warehouse_id, current_user, service)
    return await service.initiate_transfer(warehouse_id, payload, created_by=current_user["_id"])


@router.get(
    "/transfers/list",
    summary="List stock transfers [Admin / Warehouse Staff]",
)
async def list_transfers(
    warehouse_id: Optional[str] = Query(default=None),
    status: Optional[TransferStatus] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: WarehouseService = Depends(get_warehouse_service),
    current_user: dict = Depends(require_admin_or_warehouse_staff),
):
    # Staff can only view transfers for their assigned warehouses
    if current_user["role"] == UserRole.WAREHOUSE_STAFF.value and not warehouse_id:
        raise HTTPException(
            status_code=400,
            detail="Warehouse staff must specify a warehouse_id to view transfers."
        )
    return await service.list_transfers(
        warehouse_id=warehouse_id,
        status=status.value if status else None,
        page=page, page_size=page_size,
    )