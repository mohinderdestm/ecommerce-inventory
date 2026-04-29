from fastapi import APIRouter, status,Depends
from app.schemas.sales_order_schema import OrderCreate,OrderStatusUpdate
from app.services.sales_order_service import OrderService
from app.repositories.sales_order_repository import OrderRepository
from app.core.dependencies import get_current_user


router = APIRouter(prefix="/orders", tags=["Orders"])

repo = OrderRepository()
service = OrderService(repo)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(payload: OrderCreate, user=Depends(get_current_user)):
    return await service.create_order(payload,user)


@router.get("/", status_code=status.HTTP_200_OK)
async def get_orders():
    return await service.get_orders()

@router.put("/{order_id}/status")
async def update_order_status(order_id: str, payload: OrderStatusUpdate):
    return await service.update_status(order_id, payload.status)