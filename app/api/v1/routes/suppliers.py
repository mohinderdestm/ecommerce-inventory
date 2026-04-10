from fastapi import APIRouter, Depends, Query, Form
from typing import Optional
from app.services.supplier_service import SupplierService
from app.core.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.post("/")
async def create_supplier(
    name: str = Form(...),
    contact_person: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    address: str = Form(""),
    gst_id: str = Form(""),
    payment_terms: str = Form("Net 30"),
    user=Depends(require_roles(["admin"]))
):
    data = {
        "name": name, "contact_person": contact_person,
        "phone": phone, "email": email, "address": address,
        "gst_id": gst_id, "payment_terms": payment_terms
    }
    return await SupplierService.create(data, user["user_id"])


@router.get("/")
async def get_suppliers(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    user=Depends(get_current_user)
):
    return await SupplierService.get_all(page, limit, status)


@router.get("/search")
async def search_suppliers(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user=Depends(get_current_user)
):
    return await SupplierService.search(q, page, limit)


@router.get("/{supplier_id}")
async def get_supplier(supplier_id: str, user=Depends(get_current_user)):
    return await SupplierService.get_by_id(supplier_id)


@router.get("/{supplier_id}/products")
async def get_supplier_products(
    supplier_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50),
    user=Depends(get_current_user)
):
    return await SupplierService.get_products(supplier_id, page, limit)


@router.get("/{supplier_id}/performance")
async def get_supplier_performance(
    supplier_id: str,
    user=Depends(require_roles(["admin", "supplier"]))
):
    return await SupplierService.get_performance(supplier_id)


@router.put("/{supplier_id}")
async def update_supplier(
    supplier_id: str,
    name: Optional[str] = Form(None),
    contact_person: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    gst_id: Optional[str] = Form(None),
    payment_terms: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    user=Depends(require_roles(["admin"]))
):
    data = {
        "name": name, "contact_person": contact_person, "phone": phone,
        "email": email, "address": address, "gst_id": gst_id,
        "payment_terms": payment_terms, "status": status
    }
    return await SupplierService.update(supplier_id, data)


@router.patch("/{supplier_id}/rating")
async def update_supplier_rating(
    supplier_id: str,
    rating: float = Form(..., ge=0, le=5),
    user=Depends(require_roles(["admin"]))
):
    return await SupplierService.update_rating(supplier_id, rating)


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: str,
    user=Depends(require_roles(["admin"]))
):
    return await SupplierService.delete(supplier_id)