from datetime import datetime


class WarehouseModel:

    @staticmethod
    def warehouse_dict(data: dict, user: dict) -> dict:
        return {
            "name": data.get("name"),
            "code": data.get("code"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "address": {
                "street": data.get("street"),
                "city": data.get("city"),
                "state": data.get("state"),
                "country": data.get("country"),
                "pincode": data.get("pincode"),
            },
            "capacity": data.get("capacity", 0),
            "is_active": data.get("is_active", True),
            "created_by": {
                "id": user.get("id"),
                "name": user.get("name"),
                "email": user.get("email"),
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    @staticmethod
    def response(warehouse) -> dict:
        return {
            "id": str(warehouse["_id"]),
            "name": warehouse.get("name"),
            "code": warehouse.get("code"),
            "email": warehouse.get("email"),
            "phone": warehouse.get("phone"),
            "address": warehouse.get("address"),
            "capacity": warehouse.get("capacity"),
            "is_active": warehouse.get("is_active"),
            "created_by": warehouse.get("created_by"),
            "created_at": warehouse.get("created_at"),
            "updated_at": warehouse.get("updated_at"),
        }
