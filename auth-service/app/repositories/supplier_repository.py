from typing import Optional
from bson import ObjectId
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class SupplierRepository:

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["suppliers"]

    def _serialize(self, doc: dict) -> dict:
        if not doc:
            return doc
        doc["_id"] = str(doc["_id"])
        if "product_ids" in doc:
            doc["product_ids"] = [
                str(pid) if isinstance(pid, ObjectId) else pid
                for pid in doc["product_ids"]
            ]
        return doc

    # Core CRUD 

    async def create(self, doc: dict) -> dict:
        result = await self.collection.insert_one(doc)
        created = await self.collection.find_one({"_id": result.inserted_id})
        return self._serialize(created)

    async def find_by_id(self, supplier_id: str) -> Optional[dict]:
        try:
            doc = await self.collection.find_one({"_id": ObjectId(supplier_id)})
            return self._serialize(doc) if doc else None
        except Exception:
            return None

    async def find_by_email(self, email: str) -> Optional[dict]:
        doc = await self.collection.find_one({"email": email.lower().strip()})
        return self._serialize(doc) if doc else None

    async def find_by_gst(self, gst_number: str) -> Optional[dict]:
        doc = await self.collection.find_one({"gst_number": gst_number.upper().strip()})
        return self._serialize(doc) if doc else None

    async def email_exists(self, email: str, exclude_id: Optional[str] = None) -> bool:
        query: dict = {"email": email.lower().strip()}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        return await self.collection.count_documents(query) > 0

    async def gst_exists(self, gst_number: str, exclude_id: Optional[str] = None) -> bool:
        if not gst_number:
            return False
        query: dict = {"gst_number": gst_number.upper().strip()}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        return await self.collection.count_documents(query) > 0

    async def update(self, supplier_id: str, update_data: dict) -> Optional[dict]:
        update_data["updated_at"] = datetime.now(timezone.utc)
        try:
            await self.collection.update_one(
                {"_id": ObjectId(supplier_id)},
                {"$set": update_data}
            )
            return await self.find_by_id(supplier_id)
        except Exception as e:
            logger.error(f"Supplier update failed: {e}")
            return None

    async def delete(self, supplier_id: str) -> bool:
        try:
            result = await self.collection.delete_one({"_id": ObjectId(supplier_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    # Listing & Search 

    async def list_suppliers(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        query: dict = {}

        if status:
            query["status"] = status

        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"contact_person": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"gst_number": {"$regex": search, "$options": "i"}},
            ]

        total = await self.collection.count_documents(query)
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("name", 1)
        suppliers = [self._serialize(doc) async for doc in cursor]
        return suppliers, total

    # Supplier-Product Mapping 

    async def add_products(self, supplier_id: str, product_ids: list[str]) -> Optional[dict]:
        try:
            await self.collection.update_one(
                {"_id": ObjectId(supplier_id)},
                {
                    "$addToSet": {"product_ids": {"$each": product_ids}},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                }
            )
            return await self.find_by_id(supplier_id)
        except Exception as e:
            logger.error(f"add_products failed: {e}")
            return None

    async def remove_products(self, supplier_id: str, product_ids: list[str]) -> Optional[dict]:
        try:
            await self.collection.update_one(
                {"_id": ObjectId(supplier_id)},
                {
                    "$pull": {"product_ids": {"$in": product_ids}},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                }
            )
            return await self.find_by_id(supplier_id)
        except Exception as e:
            logger.error(f"remove_products failed: {e}")
            return None

    async def find_by_product_id(self, product_id: str) -> list[dict]:
        cursor = self.collection.find({"product_ids": product_id})
        return [self._serialize(doc) async for doc in cursor]