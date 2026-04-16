from datetime import datetime


class WarehouseStaffModel:

    @staticmethod
    def create_dict(warehouse, staff):
        return {
            "warehouse_id": str(warehouse["_id"]),
            "warehouse_name": warehouse.get("name"),
            "warehouse_city": warehouse.get("city"),
            "warehouse_code": warehouse.get("code"),
            "staff_id": str(staff["_id"]),
            "staff_name": staff.get("name"),
            "staff_email": staff.get("email"),
            "staff_phone": staff.get("phone"),
            "assigned_at": datetime.utcnow(),
        }

    @staticmethod
    def response(data):
        return {
            "id": str(data["_id"]),
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
            },
            "assigned_at": data.get("assigned_at"),
        }
