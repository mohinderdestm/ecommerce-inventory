from datetime import datetime
from app.core.database import db

class NotificationService:

    @staticmethod
    async def create(data: dict):
        await db["notifications"].insert_one({
            **data,
            "is_read": False,
            "created_at": datetime.utcnow()
        })

    # @staticmethod
    # async def get(user_id: str = None, role: str = None):
    #     query = {}

    #     if user_id:
    #         query["user_id"] = user_id
    #     if role:
    #         query["role"] = role

    #     data = await db["notifications"].find(query).sort("created_at", -1).to_list(100)

    #     for d in data:
    #         d["id"] = str(d["_id"])
    #         del d["_id"]

    #     return data

    @staticmethod
    async def get(user_id: str = None, role: str = None):
        query = {}

        # ✅ ADMIN: only specific notifications
        if role == "admin":
           query["role"] = "admin"
           query["type"] = {
             "$in": ["low_stock", "order_confirmed", "order_cancelled"]
        }

          # ✅ USER: only their notifications
        if user_id:
           query["user_id"] = user_id

        data = await db["notifications"].find(query).sort("created_at", -1).to_list(100)

        for d in data:
           d["id"] = str(d["_id"])
           del d["_id"]

        return data

    @staticmethod
    async def mark_all_read(user_id: str = None, role: str = None):
        query = {}

        if user_id:
            query["user_id"] = user_id
        elif role:
            query["role"] = role

        await db["notifications"].update_many(
            query,
            {"$set": {"is_read": True}}
        )