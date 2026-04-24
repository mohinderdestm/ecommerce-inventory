from fastapi import APIRouter
from app.api.v1.routes import (
    auth,
    products,
    staff_routes,
    users,
    health,
    supplier_routes,
    order,
    warehouse_routes,
    warehouse_staff_routes,
    warehouse_stock_routes,
    inventory_movement_routes,
    purchase_order_routes,
    notification_routes,
)

api_router = APIRouter()


api_router.include_router(auth.router)
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(products.router)
api_router.include_router(supplier_routes.router)
api_router.include_router(order.router)
api_router.include_router(warehouse_routes.router)
api_router.include_router(warehouse_staff_routes.router)
api_router.include_router(staff_routes.router)
api_router.include_router(warehouse_stock_routes.router)
api_router.include_router(inventory_movement_routes.router)
api_router.include_router(purchase_order_routes.router)
api_router.include_router(notification_routes.router)
