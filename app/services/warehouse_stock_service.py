from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException

from app.core.database import db
from app.models.warehouse_stock_model import WarehouseStock
from app.repositories.warehouse_stock_repository import WarehouseStockRepository
from app.services.inventory_movement_service import InventoryMovementService


class WarehouseStockService:
    @staticmethod
    def _check_manage_access(user):
        if user["role"] not in ["supplier", "manager", "admin"]:
            raise HTTPException(status_code=403, detail="Only supplier, manager, and admin allowed")

    @staticmethod
    async def _get_warehouse(warehouse_id: str):
        warehouse = await db["warehouses"].find_one({"_id": ObjectId(warehouse_id)})
        if not warehouse:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        return warehouse

    @staticmethod
    def _resolve_variant_details(product: dict, variant_sku: str | None):
        variant_name = "Base Product"
        final_sku = product.get("sku")

        if variant_sku and variant_sku != product.get("sku"):
            final_sku = None
            for variant in product.get("variants", []):
                if variant.get("sku") == variant_sku:
                    final_sku = variant.get("sku")
                    variant_name = variant.get("name", "Variant")
                    break
        elif variant_sku == product.get("sku"):
            final_sku = product.get("sku")

        if not final_sku:
            raise HTTPException(status_code=404, detail="SKU not found")

        return final_sku, variant_name

    @staticmethod
    async def assign_stock_entry(
        warehouse_id: str,
        product: dict,
        variant_sku: str,
        quantity: int,
        variant_name: str = "Base Product",
        performed_by: dict | None = None,
        reference_type: str = "manual_stock",
        reference_id: str | None = None,
        remarks: str | None = None,
        movement_type: str = "inward",
    ):
        if quantity <= 0:
            return {"message": "Skipped empty stock allocation"}

        warehouse = await WarehouseStockService._get_warehouse(warehouse_id)
        existing = await WarehouseStockRepository.find_one(warehouse_id, variant_sku)

        if existing:
            await WarehouseStockRepository.increase_stock(warehouse_id, variant_sku, quantity)
        else:
            stock = WarehouseStock(
                warehouse_id=ObjectId(warehouse_id),
                warehouse_name=warehouse.get("name"),
                product_id=ObjectId(product["id"]),
                product_name=product.get("name"),
                product_sku=product.get("sku"),
                variant_sku=variant_sku,
                variant_name=variant_name,
                quantity=quantity,
            )
            await WarehouseStockRepository.create(stock.dict())

        await InventoryMovementService.record_movement(
            product_id=product["id"],
            product_name=product.get("name"),
            variant_sku=variant_sku,
            variant_name=variant_name,
            warehouse_id=warehouse_id,
            warehouse_name=warehouse.get("name"),
            movement_type=movement_type,
            quantity=quantity,
            delta=quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            performed_by=performed_by,
            remarks=remarks,
        )
        return {"message": "Stock assigned"}

    @staticmethod
    async def reserve_stock(
        product: dict,
        variant_sku: str | None,
        quantity: int,
        performed_by: dict | None = None,
        reference_type: str = "sales_order",
        reference_id: str | None = None,
        remarks: str | None = None,
    ):
        final_sku, variant_name = WarehouseStockService._resolve_variant_details(product, variant_sku)
        available_rows = await WarehouseStockRepository.find_available_stock(product["id"], final_sku)

        total_available = sum(int(row.get("quantity", 0)) for row in available_rows)
        if total_available < quantity:
            product_label = (
                f"{product.get('name')} ({variant_name})"
                if variant_sku and variant_sku != product.get("sku")
                else product.get("name")
            )
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient warehouse stock for {product_label}",
            )

        remaining = quantity
        allocations = []

        for row in available_rows:
            if remaining <= 0:
                break

            available_qty = int(row.get("quantity", 0))
            take_qty = min(available_qty, remaining)
            if take_qty <= 0:
                continue

            warehouse_id = str(row["warehouse_id"])
            await WarehouseStockRepository.decrease_stock(warehouse_id, final_sku, take_qty)

            await InventoryMovementService.record_movement(
                product_id=product["id"],
                product_name=product.get("name"),
                variant_sku=final_sku,
                variant_name=variant_name,
                warehouse_id=warehouse_id,
                warehouse_name=row.get("warehouse_name"),
                movement_type="outward",
                quantity=take_qty,
                delta=-take_qty,
                reference_type=reference_type,
                reference_id=reference_id,
                performed_by=performed_by,
                remarks=remarks,
            )

            allocations.append(
                {
                    "warehouse_id": warehouse_id,
                    "warehouse_name": row.get("warehouse_name"),
                    "quantity": take_qty,
                }
            )
            remaining -= take_qty

        return {
            "variant_sku": final_sku,
            "variant_name": variant_name,
            "warehouse_allocations": allocations,
            "total_reserved": quantity,
        }

    @staticmethod
    async def reserve_stock_from_selected_warehouse(
        product: dict,
        variant_sku: str | None,
        warehouse_id: str,
        quantity: int,
        performed_by: dict | None = None,
        reference_type: str = "sales_order",
        reference_id: str | None = None,
        remarks: str | None = None,
    ):
        final_sku, variant_name = WarehouseStockService._resolve_variant_details(product, variant_sku)
        selected_stock = await WarehouseStockRepository.find_one(warehouse_id, final_sku)

        if not selected_stock:
            raise HTTPException(
                status_code=404,
                detail="Selected warehouse does not have this product in stock",
            )

        selected_quantity = int(selected_stock.get("quantity", 0))
        if selected_quantity < quantity:
            product_label = (
                f"{product.get('name')} ({variant_name})"
                if variant_sku and variant_sku != product.get("sku")
                else product.get("name")
            )
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock in selected warehouse for {product_label}",
            )

        await WarehouseStockRepository.decrease_stock(warehouse_id, final_sku, quantity)
        await InventoryMovementService.record_movement(
            product_id=product["id"],
            product_name=product.get("name"),
            variant_sku=final_sku,
            variant_name=variant_name,
            warehouse_id=warehouse_id,
            warehouse_name=selected_stock.get("warehouse_name"),
            movement_type="outward",
            quantity=quantity,
            delta=-quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            performed_by=performed_by,
            remarks=remarks,
        )

        return {
            "variant_sku": final_sku,
            "variant_name": variant_name,
            "warehouse_allocations": [
                {
                    "warehouse_id": warehouse_id,
                    "warehouse_name": selected_stock.get("warehouse_name"),
                    "quantity": quantity,
                }
            ],
            "total_reserved": quantity,
        }

    @staticmethod
    async def get_warehouse_candidates_for_restore(product: dict, variant_sku: str | None):
        final_sku, _ = WarehouseStockService._resolve_variant_details(product, variant_sku)
        return await WarehouseStockRepository.find_available_stock(product["id"], final_sku)

    @staticmethod
    async def restore_stock_allocations(
        product: dict,
        variant_sku: str | None,
        allocations: list[dict],
        performed_by: dict | None = None,
        reference_type: str = "sales_order_cancellation",
        reference_id: str | None = None,
        remarks: str | None = None,
    ):
        if not allocations:
            return

        final_sku, variant_name = WarehouseStockService._resolve_variant_details(product, variant_sku)

        for allocation in allocations:
            warehouse_id = allocation.get("warehouse_id")
            quantity = int(allocation.get("quantity") or 0)
            if not warehouse_id or quantity <= 0:
                continue

            existing = await WarehouseStockRepository.find_one(warehouse_id, final_sku)
            if existing:
                await WarehouseStockRepository.increase_stock(warehouse_id, final_sku, quantity)
                warehouse_name = existing.get("warehouse_name")
            else:
                warehouse = await WarehouseStockService._get_warehouse(warehouse_id)
                warehouse_name = allocation.get("warehouse_name") or warehouse.get("name")
                stock = WarehouseStock(
                    warehouse_id=ObjectId(warehouse_id),
                    warehouse_name=warehouse_name,
                    product_id=ObjectId(product["id"]),
                    product_name=product.get("name"),
                    product_sku=product.get("sku"),
                    variant_sku=final_sku,
                    variant_name=variant_name,
                    quantity=quantity,
                )
                await WarehouseStockRepository.create(stock.dict())

            await InventoryMovementService.record_movement(
                product_id=product["id"],
                product_name=product.get("name"),
                variant_sku=final_sku,
                variant_name=variant_name,
                warehouse_id=warehouse_id,
                warehouse_name=warehouse_name,
                movement_type="return",
                quantity=quantity,
                delta=quantity,
                reference_type=reference_type,
                reference_id=reference_id,
                performed_by=performed_by,
                remarks=remarks,
            )

    @staticmethod
    async def assign_stock(data, user):
        WarehouseStockService._check_manage_access(user)
        await WarehouseStockService._get_warehouse(data.warehouse_id)

        product = await db["products"].find_one({"_id": ObjectId(data.product_id)})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        final_sku, variant_name = WarehouseStockService._resolve_variant_details(
            {"id": data.product_id, **product}, data.variant_sku
        )
        return await WarehouseStockService.assign_stock_entry(
            data.warehouse_id,
            {"id": data.product_id, **product},
            final_sku,
            data.quantity,
            variant_name=variant_name,
            performed_by=user,
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            remarks=data.remarks,
            movement_type="inward",
        )

    @staticmethod
    async def get_warehouse_stock(warehouse_id):
        data = await WarehouseStockRepository.find_by_warehouse(warehouse_id)
        result = []
        for i in data:
            result.append(
                {
                    "id": str(i.get("_id")),
                    "warehouse_id": str(i.get("warehouse_id")),
                    "warehouse_name": i.get("warehouse_name"),
                    "product_id": str(i.get("product_id")),
                    "product_name": i.get("product_name"),
                    "product_sku": i.get("product_sku"),
                    "variant_sku": i.get("variant_sku"),
                    "variant_name": i.get("variant_name"),
                    "quantity": i.get("quantity"),
                    "created_at": i.get("created_at"),
                    "updated_at": i.get("updated_at"),
                }
            )
        return result

    @staticmethod
    async def update_stock(warehouse_id, sku, qty, user, reference_type="manual_adjustment", reference_id=None, remarks=None):
        WarehouseStockService._check_manage_access(user)

        existing = await WarehouseStockRepository.find_one(warehouse_id, sku)
        if not existing:
            raise HTTPException(status_code=404, detail="Stock row not found")

        old_qty = int(existing.get("quantity") or 0)
        new_qty = int(qty)
        delta = new_qty - old_qty

        await WarehouseStockRepository.update_stock(warehouse_id, sku, new_qty)

        if delta != 0:
            await InventoryMovementService.record_movement(
                product_id=str(existing.get("product_id")),
                product_name=existing.get("product_name"),
                variant_sku=existing.get("variant_sku"),
                variant_name=existing.get("variant_name"),
                warehouse_id=warehouse_id,
                warehouse_name=existing.get("warehouse_name"),
                movement_type="inward" if delta > 0 else "outward",
                quantity=abs(delta),
                delta=delta,
                reference_type=reference_type,
                reference_id=reference_id,
                performed_by=user,
                remarks=remarks or "Stock updated manually",
            )

        return {"message": "Stock updated"}

    @staticmethod
    async def transfer_stock(data, user):
        WarehouseStockService._check_manage_access(user)

        source = await WarehouseStockRepository.find_one(data.from_warehouse, data.variant_sku)
        if not source or int(source.get("quantity") or 0) < data.quantity:
            raise HTTPException(status_code=400, detail="Not enough stock")

        await WarehouseStockRepository.decrease_stock(data.from_warehouse, data.variant_sku, data.quantity)

        destination = await WarehouseStockRepository.find_one(data.to_warehouse, data.variant_sku)
        if destination:
            await WarehouseStockRepository.increase_stock(data.to_warehouse, data.variant_sku, data.quantity)
            destination_name = destination.get("warehouse_name")
        else:
            destination_warehouse = await WarehouseStockService._get_warehouse(data.to_warehouse)
            destination_name = destination_warehouse.get("name")
            new_stock = {
                "warehouse_id": ObjectId(data.to_warehouse),
                "warehouse_name": destination_name,
                "product_id": source.get("product_id"),
                "product_name": source.get("product_name"),
                "product_sku": source.get("product_sku"),
                "variant_sku": source.get("variant_sku"),
                "variant_name": source.get("variant_name"),
                "quantity": data.quantity,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            await WarehouseStockRepository.create(new_stock)

        transfer_ref = data.reference_id or f"TRF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        reference_type = data.reference_type or "warehouse_transfer"

        await InventoryMovementService.record_movement(
            product_id=str(source.get("product_id")),
            product_name=source.get("product_name"),
            variant_sku=source.get("variant_sku"),
            variant_name=source.get("variant_name"),
            warehouse_id=data.from_warehouse,
            warehouse_name=source.get("warehouse_name"),
            movement_type="transfer",
            quantity=data.quantity,
            delta=-int(data.quantity),
            reference_type=reference_type,
            reference_id=transfer_ref,
            performed_by=user,
            remarks=data.remarks,
        )
        await InventoryMovementService.record_movement(
            product_id=str(source.get("product_id")),
            product_name=source.get("product_name"),
            variant_sku=source.get("variant_sku"),
            variant_name=source.get("variant_name"),
            warehouse_id=data.to_warehouse,
            warehouse_name=destination_name,
            movement_type="transfer",
            quantity=data.quantity,
            delta=int(data.quantity),
            reference_type=reference_type,
            reference_id=transfer_ref,
            performed_by=user,
            remarks=data.remarks,
        )

        return {"message": "Stock transferred"}
