from datetime import datetime


class StaffModel:

    @staticmethod
    def create_dict(data: dict, user: dict):
        return {
            "name": data.get("name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "role": data.get("role"),
            "is_active": True,
            "created_by": {
                "id": user.get("id"),
                "name": user.get("name"),
                "email": user.get("email"),
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    @staticmethod
    def response(data):
        return {
            "id": str(data["_id"]),
            "name": data.get("name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "role": data.get("role"),
            "is_active": data.get("is_active"),
            "created_by": data.get("created_by"),
            "created_at": data.get("created_at"),
        }
