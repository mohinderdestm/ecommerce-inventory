from fastapi import HTTPException
from datetime import datetime, timezone
from app.models.purchase_order import (
    build_purchase_order_item,
    build_purchase_order_document,
    PurchaseOrderStatus,
    VALID_TRANSITIONS
)
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderReceive, PurchaseOrderStatusUpdate
from app.repositories import purchase_order_repository as repo
from app.services.inventory_movement_service import InventoryMovementService
from app.repositories.inventory_movement_repository import InventoryMovementRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.inventory_movement import InventoryMovementCreate
from app.models.inventory_movement import MovementType
from app.core.database import get_database
from app.services.warehouse_service import WarehouseService
from app.repositories.user_repository import UserRepository

def get_inventory_service() -> InventoryMovementService:
    db = get_database()
    return InventoryMovementService(
        movement_repo=InventoryMovementRepository(db),
        warehouse_repo=WarehouseRepository(db),
        product_repo=ProductRepository(db),
    )

def get_warehouse_svc() -> WarehouseService:
    db = get_database()
    return WarehouseService(
        warehouse_repo=WarehouseRepository(db),
        product_repo=ProductRepository(db),
        user_repo=UserRepository(db),
        movement_repo=InventoryMovementRepository(db),
    )

async def create_purchase_order(data: PurchaseOrderCreate, created_by: str) -> dict:
    items = []
    for i in data.items:
        items.append(
            build_purchase_order_item(
                product_id=i.product_id,
                product_name=i.product_name,
                sku=i.sku,
                ordered_quantity=i.ordered_quantity,
                unit_cost=i.unit_cost,
                variant_id=i.variant_id,
                tax_percentage=i.tax_percentage,
            )
        )

    doc = build_purchase_order_document(
        supplier_id=data.supplier_id,
        supplier_name=data.supplier_name,
        items=items,
        destination_warehouse_id=data.destination_warehouse_id,
        created_by=created_by,
        notes=data.notes,
    )
    po_id = await repo.create_purchase_order(doc)
    return await repo.get_purchase_order(po_id)

async def get_purchase_order(po_id: str) -> dict:
    po = await repo.get_purchase_order(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

async def list_purchase_orders(skip: int = 0, limit: int = 50, status: str = None) -> dict:
    filters = {}
    if status:
        filters["status"] = status
    pos = await repo.list_purchase_orders(skip, limit, filters)
    total = await repo.count_purchase_orders(filters)
    return {"data": pos, "total": total, "skip": skip, "limit": limit}

async def update_status(po_id: str, payload: PurchaseOrderStatusUpdate, updated_by: str) -> dict:
    po = await get_purchase_order(po_id)
    current_status = po["status"]
    new_status = payload.status.value

    # Prevent invalid transitions
    if new_status not in VALID_TRANSITIONS.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {current_status} to {new_status}"
        )

    updates = {
        "status": new_status,
        "updated_at": datetime.now(timezone.utc),
        "updated_by": updated_by
    }

    # Append to history
    new_history = po.get("status_history", [])
    new_history.append({
        "status": new_status,
        "changed_by": updated_by,
        "timestamp": datetime.now(timezone.utc),
        "notes": payload.notes or f"Status changed to {new_status}"
    })
    updates["status_history"] = new_history

    await repo.update_purchase_order(po_id, updates)
    return await get_purchase_order(po_id)

async def receive_items(po_id: str, payload: PurchaseOrderReceive, received_by: str) -> dict:
    po = await get_purchase_order(po_id)
    
    if po["status"] not in [PurchaseOrderStatus.APPROVED.value, PurchaseOrderStatus.PARTIALLY_RECEIVED.value]:
        raise HTTPException(status_code=400, detail="Cannot receive items for a PO that is not approved or partially received")

    updated_items = []
    all_completed = True

    # Map item receipts by product_id (and variant_id)
    receipts_map = {}
    for r in payload.items:
        key = f"{r.product_id}_{r.variant_id}" if r.variant_id else r.product_id
        receipts_map[key] = r.received_quantity

    for item in po["items"]:
        key = f"{item['product_id']}_{item.get('variant_id')}" if item.get('variant_id') else item['product_id']
        qty_to_receive = receipts_map.get(key, 0)

        if qty_to_receive > 0:
            if item["received_quantity"] + qty_to_receive > item["ordered_quantity"]:
                raise HTTPException(status_code=400, detail=f"Cannot receive more than ordered for {item['product_name']}")
            
            item["received_quantity"] += qty_to_receive
            
            # Record inventory inward movement
            inv_payload = InventoryMovementCreate(
                product_id=item["product_id"],
                warehouse_id=po["destination_warehouse_id"],
                movement_type=MovementType.INWARD,
                quantity=qty_to_receive,
                variant_id=item.get("variant_id"),
                remarks=payload.notes or f"Received against PO {po['po_number']}"
            )
            inv_service = get_inventory_service()
            await inv_service.record_manual_movement(inv_payload, performed_by=received_by)

        if item["received_quantity"] < item["ordered_quantity"]:
            all_completed = False
            
        updated_items.append(item)

    # Check and reset low stock alerts for received products
    ws = get_warehouse_svc()
    for product_id in set(r.product_id for r in payload.items):
        await ws.check_and_trigger_low_stock_alert(product_id)

    new_status = PurchaseOrderStatus.COMPLETED.value if all_completed else PurchaseOrderStatus.PARTIALLY_RECEIVED.value

    updates = {
        "items": updated_items,
        "updated_at": datetime.now(timezone.utc),
        "updated_by": received_by
    }
    
    # If status changes, add to history
    if po["status"] != new_status:
        updates["status"] = new_status
        new_history = po.get("status_history", [])
        new_history.append({
            "status": new_status,
            "changed_by": received_by,
            "timestamp": datetime.now(timezone.utc),
            "notes": "System auto-updated upon item receipt"
        })
        updates["status_history"] = new_history

    if payload.invoice_metadata:
        updates["invoice_metadata"] = payload.invoice_metadata.dict(exclude_none=True)

    await repo.update_purchase_order(po_id, updates)
    return await get_purchase_order(po_id)
