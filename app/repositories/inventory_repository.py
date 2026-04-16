from bson import ObjectId
from app.core.database import db

class InventoryRepository:
    def __init__(self, db):
        self.collection = db["inventory"]

    async def get_inventory(self, product_id, warehouse_id):
        return await self.collection.find_one({
            "product_id": product_id,
            "warehouse_id": warehouse_id
        })

    async def create(self, data):
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

 

    async def update_stock(self, product_id, warehouse_id, quantity):
        products = db["products"]
        warehouses = db["warehouses"]

        # get names
        product = await products.find_one({"_id": ObjectId(product_id)})
        warehouse = await warehouses.find_one({"_id": ObjectId(warehouse_id)})

        product_name = product.get("name") if product else None
        warehouse_name = warehouse.get("name") if warehouse else None

        existing = await self.collection.find_one({
            "product_id": product_id,
            "warehouse_id": warehouse_id
        })

        if existing:
            await self.collection.update_one(
                {"_id": existing["_id"]},
                {
                    "$inc": {"stock": quantity},
                    "$set": {
                        "product_name": product_name,
                        "warehouse_name": warehouse_name
                    }
                }
            )
        else:
            await self.collection.insert_one({
                "product_id": product_id,
                "product_name": product_name,
                "warehouse_id": warehouse_id,
                "warehouse_name": warehouse_name,
                "stock": quantity
            })