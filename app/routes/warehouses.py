from fastapi import APIRouter, Depends
from app.schemas.warehouse_schema import WarehouseCreate, WarehouseUpdate
from app.repositories.warehouse_repository import WarehouseRepository
from app.services.warehouse_service import WarehouseService
from app.core.dependencies import required_roles
from app.core.database import get_db

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])

@router.post("/")
async def create_warehouse(
    payload: WarehouseCreate,
    db=Depends(get_db),
    user=Depends(required_roles(["admin", "inventory_manager"]))
):
    service = WarehouseService(WarehouseRepository(db))
    return await service.create_warehouse(payload,user)


@router.get("/")
async def list_warehouses(
    db=Depends(get_db),
    user=Depends(required_roles(["admin", "inventory_manager"]))
):
    service = WarehouseService(WarehouseRepository(db))
    return await service.list_warehouses()


@router.get("/{warehouse_id}")
async def get_warehouse(
    warehouse_id: str,
    db=Depends(get_db)
):
    service = WarehouseService(WarehouseRepository(db))
    return await service.get_warehouse(warehouse_id)


@router.put("/{warehouse_id}")
async def update_warehouse(
    warehouse_id: str,
    payload: WarehouseUpdate,
    db=Depends(get_db),
    user=Depends(required_roles(["admin"]))
):
    service = WarehouseService(WarehouseRepository(db))
    return await service.update_warehouse(warehouse_id, payload)


@router.delete("/{warehouse_id}")
async def delete_warehouse(
    warehouse_id: str,
    db=Depends(get_db),
    user=Depends(required_roles(["admin"]))
):
    service = WarehouseService(WarehouseRepository(db))
    return await service.delete_warehouse(warehouse_id)

@router.post("/{warehouse_id}/assign-staff")
async def assign_staff(
    warehouse_id: str,
    user_id: str,
    db=Depends(get_db),
    user=Depends(required_roles(["admin"]))
):
    repo = WarehouseRepository(db)

    await repo.add_staff(warehouse_id, user_id)

    return {"message": "Staff assigned successfully"}

@router.get("/{warehouse_id}/inventory")
async def get_warehouse_inventory(
    warehouse_id: str,
    db=Depends(get_db),
    user=Depends(required_roles(["admin", "inventory_manager"]))
):
    service = WarehouseService(WarehouseRepository(db))
    return await service.get_warehouse_inventory(warehouse_id)

