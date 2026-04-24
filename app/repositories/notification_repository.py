from datetime import datetime
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId

from app.core.database import db


collection = db["notifications"]


class NotificationRepository:
    @staticmethod
    def _to_object_id(value: Optional[str]):
        if not value:
            return None
        try:
            return ObjectId(value)
        except (InvalidId, TypeError):
            return None

    @staticmethod
    async def create(data: dict):
        result = await collection.insert_one(data)
        return str(result.inserted_id)

    @staticmethod
    async def get_by_id(notification_id: str):
        object_id = NotificationRepository._to_object_id(notification_id)
        if not object_id:
            return None
        return await collection.find_one({"_id": object_id})

    @staticmethod
    async def find_active_by_dedupe_key(dedupe_key: str):
        if not dedupe_key:
            return None
        return await collection.find_one({"dedupe_key": dedupe_key})

    @staticmethod
    async def list_for_user(
        role: str,
        email: str,
        include_read: bool = False,
        limit: int = 100,
    ):
        query = NotificationRepository._build_user_query(role, email)
        if not include_read:
            query["is_read"] = False

        cursor = (
            collection.find(query)
            .sort("created_at", -1)
            .limit(max(1, min(limit, 1000)))
        )
        return await cursor.to_list(length=None)

    @staticmethod
    async def count_unread(role: str, email: str):
        query = NotificationRepository._build_user_query(role, email)
        query["is_read"] = False
        return await collection.count_documents(query)

    @staticmethod
    async def summarize_for_user(role: str, email: str):
        query = NotificationRepository._build_user_query(role, email)
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "unread": {"$sum": {"$cond": [{"$eq": ["$is_read", False]}, 1, 0]}},
                    "critical": {
                        "$sum": {"$cond": [{"$eq": ["$severity", "critical"]}, 1, 0]}
                    },
                    "warning": {
                        "$sum": {"$cond": [{"$eq": ["$severity", "warning"]}, 1, 0]}
                    },
                    "info": {"$sum": {"$cond": [{"$eq": ["$severity", "info"]}, 1, 0]}},
                }
            },
        ]
        result = await collection.aggregate(pipeline).to_list(length=1)
        if not result:
            return {
                "total": 0,
                "unread": 0,
                "critical": 0,
                "warning": 0,
                "info": 0,
                "action_required": 0,
            }
        row = result[0]
        action_required = int(row.get("critical") or 0) + int(row.get("warning") or 0)
        return {
            "total": int(row.get("total") or 0),
            "unread": int(row.get("unread") or 0),
            "critical": int(row.get("critical") or 0),
            "warning": int(row.get("warning") or 0),
            "info": int(row.get("info") or 0),
            "action_required": action_required,
        }

    @staticmethod
    async def mark_read(notification_id: str):
        object_id = NotificationRepository._to_object_id(notification_id)
        if not object_id:
            return None
        return await collection.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )

    @staticmethod
    async def mark_all_read(role: str, email: str):
        query = NotificationRepository._build_user_query(role, email)
        query["is_read"] = False
        return await collection.update_many(
            query,
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )

    @staticmethod
    async def list_logs(limit: int = 500):
        cursor = (
            collection.find({}).sort("created_at", -1).limit(max(1, min(limit, 2000)))
        )
        return await cursor.to_list(length=None)

    @staticmethod
    def _build_user_query(role: str, email: str):
        return {
            "$or": [
                {"target_roles": {"$in": [role]}},
                {"target_users": {"$in": [email]}},
            ]
        }
