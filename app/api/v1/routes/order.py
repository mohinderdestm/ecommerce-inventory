from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order_service import OrderService
from app.utils.dependencies import get_current_user
from typing import List

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse)
async def create_new_order(
    order_data: OrderCreate, current_user: dict = Depends(get_current_user)
):

    return await OrderService.place_order(order_data, current_user)


@router.get("/", response_model=List[OrderResponse])
async def get_orders(current_user: dict = Depends(get_current_user)):

    return await OrderService.get_orders_for_user(current_user)


@router.post("/{order_id}/cancel")
async def cancel_order(order_id: str, current_user: dict = Depends(get_current_user)):
    return await OrderService.cancel_order(order_id, current_user)


@router.put("/{order_id}/confirm", status_code=status.HTTP_200_OK)
async def confirm_user_order(
    order_id: str, current_user: dict = Depends(get_current_user)
):

    return await OrderService.confirm_order(order_id, current_user)
