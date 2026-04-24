def inventory_movement_model(movement: dict) -> dict:
    performed_by = movement.get("performed_by") or {}

    return {
        "id": str(movement["_id"]),
        "product_id": (
            str(movement.get("product_id")) if movement.get("product_id") else None
        ),
        "product_name": movement.get("product_name"),
        "variant_sku": movement.get("variant_sku"),
        "variant_name": movement.get("variant_name"),
        "warehouse_id": (
            str(movement.get("warehouse_id")) if movement.get("warehouse_id") else None
        ),
        "warehouse_name": movement.get("warehouse_name"),
        "movement_type": movement.get("movement_type"),
        "quantity": int(movement.get("quantity") or 0),
        "delta": int(movement.get("delta") or 0),
        "reference_type": movement.get("reference_type"),
        "reference_id": movement.get("reference_id"),
        "performed_by": {
            "id": performed_by.get("id"),
            "name": performed_by.get("name"),
            "email": performed_by.get("email"),
            "role": performed_by.get("role"),
        },
        "remarks": movement.get("remarks"),
        "created_at": movement.get("created_at"),
    }
