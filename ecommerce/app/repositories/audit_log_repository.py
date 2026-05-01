from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, Tuple

class AuditLogRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["audit_logs"]

    async def create(self, doc: dict) -> dict:
        result = await self.collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc

    async def search(
        self,
        entity_type: Optional[str],
        user_id: Optional[str],
        action: Optional[str],
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[list[dict], int]:
        filter_query = {}
        if entity_type:
            filter_query["entity_type"] = entity_type
        if user_id:
            filter_query["user_id"] = user_id
        if action:
            filter_query["action"] = action

        cursor = self.collection.find(filter_query).sort("timestamp", -1).skip(skip).limit(limit)
        logs = []
        async for log in cursor:
            log["_id"] = str(log["_id"])
            logs.append(log)

        total = await self.collection.count_documents(filter_query)
        return logs, total
