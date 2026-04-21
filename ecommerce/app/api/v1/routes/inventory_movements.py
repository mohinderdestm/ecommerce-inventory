from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.schemas.inventory_movement import (
    InventoryMovementCreate,
    InventoryMovementResponse,
    InventoryMovementListResponse,
    InventoryLedgerResponse,
)
from app.services.inventory_movement_service import InventoryMovementService
from app.repositories.inventory_movement_repository import InventoryMovementRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.product_repository import ProductRepository
from app.utils.dependencies import (
    get_current_user,
    require_admin_or_inventory_manager,
    require_admin_or_warehouse_staff,
    get_db,
)
from app.models.inventory_movement import MovementType
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/inventory-movements", tags=["Inventory Movements"])


def get_movement_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> InventoryMovementService:
    return InventoryMovementService(
        movement_repo=InventoryMovementRepository(db),
        warehouse_repo=WarehouseRepository(db),
        product_repo=ProductRepository(db),
    )


@router.post(
    "/",
    response_model=InventoryMovementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record manual inventory movement [Admin / Inventory Manager]",
)
async def record_movement(
    payload: InventoryMovementCreate,
    service: InventoryMovementService = Depends(get_movement_service),
    current_user: dict = Depends(require_admin_or_inventory_manager),
):

    return await service.record_manual_movement(payload, performed_by=current_user["_id"])


@router.get(
    "/",
    response_model=InventoryMovementListResponse,
    summary="List all inventory movements",
)
async def list_movements(
    product_id: Optional[str] = Query(default=None),
    warehouse_id: Optional[str] = Query(default=None),
    movement_type: Optional[MovementType] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: InventoryMovementService = Depends(get_movement_service),
    _: dict = Depends(require_admin_or_warehouse_staff),
):
    return await service.list_movements(
        product_id=product_id,
        warehouse_id=warehouse_id,
        movement_type=movement_type,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/ledger/{product_id}",
    response_model=InventoryLedgerResponse,
    summary="Get inventory ledger for a product",
)
async def get_ledger(
    product_id: str,
    service: InventoryMovementService = Depends(get_movement_service),
    _: dict = Depends(require_admin_or_warehouse_staff),
):
    return await service.get_product_ledger(product_id)
