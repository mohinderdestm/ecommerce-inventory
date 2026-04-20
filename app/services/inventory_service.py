from fastapi import HTTPException
from datetime import datetime
from app.core.database import db
from bson import ObjectId

class InventoryService:
    def __init__(self, repo):
        self.repo = repo

    async def move_stock(self, data, user):
        payload = data.dict()

        movements = db["inventory_logs"]
        products = db["products"]
        warehouses = db["warehouses"]

        product_id = payload["product_id"]
        qty = payload["quantity"]
        movement_type = payload["movement_type"]

        # ✅ product name
        product = await products.find_one({"_id": ObjectId(product_id)})
        product_name = product.get("name") if product else None

        # ================= INWARD =================
        if movement_type == "inward":
            warehouse_id = payload["warehouse_id"]

            warehouse = await warehouses.find_one({"_id": ObjectId(warehouse_id)})
            warehouse_name = warehouse.get("name") if warehouse else None

            # ✅ FIX: update stock
            await self.repo.update_stock(product_id, warehouse_id, qty)

            await movements.insert_one({
                "product_id": product_id,
                "product_name": product_name,
                "warehouse_id": warehouse_id,
                "warehouse_name": warehouse_name,
                "movement_type": "inward",
                "quantity": qty,
                "performed_by": str(user["_id"]),
                "timestamp": datetime.utcnow(),
                "remarks": "Stock added"
            })

        # ================= OUTWARD =================
        elif movement_type == "outward":
            warehouse_id = payload["warehouse_id"]

            warehouse = await warehouses.find_one({"_id": ObjectId(warehouse_id)})
            warehouse_name = warehouse.get("name") if warehouse else None

            # ✅ FIX: get existing stock
            existing = await self.repo.get_inventory(product_id, warehouse_id)

            if not existing or existing.get("stock", 0) < qty:
                raise HTTPException(400, "Insufficient stock")

            await self.repo.update_stock(product_id, warehouse_id, -qty)

            await movements.insert_one({
                "product_id": product_id,
                "product_name": product_name,
                "warehouse_id": warehouse_id,
                "warehouse_name": warehouse_name,
                "movement_type": "outward",
                "quantity": qty,
                "performed_by": str(user["_id"]),
                "timestamp": datetime.utcnow(),
                "remarks": "Stock removed"
            })

        # ================= TRANSFER =================
        elif movement_type == "transfer":
            from_wh = payload["from_warehouse_id"]
            to_wh = payload["to_warehouse_id"]

            if from_wh == to_wh:
                raise HTTPException(400, "Same warehouse not allowed")

            # warehouse names
            from_wh_data = await warehouses.find_one({"_id": ObjectId(from_wh)})
            to_wh_data = await warehouses.find_one({"_id": ObjectId(to_wh)})

            from_name = from_wh_data.get("name") if from_wh_data else None
            to_name = to_wh_data.get("name") if to_wh_data else None

            # check stock
            existing = await self.repo.get_inventory(product_id, from_wh)

            if not existing or existing.get("stock", 0) < qty:
                raise HTTPException(400, "Insufficient stock")

            # deduct from source
            await self.repo.update_stock(product_id, from_wh, -qty)

            # add to destination
            await self.repo.update_stock(product_id, to_wh, qty)

            #  OUT log
            await movements.insert_one({
                "product_id": product_id,
                "product_name": product_name,
                "warehouse_id": from_wh,
                "warehouse_name": from_name,
                "movement_type": "transfer_out",
                "quantity": qty,
                "performed_by": str(user["_id"]),
                "timestamp": datetime.utcnow(),
                "remarks": f"Transferred to {to_name}"
            })

            #  IN log
            await movements.insert_one({
                "product_id": product_id,
                "product_name": product_name,
                "warehouse_id": to_wh,
                "warehouse_name": to_name,
                "movement_type": "transfer",
                "quantity": qty,
                "performed_by": str(user["_id"]),
                "timestamp": datetime.utcnow(),
                "remarks": f"Received from {from_name}"
            })

        else:
            raise HTTPException(400, "Invalid movement type")

        return {"message": "Stock updated successfully"}