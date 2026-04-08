from datetime import datetime


def supplier_model(supplier: dict) -> dict:
    return {
        "name": supplier.get("name"),
        "contact_person": supplier.get("contact_person"),
        "phone": supplier.get("phone"),
        "email": supplier.get("email"),
        "address": supplier.get("address"),
        "gst": supplier.get("gst"),
        "payment_terms": supplier.get("payment_terms"),
        "rating": supplier.get("rating", 0),
        "is_active": supplier.get("is_active", True),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
