from bson import ObjectId


def order_model(order) -> dict:
    return {
        "id": str(order["_id"]),
        "customer_name": order.get("customer_name"),
        "customer_email": order.get("customer_email"),
        "shipping_address": order.get("shipping_address"),
        "payment_method": order.get("payment_method"),
        "order_reference": order.get("order_reference"),
        "items": [
            {
                "product_id": str(item["product_id"]),
                "variant_sku": item.get("variant_sku"),
                "warehouse_id": item.get("warehouse_id"),
                "name": item.get("name"),
                "quantity": item.get("quantity"),
                "price_at_purchase": item.get("price_at_purchase"),
                "supplier_email": item.get("supplier_email"),
            }
            for item in order.get("items", [])
        ],
        "total_amount": order.get("total_amount"),
        "status": order.get("status", "pending"),
        "created_at": order.get("created_at"),
        "user_details": order.get("user_details"),
        "confirmation_email_sent": order.get("confirmation_email_sent"),
    }
