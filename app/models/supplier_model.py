from datetime import datetime

class SupplierModel:
    @staticmethod
    def create(data: dict, user_id: str) -> dict:
        return {
            "name": data["name"],
            "contact_person": data.get("contact_person", ""),
            "phone": data.get("phone", ""),
            "email": data.get("email", ""),
            "address": data.get("address", ""),
            "gst_id": data.get("gst_id", ""),
            "payment_terms": data.get("payment_terms", "Net 30"),
            "rating": 0,
            "total_orders": 0,
            "total_amount": 0,
            "status": data.get("status", "active"),
            "created_by": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }