from fastapi import APIRouter, Depends
from app.schemas.purchase_order_schema import PurchaseCreate,PurchaseStatusUpdate,ReceiveItems,InvoiceData
from app.services.purchase_order_service import PurchaseService
from app.repositories.purchase_order_repository import PurchaseRepository
from app.core.database import get_db

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


def get_service(db=Depends(get_db)):
    repo = PurchaseRepository(db)
    return PurchaseService(repo)


# ✅ CREATE PO
@router.post("/")
async def create_po(payload: PurchaseCreate, service=Depends(get_service)):
    return await service.create_po(payload)


# ✅ LIST PO
@router.get("/")
async def list_po(service=Depends(get_service)):
    return await service.list_po()


# ✅ UPDATE STATUS
@router.put("/{po_id}/status")
async def update_status(
    po_id: str,
    payload: PurchaseStatusUpdate,
    service=Depends(get_service)
):
    return await service.update_status(po_id, payload.status)


# ✅ RECEIVE ITEMS
@router.put("/{po_id}/receive")
async def receive_items(
    po_id: str,
    payload: ReceiveItems,
    service=Depends(get_service)
):
    return await service.receive_items(po_id, payload)


# ✅ ADD INVOICE
@router.put("/{po_id}/invoice")
async def attach_invoice(
    po_id: str,
    payload: InvoiceData,   # 🔥 THIS IS THE FIX
    service=Depends(get_service)
):
    return await service.attach_invoice(
        po_id,
        payload.invoice_number,
        payload.invoice_date
    )