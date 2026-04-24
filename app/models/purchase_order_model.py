def purchase_order_model(order: dict) -> dict:
    created_by = order.get("created_by") or {}
    approved_by = order.get("approved_by") or {}
    rejected_by = order.get("rejected_by") or {}

    return {
        "id": str(order["_id"]),
        "po_number": order.get("po_number"),
        "supplier_email": order.get("supplier_email"),
        "supplier_name": order.get("supplier_name"),
        "status": order.get("status"),
        "items": order.get("items", []),
        "invoice_metadata": order.get("invoice_metadata", {}),
        "receipts": order.get("receipts", []),
        "notes": order.get("notes"),
        "created_by": created_by,
        "approved_by": approved_by,
        "rejected_by": rejected_by,
        "submitted_at": order.get("submitted_at"),
        "approved_at": order.get("approved_at"),
        "rejected_at": order.get("rejected_at"),
        "received_at": order.get("received_at"),
        "created_at": order.get("created_at"),
        "updated_at": order.get("updated_at"),
    }
