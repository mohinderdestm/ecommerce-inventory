from fastapi import APIRouter, Depends
from app.schemas.warehouse_schema import WarehouseCreate, WarehouseUpdate
from app.services.warehouse_service import WarehouseService
from app.utils.dependencies import get_current_user
from app.schemas.warehouse_schema import BulkWarehouseCreate

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])


@router.post("/")
async def create_warehouse(data: WarehouseCreate, user=Depends(get_current_user)):
    return await WarehouseService.create_warehouse(data, user)


@router.get("/")
async def get_all_warehouses(user=Depends(get_current_user)):
    return await WarehouseService.get_all_warehouses(user)


@router.get("/{warehouse_id}")
async def get_warehouse(warehouse_id: str, user=Depends(get_current_user)):
    return await WarehouseService.get_warehouse(warehouse_id, user)


@router.put("/{warehouse_id}")
async def update_warehouse(
    warehouse_id: str, data: WarehouseUpdate, user=Depends(get_current_user)
):
    return await WarehouseService.update_warehouse(warehouse_id, data, user)


@router.delete("/{warehouse_id}")
async def delete_warehouse(warehouse_id: str, user=Depends(get_current_user)):
    return await WarehouseService.delete_warehouse(warehouse_id, user)


@router.post("/bulk")
async def bulk_create_warehouses(
    data: BulkWarehouseCreate, user=Depends(get_current_user)
):
    return await WarehouseService.bulk_create_warehouses(data, user)
