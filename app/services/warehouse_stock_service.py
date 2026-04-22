from datetime import datetime
from bson import ObjectId
from app.repositories.warehouse_stock_repository import WarehouseStockRepository
from app.models.warehouse_stock_model import WarehouseStock
from app.core.database import db


class WarehouseStockService:

    @staticmethod
    async def assign_stock(data, user):

        if user["role"] not in ["supplier", "manager"]:
            raise Exception("Only supplier & manager allowed")

        warehouse = await db["warehouses"].find_one(
            {"_id": ObjectId(data.warehouse_id)}
        )

        if not warehouse:
            raise Exception("Warehouse not found")

        product = await db["products"].find_one({"_id": ObjectId(data.product_id)})

        if not product:
            raise Exception("Product not found")

        variant_name = "Base Product"
        final_sku = None

        if data.variant_sku == product.get("sku"):
            final_sku = product.get("sku")
        else:
            for v in product.get("variants", []):
                if v.get("sku") == data.variant_sku:
                    final_sku = v.get("sku")
                    variant_name = v.get("name")
                    break

        if not final_sku:
            raise Exception("SKU not found")

        existing = await WarehouseStockRepository.find_one(data.warehouse_id, final_sku)

        if existing:
            await WarehouseStockRepository.increase_stock(
                data.warehouse_id, final_sku, data.quantity
            )
            return {"message": "Stock increased"}

        stock = WarehouseStock(
            warehouse_id=ObjectId(data.warehouse_id),
            warehouse_name=warehouse.get("name"),
            product_id=ObjectId(data.product_id),
            product_name=product.get("name"),
            product_sku=product.get("sku"),
            variant_sku=final_sku,
            variant_name=variant_name,
            quantity=data.quantity,
        )

        await WarehouseStockRepository.create(stock.dict())

        return {"message": "Stock assigned"}

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

        if user["role"] not in ["supplier", "manager"]:
            raise Exception("Only supplier & manager allowed")

        await WarehouseStockRepository.update_stock(warehouse_id, sku, qty)
        return {"message": "Stock updated"}

    @staticmethod
    async def transfer_stock(data, user):

        if user["role"] not in ["supplier", "manager"]:
            raise Exception("Only supplier & manager allowed")

        source = await WarehouseStockRepository.find_one(
            data.from_warehouse, data.variant_sku
        )

        if not source or source["quantity"] < data.quantity:
            raise Exception("Not enough stock")

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

            new_stock = {
                "warehouse_id": ObjectId(data.to_warehouse),
                "warehouse_name": source.get("warehouse_name"),
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
