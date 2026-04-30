from datetime import datetime


class WarehouseStaffModel:

    @staticmethod
    def create_dict(warehouse, staff):
        return {
            "warehouse_id": str(warehouse["_id"]),
            "warehouse_name": warehouse.get("name"),
            "warehouse_city": (warehouse.get("address") or {}).get("city"),
            "warehouse_code": warehouse.get("code"),
            "staff_id": str(staff["_id"]),
            "staff_name": staff.get("name"),
            "staff_email": staff.get("email"),
            "staff_phone": staff.get("phone"),
            "staff_role": staff.get("role"),
            "staff_is_active": staff.get("is_active", True),
            "assigned_at": datetime.utcnow(),
        }

    @staticmethod
    def response(data):
        return {
            "id": str(data["_id"]),
            "warehouse_id": data.get("warehouse_id"),
            "warehouse_name": data.get("warehouse_name"),
            "warehouse_code": data.get("warehouse_code"),
            "staff_id": data.get("staff_id"),
            "staff_name": data.get("staff_name"),
            "staff_email": data.get("staff_email"),
            "staff_phone": data.get("staff_phone"),
            "staff_role": data.get("staff_role"),
            "staff_is_active": data.get("staff_is_active"),
            "warehouse": {
                "id": data.get("warehouse_id"),
                "name": data.get("warehouse_name"),
                "city": data.get("warehouse_city"),
                "code": data.get("warehouse_code"),
            },
            "staff": {
                "id": data.get("staff_id"),
                "name": data.get("staff_name"),
                "email": data.get("staff_email"),
                "phone": data.get("staff_phone"),
                "role": data.get("staff_role"),
                "is_active": data.get("staff_is_active"),
            },
            "assigned_at": data.get("assigned_at"),
        }
