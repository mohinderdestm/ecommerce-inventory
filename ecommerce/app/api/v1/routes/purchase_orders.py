from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderStatusUpdate,
    PurchaseOrderReceive,
    PurchaseOrderResponse
)
from app.services import purchase_order_service as service
from app.api.v1.routes.auth import get_current_user

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])

# Ensure admin or inventory_manager role
def require_manager(user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "inventory_manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return user

@router.post("/", response_model=PurchaseOrderResponse)
async def create_purchase_order(
    payload: PurchaseOrderCreate,
    current_user: dict = Depends(require_manager)
):
    return await service.create_purchase_order(payload, created_by=current_user["_id"])

@router.get("/")
async def list_purchase_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    status: str = Query(None),
    current_user: dict = Depends(require_manager)
):
    return await service.list_purchase_orders(skip, limit, status)

@router.get("/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_id: str,
    current_user: dict = Depends(require_manager)
):
    return await service.get_purchase_order(po_id)

@router.patch("/{po_id}/status", response_model=PurchaseOrderResponse)
async def update_po_status(
    po_id: str,
    payload: PurchaseOrderStatusUpdate,
    current_user: dict = Depends(require_manager)
):
    return await service.update_status(po_id, payload, updated_by=current_user["_id"])

@router.post("/{po_id}/receive", response_model=PurchaseOrderResponse)
async def receive_items(
    po_id: str,
    payload: PurchaseOrderReceive,
    current_user: dict = Depends(require_manager)
):
    return await service.receive_items(po_id, payload, received_by=current_user["_id"])
