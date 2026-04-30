from app.core.database import db

collection = db["audit"]


class AuditRepository:
    @staticmethod
    async def create(data: dict):
        return await collection.insert_one(data)

    @staticmethod
    async def list_logs(query: dict, limit: int = 200):
        cursor = collection.find(query).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=None)
