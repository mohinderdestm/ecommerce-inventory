from bson import ObjectId


def product_model(product) -> dict:
    return {
        "id": str(product["_id"]),
        "name": product.get("name") or product.get("title") or "Unnamed Product",
        "description": product.get("description", ""),
        "category": product.get("category", ""),
        "selling_price": product.get("selling_price") or product.get("price") or 0,
        "reorder_level": product.get("reorder_level") or product.get("quantity") or 0,
        "image": product.get("image") or None,
        "status": product.get("status", "active"),
    }
