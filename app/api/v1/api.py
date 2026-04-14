from fastapi import APIRouter
from app.api.v1.routes import auth, products, users, health, supplier_routes, order

api_router = APIRouter()


api_router.include_router(auth.router)
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(products.router)
api_router.include_router(supplier_routes.router)
api_router.include_router(order.router)
