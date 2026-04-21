from typing import Optional
from fastapi import HTTPException
import logging

from app.repositories.inventory_movement_repository import InventoryMovementRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.product_repository import ProductRepository
from app.models.inventory_movement import build_inventory_movement_document, MovementType
from app.schemas.inventory_movement import InventoryMovementCreate

logger = logging.getLogger(__name__)


class InventoryMovementService:
    def __init__(
        self,
        movement_repo: InventoryMovementRepository,
        warehouse_repo: WarehouseRepository,
        product_repo: ProductRepository,
    ):
        self.repo = movement_repo
        self.warehouse_repo = warehouse_repo
        self.product_repo = product_repo

    async def record_manual_movement(self, payload: InventoryMovementCreate, performed_by: str) -> dict:
        """
        Record a manual inventory movement and update actual stock.
        Only allows INWARD, OUTWARD, RETURN, DAMAGED, EXPIRED.
        TRANSFERS should be handled via WarehouseService.initiate_transfer.
        """
        if payload.movement_type in [MovementType.TRANSFER_IN, MovementType.TRANSFER_OUT]:
            raise HTTPException(
                status_code=400,
                detail="Use the warehouse transfer endpoint for warehouse-to-warehouse transfers."
            )

        product = await self.product_repo.find_by_id(payload.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        wh = await self.warehouse_repo.find_by_id(payload.warehouse_id)
        if not wh or not wh.get("is_active"):
            raise HTTPException(status_code=404, detail="Warehouse not found or inactive.")

        # Determine stock delta
        # INWARD, RETURN -> increase stock
        # OUTWARD, DAMAGED, EXPIRED -> decrease stock
        delta = payload.quantity
        if payload.movement_type in [MovementType.OUTWARD, MovementType.DAMAGED, MovementType.EXPIRED, MovementType.TRANSFER_OUT]:
            delta = -payload.quantity

        # Prevent negative stock for outward/damaged/expired
        if delta < 0:
            existing_stock = await self.warehouse_repo.get_stock_entry(
                payload.warehouse_id, payload.product_id, payload.variant_id
            )
            current_qty = existing_stock["quantity"] if existing_stock else 0
            if current_qty + delta < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock. Current: {current_qty}, Requested reduction: {abs(delta)}"
                )

        # Update actual stock
        await self.warehouse_repo.upsert_stock(
            warehouse_id=payload.warehouse_id,
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            quantity_delta=delta
        )

        # Log movement
        doc = build_inventory_movement_document(
            product_id=payload.product_id,
            warehouse_id=payload.warehouse_id,
            movement_type=payload.movement_type,
            quantity=payload.quantity,
            reference_type="MANUAL",
            performed_by=performed_by,
            variant_id=payload.variant_id,
            remarks=payload.remarks,
        )
        created = await self.repo.create(doc)
        logger.info(f"Manual inventory movement recorded: {payload.movement_type} {payload.quantity} for product {payload.product_id} by {performed_by}")
        return created

    async def list_movements(
        self,
        product_id: Optional[str],
        warehouse_id: Optional[str],
        movement_type: Optional[MovementType],
        page: int,
        page_size: int,
    ) -> dict:
        skip = (page - 1) * page_size
        movements, total = await self.repo.list_movements(
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=movement_type.value if movement_type else None,
            skip=skip,
            limit=page_size
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "movements": movements
        }

    async def get_product_ledger(self, product_id: str) -> dict:
        product = await self.product_repo.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        movements = await self.repo.get_all_for_product(product_id)

        ledger = {
            "product_id": product_id,
            "total_inward": 0,
            "total_outward": 0,
            "total_return": 0,
            "total_damaged": 0,
            "total_expired": 0,
            "total_transfer": 0,
            "current_stock_estimate": 0,
            "movements": movements
        }

        for mov in movements:
            qty = mov["quantity"]
            mtype = mov["movement_type"]
            
            if mtype == MovementType.INWARD.value:
                ledger["total_inward"] += qty
                ledger["current_stock_estimate"] += qty
            elif mtype == MovementType.RETURN.value:
                ledger["total_return"] += qty
                ledger["current_stock_estimate"] += qty
            elif mtype == MovementType.OUTWARD.value:
                ledger["total_outward"] += qty
                ledger["current_stock_estimate"] -= qty
            elif mtype == MovementType.DAMAGED.value:
                ledger["total_damaged"] += qty
                ledger["current_stock_estimate"] -= qty
            elif mtype == MovementType.EXPIRED.value:
                ledger["total_expired"] += qty
                ledger["current_stock_estimate"] -= qty
            elif mtype == MovementType.TRANSFER_IN.value:
                ledger["total_transfer"] += qty
                ledger["current_stock_estimate"] += qty
            elif mtype == MovementType.TRANSFER_OUT.value:
                ledger["total_transfer"] += qty
                ledger["current_stock_estimate"] -= qty

        return ledger
