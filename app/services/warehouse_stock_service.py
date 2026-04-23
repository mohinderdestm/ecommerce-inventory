from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from app.repositories.warehouse_stock_repository import WarehouseStockRepository
from app.models.warehouse_stock_model import WarehouseStock
from app.core.database import db


class WarehouseStockService:
    @staticmethod
    def _check_manage_access(user):
        if user["role"] not in ["supplier", "manager"]:
            raise HTTPException(status_code=403, detail="Only supplier & manager allowed")

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
    ):
        if quantity <= 0:
            return {"message": "Skipped empty stock allocation"}

        warehouse = await WarehouseStockService._get_warehouse(warehouse_id)
        existing = await WarehouseStockRepository.find_one(warehouse_id, variant_sku)

        if existing:
            await WarehouseStockRepository.increase_stock(
                warehouse_id, variant_sku, quantity
            )
            return {"message": "Stock increased"}

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
        return {"message": "Stock assigned"}

    @staticmethod
    async def reserve_stock(product: dict, variant_sku: str | None, quantity: int):
        final_sku, variant_name = WarehouseStockService._resolve_variant_details(
            product, variant_sku
        )
        available_rows = await WarehouseStockRepository.find_available_stock(
            product["id"], final_sku
        )

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

            await WarehouseStockRepository.decrease_stock(
                str(row["warehouse_id"]), final_sku, take_qty
            )
            allocations.append(
                {
                    "warehouse_id": str(row["warehouse_id"]),
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
    ):
        final_sku, variant_name = WarehouseStockService._resolve_variant_details(
            product, variant_sku
        )
        selected_stock = await WarehouseStockRepository.find_one(
            warehouse_id, final_sku
        )

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
    async def get_warehouse_candidates_for_restore(
        product: dict, variant_sku: str | None
    ):
        final_sku, _ = WarehouseStockService._resolve_variant_details(product, variant_sku)
        return await WarehouseStockRepository.find_available_stock(product["id"], final_sku)

    @staticmethod
    async def restore_stock_allocations(
        product: dict, variant_sku: str | None, allocations: list[dict]
    ):
        if not allocations:
            return

        final_sku, variant_name = WarehouseStockService._resolve_variant_details(
            product, variant_sku
        )

        for allocation in allocations:
            warehouse_id = allocation.get("warehouse_id")
            quantity = int(allocation.get("quantity") or 0)
            if not warehouse_id or quantity <= 0:
                continue

            existing = await WarehouseStockRepository.find_one(warehouse_id, final_sku)
            if existing:
                await WarehouseStockRepository.increase_stock(
                    warehouse_id, final_sku, quantity
                )
                continue

            warehouse = await WarehouseStockService._get_warehouse(warehouse_id)
            stock = WarehouseStock(
                warehouse_id=ObjectId(warehouse_id),
                warehouse_name=allocation.get("warehouse_name") or warehouse.get("name"),
                product_id=ObjectId(product["id"]),
                product_name=product.get("name"),
                product_sku=product.get("sku"),
                variant_sku=final_sku,
                variant_name=variant_name,
                quantity=quantity,
            )
            await WarehouseStockRepository.create(stock.dict())

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
    async def update_stock(warehouse_id, sku, qty, user):
        WarehouseStockService._check_manage_access(user)

        await WarehouseStockRepository.update_stock(warehouse_id, sku, qty)
        return {"message": "Stock updated"}

    @staticmethod
    async def transfer_stock(data, user):
        WarehouseStockService._check_manage_access(user)

        source = await WarehouseStockRepository.find_one(
            data.from_warehouse, data.variant_sku
        )

        if not source or source["quantity"] < data.quantity:
            raise HTTPException(status_code=400, detail="Not enough stock")

        await WarehouseStockRepository.decrease_stock(
            data.from_warehouse, data.variant_sku, data.quantity
        )

        destination = await WarehouseStockRepository.find_one(
            data.to_warehouse, data.variant_sku
        )

        if destination:

            await WarehouseStockRepository.increase_stock(
                data.to_warehouse, data.variant_sku, data.quantity
            )
        else:
            destination_warehouse = await WarehouseStockService._get_warehouse(
                data.to_warehouse
            )

            new_stock = {
                "warehouse_id": ObjectId(data.to_warehouse),
                "warehouse_name": destination_warehouse.get("name"),
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

        return {"message": "Stock transferred"}
