from bson import ObjectId


def product_model(product) -> dict:
    data = {
        "id": str(product["_id"]),
        "name": product.get("name") or product.get("title") or "Unnamed Product",
        "description": product.get("description", ""),
        "category": product.get("category", ""),
        "brand": product.get("brand", ""),
        "cost_price": product.get("cost_price", 0),
        "selling_price": product.get("selling_price") or product.get("price") or 0,
        "reorder_level": product.get("reorder_level") or product.get("quantity") or 0,
        "low_stock_threshold": product.get("low_stock_threshold", 5),
        "tax": product.get("tax", 0),
        "unit": product.get("unit", "piece"),
        "expiry_date": product.get("expiry_date"),
        "sku": product.get("sku", "N/A"),
        "image": product.get("image") or None,
        "status": product.get("status", "active"),
        "variants": product.get("variants", []),
        "supplier_email": product.get("supplier_email"),
    }

    if "supplier_details" in product:
        supplier = product["supplier_details"]
        if isinstance(supplier, list) and len(supplier) > 0:
            supp = supplier[0]
            data["supplier_details"] = {
                "id": str(supp["_id"]),
                "name": supp.get("name"),
                "contact_person": supp.get("contact_person"),
                "phone": supp.get("phone"),
                "email": supp.get("email"),
                "address": supp.get("address"),
                "gst": supp.get("gst"),
                "payment_terms": supp.get("payment_terms"),
                "rating": supp.get("rating", 0),
                "is_active": supp.get("is_active", True),
            }
    return data
