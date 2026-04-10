from datetime import datetime
from bson import ObjectId

class UserModel:

    @staticmethod
    def create_user_dict(data: dict):
        return {
            "name": data.get("name"),
            "email": data.get("email"),
            "password": data.get("password"),
            "role": data.get("role"),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

    @staticmethod
    def serialize(user) -> dict:
        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "is_active": user["is_active"],
            "created_at": user["created_at"]
        }