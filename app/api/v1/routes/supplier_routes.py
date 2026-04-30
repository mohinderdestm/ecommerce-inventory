from fastapi import APIRouter, HTTPException, Depends
from app.schemas.supplier_schema import SupplierCreate, SupplierUpdate
from app.services.supplier_service import SupplierService
from app.utils.dependencies import (
    get_current_user,
    get_request_audit_context,
    require_role,
)

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])

service = SupplierService()


@router.post("/")
async def create_supplier(
    supplier: SupplierCreate,
    user=Depends(require_role(["admin", "supplier"])),
    audit_context=Depends(get_request_audit_context),
):
    return {"id": await service.create_supplier(supplier, user, audit_context)}


@router.get("/")
async def get_suppliers(user=Depends(get_current_user)):
    return await service.get_suppliers()


@router.get("/{supplier_id}")
async def get_supplier(supplier_id: str, user=Depends(get_current_user)):
    try:
        return await service.get_supplier(supplier_id)
    except:
        raise HTTPException(status_code=404, detail="Supplier not found")


@router.patch("/{supplier_id}")
async def update_supplier(
    supplier_id: str,
    supplier: SupplierUpdate,
    user=Depends(require_role(["admin", "supplier"])),
    audit_context=Depends(get_request_audit_context),
):
    try:
        return await service.update_supplier(supplier_id, supplier, user, audit_context)
    except:
        raise HTTPException(status_code=404, detail="Supplier not found")


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: str,
    user=Depends(require_role(["admin", "supplier"])),
    audit_context=Depends(get_request_audit_context),
):
    await service.delete_supplier(supplier_id, user, audit_context)
    return {"message": "Supplier deleted"}
