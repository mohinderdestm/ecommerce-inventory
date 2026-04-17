from fastapi import APIRouter, Depends
from app.schemas.warehouse_stock_schema import *
from app.services.warehouse_stock_service import WarehouseStockService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/warehouse-stock", tags=["Warehouse Stock"])


@router.post("/assign")
async def assign_stock(data: AssignStockSchema, user=Depends(get_current_user)):
    return await WarehouseStockService.assign_stock(data, user)


@router.get("/{warehouse_id}")
async def get_stock(warehouse_id: str, user=Depends(get_current_user)):
    return await WarehouseStockService.get_warehouse_stock(warehouse_id)


@router.put("/{warehouse_id}/{sku}")
async def update_stock(
    warehouse_id: str, sku: str, data: UpdateStockSchema, user=Depends(get_current_user)
):
    return await WarehouseStockService.update_stock(
        warehouse_id, sku, data.quantity, user
    )


@router.post("/transfer")
async def transfer_stock(data: TransferStockSchema, user=Depends(get_current_user)):
    return await WarehouseStockService.transfer_stock(data, user)
