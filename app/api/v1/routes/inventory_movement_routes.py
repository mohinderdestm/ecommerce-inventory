from typing import Optional, List

from fastapi import APIRouter, Depends, Query

from app.schemas.inventory_movement_schema import (
    InventoryMovementCreate,
    InventoryMovementResponse,
)
from app.services.inventory_movement_service import InventoryMovementService
from app.utils.dependencies import get_current_user, get_request_audit_context

router = APIRouter(prefix="/inventory-movements", tags=["Inventory Movements"])


@router.post("/", response_model=dict)
async def create_inventory_movement(
    data: InventoryMovementCreate,
    user=Depends(get_current_user),
    audit_context=Depends(get_request_audit_context),
):
    return await InventoryMovementService.create_manual_movement(
        data, user, audit_context=audit_context
    )


@router.get("/", response_model=List[InventoryMovementResponse])
async def list_inventory_movements(
    product_id: Optional[str] = Query(default=None),
    warehouse_id: Optional[str] = Query(default=None),
    movement_type: Optional[str] = Query(default=None),
    reference_type: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    user=Depends(get_current_user),
):
    return await InventoryMovementService.list_movements(
        user=user,
        product_id=product_id,
        warehouse_id=warehouse_id,
        movement_type=movement_type,
        reference_type=reference_type,
        limit=limit,
    )


@router.get("/ledger/{product_id}")
async def get_product_ledger(
    product_id: str,
    warehouse_id: Optional[str] = Query(default=None),
    user=Depends(get_current_user),
):
    return await InventoryMovementService.product_ledger(
        product_id=product_id,
        warehouse_id=warehouse_id,
        user=user,
    )
