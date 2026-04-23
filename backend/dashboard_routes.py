from fastapi import APIRouter
from database import products_collection, orders_collection

router = APIRouter()

@router.get("/dashboard")
async def dashboard():

    total_products = await products_collection.count_documents({})
    total_orders = await orders_collection.count_documents({})

    orders = await orders_collection.find().to_list(100)
    revenue = sum(o.get("total", 0) for o in orders)

    # 🔥 LOW STOCK (example: stock < 5)
    low_stock = 0
    products = await products_collection.find().to_list(100)

    for p in products:
        for v in p.get("variants", []):
            if v.get("stock", 0) < 5:
                low_stock += 1

    # 🔥 RECENT ORDERS
    recent_orders = [
        {
            "id": str(o["_id"]),
            "customer": o.get("customer_name", "Unknown"),
            "total": o.get("total", 0)
        }
        for o in orders[:5]
    ]

    return {
        "products": total_products,
        "orders": total_orders,
        "revenue": revenue,
        "lowStock": low_stock,
        "recentOrders": recent_orders
    }