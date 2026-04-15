from typing import Optional
from bson import ObjectId
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class WarehouseRepository:

    def __init__(self, db: AsyncIOMotorDatabase):
        self.warehouses = db["warehouses"]
        self.stock = db["warehouse_stock"]
        self.transfers = db["stock_transfers"]

    def _serialize(self, doc: dict) -> dict:
        if not doc:
            return doc
        doc["_id"] = str(doc["_id"])
        if "staff_ids" in doc:
            doc["staff_ids"] = [str(s) for s in doc["staff_ids"]]
        return doc

    def _serialize_stock(self, doc: dict) -> dict:
        if not doc:
            return doc
        doc["_id"] = str(doc["_id"])
        return doc

    # Warehouse CRUD 

    async def create(self, doc: dict) -> dict:
        result = await self.warehouses.insert_one(doc)
        created = await self.warehouses.find_one({"_id": result.inserted_id})
        return self._serialize(created)

    async def find_by_id(self, warehouse_id: str) -> Optional[dict]:
        try:
            doc = await self.warehouses.find_one({"_id": ObjectId(warehouse_id)})
            return self._serialize(doc) if doc else None
        except Exception:
            return None

    async def name_exists(self, name: str, exclude_id: Optional[str] = None) -> bool:
        query: dict = {"name": {"$regex": f"^{name.strip()}$", "$options": "i"}}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        return await self.warehouses.count_documents(query) > 0

    async def update(self, warehouse_id: str, update_data: dict) -> Optional[dict]:
        update_data["updated_at"] = datetime.now(timezone.utc)
        await self.warehouses.update_one(
            {"_id": ObjectId(warehouse_id)},
            {"$set": update_data}
        )
        return await self.find_by_id(warehouse_id)

    async def delete(self, warehouse_id: str) -> bool:
        result = await self.warehouses.delete_one({"_id": ObjectId(warehouse_id)})
        return result.deleted_count > 0

    async def list_warehouses(
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
                {"address.city": {"$regex": search, "$options": "i"}},
            ]
        total = await self.warehouses.count_documents(query)
        cursor = self.warehouses.find(query).skip(skip).limit(limit).sort("name", 1)
        return [self._serialize(doc) async for doc in cursor], total

    # Staff Assignment 

    async def assign_staff(self, warehouse_id: str, user_ids: list[str]) -> Optional[dict]:
        await self.warehouses.update_one(
            {"_id": ObjectId(warehouse_id)},
            {
                "$addToSet": {"staff_ids": {"$each": user_ids}},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            }
        )
        return await self.find_by_id(warehouse_id)

    async def unassign_staff(self, warehouse_id: str, user_ids: list[str]) -> Optional[dict]:
        await self.warehouses.update_one(
            {"_id": ObjectId(warehouse_id)},
            {
                "$pull": {"staff_ids": {"$in": user_ids}},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            }
        )
        return await self.find_by_id(warehouse_id)

    # Stock Management
    async def get_stock_entry(
        self,
        warehouse_id: str,
        product_id: str,
        variant_id: Optional[str],
    ) -> Optional[dict]:
        query = {"warehouse_id": warehouse_id, "product_id": product_id, "variant_id": variant_id}
        doc = await self.stock.find_one(query)
        return self._serialize_stock(doc) if doc else None

    async def upsert_stock(
        self,
        warehouse_id: str,
        product_id: str,
        variant_id: Optional[str],
        quantity_delta: int,
    ) -> dict:
        query = {"warehouse_id": warehouse_id, "product_id": product_id, "variant_id": variant_id}
        now = datetime.now(timezone.utc)
        result = await self.stock.find_one_and_update(
            query,
            {
                "$inc": {"quantity": quantity_delta},
                "$set": {"updated_at": now},
                "$setOnInsert": {
                    "warehouse_id": warehouse_id,
                    "product_id": product_id,
                    "variant_id": variant_id,
                    "created_at": now,
                },
            },
            upsert=True,
            return_document=True,
        )
        return self._serialize_stock(result)

    async def get_warehouse_stock_summary(self, warehouse_id: str) -> list[dict]:
        cursor = self.stock.find(
            {"warehouse_id": warehouse_id, "quantity": {"$gt": 0}}
        ).sort("product_id", 1)
        return [self._serialize_stock(doc) async for doc in cursor]

    async def get_product_stock_across_warehouses(self, product_id: str) -> list[dict]:
        cursor = self.stock.find({"product_id": product_id}).sort("quantity", -1)
        return [self._serialize_stock(doc) async for doc in cursor]

    # Stock Transfers 

    async def create_transfer(self, doc: dict) -> dict:
        result = await self.transfers.insert_one(doc)
        created = await self.transfers.find_one({"_id": result.inserted_id})
        return self._serialize_stock(created)

    async def find_transfer_by_id(self, transfer_id: str) -> Optional[dict]:
        try:
            doc = await self.transfers.find_one({"_id": ObjectId(transfer_id)})
            return self._serialize_stock(doc) if doc else None
        except Exception:
            return None

    async def update_transfer(self, transfer_id: str, update_data: dict) -> Optional[dict]:
        update_data["updated_at"] = datetime.now(timezone.utc)
        await self.transfers.update_one(
            {"_id": ObjectId(transfer_id)},
            {"$set": update_data}
        )
        return await self.find_transfer_by_id(transfer_id)

    async def list_transfers(
        self,
        warehouse_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        query: dict = {}
        if warehouse_id:
            query["$or"] = [
                {"from_warehouse_id": warehouse_id},
                {"to_warehouse_id": warehouse_id},
            ]
        if status:
            query["status"] = status
        total = await self.transfers.count_documents(query)
        cursor = self.transfers.find(query).skip(skip).limit(limit).sort("created_at", -1)
        return [self._serialize_stock(doc) async for doc in cursor], total