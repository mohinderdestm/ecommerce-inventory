from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.schemas.purchase_order_schema import (
    PurchaseOrderCreate,
    PurchaseOrderAddItems,
    PurchaseOrderInvoiceMetadata,
    PurchaseOrderReceive,
    PurchaseOrderActionNote,
)
from app.services.purchase_order_service import PurchaseOrderService
from app.utils.dependencies import get_current_user


router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


@router.post("/")
async def create_purchase_order(
    data: PurchaseOrderCreate, user=Depends(get_current_user)
):
    return await PurchaseOrderService.create_draft(data, user)


@router.get("/")
async def get_purchase_orders(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    user=Depends(get_current_user),
):
    return await PurchaseOrderService.list_purchase_orders(
        user, status=status, limit=limit
    )


@router.get("/{po_id}")
async def get_purchase_order(po_id: str, user=Depends(get_current_user)):
    return await PurchaseOrderService.get_purchase_order(po_id, user)


@router.post("/{po_id}/items")
async def add_items(
    po_id: str, data: PurchaseOrderAddItems, user=Depends(get_current_user)
):
    return await PurchaseOrderService.add_items(po_id, data, user)


@router.put("/{po_id}/submit")
async def submit_purchase_order(
    po_id: str, data: PurchaseOrderActionNote, user=Depends(get_current_user)
):
    return await PurchaseOrderService.submit(po_id, user, remarks=data.remarks)


@router.put("/{po_id}/approve")
async def approve_purchase_order(
    po_id: str, data: PurchaseOrderActionNote, user=Depends(get_current_user)
):
    return await PurchaseOrderService.approve(po_id, user, remarks=data.remarks)


@router.put("/{po_id}/reject")
async def reject_purchase_order(
    po_id: str, data: PurchaseOrderActionNote, user=Depends(get_current_user)
):
    return await PurchaseOrderService.reject(po_id, user, remarks=data.remarks)


@router.put("/{po_id}/cancel")
async def cancel_purchase_order(
    po_id: str, data: PurchaseOrderActionNote, user=Depends(get_current_user)
):
    return await PurchaseOrderService.cancel(po_id, user, remarks=data.remarks)


@router.put("/{po_id}/invoice")
async def update_invoice(
    po_id: str, data: PurchaseOrderInvoiceMetadata, user=Depends(get_current_user)
):
    return await PurchaseOrderService.update_invoice_metadata(po_id, data, user)


@router.post("/{po_id}/receive")
async def receive_purchase_order(
    po_id: str, data: PurchaseOrderReceive, user=Depends(get_current_user)
):
    return await PurchaseOrderService.receive(po_id, data, user)
