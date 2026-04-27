from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class UserRepository:

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["users"]

    def _serialize(self, doc: dict) -> dict:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def create(self, user_doc: dict) -> dict:
        result = await self.collection.insert_one(user_doc)
        created = await self.collection.find_one({"_id": result.inserted_id})
        return self._serialize(created)

    async def find_by_id(self, user_id: str) -> Optional[dict]:
        try:
            doc = await self.collection.find_one({"_id": ObjectId(user_id)})
            return self._serialize(doc) if doc else None
        except Exception:
            return None

    async def find_by_email(self, email: str) -> Optional[dict]:
        doc = await self.collection.find_one({"email": email.lower().strip()})
        return self._serialize(doc) if doc else None

    async def find_by_username(self, username: str) -> Optional[dict]:
        doc = await self.collection.find_one({"username": username.lower().strip()})
        return self._serialize(doc) if doc else None

    async def get_admins(self) -> list[dict]:
        cursor = self.collection.find({"role": "ADMIN"})
        return [self._serialize(doc) async for doc in cursor]

    async def email_exists(self, email: str) -> bool:
        count = await self.collection.count_documents({"email": email.lower().strip()})
        return count > 0

    async def username_exists(self, username: str) -> bool:
        count = await self.collection.count_documents({"username": username.lower().strip()})
        return count > 0

    async def update(self, user_id: str, update_data: dict) -> Optional[dict]:
        update_data["updated_at"] = datetime.now(timezone.utc)
        try:
            await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            return await self.find_by_id(user_id)
        except Exception as e:
            logger.error(f"Update failed for user {user_id}: {e}")
            return None

    async def update_last_login(self, user_id: str):
        try:
            await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )
        except Exception:
            pass  # Non-critical, don't raise

    async def delete(self, user_id: str) -> bool:
        try:
            result = await self.collection.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def list_users(
        self,
        role: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        query: dict = {}
        if role:
            query["role"] = role
        if status:
            query["status"] = status

        total = await self.collection.count_documents(query)
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        users = [self._serialize(doc) async for doc in cursor]
        return users, total