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

        def clean(value, fallback="N/A"):
            if value in [None, "", "string", "null"]:
                return fallback
            return value

        address = warehouse.get("address") or {}

        return {
            "id": str(warehouse["_id"]),
            "name": clean(warehouse.get("name")),
            "code": clean(warehouse.get("code")),
            "email": clean(warehouse.get("email")),
            "phone": clean(warehouse.get("phone")),
            "address": {
                "street": clean(address.get("street")),
                "city": clean(address.get("city")),
                "state": clean(address.get("state")),
                "country": clean(address.get("country")),
                "pincode": clean(address.get("pincode")),
            },
            "capacity": (
                warehouse.get("capacity")
                if warehouse.get("capacity") is not None
                else 0
            ),
            "is_active": warehouse.get("is_active", True),
            "created_by": (
                {
                    "id": warehouse.get("created_by", {}).get("id"),
                    "name": clean(warehouse.get("created_by", {}).get("name")),
                    "email": clean(warehouse.get("created_by", {}).get("email")),
                }
                if warehouse.get("created_by")
                else {}
            ),
            "created_at": warehouse.get("created_at"),
            "updated_at": warehouse.get("updated_at"),
        }
