from app.core.database import db
from bson import ObjectId
from datetime import datetime

class SupplierRepository:

    @staticmethod
    def serialize(supplier) -> dict:
        if not supplier:
            return None
        return {
            "id": str(supplier["_id"]),
            "name": supplier.get("name", ""),
            "contact_person": supplier.get("contact_person", ""),
            "phone": supplier.get("phone", ""),
            "email": supplier.get("email", ""),
            "address": supplier.get("address", ""),
            "gst_id": supplier.get("gst_id", ""),
            "payment_terms": supplier.get("payment_terms", ""),
            "rating": supplier.get("rating", 0),
            "total_orders": supplier.get("total_orders", 0),
            "total_amount": supplier.get("total_amount", 0),
            "status": supplier.get("status", "active"),
            "created_at": supplier.get("created_at"),
            "updated_at": supplier.get("updated_at")
        }

    @staticmethod
    async def create(supplier: dict):
        result = await db["suppliers"].insert_one(supplier)
        return str(result.inserted_id)

    @staticmethod
    async def get_all(skip: int = 0, limit: int = 50, status: str = None):
        query = {"status": status} if status else {}
        suppliers = []
        async for s in db["suppliers"].find(query).skip(skip).limit(limit).sort("name", 1):
            suppliers.append(SupplierRepository.serialize(s))
        total = await db["suppliers"].count_documents(query)
        return {"suppliers": suppliers, "total": total}

    @staticmethod
    async def get_by_id(supplier_id: str):
        if not ObjectId.is_valid(supplier_id):
            return None
        supplier = await db["suppliers"].find_one({"_id": ObjectId(supplier_id)})
        return SupplierRepository.serialize(supplier)

    @staticmethod
    async def search(query: str, skip: int = 0, limit: int = 50):
        filter_query = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"contact_person": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}}
            ]
        }
        suppliers = []
        async for s in db["suppliers"].find(filter_query).skip(skip).limit(limit):
            suppliers.append(SupplierRepository.serialize(s))
        total = await db["suppliers"].count_documents(filter_query)
        return {"suppliers": suppliers, "total": total}

    @staticmethod
    async def update(supplier_id: str, data: dict):
        if not ObjectId.is_valid(supplier_id):
            return False
        data["updated_at"] = datetime.utcnow()
        result = await db["suppliers"].update_one(
            {"_id": ObjectId(supplier_id)},
            {"$set": data}
        )
        return result.modified_count > 0

    @staticmethod
    async def update_stats(supplier_id: str, order_amount: float):
        """Update supplier performance stats"""
        if not ObjectId.is_valid(supplier_id):
            return False
        await db["suppliers"].update_one(
            {"_id": ObjectId(supplier_id)},
            {
                "$inc": {"total_orders": 1, "total_amount": order_amount},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

    @staticmethod
    async def update_rating(supplier_id: str, rating: float):
        if not ObjectId.is_valid(supplier_id):
            return False
        await db["suppliers"].update_one(
            {"_id": ObjectId(supplier_id)},
            {"$set": {"rating": rating, "updated_at": datetime.utcnow()}}
        )

    @staticmethod
    async def delete(supplier_id: str):
        if not ObjectId.is_valid(supplier_id):
            return False
        result = await db["suppliers"].delete_one({"_id": ObjectId(supplier_id)})
        return result.deleted_count > 0

    @staticmethod
    async def get_products(supplier_id: str):
        """Get all products from this supplier"""
        products = []
        async for p in db["products"].find({"supplier_id": supplier_id}):
            p["id"] = str(p["_id"])
            del p["_id"]
            products.append(p)
        return products