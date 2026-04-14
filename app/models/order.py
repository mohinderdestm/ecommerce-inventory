from bson import ObjectId


def order_model(order) -> dict:
    return {
        "id": str(order["_id"]),
        "customer_name": order.get("customer_name"),
        "items": [
            {
                "product_id": str(item["product_id"]),
                "name": item.get("name"),
                "quantity": item.get("quantity"),
                "price_at_purchase": item.get("price_at_purchase"),
            }
            for item in order.get("items", [])
        ],
        "total_amount": order.get("total_amount"),
        "status": order.get("status", "pending"),
        "created_at": order.get("created_at"),
    }
