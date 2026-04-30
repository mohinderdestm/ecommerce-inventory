from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException

from app.models.inventory_movement_model import inventory_movement_model
from app.repositories.inventory_movement_repository import InventoryMovementRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.warehouse_stock_repository import WarehouseStockRepository
from app.services.audit_service import AuditService


class InventoryMovementService:
    VIEW_ROLES = {"admin", "manager"}
    MANAGE_ROLES = {"admin", "manager"}

    @staticmethod
    def _check_view_access(user: dict):
        if user.get("role") not in InventoryMovementService.VIEW_ROLES:
            raise HTTPException(
                status_code=403,
                detail="Only admin and manager can view inventory movement details.",
            )

    @staticmethod
    def _check_manage_access(user: dict):
        if user.get("role") not in InventoryMovementService.MANAGE_ROLES:
            raise HTTPException(
                status_code=403,
                detail="Only admin and manager can create manual inventory movements.",
            )

    @staticmethod
    def _actor(user: Optional[dict]):
        if not user:
            return {"id": None, "name": "System", "email": None, "role": "system"}
        return {
            "id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
        }

    @staticmethod
    def _resolve_variant(product: dict, variant_sku: Optional[str]):
        if not variant_sku or variant_sku == product.get("sku"):
            return product.get("sku"), "Base Product"

        for variant in product.get("variants", []):
            if variant.get("sku") == variant_sku:
                return variant_sku, variant.get("name", "Variant")

        raise HTTPException(
            status_code=404, detail=f"Variant SKU {variant_sku} not found"
        )

    @staticmethod
    def _stock_snapshot(
        *,
        warehouse_id: str,
        warehouse_name: str,
        product: dict,
        variant_sku: str,
        variant_name: str,
        quantity: int,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        remarks: Optional[str] = None,
    ):
        return {
            "warehouse_id": warehouse_id,
            "warehouse_name": warehouse_name,
            "product_id": product.get("id"),
            "product_name": product.get("name"),
            "product_sku": product.get("sku"),
            "variant_sku": variant_sku,
            "variant_name": variant_name,
            "quantity": int(quantity),
            "reference_type": reference_type,
            "reference_id": reference_id,
            "remarks": remarks,
        }

    @staticmethod
    async def _audit_stock_change(
        *,
        user: dict,
        action: str,
        warehouse_id: str,
        warehouse_name: str,
        product: dict,
        variant_sku: str,
        variant_name: str,
        old_qty: int,
        new_qty: int,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        remarks: Optional[str] = None,
        audit_context: Optional[dict] = None,
    ):
        await AuditService.safe_log_action(
            user=user,
            action=action,
            entity_type="warehouse_stock",
            entity_id=f"{warehouse_id}:{variant_sku}",
            old_value=InventoryMovementService._stock_snapshot(
                warehouse_id=warehouse_id,
                warehouse_name=warehouse_name,
                product=product,
                variant_sku=variant_sku,
                variant_name=variant_name,
                quantity=old_qty,
                reference_type=reference_type,
                reference_id=reference_id,
                remarks=remarks,
            ),
            new_value=InventoryMovementService._stock_snapshot(
                warehouse_id=warehouse_id,
                warehouse_name=warehouse_name,
                product=product,
                variant_sku=variant_sku,
                variant_name=variant_name,
                quantity=new_qty,
                reference_type=reference_type,
                reference_id=reference_id,
                remarks=remarks,
            ),
            audit_context=audit_context,
        )

    @staticmethod
    async def record_movement(
        *,
        product_id: str,
        product_name: str,
        variant_sku: str,
        variant_name: str,
        warehouse_id: str,
        warehouse_name: str,
        movement_type: str,
        quantity: int,
        delta: int,
        reference_type: str = "manual",
        reference_id: Optional[str] = None,
        performed_by: Optional[dict] = None,
        remarks: Optional[str] = None,
    ):
        movement_doc = {
            "product_id": ObjectId(product_id),
            "product_name": product_name,
            "variant_sku": variant_sku,
            "variant_name": variant_name,
            "warehouse_id": ObjectId(warehouse_id),
            "warehouse_name": warehouse_name,
            "movement_type": movement_type,
            "quantity": int(abs(quantity)),
            "delta": int(delta),
            "reference_type": reference_type,
            "reference_id": reference_id,
            "performed_by": InventoryMovementService._actor(performed_by),
            "remarks": remarks,
            "created_at": datetime.utcnow(),
        }
        movement_id = await InventoryMovementRepository.create(movement_doc)
        created = await InventoryMovementRepository.get_by_id(movement_id)
        return inventory_movement_model(created)

    @staticmethod
    async def _increase_stock(
        product: dict,
        warehouse_id: str,
        warehouse_name: str,
        variant_sku: str,
        variant_name: str,
        quantity: int,
    ):
        existing = await WarehouseStockRepository.find_one(warehouse_id, variant_sku)
        if existing:
            await WarehouseStockRepository.increase_stock(
                warehouse_id, variant_sku, quantity
            )
            return

        await WarehouseStockRepository.create(
            {
                "warehouse_id": ObjectId(warehouse_id),
                "warehouse_name": warehouse_name,
                "product_id": ObjectId(product["id"]),
                "product_name": product.get("name"),
                "product_sku": product.get("sku"),
                "variant_sku": variant_sku,
                "variant_name": variant_name,
                "quantity": quantity,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

    @staticmethod
    async def _decrease_stock(warehouse_id: str, variant_sku: str, quantity: int):
        existing = await WarehouseStockRepository.find_one(warehouse_id, variant_sku)
        if not existing or int(existing.get("quantity") or 0) < quantity:
            raise HTTPException(
                status_code=400, detail="Insufficient stock for movement"
            )
        await WarehouseStockRepository.decrease_stock(
            warehouse_id, variant_sku, quantity
        )

    @staticmethod
    async def create_manual_movement(
        data, user: dict, audit_context: Optional[dict] = None
    ):
        InventoryMovementService._check_manage_access(user)

        product = await ProductRepository.get_product_by_id(data.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        source_warehouse = await WarehouseRepository.get_by_id(data.warehouse_id)
        if not source_warehouse:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        final_sku, variant_name = InventoryMovementService._resolve_variant(
            product, data.variant_sku
        )
        movement_type = data.movement_type
        quantity = int(data.quantity)

        if movement_type in {"inward", "return"}:
            before_row = await WarehouseStockRepository.find_one(
                data.warehouse_id, final_sku
            )
            old_qty = int((before_row or {}).get("quantity") or 0)
            await InventoryMovementService._increase_stock(
                product,
                data.warehouse_id,
                source_warehouse.get("name"),
                final_sku,
                variant_name,
                quantity,
            )
            entry = await InventoryMovementService.record_movement(
                product_id=product["id"],
                product_name=product.get("name"),
                variant_sku=final_sku,
                variant_name=variant_name,
                warehouse_id=data.warehouse_id,
                warehouse_name=source_warehouse.get("name"),
                movement_type=movement_type,
                quantity=quantity,
                delta=quantity,
                reference_type=data.reference_type,
                reference_id=data.reference_id,
                performed_by=user,
                remarks=data.remarks,
            )
            await InventoryMovementService._audit_stock_change(
                user=user,
                action="inventory_movement.create",
                warehouse_id=data.warehouse_id,
                warehouse_name=source_warehouse.get("name"),
                product=product,
                variant_sku=final_sku,
                variant_name=variant_name,
                old_qty=old_qty,
                new_qty=old_qty + quantity,
                reference_type=data.reference_type,
                reference_id=data.reference_id,
                remarks=data.remarks,
                audit_context=audit_context,
            )
            return {"message": "Movement recorded", "entries": [entry]}

        if movement_type in {"outward", "damaged", "expired"}:
            before_row = await WarehouseStockRepository.find_one(
                data.warehouse_id, final_sku
            )
            old_qty = int((before_row or {}).get("quantity") or 0)
            await InventoryMovementService._decrease_stock(
                data.warehouse_id, final_sku, quantity
            )
            entry = await InventoryMovementService.record_movement(
                product_id=product["id"],
                product_name=product.get("name"),
                variant_sku=final_sku,
                variant_name=variant_name,
                warehouse_id=data.warehouse_id,
                warehouse_name=source_warehouse.get("name"),
                movement_type=movement_type,
                quantity=quantity,
                delta=-quantity,
                reference_type=data.reference_type,
                reference_id=data.reference_id,
                performed_by=user,
                remarks=data.remarks,
            )
            await InventoryMovementService._audit_stock_change(
                user=user,
                action="inventory_movement.create",
                warehouse_id=data.warehouse_id,
                warehouse_name=source_warehouse.get("name"),
                product=product,
                variant_sku=final_sku,
                variant_name=variant_name,
                old_qty=old_qty,
                new_qty=old_qty - quantity,
                reference_type=data.reference_type,
                reference_id=data.reference_id,
                remarks=data.remarks,
                audit_context=audit_context,
            )
            return {"message": "Movement recorded", "entries": [entry]}

        if movement_type == "transfer":
            destination_id = data.destination_warehouse_id
            if not destination_id:
                raise HTTPException(
                    status_code=422,
                    detail="Destination warehouse is required for transfer",
                )
            if destination_id == data.warehouse_id:
                raise HTTPException(
                    status_code=422,
                    detail="Source and destination warehouse cannot be same",
                )

            destination_warehouse = await WarehouseRepository.get_by_id(destination_id)
            if not destination_warehouse:
                raise HTTPException(
                    status_code=404, detail="Destination warehouse not found"
                )

            source_before = await WarehouseStockRepository.find_one(
                data.warehouse_id, final_sku
            )
            destination_before = await WarehouseStockRepository.find_one(
                destination_id, final_sku
            )
            source_old_qty = int((source_before or {}).get("quantity") or 0)
            destination_old_qty = int((destination_before or {}).get("quantity") or 0)
            await InventoryMovementService._decrease_stock(
                data.warehouse_id, final_sku, quantity
            )
            await InventoryMovementService._increase_stock(
                product,
                destination_id,
                destination_warehouse.get("name"),
                final_sku,
                variant_name,
                quantity,
            )

            transfer_ref = (
                data.reference_id or f"TRF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            )

            source_entry = await InventoryMovementService.record_movement(
                product_id=product["id"],
                product_name=product.get("name"),
                variant_sku=final_sku,
                variant_name=variant_name,
                warehouse_id=data.warehouse_id,
                warehouse_name=source_warehouse.get("name"),
                movement_type="transfer",
                quantity=quantity,
                delta=-quantity,
                reference_type=data.reference_type or "warehouse_transfer",
                reference_id=transfer_ref,
                performed_by=user,
                remarks=data.remarks,
            )
            destination_entry = await InventoryMovementService.record_movement(
                product_id=product["id"],
                product_name=product.get("name"),
                variant_sku=final_sku,
                variant_name=variant_name,
                warehouse_id=destination_id,
                warehouse_name=destination_warehouse.get("name"),
                movement_type="transfer",
                quantity=quantity,
                delta=quantity,
                reference_type=data.reference_type or "warehouse_transfer",
                reference_id=transfer_ref,
                performed_by=user,
                remarks=data.remarks,
            )
            await InventoryMovementService._audit_stock_change(
                user=user,
                action="inventory_movement.transfer_out",
                warehouse_id=data.warehouse_id,
                warehouse_name=source_warehouse.get("name"),
                product=product,
                variant_sku=final_sku,
                variant_name=variant_name,
                old_qty=source_old_qty,
                new_qty=source_old_qty - quantity,
                reference_type=data.reference_type or "warehouse_transfer",
                reference_id=transfer_ref,
                remarks=data.remarks,
                audit_context=audit_context,
            )
            await InventoryMovementService._audit_stock_change(
                user=user,
                action="inventory_movement.transfer_in",
                warehouse_id=destination_id,
                warehouse_name=destination_warehouse.get("name"),
                product=product,
                variant_sku=final_sku,
                variant_name=variant_name,
                old_qty=destination_old_qty,
                new_qty=destination_old_qty + quantity,
                reference_type=data.reference_type or "warehouse_transfer",
                reference_id=transfer_ref,
                remarks=data.remarks,
                audit_context=audit_context,
            )
            return {
                "message": "Transfer movement recorded",
                "entries": [source_entry, destination_entry],
            }

        raise HTTPException(
            status_code=422, detail=f"Unsupported movement type: {movement_type}"
        )

    @staticmethod
    async def list_movements(
        user: dict,
        product_id: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        movement_type: Optional[str] = None,
        reference_type: Optional[str] = None,
        limit: int = 200,
    ):
        InventoryMovementService._check_view_access(user)
        rows = await InventoryMovementRepository.list_movements(
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=movement_type,
            reference_type=reference_type,
            limit=limit,
        )
        return [inventory_movement_model(row) for row in rows]

    @staticmethod
    async def product_ledger(
        product_id: str, user: dict, warehouse_id: Optional[str] = None
    ):
        InventoryMovementService._check_view_access(user)

        product = await ProductRepository.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        rows = await InventoryMovementRepository.get_product_ledger(
            product_id, warehouse_id=warehouse_id
        )
        summary = await InventoryMovementRepository.summarize_product_balance(
            product_id
        )

        return {
            "product": {
                "id": product["id"],
                "name": product.get("name"),
                "sku": product.get("sku"),
            },
            "summary": summary,
            "entries": [inventory_movement_model(row) for row in rows],
        }
